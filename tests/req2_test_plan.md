# requirement_2 테스트 설계서 (TE)

| 항목 | 내용 |
|------|------|
| 대상 요구사항 | `requirement_2.md` — 가전 목록 + 사용 현황 + 주간 사용량 차트 |
| 기준 코드 | `main` `125dec8` (요구사항 #1 검증 완료 시점) |
| 작성자 | 최민석 (PM / TE) |
| 작성일 | 2026-10-01 |
| 자동화 | `tests/req2_e2e_test.py` (API 10건 + UI 27건) |

## 1. 검증 범위

| 포함 | 제외 |
|------|------|
| `GET /api/subscribers/{userId}/devices` (정상 / 빈 목록 / 404) | 상태별 Badge **색상** (요구사항 #3 `badgeClass()`) |
| `GET /api/devices/{deviceId}/usage` (정상 / 404) | 배포 환경 검증 (배포 후 `--base-url`로 별도 실행) |
| 구독자 클릭 → 가전 Table, 안내 메시지 2종 | |
| 가전 검색 (type / model / status / deviceId / location), 상태 필터 4종 | |
| 가전 클릭 → 사용 현황 8개 항목, Bar Chart, 차트 갱신 | |
| 요구사항 #1 회귀 (구독자 API / 검색) | |

기대 결과는 `app/data/dummy_data.py`(`devices_by_user`, `usage_by_device`)를 기준으로 한다.

## 2. 현재 구현 상태 (기준 코드 분석)

| 대상 | 파일 | 상태 | 비고 |
|------|------|:----:|------|
| 가전 목록 API | `app/api/subscribers.py` | ✅ 구현됨 | U001 → 2개, U005 → `[]`, U999 → 404 확인 |
| 사용 현황 API | `app/api/devices.py` | ✅ 구현됨 (`2256f30`) | API-01~10 전부 PASS (2026-10-01) |
| `selectSubscriber` / `renderDevices` / `selectDevice` / `renderUsageChart` | `app/static/app.js` | ❌ 미구현 | 주석만 있음 |
| 가전 검색·필터 이벤트 | `app/static/app.js` `bindEvents()` | ❌ 주석 처리 | |

### ⚠️ 사전 발견 이슈: CSS-1 (FE 참고)

`app/static/style.css`에서 `.usage-detail { display: flex; }`가 `.hidden { display: none; }`보다 **뒤에** 같은 우선순위로 선언돼 있다. 그래서 `usage-detail`에 `hidden` 클래스를 붙여도 화면에서 숨겨지지 않는다.

- 영향: 첫 화면부터 빈 사용 현황 상세 영역이 보인다. 구독자를 바꿔 "사용 현황 초기화"를 해도 상세 영역이 남는다 (UI-00, UI-24 FAIL).
- 수정 예: `.hidden { display: none !important; }`. 또는 `.usage-detail.hidden { display: none; }`을 추가한다.
- 근거: 요구사항 문서대로 만든 참조 구현으로 실행하면 원본 CSS에서는 35/37, CSS를 수정하면 37/37이다.

## 3. 테스트 케이스

### 3-1. 요구사항 문서 TE 시나리오 #1~#12 → 자동화 TC

| # | 시나리오 | 예상 결과 | TC |
|---|---------|----------|----|
| 1 | `/api/subscribers/U001/devices` | 가전 2개 JSON | API-01 |
| 2 | `/api/subscribers/U005/devices` | `[]` | API-02 |
| 3 | `/api/subscribers/U999/devices` | 404 | API-03 |
| 4 | U001 클릭 | D001, D002 표시 | UI-01 |
| 5 | U005 클릭 | "No registered devices" | UI-04 |
| 6 | 가전 검색 "TV" | TV 타입만 (U001 → D001) | UI-05 |
| 7 | 상태 필터 "Online" | Online만 (U003 → D004, D005) | UI-06 |
| 8 | `/api/devices/D001/usage` | 사용 현황 JSON | API-06, API-07 |
| 9 | `/api/devices/D999/usage` | 404 | API-08 |
| 10 | D001 클릭 | 전원 상태, 누적 시간 등 표시 | UI-19, UI-20 |
| 11 | D001 클릭 시 Bar Chart | 요일별 사용량 차트 | UI-21 |
| 12 | 다른 가전 클릭 | 이전 차트 제거, 새 차트 표시 | UI-23 |

### 3-2. 보강 케이스 (완료 조건과 FE 지침에서 도출)

| TC | 시나리오 | 기대 결과 | 근거 |
|----|---------|----------|------|
| API-04 | 5명 전체 가전 목록 | 기준 데이터와 일치 (필드 6개) | 데이터 구조 명세 |
| API-05 | `deviceCount` vs 실제 가전 수 | 5명 모두 일치 | 화면 Devices 열과 목록의 일관성 |
| API-09 | 디바이스 8개 전체 사용 현황 | 일치 + 주간 데이터 7개 | 차트 입력값 |
| API-10 | 회귀: `/api/subscribers` | 5명 | 요구사항 #1 |
| UI-00 | 초기 화면 | 안내 문구만 보이고 가전 Table·사용 현황 상세는 숨김 | HTML 초기 상태 |
| UI-02 | 가전 컬럼·값 | ID/Type/Model/Location/Status, status는 `span.badge` | FE Step 2-4 |
| UI-03 | 구독자 행 선택 표시 | 클릭한 행만 `selected` | FE Step 1-2 (요구사항 #1에서 보류한 항목) |
| UI-07~10 | 모델명(대소문자 무시) / 위치 / 상태 텍스트 / ID 검색 | 해당 가전만 | 완료 조건 "모델명/타입/상태/위치 검색" |
| UI-11~13 | Offline / Standby / Error 필터 | 해당 가전만 | 완료 조건 "상태 필터 4종" |
| UI-14 | 검색 + 필터 동시 적용 | AND 조합 | |
| UI-15 | 필터 해제 + 검색어 삭제 | 전체 복원 | |
| UI-16 | 필터 결과 없음 | "No devices matched" | FE Step 2-3 |
| UI-17 | 다른 구독자 클릭 | 가전 목록 교체 | |
| UI-18 | 키 입력 실시간 반영 | 새로고침 없이 갱신 | 이벤트 바인딩 |
| UI-22 | 가전 행 선택 표시 | 클릭한 가전만 `selected` | FE Step 3-2 |
| UI-24 | 가전 선택 후 구독자 변경 | 사용 현황 초기화 | FE Step 1-3 |
| UI-25 | 회귀: 구독자 검색 "Kim" | U001 | 요구사항 #1 |
| UI-26 | 전체 실행 중 JS 오류 | 0건 | |

## 4. 판정 기준

- **PASS**: 화면 또는 응답이 기대 결과와 일치
- **FAIL**: 불일치, 예외, 시간 초과(3~5초). 실패 화면은 `tests/reports/screenshots/req2_*.png`에 저장
- **BLOCKED**: 선행 조건이 실패해 실행할 수 없음. 사용 현황 API(API-06) 또는 가전 목록 화면(UI-01)이 실패하면 UI-19~24는 BLOCKED로 기록한다. BLOCKED는 PASS로 세지 않는다.
- 종료 코드: 전부 PASS일 때만 0. FAIL이나 BLOCKED가 하나라도 있으면 1 → PR 머지 기준으로 쓴다.

화면 판정은 FE 구현 방식에 묶이지 않도록 다음 기준만 사용한다.

| 대상 | 판정 기준 |
|------|------|
| 행 | `#device-body`에서 실제로 보이는 `tr`의 첫 번째 셀 ID |
| 안내 메시지 | Devices 패널에 보이는 텍스트 |
| 숨김 여부 | 요소가 실제 화면에 렌더링되는지 (`getClientRects`) |
| 차트 | `Chart.getChart('usageChart')`의 type, labels, data와 전체 차트 인스턴스 수 |

## 5. 실행 방법

```bash
pip install -r tests/requirements-te.txt
python -m playwright install chromium
python tests/req2_e2e_test.py              # --headed : 브라우저 표시
python tests/req2_e2e_test.py --base-url https://<배포 URL>
```

## 6. 스크립트 사전 검증 결과

| 대상 코드 | 결과 | 해석 |
|------|------|------|
| 현재 `main` (`125dec8`, 구현 전) | PASS 8 / FAIL 23 / BLOCKED 6 | 이미 구현된 가전 목록 API와 회귀 항목만 PASS, 나머지는 기대대로 FAIL/BLOCKED |
| 요구사항 문서대로 만든 참조 구현 + 원본 CSS | PASS 35 / FAIL 2 | CSS-1 이슈만 FAIL (UI-00, UI-24) |
| 참조 구현 + CSS-1 수정 | **PASS 37 / FAIL 0** | 올바른 구현은 전부 통과함 → 스크립트 신뢰 가능 |

참조 구현은 스크립트를 검증하기 위한 임시 코드다. 저장소에는 커밋하지 않았다.
