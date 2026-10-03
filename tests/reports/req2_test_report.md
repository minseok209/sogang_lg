# requirement_2 최종 검증 Report

| 항목 | 내용 |
|------|------|
| 프로젝트 | webOS Subscription Management Dashboard |
| 검증 대상 | `requirement_2.md` — 가전 목록 + 사용 현황 + 주간 사용량 차트 |
| 대상 커밋 | `1b74eca` (BE `2256f30` + FE `bc6748e` + BUG-2 수정) |
| 검증 일시 | 2026-10-01 |
| 검증 환경 | macOS, Python 3.14, FastAPI 0.142 / Starlette 1.7, Playwright 1.63 Chromium, Chart.js (CDN) |
| 작성자 | 최민석 (PM / TE) |
| 테스트 설계 | [`tests/req2_test_plan.md`](../req2_test_plan.md) |

## 1. 결과 요약

| 검증 | 스크립트 | 결과 | 상세 |
|------|------|:----:|------|
| 요구사항 #2 API + 실제 브라우저 E2E | `tests/req2_e2e_test.py` | **38 / 38 PASS** | [req2_e2e_report.md](req2_e2e_report.md) |
| 요구사항 #1 회귀 (E2E) | `tests/req1_e2e_test.py` | **33 / 33 PASS** | 같은 커밋에서 재실행 |
| 요구사항 #1 회귀 (템플릿) | `tests/req1_test_template.py` | **17 / 17 PASS** | 같은 커밋에서 재실행 |

**종합 판정: PASS. `main` 반영을 승인한다.**

## 2. 완료 조건 대조

| 완료 조건 | 근거 TC | 판정 |
|------|------|:----:|
| `GET /api/subscribers/{userId}/devices` API가 정상 동작한다 | API-01, 02, 04, 05 | ✅ |
| 구독자 행 클릭 시 가전 목록이 Table에 표시된다 | UI-01~03, 17, 27 | ✅ (BUG-2 수정 후) |
| 가전이 없는 사용자 선택 시 안내 메시지가 표시된다 | UI-04 | ✅ |
| 모델명 / 타입 / 상태 / 위치 기준 검색이 동작한다 | UI-05, 07~10, 14, 15, 18 | ✅ |
| Online / Offline / Standby / Error 상태 필터가 동작한다 | UI-06, 11~13, 16 | ✅ |
| 존재하지 않는 사용자 ID 요청 시 404 에러를 반환한다 | API-03 | ✅ |
| `GET /api/devices/{deviceId}/usage` API가 정상 동작한다 | API-06, 07, 09 | ✅ |
| 가전 행 클릭 시 사용 현황 정보가 표시된다 | UI-19, 20, 22, 24 | ✅ |
| 주간 사용량이 Bar Chart(요일 기준)로 표시된다 | UI-21, 23 | ✅ |
| 존재하지 않는 디바이스 ID 요청 시 404 에러를 반환한다 | API-08 | ✅ |
| TE의 검증 Report가 작성되었다 | 본 문서 | ✅ |

## 3. 요구사항 문서 TE 시나리오 결과

| # | 테스트 시나리오 | 예상 결과 | 실제 결과 | 결과 |
|---|----------------|----------|-----------|:----:|
| 1 | `/api/subscribers/U001/devices` 호출 | 2개 가전 JSON 반환 | 200, D001, D002 | ✅ PASS |
| 2 | `/api/subscribers/U005/devices` 호출 | 빈 배열 `[]` 반환 | 200, `[]` | ✅ PASS |
| 3 | `/api/subscribers/U999/devices` 호출 | 404 에러 반환 | 404 | ✅ PASS |
| 4 | U001 클릭 시 가전 Table 표시 | D001, D002 표시 | D001, D002 | ✅ PASS |
| 5 | U005 클릭 시 안내 메시지 | "No registered devices" 표시 | 메시지 표시, 0행 | ✅ PASS |
| 6 | 가전 검색 "TV" 입력 | TV 타입만 표시 | U001 → D001 | ✅ PASS |
| 7 | 가전 상태 필터 "Online" 선택 | Online 가전만 표시 | U003 → D004, D005 | ✅ PASS |
| 8 | `/api/devices/D001/usage` 호출 | 사용 현황 JSON 반환 | 200, 9개 필드 기준 데이터와 일치 | ✅ PASS |
| 9 | `/api/devices/D999/usage` 호출 | 404 에러 반환 | 404 | ✅ PASS |
| 10 | D001 클릭 시 사용 현황 표시 | 전원 상태, 누적 시간 등 표시 | 8개 항목 표시, Power/Health는 badge | ✅ PASS |
| 11 | D001 클릭 시 Bar Chart 표시 | 요일별 사용량 차트 | bar, Mon~Sun, [2, 3, 1, 4, 2, 3, 3] | ✅ PASS |
| 12 | 다른 가전 클릭 시 차트 갱신 | 이전 차트 제거, 새 차트 표시 | D002 데이터로 교체, 차트 인스턴스 1개 | ✅ PASS |

## 4. 발견 결함

| ID | 내용 | 심각도 | 담당 | 상태 |
|----|------|:------:|:----:|:----:|
| CSS-1 | `.usage-detail`이 `.hidden`을 덮어써 사용 현황 상세 영역이 숨겨지지 않음 (스켈레톤 CSS) | 중간 | FE | FE가 구현 시 수정 (`bc6748e`) · PASS |
| BUG-2 | 구독자를 바꾼 직후 가전을 조회하는 동안 이전 구독자의 가전 목록이 남아 클릭 가능 → 다른 사용자의 사용 현황이 표시됨 | 중간 | FE | TE가 수정 (`1b74eca`) · 재검증 PASS |

**BUG-2 상세**

- 발견 경위: FE 코드 리뷰. `selectSubscriber()`가 가전 조회 응답을 받기 전까지 `currentDevices`와 Table을 그대로 둔다.
- 재현:
  1. U001을 클릭해 D001, D002를 띄운다.
  2. U003의 가전 조회 응답이 1.5초 늦게 오도록 지연시키고 U003을 클릭한다.
  3. 응답이 오기 전에 화면에 남아 있는 D001을 클릭한다.
  4. 결과: 화면에 U003의 가전 목록(D004~D006)과 **U001 소유인 D001의 사용 현황**이 함께 표시된다.
- 영향: 로컬에서는 응답이 빨라 잘 드러나지 않는다. 배포 환경(Render 무료 인스턴스 등)처럼 응답이 느리면 사용자에게 잘못된 정보를 보여줄 수 있다.
- 조치: 조회를 시작할 때 `currentDevices = undefined`로 비우고 "Loading devices..." 메시지를 표시한다 (`app/static/app.js` 5줄).
- 재검증: 회귀 테스트 UI-27을 추가했다. 수정 전 코드에서는 FAIL(조회 중 D001, D002가 남음), 수정 후에는 PASS(조회 중 0행). 전체 38/38 PASS.

## 5. 참고 (요구사항 #2 범위 외)

- 상태 Badge 색상이 아직 적용되지 않는다. `badgeClass()`가 요구사항 #3에서 구현할 부분이다.
- 구독자를 바꿔도 가전 검색어와 상태 필터는 유지된다. 요구사항에 정해진 동작이 없어 결함으로 보지 않았다.
- BE와 FE 모두 요구사항 #2 문서의 브랜치 → PR 방식 대신 `main`에 직접 push했다. 다음 요구사항부터는 PR로 올린 뒤 이 Report 기준으로 머지하도록 안내한다 (PM).
