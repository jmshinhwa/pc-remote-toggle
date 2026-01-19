# PC Remote MCP Server
# Desktop Commander + Filesystem for Claude Web

## 🎯 기능

Claude 웹에서 정민님 PC를 제어할 수 있는 MCP 서버입니다.

### Filesystem 도구
- `list_directory` - 폴더 목록 조회
- `read_file` - 파일 읽기
- `write_file` - 파일 쓰기
- `delete_path` - 파일/폴더 삭제
- `move_path` - 이동/이름변경
- `copy_path` - 복사
- `create_directory` - 폴더 생성
- `get_file_info` - 파일 정보

### Desktop Commander 도구
- `execute_command` - 쉘 명령어 실행
- `run_python` - Python 코드 실행
- `git_command` - Git 명령 실행
- `git_push` - Git 자동 푸시
- `list_processes` - 프로세스 목록
- `get_system_info` - 시스템 정보

## 📦 설치

```powershell
cd ~/Desktop/pc-remote-toggle
git pull
pip install -r requirements.txt
```

## 🚀 실행

### MCP 서버 (통합 서버)

```powershell
cd ~/Desktop/pc-remote-toggle
python unified_server.py
```

또는 창 없이:
```powershell
pythonw unified_server.py
```

서버는 포트 8765에서 실행되며, 모든 도구(Filesystem + Commander)를 제공합니다.

### 서비스 매니저 (트레이 앱)

```powershell
cd ~/Desktop/pc-remote-toggle
python tray_manager.py
```

또는 빌드한 exe 실행:
```powershell
ServiceManager.exe
```

트레이 앱을 통해 MCP 서버와 깃허브 싱크를 ON/OFF 할 수 있습니다.

## 📋 사용법

### MCP 서버

1. `unified_server.py` 실행
2. 서버가 포트 8765에서 시작됨
3. API Key: `config.py`에 설정된 값 사용
4. 콘솔에 표시된 정보 확인:
   - URL: `http://127.0.0.1:8765/mcp`
   - API Key: `config.py`에서 설정한 키 (마스킹되어 표시됨)
   - 제공 도구: 24개 (Filesystem 12개 + Commander 12개)

5. Claude 웹에서 사용시 URL에 API key 추가:
   - `http://127.0.0.1:8765/mcp?key=YOUR_API_KEY`
   - API_KEY는 `config.py` 파일에서 확인
   - 또는 Cloudflare 터널 사용

### 서비스 매니저

1. `ServiceManager.exe` 또는 `python tray_manager.py` 실행
2. 시스템 트레이에 아이콘 생성
3. 우클릭 → 메뉴 표시:
   - 🔵 MCP 서버 [ON/OFF]
   - 🔵 깃허브 싱크 [ON/OFF]
   - 종료
4. 메뉴 클릭 → 서비스 ON/OFF 토글
5. 🔵 파란불 = 실행 중, 🔴 빨간불 = 중지

## 🔧 서비스 매니저 빌드

PyInstaller를 사용하여 단일 실행 파일로 빌드:

```powershell
pip install pyinstaller
pyinstaller --onefile --noconsole --name "ServiceManager" tray_manager.py
```

빌드된 파일: `dist/ServiceManager.exe`

## 🔐 보안

- API Key로 인증 (config.py에서 변경)
- 터널 OFF 하면 외부 접근 완전 차단
- 필요할 때만 ON

## ⚙️ 설정

`config.py` 파일에서:
```python
API_KEY = "your-secret-key"  # 원하는 값으로 변경
TUNNEL_PORT = 8765  # 포트 변경 가능
```
