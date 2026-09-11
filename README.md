# LMS 미납자 관리 자동화

LMS(토크스테이션) 관리자 페이지의 '수강료관리 > 일일정산달력'에서 미납자(원어민 미납)
인원수를 자동으로 조회해 일별 보고서 텍스트를 만들어주는 사내 자동화 도구.

## 기술 스택

- Frontend/실행파일: Electron + electron-store
- 자동화: Python 3.x + Selenium 4.6+ (Selenium Manager로 드라이버 자동 관리, headless 금지)
- Electron ↔ Python 통신: `child_process.spawn`으로 Python 워커 실행,
  Python은 stdout에 진행 상황을 한 줄씩 JSON으로 출력
  (`{"type":"period","kind":"month","label":"9월","status":"success","count":107}`)
- 클립보드 복사: pyperclip (Python 스크립트를 통해 처리)

## 폴더 구조

```
electron/                 Electron 프론트
  main/                    메인 프로세스 (창 생성, IPC, python 워커 spawn)
  renderer/                렌더러 (사이드바, 미납자 관리 화면)
python/                   자동화 워커 (Electron과 완전 분리)
  worker/
    main.py                entrypoint (--job, stdin으로 설정 JSON 수신)
    control.py             일시정지/중단 제어
    lms/                   LMS 화면 조작 (로그인, 네비게이션, 미납자 조회)
    jobs/                  작업 오케스트레이션 (미납자 보고, 수동 조회, 로그인 테스트)
    utils/                 progress emit, 기간 계산(periods.py), /data 백업, clipboard(pyperclip)
data/                     작업 결과 백업 (/data/YYYYMMDD/작업명.json, gitignore)
log/                      실행 로그 (gitignore)
```

새 작업을 추가할 때:
1. `python/worker/jobs/`에 새 작업 파일 추가, `worker/main.py`의 `JOBS`에 등록
2. `electron/renderer/js/views/`에 새 뷰 파일 추가, `app.js`의 `VIEW_RENDERERS`에 등록
3. `electron/renderer/js/sidebar.js`의 `JOBS` 배열에 사이드바 항목 추가

## 초기 설정

```bash
npm install

python3 -m venv .venv          # (선택) 가상환경
source .venv/bin/activate
pip install -r python/requirements.txt

cp .env.example .env           # 값만 채우기 (다른 LMS 자동화 도구와 동일한 .env를 재사용해도 됨)
```

`.env`에 채워야 하는 값:

- `LMS_ID`, `LMS_PASSWORD`
- `LMS_BASE_URL` (TODO: 실제 로그인 페이지 URL 확정 필요)

## 실행

```bash
npm start
```

사이드바 "설치가 필요한 목록"에서 Selenium 미설치가 감지되면 클릭 후
설치 확인 팝업에서 확인을 누르면 `pip install -r python/requirements.txt`가
자동 실행된다.

## 사용 방법 (미납자 관리 화면)

1. "LMS 로그인 테스트"로 로그인이 되는지 먼저 확인한다.
2. "직접 기간 조회"에서 임의의 기간(기본값: 어제 하루)을 넣고 결과가 잘 나오는지 확인한다.
3. "기준일"(기본값: 오늘)을 확인한 뒤 "보고서 생성 시작"을 누르면,
   - 2023-01-01부터 기준일의 전날까지를 6개월 단위로 나눠 순서대로 조회하고,
   - 기준일의 전날이 속한 달(부분월)과 그 이전 4개월도 함께 조회해서,
   - 아래 "보고서 요약"에 최종 보고서 텍스트를 만들어준다. "결과 클립보드 복사"로 바로 공유 가능.

## 현재 상태 / 다음 단계

`python/worker/lms/auth.py`, `navigation.py`의 로그인 폼/LNB 메뉴 선택자는 아직
실제 화면을 보고 확정한 것이 아니라 TODO로 표시되어 있다 (일일정산달력 페이지 내부의
날짜 입력/검색/결과 파싱 선택자는 실제 제공된 HTML 기준으로 확정되어 있음). 처음
실행할 때 "LMS 로그인 테스트"와 "직접 기간 조회"로 먼저 확인하면서, 안 되는 부분의
`driver.find_element(...)` 선택자를 실제 화면에 맞게 수정하면 된다.
