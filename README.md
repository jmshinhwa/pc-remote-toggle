# PC Remote Toggle
# Cloudflare 터널 토글 스위치 + API 키 인증 MCP 서버

## 기능
- 🟢 시스템 트레이 토글 스위치
- 🔐 API 키 인증 (허가된 접근만 가능)
- 🌐 Cloudflare 터널 자동 연결/해제
- 💻 원격에서 PC 명령어 실행 가능

## 설치

### 1. 필수 프로그램
- Python 3.10+
- Cloudflared (Cloudflare 터널 클라이언트)

### 2. Cloudflared 설치
```powershell
# Windows (winget)
winget install Cloudflare.cloudflared

# 또는 직접 다운로드
# https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
```

### 3. 이 레포 클론
```powershell
cd ~/Desktop
git clone https://github.com/jmshinhwa/pc-remote-toggle.git
cd pc-remote-toggle
```

### 4. Python 패키지 설치
```powershell
pip install pystray pillow flask
```

### 5. 실행
```powershell
python toggle_app.py
```

## 사용법

1. 실행하면 시스템 트레이에 아이콘 생김
2. 🔴 아이콘 클릭 → 메뉴에서 "터널 ON" 선택
3. 🟢 터널 URL이 표시됨 → Claude한테 알려주기
4. 끝나면 "터널 OFF" 선택

## 보안

- `config.py`에서 API_KEY 변경 가능
- API 키 없는 요청은 모두 거부됨
- 터널 OFF 하면 외부 접근 완전 차단

## Claude에게 알려줄 정보
1. 터널 URL (매번 바뀜)
2. API_KEY (config.py에 있는 값)
