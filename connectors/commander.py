"""
Commander Connector - 명령어/프로세스 관련 도구들
호스트: pc-cmd.jmshinhwa.org
"""
import os
import subprocess
import platform
import threading
import time
from datetime import datetime

# 도구 이름 목록 (필터링용)
TOOLS = [
    "execute_command",
    "start_process",
    "read_process_output",
    "interact_with_process",
    "force_terminate",
    "list_sessions",
    "run_python",
    "git_command",
    "git_push",
    "list_processes",
    "kill_process",
    "get_system_info",
]

# 프로세스 관리
active_processes = {}
process_lock = threading.Lock()


class ProcessSession:
    def __init__(self, pid, process, command, shell):
        self.pid = pid
        self.process = process
        self.command = command
        self.shell = shell
        self.start_time = datetime.now()
        self.output_buffer = []
        self.is_running = True
        
    def read_output(self):
        try:
            while self.is_running:
                line = self.process.stdout.readline()
                if line:
                    self.output_buffer.append(line)
                elif self.process.poll() is not None:
                    self.is_running = False
                    break
        except:
            self.is_running = False


def register_tools(mcp):
    """MCP 서버에 Commander 도구들 등록"""
    
    @mcp.tool()
    def execute_command(command: str, cwd: str = "~", timeout: int = 60, shell: str = "powershell.exe") -> dict:
        """명령어를 실행하고 완료될 때까지 기다립니다."""
        try:
            cwd = os.path.expanduser(cwd)
            
            if "powershell" in shell.lower():
                full_cmd = f'powershell.exe -Command "{command}"'
            elif "cmd" in shell.lower():
                full_cmd = f'cmd.exe /c {command}'
            else:
                full_cmd = command
            
            result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=cwd)
            return {"success": True, "stdout": result.stdout[:50000], "stderr": result.stderr[:10000], "returncode": result.returncode}
        except subprocess.TimeoutExpired:
            return {"error": f"Timeout after {timeout} seconds"}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def start_process(command: str, timeout_ms: int = 30000, shell: str = "powershell.exe", cwd: str = "~") -> dict:
        """새 프로세스를 시작합니다."""
        try:
            cwd = os.path.expanduser(cwd)
            
            if "powershell" in shell.lower():
                full_cmd = ["powershell.exe", "-Command", command]
            elif "cmd" in shell.lower():
                full_cmd = ["cmd.exe", "/c", command]
            else:
                full_cmd = [shell, "-c", command]
            
            process = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                       stdin=subprocess.PIPE, text=True, cwd=cwd, bufsize=1)
            
            pid = process.pid
            session = ProcessSession(pid, process, command, shell)
            
            output_thread = threading.Thread(target=session.read_output, daemon=True)
            output_thread.start()
            
            with process_lock:
                active_processes[pid] = session
            
            timeout_sec = timeout_ms / 1000
            start_time = time.time()
            initial_output = []
            
            while time.time() - start_time < timeout_sec:
                with process_lock:
                    if pid in active_processes:
                        if active_processes[pid].output_buffer:
                            initial_output = active_processes[pid].output_buffer.copy()
                            active_processes[pid].output_buffer.clear()
                        if not active_processes[pid].is_running:
                            break
                time.sleep(0.1)
            
            output_text = "".join(initial_output)
            return {"success": True, "pid": pid, "command": command, "shell": shell, 
                    "is_running": session.is_running, "initial_output": output_text[:50000]}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def read_process_output(pid: int, timeout_ms: int = 5000, offset: int = 0, length: int = 1000) -> dict:
        """실행 중인 프로세스의 출력을 읽습니다."""
        try:
            with process_lock:
                if pid not in active_processes:
                    return {"error": f"Process {pid} not found"}
                session = active_processes[pid]
            
            timeout_sec = timeout_ms / 1000
            start_time = time.time()
            
            while time.time() - start_time < timeout_sec:
                with process_lock:
                    if session.output_buffer or not session.is_running:
                        break
                time.sleep(0.1)
            
            with process_lock:
                lines = session.output_buffer.copy()
                session.output_buffer.clear()
            
            if offset < 0:
                lines = lines[offset:]
            else:
                lines = lines[offset:offset + length]
            
            output = "".join(lines)
            return {"success": True, "pid": pid, "output": output[:50000], "lines_read": len(lines), "is_running": session.is_running}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def interact_with_process(pid: int, input_text: str, timeout_ms: int = 8000) -> dict:
        """실행 중인 프로세스에 입력을 보내고 응답을 받습니다."""
        try:
            with process_lock:
                if pid not in active_processes:
                    return {"error": f"Process {pid} not found"}
                session = active_processes[pid]
            
            if not session.is_running:
                return {"error": "Process has finished"}
            
            session.process.stdin.write(input_text + "\n")
            session.process.stdin.flush()
            
            timeout_sec = timeout_ms / 1000
            start_time = time.time()
            
            while time.time() - start_time < timeout_sec:
                with process_lock:
                    if session.output_buffer or not session.is_running:
                        break
                time.sleep(0.1)
            
            with process_lock:
                lines = session.output_buffer.copy()
                session.output_buffer.clear()
            
            output = "".join(lines)
            return {"success": True, "pid": pid, "output": output[:50000], "is_running": session.is_running}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def force_terminate(pid: int) -> dict:
        """프로세스를 강제 종료합니다."""
        try:
            with process_lock:
                if pid not in active_processes:
                    return {"error": f"Process {pid} not found"}
                session = active_processes[pid]
            
            session.process.terminate()
            session.is_running = False
            
            with process_lock:
                del active_processes[pid]
            
            return {"success": True, "pid": pid, "status": "terminated"}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def list_sessions() -> dict:
        """현재 활성화된 프로세스 세션 목록을 조회합니다."""
        try:
            sessions = []
            with process_lock:
                for pid, session in active_processes.items():
                    runtime = (datetime.now() - session.start_time).total_seconds()
                    sessions.append({
                        "pid": pid, "command": session.command[:100], "shell": session.shell,
                        "is_running": session.is_running, "runtime_seconds": round(runtime, 1),
                        "buffer_lines": len(session.output_buffer)
                    })
            return {"success": True, "sessions": sessions, "count": len(sessions)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def run_python(script: str, cwd: str = "~", timeout: int = 120) -> dict:
        """Python 스크립트를 실행합니다."""
        try:
            cwd = os.path.expanduser(cwd)
            result = subprocess.run(["python", "-c", script], capture_output=True, text=True, timeout=timeout, cwd=cwd)
            return {"success": True, "stdout": result.stdout[:50000], "stderr": result.stderr[:10000], "returncode": result.returncode}
        except subprocess.TimeoutExpired:
            return {"error": f"Timeout after {timeout} seconds"}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def git_command(repo_path: str, command: str) -> dict:
        """Git 명령을 실행합니다."""
        try:
            repo = os.path.expanduser(repo_path)
            result = subprocess.run(f"git {command}", shell=True, capture_output=True, text=True, timeout=60, cwd=repo)
            return {"success": True, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def git_push(repo_path: str, message: str = "auto sync") -> dict:
        """Git add, commit, push를 한번에 실행합니다."""
        try:
            repo = os.path.expanduser(repo_path)
            results = []
            for cmd in ["add .", f'commit -m "{message}"', "push"]:
                r = subprocess.run(f"git {cmd}", shell=True, capture_output=True, text=True, cwd=repo)
                results.append({"command": cmd, "stdout": r.stdout, "stderr": r.stderr, "returncode": r.returncode})
            return {"success": True, "results": results}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def list_processes(filter_name: str = "") -> dict:
        """시스템 프로세스 목록을 조회합니다."""
        try:
            result = subprocess.run('tasklist /FO CSV', shell=True, capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if filter_name:
                lines = [l for l in lines if filter_name.lower() in l.lower()]
            return {"success": True, "processes": lines[:100]}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def kill_process(name_or_pid: str) -> dict:
        """프로세스를 강제 종료합니다."""
        try:
            if name_or_pid.isdigit():
                cmd = f'taskkill /F /PID {name_or_pid}'
            else:
                cmd = f'taskkill /F /IM "{name_or_pid}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return {"success": True, "stdout": result.stdout, "stderr": result.stderr}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def get_system_info() -> dict:
        """시스템 정보를 조회합니다."""
        try:
            import psutil
            has_psutil = True
        except:
            has_psutil = False
        
        info = {
            "success": True, "os": platform.system(), "os_version": platform.version(),
            "hostname": platform.node(), "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "home": os.path.expanduser("~"), "cwd": os.getcwd()
        }
        
        if has_psutil:
            import psutil
            info["cpu_percent"] = psutil.cpu_percent()
            info["memory_percent"] = psutil.virtual_memory().percent
            info["disk_percent"] = psutil.disk_usage('/').percent
        
        return info
