# macOS 설치 및 실행 가이드 (초보자용)

이 문서는 **터미널 사용 없이** 더블클릭으로 실행하는 방법까지 안내합니다.

## 1) 파이썬 설치
1. [python.org](https://www.python.org/downloads/macos/)에서 **Python 3** 최신 버전을 다운로드합니다.
2. 설치 파일을 실행하고 안내에 따라 설치합니다.
3. 설치가 끝나면 **응용 프로그램 > 터미널**에서 아래 명령으로 확인합니다.
   ```bash
   python3 --version
   ```

## 2) 프로젝트 준비
1. 이 저장소를 다운로드(또는 압축 해제)합니다.
2. 다운로드한 폴더를 열고, 다음 파일이 있는지 확인합니다.
   - `app.py`
   - `routine_tracker.py`
   - `requirements.txt`

## 3) 필수 패키지 설치
터미널에서 프로젝트 폴더로 이동한 뒤 아래를 실행합니다.
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## 4) 더블클릭 실행 (가장 쉬운 방법)
### 방법 A: launch.command (가장 간단)
1. `launch.command` 파일을 더블클릭합니다.
2. 처음 실행 시 보안 경고가 나오면 **시스템 설정 > 개인정보 보호 및 보안**에서 허용합니다.
3. 브라우저가 자동으로 열리며 `http://localhost:8501`에서 앱이 실행됩니다.

### 방법 B: 앱(.app) 생성 후 더블클릭
1. 터미널에서 아래 명령을 실행합니다.
   ```bash
   bash build_mac_app.sh
   ```
2. 같은 폴더에 `Routine Score Tracker.app`이 생성됩니다.
3. 해당 앱을 더블클릭하면 브라우저가 자동으로 열립니다.

## 5) 종료 방법
- 브라우저 탭을 닫아도 서버는 백그라운드에서 계속 실행될 수 있습니다.
- 완전히 종료하려면 **활동 모니터**에서 `python3` 프로세스를 종료하거나, 터미널에서:
  ```bash
  pkill -f streamlit
  ```

## 6) 문제 해결
- 브라우저가 열리지 않으면 직접 `http://localhost:8501`로 접속하세요.
- 포트 충돌 시 `launch.command` 또는 `build_mac_app.sh`에서 `--server.port` 숫자를 변경하세요.
