"""
PC Remote Toggle - 시스템 트레이 토글 앱
Cloudflare 터널 ON/OFF + API 키 인증 MCP 서버
"""

import subprocess
import threading
import os
import sys
import re
from flask import Flask, request, jsonify
import pystray
from PIL import Image, ImageDraw
from config import API_KEY, TUNNEL_PORT

# === Flask 서버 (MCP 역할) ===
app = Flask(__name__)

def check_api_key():
    """API 키 검증"""
    key = request.headers.get("X-API-Key")
    if key != API_KEY:
        return False
    return True

@app.route("/health", methods=["GET"])
def health():
    """상태 확인"""
    if not check_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"status": "ok", "message": "PC Remote Toggle 연결됨!"})

@app.route("/execute", methods=["POST"])
def execute_command():
    """명령어 실행"""
    if not check_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    command = data.get("command", "")
    
    if not command:
        return jsonify({"error": "No command provided"}), 400
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.path.expanduser("~")
        )
        return jsonify({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Command timeout (60s)"}), 408
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/read_file", methods=["POST"])
def read_file():
    """파일 읽기"""
    if not check_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    filepath = data.get("path", "")
    
    try:
        filepath = os.path.expanduser(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/write_file", methods=["POST"])
def write_file():
    """파일 쓰기"""
    if not check_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    filepath = data.get("path", "")
    content = data.get("content", "")
    
    try:
        filepath = os.path.expanduser(filepath)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return jsonify({"success": True, "path": filepath})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/list_dir", methods=["POST"])
def list_directory():
    """디렉토리 목록"""
    if not check_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    dirpath = data.get("path", "~")
    
    try:
        dirpath = os.path.expanduser(dirpath)
        items = os.listdir(dirpath)
        result = []
        for item in items:
            full_path = os.path.join(dirpath, item)
            result.append({
                "name": item,
                "is_dir": os.path.isdir(full_path),
                "size": os.path.getsize(full_path) if os.path.isfile(full_path) else 0
            })
        return jsonify({"items": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/git_push", methods=["POST"])
def git_push():
    """Git 자동 푸시"""
    if not check_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    repo_path = data.get("path", "")
    message = data.get("message", "auto sync")
    
    try:
        repo_path = os.path.expanduser(repo_path)
        commands = [
            f'cd "{repo_path}" && git add .',
            f'cd "{repo_path}" && git commit -m "{message}"',
            f'cd "{repo_path}" && git push'
        ]
        
        results = []
        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            results.append({
                "command": cmd,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            })
        
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# === 시스템 트레이 앱 ===
class TunnelToggle:
    def __init__(self):
        self.tunnel_process = None
        self.server_thread = None
        self.tunnel_url = None
        self.is_running = False
        
    def create_icon(self, color):
        """아이콘 생성"""
        image = Image.new('RGB', (64, 64), color=color)
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill=color)
        return image
    
    def get_icon(self):
        """현재 상태에 따른 아이콘"""
        if self.is_running:
            return self.create_icon('green')
        return self.create_icon('red')
    
    def start_server(self):
        """Flask 서버 시작"""
        app.run(host='127.0.0.1', port=TUNNEL_PORT, threaded=True, use_reloader=False)
    
    def start_tunnel(self, icon):
        """터널 시작"""
        if self.is_running:
            return
        
        # Flask 서버 시작
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()
        
        # Cloudflare 터널 시작
        try:
            self.tunnel_process = subprocess.Popen(
                ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{TUNNEL_PORT}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 터널 URL 추출
            def read_tunnel_url():
                for line in self.tunnel_process.stderr:
                    match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                    if match:
                        self.tunnel_url = match.group(0)
                        print(f"\n{'='*50}")
                        print(f"🟢 터널 활성화!")
                        print(f"📍 URL: {self.tunnel_url}")
                        print(f"🔑 API Key: {API_KEY}")
                        print(f"{'='*50}\n")
                        break
            
            url_thread = threading.Thread(target=read_tunnel_url, daemon=True)
            url_thread.start()
            
            self.is_running = True
            icon.icon = self.get_icon()
            icon.title = "터널 ON"
            
        except FileNotFoundError:
            print("❌ cloudflared가 설치되어 있지 않습니다!")
            print("설치: winget install Cloudflare.cloudflared")
    
    def stop_tunnel(self, icon):
        """터널 종료"""
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
        """현재 URL 표시"""
        if self.tunnel_url:
            print(f"\n📍 현재 터널 URL: {self.tunnel_url}")
            print(f"🔑 API Key: {API_KEY}\n")
        else:
            print("\n❌ 터널이 실행중이지 않습니다\n")
    
    def quit_app(self, icon):
        """앱 종료"""
        self.stop_tunnel(icon)
        icon.stop()
    
    def run(self):
        """앱 실행"""
        icon = pystray.Icon(
            "PC Remote Toggle",
            self.get_icon(),
            "터널 OFF",
            menu=pystray.Menu(
                pystray.MenuItem("🟢 터널 ON", self.start_tunnel),
                pystray.MenuItem("🔴 터널 OFF", self.stop_tunnel),
                pystray.MenuItem("📍 URL 보기", self.show_url),
                pystray.MenuItem("❌ 종료", self.quit_app)
            )
        )
        
        print("\n" + "="*50)
        print("PC Remote Toggle 시작됨!")
        print("시스템 트레이에서 아이콘을 클릭하세요")
        print("="*50 + "\n")
        
        icon.run()


if __name__ == "__main__":
    toggle = TunnelToggle()
    toggle.run()
