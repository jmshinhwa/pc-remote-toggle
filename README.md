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

### MCP 서버 (Cloudflare 터널 방식)

```powershell
cd ~/Desktop/pc-remote-toggle
python mcp_server.py
```

또는 창 없이:
```powershell
pythonw mcp_server.py
```

### 서비스 매니저 (트레이 앱)

```powershell
cd ~/Desktop/pc-remote-toggle
python tray_manager.py
```

또는 빌드한 exe 실행:
```powershell
ServiceManager.exe
```

## 📋 사용법

### MCP 서버

1. 실행 → 시스템 트레이에 🔴 아이콘
2. 우클릭 → "🟢 터널 ON"
3. 콘솔에 표시된 정보:
   - MCP URL: `https://xxx.trycloudflare.com/mcp`
   - API Key: `config.py`에 설정된 값

4. Claude 웹 → 설정 → 커넥터 → 커스텀 추가
   - URL: 위에 표시된 MCP URL 입력

### 서비스 매니저

1. `ServiceManager.exe` 실행 → 시스템 트레이에 아이콘 생성
2. 우클릭 → 메뉴 표시:
   - 파일시스템 🔵/🔴
   - 데스크탑 커맨더 🔵/🔴
   - 깃허브 오토싱크 🔵/🔴
   - 종료
3. 메뉴 클릭 → 서비스 ON/OFF 토글
4. 🔵 파란불 = 실행 중, 🔴 빨간불 = 중지

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
