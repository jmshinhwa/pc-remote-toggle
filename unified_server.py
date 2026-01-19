"""
통합 MCP 서버 - 모든 도구 통합 (Filesystem + Commander + VSCode)
포트 8765, 단일 엔드포인트로 모든 도구 제공
"""

import os
import subprocess
import sys
import shutil
from typing import List
from fastmcp import FastMCP
from config import API_KEY

# MCP 서버 생성
mcp = FastMCP(name="PC-Remote-Unified")

# 프로세스 세션 관리 (Commander용)
process_sessions = {}

# ============================================================================
# Filesystem 도구들
# ============================================================================

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
def read_file(path: str, offset: int = 0, length: int = -1, head: int = -1, tail: int = -1) -> dict:
    """파일 내용을 읽습니다. offset/length/head/tail 지원"""
    try:
        path = os.path.expanduser(path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # head: 처음 n줄
        if head > 0:
            lines = content.split('\n')
            content = '\n'.join(lines[:head])
        # tail: 마지막 n줄
        elif tail > 0:
            lines = content.split('\n')
            content = '\n'.join(lines[-tail:])
        # offset/length: 바이트 범위
        elif offset > 0 or length > 0:
            if length > 0:
                content = content[offset:offset+length]
            else:
                content = content[offset:]
        
        return {"success": True, "path": path, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def read_multiple_files(paths: List[str]) -> dict:
    """여러 파일을 한번에 읽습니다."""
    results = []
    for p in paths:
        result = read_file(p)
        results.append({"path": p, "result": result})
    return {"success": True, "files": results}

@mcp.tool()
def write_file(path: str, content: str, mode: str = "rewrite") -> dict:
    """파일에 내용을 씁니다. mode: rewrite(덮어쓰기) 또는 append(추가)"""
    try:
        path = os.path.expanduser(path)
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        write_mode = "a" if mode == "append" else "w"
        with open(path, write_mode, encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": path, "mode": mode}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def edit_block(path: str, start_line: int, end_line: int, new_content: str) -> dict:
    """파일의 특정 라인 범위를 편집합니다."""
    try:
        path = os.path.expanduser(path)
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # 라인 번호는 1부터 시작
        lines[start_line-1:end_line] = [new_content + '\n']
        
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        
        return {"success": True, "path": path, "edited_lines": f"{start_line}-{end_line}"}
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
def move_file(src: str, dest: str) -> dict:
    """파일이나 폴더를 이동합니다."""
    try:
        src = os.path.expanduser(src)
        dest = os.path.expanduser(dest)
        shutil.move(src, dest)
        return {"success": True, "from": src, "to": dest}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def copy_file(src: str, dest: str) -> dict:
    """파일이나 폴더를 복사합니다."""
    try:
        src = os.path.expanduser(src)
        dest = os.path.expanduser(dest)
        if os.path.isfile(src):
            shutil.copy2(src, dest)
        else:
            shutil.copytree(src, dest)
        return {"success": True, "from": src, "to": dest}
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
            shutil.rmtree(path)
        return {"success": True, "deleted": path}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def search_files(directory: str, pattern: str, max_results: int = 100) -> dict:
    """파일명으로 검색합니다."""
    try:
        directory = os.path.expanduser(directory)
        results = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if pattern.lower() in file.lower():
                    results.append(os.path.join(root, file))
                    if len(results) >= max_results:
                        break
            if len(results) >= max_results:
                break
        return {"success": True, "pattern": pattern, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def search_content(directory: str, text: str, max_results: int = 50) -> dict:
    """파일 내용에서 텍스트를 검색합니다."""
    try:
        directory = os.path.expanduser(directory)
        results = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        if text in content:
                            results.append(filepath)
                            if len(results) >= max_results:
                                break
                except:
                    continue
            if len(results) >= max_results:
                break
        return {"success": True, "text": text, "results": results}
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

# ============================================================================
# Commander 도구들
# ============================================================================

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
def start_process(command: str, session_id: str, cwd: str = "~") -> dict:
    """백그라운드 프로세스를 시작합니다."""
    try:
        cwd = os.path.expanduser(cwd)
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            cwd=cwd
        )
        process_sessions[session_id] = process
        return {
            "success": True,
            "session_id": session_id,
            "pid": process.pid,
            "command": command
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def read_process_output(session_id: str, timeout: int = 1) -> dict:
    """백그라운드 프로세스의 출력을 읽습니다."""
    try:
        if session_id not in process_sessions:
            return {"success": False, "error": "Session not found"}
        
        process = process_sessions[session_id]
        
        # 프로세스 상태 확인
        stdout_data = ""
        stderr_data = ""
        
        if process.poll() is not None:
            # 프로세스가 종료됨
            if process.stdout:
                stdout_data = process.stdout.read()
            if process.stderr:
                stderr_data = process.stderr.read()
        
        return {
            "success": True,
            "session_id": session_id,
            "stdout": stdout_data,
            "stderr": stderr_data,
            "is_running": process.poll() is None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def interact_with_process(session_id: str, input_text: str) -> dict:
    """백그라운드 프로세스에 입력을 보냅니다."""
    try:
        if session_id not in process_sessions:
            return {"success": False, "error": "Session not found"}
        
        process = process_sessions[session_id]
        if process.stdin:
            process.stdin.write(input_text + "\n")
            process.stdin.flush()
        
        return {"success": True, "session_id": session_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def force_terminate(session_id: str) -> dict:
    """백그라운드 프로세스를 강제 종료합니다."""
    try:
        if session_id not in process_sessions:
            return {"success": False, "error": "Session not found"}
        
        process = process_sessions[session_id]
        process.terminate()
        try:
            process.wait(timeout=5)
        except:
            process.kill()
        del process_sessions[session_id]
        
        return {"success": True, "session_id": session_id, "terminated": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def list_sessions() -> dict:
    """실행 중인 프로세스 세션 목록을 조회합니다."""
    sessions = []
    for session_id, process in process_sessions.items():
        sessions.append({
            "session_id": session_id,
            "pid": process.pid,
            "is_running": process.poll() is None
        })
    return {"success": True, "sessions": sessions}

@mcp.tool()
def run_python(script: str, cwd: str = "~") -> dict:
    """Python 코드를 실행합니다."""
    try:
        cwd = os.path.expanduser(cwd)
        result = subprocess.run(
            [sys.executable, "-c", script],
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
    """Git 명령을 실행합니다."""
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
        
        return {"success": True, "processes": lines[:50]}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def kill_process(pid: int) -> dict:
    """프로세스를 종료합니다."""
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=True)
        else:
            os.kill(pid, 9)
        return {"success": True, "pid": pid}
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

# ============================================================================
# VS Code 도구들
# ============================================================================

@mcp.tool()
def open_file(path: str, line: int = 1) -> dict:
    """VS Code에서 파일을 엽니다."""
    try:
        path = os.path.expanduser(path)
        if line > 1:
            result = subprocess.run(
                ["code", "--goto", f"{path}:{line}"],
                capture_output=True,
                text=True
            )
        else:
            result = subprocess.run(
                ["code", path],
                capture_output=True,
                text=True
            )
        return {"success": True, "path": path, "line": line}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def open_folder(path: str) -> dict:
    """VS Code에서 폴더를 엽니다."""
    try:
        path = os.path.expanduser(path)
        result = subprocess.run(
            ["code", path],
            capture_output=True,
            text=True
        )
        return {"success": True, "path": path}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def open_workspace(workspace_file: str) -> dict:
    """VS Code에서 워크스페이스를 엽니다."""
    try:
        workspace_file = os.path.expanduser(workspace_file)
        result = subprocess.run(
            ["code", workspace_file],
            capture_output=True,
            text=True
        )
        return {"success": True, "workspace": workspace_file}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_open_editors() -> dict:
    """열린 에디터 목록을 조회합니다 (VS Code CLI 필요)."""
    try:
        return {
            "success": True,
            "message": "VS Code CLI does not provide direct editor list. Use VS Code extensions for this feature."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# 서버 실행
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 통합 MCP 서버 시작")
    print("="*60)
    print(f"📍 MCP URL: http://127.0.0.1:8765/mcp")
    print(f"🔑 API Key: {API_KEY}")
    print(f"   (Note: API key should be configured in Cloudflare Tunnel)")
    print(f"\n📦 도구 목록:")
    print(f"   Filesystem: 12 도구")
    print(f"   Commander: 12 도구")
    print(f"   VS Code: 4 도구")
    print(f"   Total: 28 도구")
    print("="*60 + "\n")
    
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8765)
