# requirement_1 테스트 설계서 (TE)

| 항목 | 내용 |
|------|------|
| 대상 요구사항 | `requirement_1.md` — 구독 사용자 조회 + 검색/필터 |
| 대상 구현 | BE `app/api/subscribers.py` (`f2a9b4e`), FE `app/static/app.js` (`b02aae5`) |
| 작성자 | 최민석 (PM / TE) |
| 작성일 | 2026-10-01 |

## 1. 검증 범위

| 포함 | 제외 (이후 요구사항) |
|------|------|
| `GET /api/subscribers` 응답 | 가전 목록 / 사용 현황 / 차트 (요구사항 #2) |
| 대시보드 진입 시 Table 자동 표시 | 상태별 Badge 색상 (요구사항 #3, `badgeClass()`) |
| 이름 / 플랜 / 상태 / ID 검색 | 행 클릭 후 가전 조회 및 선택 강조 (`selectSubscriber()`, 요구사항 #2) |
| Active / Paused / Expired 필터, 검색+필터 조합, 실시간 반영 | |

기대 결과는 `app/data/dummy_data.py`의 사용자 5명을 기준으로 한다. 기능 문제를 덮으려고 더미 데이터를 바꾸지 않는다.

## 2. 구현 코드 분석 → 테스트 포인트

| 구현 (파일) | 코드 동작 | 도출한 테스트 |
|------|------|------|
| BE `get_subscribers()` | `subscribers` 리스트를 그대로 반환 | 200 / JSON / 5명 / 필드·타입 / 값 일치 (API-02~05) |
| BE `main.py` `root()` | Jinja2 템플릿으로 대시보드 반환 | `GET /` 200 + 필수 요소 존재 (API-06) → **BUG-1 발견** |
| FE `fetchSubscribers()` | `fetch("/api/subscribers")`, `!ok` 이면 `console.error` 후 종료 | 자동 표시 (UI-01), API 500 시 JS 예외 없음 (UI-23) |
| FE `renderSubscribers()` 필터 | `statusFilter`가 있으면 `status` 완전 일치 | 3개 상태 필터 + All Status 복귀 (UI-07, 08, 11, 12) |
| FE `renderSubscribers()` 검색 | name/plan/status/userId를 소문자로 바꿔 `includes` | 4개 기준 각각, 대소문자 무시, 부분 문자열, 대상 외 필드(organization) 미검색 (UI-05, 06, 13~16, 20) |
| FE 두 조건 처리 | 필터 `continue` 후 검색 `continue` (AND) | 조합 일치·불일치, 필터 유지 상태에서 검색어 삭제 (UI-09, 17, 18) |
| FE 셀 렌더링 | `textContent` + `?? ""`, status는 `span.badge` | 컬럼 순서·값, `deviceCount = 0` 표시, badge 구조, HTML 문자열이 실행되지 않음 (UI-02, 03, 24) |
| FE `selected` 처리 | `userId === selectedUserId`면 `selected` 클래스 | 선택 클래스 로직 (UI-21), 행 클릭 시 오류 없음 (UI-22) |
| FE 이벤트 바인딩 | 검색 `input`, 필터 `change` → `renderSubscribers` | 한 글자씩 입력할 때마다 새로고침 없이 반영 (UI-04) |

## 3. 테스트 케이스

### 3-1. 요구사항 문서 TE 시나리오 #1~#8

| # | 시나리오 | 기대 결과 | 자동화 TC |
|---|---------|----------|----------|
| 1 | `/api/subscribers` 호출 | 사용자 5명 JSON | TE-1, API-03 |
| 2 | 대시보드 접속 | 5명 자동 표시 | TE-2, UI-01 |
| 3 | 검색 "Kim" | U001 Kim Minsoo | TE-3, UI-05 |
| 4 | 검색 "Premium" | U001, U004 | TE-4, UI-06 |
| 5 | 필터 "Active" | U001, U002, U004 | TE-5, UI-07 |
| 6 | 필터 "Expired" | U005 Jung Hyerin | TE-6, UI-08 |
| 7 | 검색 + 필터 동시 적용 | 두 조건을 모두 만족하는 결과만 | TE-7, UI-09 |
| 8 | 검색어 삭제 | 전체 5명 복원 | TE-8, UI-10 |

### 3-2. 코드 분석으로 추가한 케이스

| TC | 분류 | 시나리오 | 기대 결과 |
|----|------|---------|----------|
| API-01 | API | `GET /health` | 200, `{"status":"ok"}` |
| API-02 | API | `GET /api/subscribers` 형식 | 200, `application/json` |
| API-04 | API | 필수 필드·타입 | 문자열 4개 + `deviceCount` int |
| API-05 | API | 응답 값 | 더미 데이터와 동일 |
| API-06 | API | `GET /` | 200, 검색창·필터·tbody 존재 |
| API-07 | API | 정적 파일 | app.js, style.css 200 |
| API-08 | API | `POST /api/subscribers` | 405 |
| UI-02 | UI | 컬럼·셀 값 | ID/Name/Plan/Status/Devices 일치, `0` 표시 |
| UI-03 | UI | Status 셀 | `span.badge` |
| UI-04 | UI | 실시간 반영 | 키 입력마다 갱신, 페이지 유지 |
| UI-11 | UI | 필터 "Paused" | U003 |
| UI-12 | UI | 필터를 All Status로 복귀 | 5명 |
| UI-13 | UI | ID 검색 "U003" | U003 |
| UI-14 | UI | 상태 텍스트 검색 "paused" | U003 |
| UI-15 | UI | "KIM" (대소문자) | U001 |
| UI-16 | UI | 부분 문자열 "min" | U001, U004 |
| UI-17 | UI | "Kim" + Expired | 0행 |
| UI-18 | UI | Active 유지 + 검색어 입력 후 삭제 | Active 3명 유지 |
| UI-19 | UI | 없는 검색어 "zzz" | 0행 |
| UI-20 | UI | "Yonsei" (검색 대상 외) | 0행 |
| UI-21 | UI | `selectedUserId = U002` | U002만 `selected` |
| UI-22 | UI | 행 클릭 | JS 오류 없음 |
| UI-23 | 예외 | API 500 응답 (route mock) | JS 예외 없이 빈 Table |
| UI-24 | 보안 | 이름에 `<img onerror>` (route mock) | 태그가 아닌 텍스트로 표시 |
| UI-25 | 공통 | 전체 실행 중 JS 오류 | 0건 |

## 4. 자동화 구성

| 파일 | 방식 | 다루는 범위 |
|------|------|------|
| `tests/req1_test_template.py` | 함수 직접 호출 + API + Python 필터 재현 | DEV / API / TE-1~13 |
| `tests/req1_e2e_test.py` | API(urllib) + **실제 Chromium**(Playwright)으로 `app.js` 실행 | API-01~08, UI-01~25 |

`req1_test_template.py`의 `filter_subscribers()`는 JS 규칙을 Python으로 다시 구현한 것이다. 그래서 FE 화면 검증의 근거는 `req1_e2e_test.py` 결과로 판단한다.

두 스크립트 모두 FAIL이 하나라도 있으면 종료 코드 1을 반환하므로 CI의 배포 차단 단계에 그대로 쓸 수 있다.

```bash
pip install -r tests/requirements-te.txt
python -m playwright install chromium
python tests/req1_test_template.py
python tests/req1_e2e_test.py              # --headed : 브라우저 표시, --base-url : 배포 URL 검증
```

## 5. 판정 기준

- PASS: 화면 또는 응답이 기대 결과와 정확히 일치
- FAIL: 불일치, 예외, 시간 초과(5초). 실패 화면은 `tests/reports/screenshots/`에 저장
- 선행 조건 실패(UI-01): 이후 UI 항목은 PASS로 처리하지 않고 "미실행"으로 기록
- 배포 승인 조건: 두 스크립트 모두 FAIL 0건
