"""
Filesystem Connector - 파일시스템 관련 도구들
호스트: pc.jmshinhwa.org
"""
import os
import shutil
import fnmatch
from datetime import datetime

# 도구 이름 목록 (필터링용)
TOOLS = [
    "list_directory",
    "read_file", 
    "read_multiple_files",
    "write_file",
    "edit_block",
    "create_directory",
    "move_file",
    "copy_file",
    "delete_path",
    "search_files",
    "search_content",
    "get_file_info",
]

FILE_READ_LINE_LIMIT = 1000

def expand_path(path: str) -> str:
    return os.path.expanduser(path.replace("/", os.sep).replace("\\", os.sep))


def register_tools(mcp):
    """MCP 서버에 Filesystem 도구들 등록"""
    
    @mcp.tool()
    def list_directory(path: str = "~", depth: int = 1) -> dict:
        """디렉토리 내용을 조회합니다."""
        try:
            path = expand_path(path)
            results = []
            
            def scan_dir(dir_path, current_depth, max_depth):
                if current_depth > max_depth:
                    return
                try:
                    items = os.listdir(dir_path)
                    for item in items[:200]:
                        full_path = os.path.join(dir_path, item)
                        rel_path = os.path.relpath(full_path, path)
                        is_dir = os.path.isdir(full_path)
                        try:
                            size = os.path.getsize(full_path) if not is_dir else 0
                        except:
                            size = 0
                        results.append({"name": rel_path, "is_dir": is_dir, "size": size})
                        if is_dir and current_depth < max_depth:
                            scan_dir(full_path, current_depth + 1, max_depth)
                except PermissionError:
                    results.append({"name": os.path.relpath(dir_path, path), "denied": True})
            
            scan_dir(path, 1, depth)
            return {"success": True, "path": path, "items": results}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def read_file(path: str, encoding: str = "utf-8", offset: int = 0, 
                  length: int = None, head: int = None, tail: int = None) -> dict:
        """파일 내용을 읽습니다."""
        try:
            path = expand_path(path)
            with open(path, "r", encoding=encoding, errors="replace") as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            if head is not None:
                lines = lines[:head]
            elif tail is not None:
                lines = lines[-tail:]
            elif offset < 0:
                lines = lines[offset:]
            else:
                if length is None:
                    length = FILE_READ_LINE_LIMIT
                lines = lines[offset:offset + length]
            
            content = "".join(lines)
            return {"success": True, "content": content, "total_lines": total_lines, "returned_lines": len(lines)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def read_multiple_files(paths: list, encoding: str = "utf-8") -> dict:
        """여러 파일을 동시에 읽습니다."""
        results = []
        for p in paths:
            try:
                file_path = expand_path(p)
                with open(file_path, "r", encoding=encoding, errors="replace") as f:
                    content = f.read()[:100000]
                results.append({"path": p, "success": True, "content": content})
            except Exception as e:
                results.append({"path": p, "success": False, "error": str(e)})
        return {"success": True, "results": results}

    @mcp.tool()
    def write_file(path: str, content: str, mode: str = "rewrite") -> dict:
        """파일에 내용을 씁니다."""
        try:
            path = expand_path(path)
            dir_path = os.path.dirname(path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            file_mode = "w" if mode == "rewrite" else "a"
            with open(path, file_mode, encoding="utf-8") as f:
                f.write(content)
            
            line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
            return {"success": True, "path": path, "lines_written": line_count, "mode": mode}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def edit_block(file_path: str, old_string: str, new_string: str = "", expected_replacements: int = 1) -> dict:
        """파일에서 old_string을 찾아 new_string으로 교체합니다."""
        try:
            path = expand_path(file_path)
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            
            count = content.count(old_string)
            if count == 0:
                return {"error": f"'{old_string[:50]}...' not found in file"}
            if count != expected_replacements:
                return {"error": f"Expected {expected_replacements} occurrences, found {count}"}
            
            new_content = content.replace(old_string, new_string)
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            return {"success": True, "replacements": count}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def create_directory(path: str) -> dict:
        """폴더를 생성합니다."""
        try:
            path = expand_path(path)
            os.makedirs(path, exist_ok=True)
            return {"success": True, "path": path}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def move_file(source: str, destination: str) -> dict:
        """파일이나 폴더를 이동/이름변경합니다."""
        try:
            src = expand_path(source)
            dest = expand_path(destination)
            shutil.move(src, dest)
            return {"success": True, "source": src, "destination": dest}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def copy_file(source: str, destination: str) -> dict:
        """파일이나 폴더를 복사합니다."""
        try:
            src = expand_path(source)
            dest = expand_path(destination)
            if os.path.isfile(src):
                shutil.copy2(src, dest)
            else:
                shutil.copytree(src, dest)
            return {"success": True, "source": src, "destination": dest}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def delete_path(path: str) -> dict:
        """파일이나 폴더를 삭제합니다."""
        try:
            path = expand_path(path)
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
            return {"success": True, "deleted": path}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def search_files(path: str, pattern: str, max_results: int = 100, include_hidden: bool = False) -> dict:
        """파일명으로 검색합니다."""
        try:
            path = expand_path(path)
            results = []
            pattern_lower = pattern.lower()
            
            for root, dirs, files in os.walk(path):
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    files = [f for f in files if not f.startswith('.')]
                
                for name in files + dirs:
                    if pattern_lower in name.lower():
                        full_path = os.path.join(root, name)
                        results.append({
                            "path": full_path,
                            "is_dir": os.path.isdir(full_path),
                            "size": os.path.getsize(full_path) if os.path.isfile(full_path) else 0
                        })
                        if len(results) >= max_results:
                            return {"success": True, "results": results, "truncated": True}
            
            return {"success": True, "results": results, "count": len(results)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def search_content(path: str, pattern: str, file_pattern: str = "*", 
                       max_results: int = 50, context_lines: int = 2) -> dict:
        """파일 내용에서 텍스트를 검색합니다."""
        try:
            path = expand_path(path)
            results = []
            
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
                
                for filename in files:
                    if not fnmatch.fnmatch(filename, file_pattern):
                        continue
                    
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                        
                        for i, line in enumerate(lines):
                            if pattern.lower() in line.lower():
                                start = max(0, i - context_lines)
                                end = min(len(lines), i + context_lines + 1)
                                context = "".join(lines[start:end])
                                results.append({"file": filepath, "line": i + 1, "context": context.strip()})
                                if len(results) >= max_results:
                                    return {"success": True, "results": results, "truncated": True}
                    except:
                        continue
            
            return {"success": True, "results": results, "count": len(results)}
        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    def get_file_info(path: str) -> dict:
        """파일이나 폴더의 상세 정보를 조회합니다."""
        try:
            path = expand_path(path)
            if not os.path.exists(path):
                return {"success": True, "exists": False}
            
            stat = os.stat(path)
            info = {
                "success": True, "exists": True, "path": path,
                "is_file": os.path.isfile(path), "is_dir": os.path.isdir(path),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat()
            }
            
            if os.path.isfile(path):
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        info["line_count"] = sum(1 for _ in f)
                except:
                    pass
            
            return info
        except Exception as e:
            return {"error": str(e)}
