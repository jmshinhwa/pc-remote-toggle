# 통합 MCP 서버 사용 가이드

## 개요

이 프로젝트는 하나의 통합 MCP 서버로 Filesystem, Commander, VS Code 도구를 모두 제공합니다.

## 서버 구성

### unified_server.py (포트 8765)

**통합된 도구 (총 28개):**

#### Filesystem 도구 (12개)
- `list_directory` - 디렉토리 내용 조회
- `read_file` - 파일 읽기 (offset/length/head/tail 지원)
- `read_multiple_files` - 여러 파일 한번에 읽기
- `write_file` - 파일 쓰기 (rewrite/append 모드)
- `edit_block` - 파일 특정 라인 범위 편집
- `create_directory` - 폴더 생성
- `move_file` - 파일/폴더 이동
- `copy_file` - 파일/폴더 복사
- `delete_path` - 파일/폴더 삭제
- `search_files` - 파일명으로 검색
- `search_content` - 파일 내용에서 텍스트 검색
- `get_file_info` - 파일/폴더 정보 조회

#### Commander 도구 (12개)
- `execute_command` - 쉘 명령어 실행
- `start_process` - 백그라운드 프로세스 시작
- `read_process_output` - 백그라운드 프로세스 출력 읽기
- `interact_with_process` - 백그라운드 프로세스에 입력 전송
- `force_terminate` - 백그라운드 프로세스 강제 종료
- `list_sessions` - 실행 중인 프로세스 세션 목록
- `run_python` - Python 코드 실행
- `git_command` - Git 명령 실행
- `git_push` - Git add, commit, push 한번에 실행
- `list_processes` - 실행 중인 프로세스 목록
- `kill_process` - 프로세스 종료
- `get_system_info` - 시스템 환경 정보 조회

#### VS Code 도구 (4개)
- `open_file` - VS Code에서 파일 열기
- `open_folder` - VS Code에서 폴더 열기
- `open_workspace` - VS Code에서 워크스페이스 열기
- `get_open_editors` - 열린 에디터 목록 조회

## 트레이 앱 (tray_manager.py)

### 메뉴 구성 (3개)

1. **🔵/🔴 MCP 서버 [ON/OFF]** - unified_server.py 토글
2. **🔵/🔴 깃허브 싱크 [ON/OFF]** - V128_Sync.exe 토글
3. **종료** - 트레이 앱 종료 (서비스는 계속 실행)

### 동작 방식

- **한 번 클릭 = 한 번 토글** (여러 번 클릭 불필요)
- ON 클릭 → 즉시 프로세스 시작
- OFF 클릭 → 즉시 프로세스 종료
- 상태는 실시간으로 포트/프로세스 체크

## API Key 인증

API Key는 `config.py`에 정의되어 있습니다:
```python
API_KEY = "yoojin-secret-2026-xyz789"
```

### 인증 방식

1. **로컬 접근 (127.0.0.1:8765)**: API key 검증 없음
2. **외부 접근 (Cloudflare Tunnel)**: Cloudflare Tunnel에서 API key 검증 권장

> **참고**: FastMCP의 streamable-http transport는 기본적으로 별도의 인증 메커니즘이 없습니다. 
> 보안이 필요한 경우 Cloudflare Tunnel이나 nginx 같은 리버스 프록시에서 인증을 처리하세요.

## 서버 실행

### 수동 실행
```bash
python unified_server.py
```

### 트레이 앱으로 실행
```bash
python tray_manager.py
```

트레이 아이콘에서 "MCP 서버" 메뉴를 클릭하여 ON/OFF

## 엔드포인트

- **MCP 프로토콜**: `http://127.0.0.1:8765/mcp`
- **모든 도구**: 위 엔드포인트에서 28개 도구 모두 사용 가능

## Cloudflare Tunnel 연동 (선택사항)

외부에서 접근하려면 Cloudflare Tunnel 사용:

```bash
cloudflared tunnel --url http://127.0.0.1:8765
```

생성된 URL을 Claude Desktop 설정에서 사용:
```
https://xxx.trycloudflare.com/mcp
```

## 테스트

전체 테스트 실행:
```bash
python -m py_compile unified_server.py
python -m py_compile tray_manager.py
python -c "from unified_server import mcp; print(f'✅ {mcp.name} loaded')"
```

GitHub Actions에서 자동으로 문법 체크 및 import 테스트가 실행됩니다.
