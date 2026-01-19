"""
PC Remote Toggle - 외부접속 ON/OFF 트레이 앱
서버 1개 (포트 8765) + Host로 커넥터 구분

Claude.ai 웹에서 등록:
- pc.jmshinhwa.org/mcp?key=yoojin-secret-2026-xyz789 → Filesystem
- pc-cmd.jmshinhwa.org/mcp?key=yoojin-secret-2026-xyz789 → Commander
"""
import subprocess
import os
import sys
import time
import pystray
from PIL import Image, ImageDraw

# 설정
SERVER_PORT = 8765
SERVER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unified_server.py")
PYTHON_PATH = sys.executable  # 현재 Python 경로 사용


class PCRemoteToggle:
    """외부접속 ON/OFF 토글 - 단순화 버전"""
    
    def __init__(self):
        self.server_process = None
        self.is_running = False
    
    def create_icon(self, is_on):
        """트레이 아이콘 생성 (ON=초록, OFF=빨강)"""
        color = '#00CC00' if is_on else '#CC0000'
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)
        draw.ellipse([8, 8, 56, 56], fill=color, outline='#333333', width=2)
        return image
    
    def check_port(self):
        """포트 8765가 열려있는지 확인"""
        try:
            result = subprocess.run(
                f'netstat -ano | findstr ":{SERVER_PORT}" | findstr "LISTENING"',
                shell=True, capture_output=True, text=True, timeout=3
            )
            return bool(result.stdout.strip())
        except:
            return False
    
    def get_pid_by_port(self):
        """포트로 PID 찾기"""
        try:
            result = subprocess.run(
                f'netstat -ano | findstr ":{SERVER_PORT}" | findstr "LISTENING"',
                shell=True, capture_output=True, text=True, timeout=3
            )
            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 5:
                    return int(parts[-1])
        except:
            pass
        return None
    
    def start_server(self):
        """MCP 서버 시작"""
        if self.is_running or self.check_port():
            print("⚠️ 서버 이미 실행 중")
            self.is_running = True
            return True
        
        try:
            print(f"🚀 서버 시작 중... ({SERVER_SCRIPT})")
            
            self.server_process = subprocess.Popen(
                [PYTHON_PATH, SERVER_SCRIPT],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # 시작 대기 (최대 5초)
            for _ in range(10):
                time.sleep(0.5)
                if self.check_port():
                    self.is_running = True
                    print(f"✅ 서버 시작됨! (PID: {self.server_process.pid})")
                    print(f"   → pc.jmshinhwa.org/mcp (Filesystem)")
                    print(f"   → pc-cmd.jmshinhwa.org/mcp (Commander)")
                    return True
            
            print("⚠️ 서버 시작 확인 실패")
            return False
            
        except Exception as e:
            print(f"❌ 서버 시작 실패: {e}")
            return False
    
    def stop_server(self):
        """MCP 서버 종료"""
        if not self.is_running and not self.check_port():
            print("⚠️ 서버 이미 중지됨")
            return True
        
        try:
            print("🛑 서버 종료 중...")
            
            # 방법 1: 저장된 프로세스로 종료
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait(timeout=3)
                self.server_process = None
            
            # 방법 2: 포트로 PID 찾아서 종료
            pid = self.get_pid_by_port()
            if pid:
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, timeout=3)
            
            self.is_running = False
            print("✅ 서버 종료됨")
            return True
            
        except Exception as e:
            print(f"❌ 서버 종료 실패: {e}")
            # 강제 종료 시도
            try:
                pid = self.get_pid_by_port()
                if pid:
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True)
                self.is_running = False
            except:
                pass
            return False
    
    def toggle_server(self, icon, item):
        """서버 토글"""
        if self.is_running:
            self.stop_server()
        else:
            self.start_server()
        
        # 아이콘 & 메뉴 업데이트
        icon.icon = self.create_icon(self.is_running)
        icon.title = "외부접속 ON" if self.is_running else "외부접속 OFF"
        icon.update_menu()
    
    def get_menu_text(self):
        """메뉴 텍스트"""
        if self.is_running:
            return "🟢 외부접속 [ON] → 클릭하면 OFF"
        return "🔴 외부접속 [OFF] → 클릭하면 ON"
    
    def quit_app(self, icon):
        """앱 종료 (서버도 같이 종료)"""
        print("\n👋 종료 중...")
        self.stop_server()
        icon.stop()
    
    def run(self):
        """트레이 앱 실행"""
        # 시작 시 상태 확인
        self.is_running = self.check_port()
        
        icon = pystray.Icon(
            "PC-Remote",
            self.create_icon(self.is_running),
            "외부접속 ON" if self.is_running else "외부접속 OFF",
            menu=pystray.Menu(
                pystray.MenuItem(
                    lambda _: self.get_menu_text(),
                    self.toggle_server
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("종료", self.quit_app)
            )
        )
        
        print("\n" + "="*50)
        print("🖥️  PC Remote Toggle 시작!")
        print("="*50)
        print("시스템 트레이 아이콘을 우클릭하세요")
        print(f"현재 상태: {'🟢 ON' if self.is_running else '🔴 OFF'}")
        print("="*50 + "\n")
        
        icon.run()


if __name__ == "__main__":
    app = PCRemoteToggle()
    app.run()
