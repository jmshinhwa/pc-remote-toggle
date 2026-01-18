"""
Windows 시스템 트레이 앱 - 서비스 매니저
파일시스템, 데스크탑 커맨더, 깃허브 오토싱크 서비스 ON/OFF 관리
"""

import subprocess
import os
import signal
import pystray
from PIL import Image, ImageDraw
import psutil


class ServiceManager:
    def __init__(self):
        """서비스 매니저 초기화"""
        self.services = {
            "filesystem": {
                "name": "파일시스템",
                "port": 8765,
                "command": r'"C:\Program Files\Python313\python.exe" "C:\Users\user\Desktop\pc-remote-toggle\filesystem_server.py"',
                "process": None
            },
            "commander": {
                "name": "데스크탑 커맨더",
                "port": 8766,
                "command": r'"C:\Program Files\Python313\python.exe" "C:\Users\user\Desktop\pc-remote-toggle\commander_server.py"',
                "process": None
            },
            "autosync": {
                "name": "깃허브 오토싱크",
                "port": None,
                "command": r"C:\Users\user\Desktop\V128프로젝트\V128_Sync.exe",
                "process_name": "V128_Sync",
                "process": None
            }
        }
    
    def create_icon(self, color='gray'):
        """트레이 아이콘 생성"""
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)
        draw.ellipse([8, 8, 56, 56], fill=color, outline='black', width=2)
        return image
    
    def check_port_status(self, port):
        """포트가 LISTENING 상태인지 확인"""
        try:
            result = subprocess.run(
                f'netstat -ano | findstr ":{port}" | findstr "LISTENING"',
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            return bool(result.stdout.strip())
        except Exception:
            return False
    
    def check_process_status(self, process_name):
        """프로세스명으로 실행 여부 확인"""
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                    return True
            return False
        except Exception:
            return False
    
    def get_service_status(self, service_key):
        """서비스 상태 확인 (True=실행중, False=중지)"""
        service = self.services[service_key]
        
        if service.get("port"):
            # 포트 기반 서비스
            return self.check_port_status(service["port"])
        elif service.get("process_name"):
            # 프로세스명 기반 서비스
            return self.check_process_status(service["process_name"])
        
        return False
    
    def get_pid_by_port(self, port):
        """포트를 사용하는 프로세스의 PID 찾기"""
        try:
            result = subprocess.run(
                f'netstat -ano | findstr ":{port}" | findstr "LISTENING"',
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            lines = result.stdout.strip().split('\n')
            for line in lines:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    return int(pid)
        except Exception:
            pass
        return None
    
    def get_pid_by_name(self, process_name):
        """프로세스명으로 PID 찾기"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                    return proc.info['pid']
        except Exception:
            pass
        return None
    
    def start_service(self, service_key):
        """서비스 시작"""
        service = self.services[service_key]
        
        # 이미 실행 중이면 무시
        if self.get_service_status(service_key):
            print(f"✅ {service['name']} 이미 실행 중")
            return True
        
        try:
            # 서비스 실행
            print(f"🚀 {service['name']} 시작 중...")
            
            # Windows에서 백그라운드 프로세스로 실행
            process = subprocess.Popen(
                service["command"],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            service["process"] = process
            print(f"✅ {service['name']} 시작됨 (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ {service['name']} 시작 실패: {e}")
            return False
    
    def stop_service(self, service_key):
        """서비스 종료"""
        service = self.services[service_key]
        
        # 실행 중이 아니면 무시
        if not self.get_service_status(service_key):
            print(f"✅ {service['name']} 이미 중지됨")
            return True
        
        try:
            print(f"🛑 {service['name']} 종료 중...")
            
            # PID 찾기
            pid = None
            if service.get("port"):
                pid = self.get_pid_by_port(service["port"])
            elif service.get("process_name"):
                pid = self.get_pid_by_name(service["process_name"])
            
            if pid:
                # Windows에서 프로세스 강제 종료
                try:
                    os.kill(pid, signal.SIGTERM)
                    print(f"✅ {service['name']} 종료됨 (PID: {pid})")
                except (OSError, PermissionError):
                    # SIGTERM이 안 되면 taskkill 사용
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, timeout=5)
                    print(f"✅ {service['name']} 강제 종료됨 (PID: {pid})")
                
                service["process"] = None
                return True
            else:
                print(f"⚠️ {service['name']} PID를 찾을 수 없음")
                return False
                
        except Exception as e:
            print(f"❌ {service['name']} 종료 실패: {e}")
            return False
    
    def toggle_service(self, service_key, icon):
        """서비스 ON/OFF 토글"""
        is_running = self.get_service_status(service_key)
        
        if is_running:
            self.stop_service(service_key)
        else:
            self.start_service(service_key)
        
        # 메뉴 갱신
        icon.update_menu()
    
    def get_menu_text(self, service_key):
        """메뉴 텍스트 생성 (서비스명 + 상태)"""
        service = self.services[service_key]
        is_running = self.get_service_status(service_key)
        
        status = "🔵" if is_running else "🔴"
        # 일정한 너비 유지를 위해 ljust 사용
        return f"{service['name']:<20} {status}"
    
    def quit_app(self, icon):
        """앱 종료 - 모든 서비스는 그대로 유지"""
        print("\n👋 ServiceManager 종료")
        icon.stop()
    
    def create_menu(self):
        """메뉴 생성"""
        return pystray.Menu(
            pystray.MenuItem(
                lambda _: self.get_menu_text("filesystem"),
                lambda icon, item: self.toggle_service("filesystem", icon)
            ),
            pystray.MenuItem(
                lambda _: self.get_menu_text("commander"),
                lambda icon, item: self.toggle_service("commander", icon)
            ),
            pystray.MenuItem(
                lambda _: self.get_menu_text("autosync"),
                lambda icon, item: self.toggle_service("autosync", icon)
            ),
            pystray.MenuItem("종료", self.quit_app)
        )
    
    def run(self):
        """트레이 앱 실행"""
        icon = pystray.Icon(
            "ServiceManager",
            self.create_icon('orange'),
            "Service Manager",
            menu=self.create_menu()
        )
        
        print("\n" + "="*50)
        print("🔧 Service Manager 시작됨!")
        print("시스템 트레이 아이콘을 우클릭하세요")
        print("="*50)
        
        # 초기 상태 출력
        print("\n📊 현재 서비스 상태:")
        for key, service in self.services.items():
            status = "🔵 실행중" if self.get_service_status(key) else "🔴 중지"
            print(f"  {service['name']}: {status}")
        print()
        
        icon.run()


if __name__ == "__main__":
    manager = ServiceManager()
    manager.run()
