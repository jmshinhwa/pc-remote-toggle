"""
Windows 시스템 트레이 앱 - 안정화 버전
통합 MCP 서버 + 깃허브 싱크 ON/OFF 관리

메뉴:
1. 외부접속허용 [ON/OFF] - 통합 MCP 서버
2. 깃허브싱크 [ON/OFF]
3. 종료 (모든 프로세스 정리)
"""

import subprocess
import os
import sys
import signal
import atexit
import pystray
from PIL import Image, ImageDraw
import psutil
import threading

# ==================== 경로 설정 ====================
# PyInstaller 빌드 시에도 올바른 경로 찾기
if getattr(sys, 'frozen', False):
    # exe로 실행 중
    BASE_DIR = os.path.dirname(sys.executable)
    PYTHON_EXE = r"C:\Program Files\Python313\python.exe"
else:
    # 스크립트로 실행 중
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PYTHON_EXE = sys.executable

UNIFIED_SERVER = os.path.join(BASE_DIR, "unified_server.py")

# ==================== 중복 실행 방지 ====================
def check_single_instance():
    """이미 실행 중인지 확인 (Mutex 방식)"""
    try:
        import win32event
        import win32api
        from winerror import ERROR_ALREADY_EXISTS
        
        mutex_name = "Global\\ServiceManager_YooJin_Mutex"
        mutex = win32event.CreateMutex(None, False, mutex_name)
        
        if win32api.GetLastError() == ERROR_ALREADY_EXISTS:
            return None  # 이미 실행 중
        
        return mutex  # mutex 객체 유지 (GC 방지)
    except ImportError:
        # pywin32가 없으면 lock file 방식 사용
        lock_file = os.path.join(os.environ.get('TEMP', '.'), 'ServiceManager.lock')
        
        if os.path.exists(lock_file):
            try:
                with open(lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                if psutil.pid_exists(old_pid):
                    try:
                        proc = psutil.Process(old_pid)
                        if 'ServiceManager' in proc.name() or 'python' in proc.name().lower():
                            return None  # 이미 실행 중
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except (ValueError, IOError):
                pass
        
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        
        return lock_file


class ServiceManager:
    """안정화된 서비스 매니저"""
    
    def __init__(self):
        """서비스 매니저 초기화"""
        self.service_states = {
            "mcp": False,
            "github_sync": False
        }
        
        self.services = {
            "mcp": {
                "name": "외부접속허용",
                "port": 8765,
                "command": f'"{PYTHON_EXE}" "{UNIFIED_SERVER}"',
                "process": None
            },
            "github_sync": {
                "name": "깃허브싱크",
                "process_name": "V128_Sync",
                "command": r"C:\Users\user\Desktop\V128프로젝트\V128_Sync.exe",
                "process": None
            }
        }
        
        self.icon = None
        self._lock = threading.Lock()
        
        # 종료 시 정리 등록
        atexit.register(self.cleanup_all)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # 시작 시 실제 상태 확인
        self._sync_states()
    
    def _sync_states(self):
        """실제 프로세스 상태와 동기화"""
        # MCP 서버 (포트 체크)
        self.service_states["mcp"] = self._check_port(8765)
        # 깃허브싱크 (프로세스명 체크)
        self.service_states["github_sync"] = self._check_process_name("V128_Sync")
    
    def _check_port(self, port):
        """포트 사용 중인지 확인"""
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return True
        except (psutil.AccessDenied, psutil.Error):
            pass
        return False
    
    def _check_process_name(self, name):
        """프로세스명으로 실행 중인지 확인"""
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and name.lower() in proc.info['name'].lower():
                    return True
        except (psutil.Error, psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        return False
    
    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        self.cleanup_all()
        sys.exit(0)
    
    def create_icon(self, color='orange'):
        """트레이 아이콘 생성"""
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)
        draw.ellipse([8, 8, 56, 56], fill=color, outline='black', width=2)
        return image
    
    def start_service(self, service_key):
        """서비스 시작"""
        with self._lock:
            service = self.services[service_key]
            
            # 이미 실행 중이면 스킵
            if service_key == "mcp" and self._check_port(8765):
                self.service_states[service_key] = True
                return True
            if service_key == "github_sync" and self._check_process_name("V128_Sync"):
                self.service_states[service_key] = True
                return True
            
            try:
                process = subprocess.Popen(
                    service["command"],
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                service["process"] = process
                self.service_states[service_key] = True
                return True
                
            except Exception as e:
                self.service_states[service_key] = False
                return False
    
    def stop_service(self, service_key):
        """서비스 종료"""
        with self._lock:
            service = self.services[service_key]
            
            try:
                # 저장된 프로세스로 종료 시도
                if service["process"] is not None:
                    try:
                        service["process"].terminate()
                        service["process"].wait(timeout=3)
                    except:
                        try:
                            service["process"].kill()
                        except:
                            pass
                    service["process"] = None
                
                # 포트로 프로세스 찾아서 종료
                if service.get("port"):
                    self._kill_by_port(service["port"])
                
                # 프로세스명으로 종료
                if service.get("process_name"):
                    self._kill_by_name(service["process_name"])
                
                self.service_states[service_key] = False
                return True
                
            except Exception:
                self.service_states[service_key] = False
                return False
    
    def _kill_by_port(self, port):
        """포트로 프로세스 종료"""
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    try:
                        proc = psutil.Process(conn.pid)
                        proc.terminate()
                        proc.wait(timeout=3)
                    except:
                        subprocess.run(f"taskkill /F /PID {conn.pid}", shell=True, 
                                      creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
    
    def _kill_by_name(self, process_name):
        """프로세스명으로 종료"""
        try:
            subprocess.run(f'taskkill /F /IM "{process_name}.exe"', shell=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
    
    def toggle_service(self, service_key):
        """서비스 토글"""
        def do_toggle():
            # 현재 실제 상태 확인
            if service_key == "mcp":
                is_running = self._check_port(8765)
            else:
                is_running = self._check_process_name("V128_Sync")
            
            if is_running:
                self.stop_service(service_key)
            else:
                self.start_service(service_key)
            
            # 메뉴 갱신
            if self.icon:
                self.icon.update_menu()
        
        thread = threading.Thread(target=do_toggle)
        thread.daemon = True
        thread.start()
    
    def get_menu_text(self, service_key):
        """메뉴 텍스트 생성"""
        service = self.services[service_key]
        
        # 실제 상태 확인
        if service_key == "mcp":
            is_running = self._check_port(8765)
        else:
            is_running = self._check_process_name("V128_Sync")
        
        self.service_states[service_key] = is_running
        status = "[ON]" if is_running else "[OFF]"
        return f"{service['name']} {status}"
    
    def cleanup_all(self):
        """모든 서비스 종료"""
        for service_key in self.services:
            try:
                self.stop_service(service_key)
            except:
                pass
    
    def quit_app(self):
        """앱 종료"""
        self.cleanup_all()
        if self.icon:
            self.icon.stop()
    
    def create_menu(self):
        """메뉴 생성"""
        return pystray.Menu(
            pystray.MenuItem(
                lambda _: self.get_menu_text("mcp"),
                lambda: self.toggle_service("mcp")
            ),
            pystray.MenuItem(
                lambda _: self.get_menu_text("github_sync"),
                lambda: self.toggle_service("github_sync")
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("종료", lambda: self.quit_app())
        )
    
    def run(self):
        """트레이 앱 실행"""
        self.icon = pystray.Icon(
            "ServiceManager",
            self.create_icon('orange'),
            "Service Manager",
            menu=self.create_menu()
        )
        self.icon.run()


if __name__ == "__main__":
    # 중복 실행 방지
    mutex = check_single_instance()
    if mutex is None:
        sys.exit(0)
    
    # 서비스 매니저 실행
    manager = ServiceManager()
    manager.run()
