# Service Manager - 사용 가이드

## 📋 사전 요구사항

Service Manager가 올바르게 작동하려면 다음 파일들이 지정된 경로에 있어야 합니다:

### 1. 파일시스템 서버
- 경로: `C:\Users\user\Desktop\pc-remote-toggle\filesystem_server.py`
- 포트: 8765

### 2. 데스크탑 커맨더 서버
- 경로: `C:\Users\user\Desktop\pc-remote-toggle\commander_server.py`
- 포트: 8766

### 3. 깃허브 오토싱크
- 경로: `C:\Users\user\Desktop\V128프로젝트\V128_Sync.exe`
- 프로세스명: V128_Sync

> **참고:** filesystem_server.py와 commander_server.py는 별도로 생성해야 합니다.
> 기존 mcp_server.py를 참고하여 각각의 서버를 분리하여 만들 수 있습니다.

## 🚀 실행 방법

### 방법 1: Python 스크립트로 실행

```powershell
# 의존성 설치
pip install -r requirements.txt

# 실행
python tray_manager.py
```

### 방법 2: exe 파일로 실행

```powershell
# 빌드
pip install pyinstaller
pyinstaller --onefile --noconsole --name "ServiceManager" tray_manager.py

# 실행
.\dist\ServiceManager.exe
```

## 💡 사용법

1. **ServiceManager 실행**
   - 시스템 트레이에 오렌지색 아이콘이 나타납니다
   - 콘솔에 현재 서비스 상태가 표시됩니다

2. **서비스 관리**
   - 트레이 아이콘을 **우클릭**
   - 메뉴가 나타나면 원하는 서비스 클릭
   - 🔴(빨간불) → 🔵(파란불): 서비스 시작
   - 🔵(파란불) → 🔴(빨간불): 서비스 종료

3. **상태 확인**
   - 메뉴를 열 때마다 자동으로 상태 갱신
   - 🔵 = 실행 중 (작업관리자에 프로세스 있음)
   - 🔴 = 중지됨 (프로세스 없음)

4. **종료**
   - 메뉴에서 "종료" 클릭
   - 트레이 앱만 종료됨 (실행 중인 서비스는 그대로 유지)

## 🔍 문제 해결

### 서비스가 시작되지 않는 경우

1. **경로 확인**
   - 지정된 경로에 파일이 존재하는지 확인
   - Python 설치 경로가 `C:\Program Files\Python313\python.exe`인지 확인

2. **포트 충돌**
   - 다른 프로그램이 8765, 8766 포트를 사용 중인지 확인
   - `netstat -ano | findstr "8765"` 명령으로 확인

3. **권한 문제**
   - 관리자 권한으로 실행 시도

### 서비스가 종료되지 않는 경우

1. **수동 종료**
   - 작업관리자에서 해당 프로세스를 직접 종료
   - 포트 기반: `netstat -ano | findstr "포트번호"`로 PID 확인 후 종료

2. **강제 종료**
   ```powershell
   # 포트 8765 사용 프로세스 종료
   taskkill /F /PID [PID번호]
   ```

## 📝 참고사항

- Service Manager는 서비스를 관리만 하며, 자체적으로 서비스를 제공하지 않습니다
- 각 서비스는 독립적으로 실행되므로, Service Manager 종료 후에도 계속 동작합니다
- 시스템 재부팅 시 서비스는 자동으로 시작되지 않습니다 (필요시 수동 시작)
