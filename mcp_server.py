"""
PC Remote MCP Server - Desktop Commander + Filesystem
Cloudflare 터널 + 트레이 토글 + MCP 프로토콜
"""

import subprocess
import threading
import os
import re
import time
from fastmcp import FastMCP
import pystray
from PIL import Image, ImageDraw
from config import API_KEY, TUNNEL_PORT

# === MCP 서버 설정 ===
mcp = FastMCP(name="PC-Remote")

# === Filesystem 도구들 ===
@mcp.tool()
def list_directory(path: str = "~") -> dict:
    """디렉토리 내용을 조회합니다."""
    try:
        path = os.path.expanduser(path)
        items = os.listdir(path)
        result = []
        for item in items:
            full_path = os.path.join(path, item)
            try:
                result.append({
                    "name": item,
                    "is_dir": os.path.isdir(full_path),
                    "size": os.path.getsize(full_path) if os.path.isfile(full_path) else 0
                })
            except:
                result.append({"name": item, "is_dir": False, "size": 0})
        return {"success": True, "path": path, "items": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def read_file(path: str) -> dict:
    """파일 내용을 읽습니다."""
    try:
        path = os.path.expanduser(path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"success": True, "path": path, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def write_file(path: str, content: str) -> dict:
    """파일에 내용을 씁니다."""
    try:
        path = os.path.expanduser(path)
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def delete_path(path: str) -> dict:
    """파일이나 폴더를 삭제합니다."""
    try:
        path = os.path.expanduser(path)
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            import shutil
            shutil.rmtree(path)
        return {"success": True, "deleted": path}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def move_path(src: str, dest: str) -> dict:
    """파일이나 폴더를 이동하거나 이름을 변경합니다."""
    try:
        src = os.path.expanduser(src)
        dest = os.path.expanduser(dest)
        import shutil
        shutil.move(src, dest)
        return {"success": True, "from": src, "to": dest}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def copy_path(src: str, dest: str) -> dict:
    """파일이나 폴더를 복사합니다."""
    try:
        src = os.path.expanduser(src)
        dest = os.path.expanduser(dest)
        import shutil
        if os.path.isfile(src):
            shutil.copy2(src, dest)
        else:
            shutil.copytree(src, dest)
        return {"success": True, "from": src, "to": dest}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def create_directory(path: str) -> dict:
    """폴더를 생성합니다."""
    try:
        path = os.path.expanduser(path)
        os.makedirs(path, exist_ok=True)
        return {"success": True, "created": path}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_file_info(path: str) -> dict:
    """파일이나 폴더의 상세 정보를 조회합니다."""
    try:
        path = os.path.expanduser(path)
        stat = os.stat(path)
        return {
            "success": True,
            "path": path,
            "exists": True,
            "is_file": os.path.isfile(path),
            "is_dir": os.path.isdir(path),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime
        }
    except FileNotFoundError:
        return {"success": True, "path": path, "exists": False}
    except Exception as e:
        return {"success": False, "error": str(e)}

# === Desktop Commander 도구들 ===
@mcp.tool()
def execute_command(command: str, cwd: str = "~", timeout: int = 60) -> dict:
    """쉘 명령어를 실행합니다."""
    try:
        cwd = os.path.expanduser(cwd)
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        return {
            "success": True,
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timeout ({timeout}s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def run_python(script: str, cwd: str = "~") -> dict:
    """Python 코드를 실행합니다."""
    try:
        cwd = os.path.expanduser(cwd)
        result = subprocess.run(
            ["python", "-c", script],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=cwd
        )
        return {
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Python script timeout (120s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def git_command(repo_path: str, command: str) -> dict:
    """Git 명령을 실행합니다. (예: status, pull, push, add ., commit -m 'msg')"""
    try:
        repo_path = os.path.expanduser(repo_path)
        result = subprocess.run(
            f"git {command}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=repo_path
        )
        return {
            "success": True,
            "command": f"git {command}",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def git_push(repo_path: str, message: str = "auto sync") -> dict:
    """Git add, commit, push를 한번에 실행합니다."""
    try:
        repo_path = os.path.expanduser(repo_path)
        results = []
        
        for cmd in ["add .", f'commit -m "{message}"', "push"]:
            result = subprocess.run(
                f"git {cmd}",
                shell=True,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            results.append({
                "command": f"git {cmd}",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            })
        
        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def list_processes(filter_name: str = "") -> dict:
    """실행 중인 프로세스 목록을 조회합니다."""
    try:
        if os.name == 'nt':  # Windows
            cmd = 'tasklist /FO CSV'
        else:
            cmd = 'ps aux'
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        
        if filter_name:
            lines = [l for l in lines if filter_name.lower() in l.lower()]
        
        return {"success": True, "processes": lines[:50]}  # 최대 50개
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_system_info() -> dict:
    """시스템 환경 정보를 조회합니다."""
    import platform
    return {
        "success": True,
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.architecture()[0],
        "hostname": platform.node(),
        "python_version": platform.python_version(),
        "cwd": os.getcwd(),
        "home": os.path.expanduser("~")
    }


# === 시스템 트레이 앱 ===
class TunnelToggle:
    def __init__(self):
        self.tunnel_process = None
        self.server_thread = None
        self.tunnel_url = None
        self.is_running = False
        
    def create_icon(self, color):
        image = Image.new('RGB', (64, 64), color=color)
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill=color)
        return image
    
    def get_icon(self):
        if self.is_running:
            return self.create_icon('green')
        return self.create_icon('red')
    
    def start_server(self):
        """MCP 서버 시작"""
        mcp.run(transport="streamable-http", host="127.0.0.1", port=TUNNEL_PORT)
    
    def start_tunnel(self, icon):
        if self.is_running:
            return
        
        # MCP 서버 시작
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()
        
        print("⏳ MCP 서버 시작 중...")
        time.sleep(3)  # MCP 서버 초기화 대기
        print("✅ MCP 서버 준비됨!")
        
        # Cloudflare 터널 시작
        try:
            self.tunnel_process = subprocess.Popen(
                ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{TUNNEL_PORT}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            def read_tunnel_url():
                for line in self.tunnel_process.stderr:
                    match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                    if match:
                        self.tunnel_url = match.group(0)
                        print(f"\n{'='*60}")
                        print(f"🟢 터널 활성화!")
                        print(f"📍 MCP URL: {self.tunnel_url}/mcp")
                        print(f"🔑 API Key: {API_KEY}")
                        print(f"{'='*60}")
                        print(f"\n📋 Claude 웹 커넥터 등록 정보:")
                        print(f"   URL: {self.tunnel_url}/mcp")
                        print(f"{'='*60}\n")
                        break
            
            url_thread = threading.Thread(target=read_tunnel_url, daemon=True)
            url_thread.start()
            
            self.is_running = True
            icon.icon = self.get_icon()
            icon.title = "터널 ON"
            
        except FileNotFoundError:
            print("❌ cloudflared가 설치되어 있지 않습니다!")
    
    def stop_tunnel(self, icon):
        if not self.is_running:
            return
        
        if self.tunnel_process:
            self.tunnel_process.terminate()
            self.tunnel_process = None
        
        self.tunnel_url = None
        self.is_running = False
        icon.icon = self.get_icon()
        icon.title = "터널 OFF"
        print("\n🔴 터널 종료됨\n")
    
    def show_url(self, icon):
        if self.tunnel_url:
            print(f"\n{'='*60}")
            print(f"📍 MCP URL: {self.tunnel_url}/mcp")
            print(f"🔑 API Key: {API_KEY}")
            print(f"{'='*60}\n")
        else:
            print("\n❌ 터널이 실행중이지 않습니다\n")
    
    def quit_app(self, icon):
        self.stop_tunnel(icon)
        icon.stop()
    
    def run(self):
        icon = pystray.Icon(
            "PC Remote MCP",
            self.get_icon(),
            "터널 OFF",
            menu=pystray.Menu(
                pystray.MenuItem("🟢 터널 ON", self.start_tunnel),
                pystray.MenuItem("🔴 터널 OFF", self.stop_tunnel),
                pystray.MenuItem("📍 URL/API 보기", self.show_url),
                pystray.MenuItem("❌ 종료", self.quit_app)
            )
        )
        
        print("\n" + "="*60)
        print("PC Remote MCP Server 시작됨!")
        print("시스템 트레이에서 아이콘을 클릭하세요")
        print("="*60 + "\n")
        
        icon.run()


if __name__ == "__main__":
    toggle = TunnelToggle()
    toggle.run()
