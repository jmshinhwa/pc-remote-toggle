"""
Windows 시스템 트레이 앱 - 안정화 버전
통합 MCP 서버 + 깃허브 싱크 ON/OFF 관리

메뉴:
1. 외부접속허용 [ON/OFF] - 통합 MCP 서버
2. 깃허브싱크 [ON/OFF]
3. 종료 (모든 프로세스 정리)

기능:
- 중복 실행 방지 (Mutex)
- 종료 시 모든 하위 프로세스 정리
- 안정적인 ON/OFF 토글
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
            print("⚠️ ServiceManager가 이미 실행 중입니다.")
            sys.exit(0)
        
        return mutex  # mutex 객체 유지 (GC 방지)
    except ImportError:
        # pywin32가 없으면 lock file 방식 사용
        lock_file = os.path.join(os.environ.get('TEMP', '.'), 'ServiceManager.lock')
        
        if os.path.exists(lock_file):
            try:
                with open(lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                # 해당 PID가 실제로 실행 중인지 확인
                if psutil.pid_exists(old_pid):
                    try:
                        proc = psutil.Process(old_pid)
                        if 'ServiceManager' in proc.name() or 'python' in proc.name().lower():
                            print("⚠️ ServiceManager가 이미 실행 중입니다.")
                            sys.exit(0)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except (ValueError, IOError):
                pass
        
        # 새 lock file 생성
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        
        return lock_file


class ServiceManager:
    """안정화된 서비스 매니저"""
    
    def __init__(self):
        """서비스 매니저 초기화"""
        # 상태를 내부적으로 관리 (매번 체크하지 않음)
        self.service_states = {
            "mcp": False,
            "github_sync": False
        }
        
        self.services = {
            "mcp": {
                "name": "외부접속허용",
                "port": 8765,
                "command": [
                    sys.executable,  # 현재 Python 경로
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "unified_server.py")
                ],
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
            
            # 이미 프로세스가 있고 실행 중이면 스킵
            if service["process"] is not None:
                try:
                    if service["process"].poll() is None:
                        print(f"✅ {service['name']} 이미 실행 중")
                        self.service_states[service_key] = True
                        return True
                except:
                    pass
            
            try:
                print(f"🚀 {service['name']} 시작 중...")
                
                cmd = service["command"]
                if isinstance(cmd, list):
                    process = subprocess.Popen(
                        cmd,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    process = subprocess.Popen(
                        cmd,
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                
                service["process"] = process
                self.service_states[service_key] = True
                print(f"✅ {service['name']} 시작됨 (PID: {process.pid})")
                return True
                
            except Exception as e:
                print(f"❌ {service['name']} 시작 실패: {e}")
                self.service_states[service_key] = False
                return False
    
    def stop_service(self, service_key):
        """서비스 종료"""
        with self._lock:
            service = self.services[service_key]
            
            try:
                print(f"🛑 {service['name']} 종료 중...")
                
                # 1. 저장된 프로세스로 종료 시도
                if service["process"] is not None:
                    try:
                        service["process"].terminate()
                        service["process"].wait(timeout=3)
                        print(f"✅ {service['name']} 정상 종료됨")
                    except subprocess.TimeoutExpired:
                        service["process"].kill()
                        print(f"✅ {service['name']} 강제 종료됨")
                    except:
                        pass
                    service["process"] = None
                
                # 2. 포트로 프로세스 찾아서 종료 (백업)
                if service.get("port"):
                    self._kill_by_port(service["port"])
                
                # 3. 프로세스명으로 종료 (백업)
                if service.get("process_name"):
                    self._kill_by_name(service["process_name"])
                
                self.service_states[service_key] = False
                return True
                
            except Exception as e:
                print(f"❌ {service['name']} 종료 실패: {e}")
                self.service_states[service_key] = False
                return False
    
    def _kill_by_port(self, port):
        """포트로 프로세스 종료"""
        try:
            result = subprocess.run(
                f'netstat -ano | findstr ":{port}" | findstr "LISTENING"',
                shell=True, capture_output=True, text=True, timeout=3
            )
            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 5:
                    pid = int(parts[-1])
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, timeout=3)
        except:
            pass
    
    def _kill_by_name(self, process_name):
        """프로세스명으로 종료"""
        try:
            subprocess.run(f'taskkill /F /IM "{process_name}.exe"', shell=True, timeout=3)
        except:
            pass
    
    def toggle_service(self, service_key):
        """서비스 토글 (별도 스레드에서 실행)"""
        def do_toggle():
            is_running = self.service_states.get(service_key, False)
            
            if is_running:
                self.stop_service(service_key)
            else:
                self.start_service(service_key)
            
            # 메뉴 갱신
            if self.icon:
                self.icon.update_menu()
        
        # 별도 스레드에서 실행 (UI 블로킹 방지)
        thread = threading.Thread(target=do_toggle)
        thread.daemon = True
        thread.start()
    
    def get_menu_text(self, service_key):
        """메뉴 텍스트 생성"""
        service = self.services[service_key]
        is_running = self.service_states.get(service_key, False)
        status = "[ON]" if is_running else "[OFF]"
        return f"{service['name']} {status}"
    
    def cleanup_all(self):
        """모든 서비스 종료 (프로그램 종료 시)"""
        print("\n🧹 모든 서비스 정리 중...")
        
        for service_key in self.services:
            try:
                self.stop_service(service_key)
            except:
                pass
        
        print("✅ 정리 완료")
    
    def quit_app(self):
        """앱 종료"""
        print("\n👋 ServiceManager 종료")
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
        
        print("\n" + "="*50)
        print("🔧 Service Manager 시작됨!")
        print("시스템 트레이 아이콘을 우클릭하세요")
        print("="*50)
        
        print("\n📊 현재 서비스 상태:")
        for key, service in self.services.items():
            status = "🔴 중지"
            print(f"  {service['name']}: {status}")
        print()
        
        self.icon.run()


if __name__ == "__main__":
    # 중복 실행 방지
    mutex = check_single_instance()
    
    # 서비스 매니저 실행
    manager = ServiceManager()
    manager.run()
