# requirement_1 최종 검증 Report

| 항목 | 내용 |
|------|------|
| 프로젝트 | webOS Subscription Management Dashboard |
| 검증 대상 | `requirement_1.md` — 구독 사용자 조회 + 검색/필터 |
| 대상 커밋 | `e7142f4` (BE `f2a9b4e` + FE `b02aae5` + BUG-1 수정) |
| 검증 일시 | 2026-10-01 |
| 검증 환경 | macOS, Python 3.14, FastAPI 0.142 / Starlette 1.7 / Uvicorn 0.54, Playwright 1.63 Chromium |
| 작성자 | 최민석 (PM / TE) |
| 테스트 설계 | [`tests/req1_test_plan.md`](../req1_test_plan.md) |

## 1. 결과 요약

| 검증 단계 | 스크립트 | 결과 | 상세 |
|------|------|:----:|------|
| 개발자 + API + TE 시나리오 (Python 재현) | `tests/req1_test_template.py` | **17 / 17 PASS** | [req1_report_template.md](req1_report_template.md) |
| API + 실제 브라우저 E2E (Chromium) | `tests/req1_e2e_test.py` | **33 / 33 PASS** | [req1_e2e_report.md](req1_e2e_report.md) |

**종합 판정: PASS. 배포를 승인한다.**

## 2. 완료 조건 대조

| 완료 조건 | 근거 TC | 판정 |
|------|------|:----:|
| `GET /api/subscribers` API가 정상 동작한다 | API-01~05, API-08, DEV-01, TE-1 | ✅ |
| 대시보드 진입 시 구독자 목록이 Table에 자동 표시된다 | API-06, UI-01~03 | ✅ (BUG-1 수정 후) |
| 이름 / 플랜 / 상태 / ID 기준 검색이 동작한다 | UI-05, 06, 13~16, 19, 20 | ✅ |
| Active / Paused / Expired 상태 필터가 동작한다 | UI-07, 08, 11, 12 | ✅ |
| 검색/필터 결과가 실시간 반영된다 | UI-04, 09, 10, 17, 18 | ✅ |
| TE의 검증 Report가 작성되었다 | 본 문서 | ✅ |

## 3. 요구사항 문서 TE 시나리오 결과

| # | 테스트 시나리오 | 예상 결과 | 실제 결과 (브라우저) | 결과 |
|---|----------------|----------|-----------|:----:|
| 1 | `/api/subscribers` 호출 | 5명의 사용자 목록 JSON 반환 | 200, 5명 (U001~U005) | ✅ PASS |
| 2 | 대시보드 접속 시 Table 자동 표시 | 5명 목록 표시 | 5행 자동 표시 | ✅ PASS |
| 3 | 검색창에 "Kim" 입력 | Kim Minsoo만 표시 | U001 | ✅ PASS |
| 4 | 검색창에 "Premium" 입력 | Premium 플랜 사용자만 표시 | U001, U004 | ✅ PASS |
| 5 | 상태 필터 "Active" 선택 | Active 사용자만 표시 | U001, U002, U004 | ✅ PASS |
| 6 | 상태 필터 "Expired" 선택 | Jung Hyerin만 표시 | U005 | ✅ PASS |
| 7 | 검색 + 필터 동시 적용 ("Kim" + Active) | 두 조건 모두 만족하는 결과만 표시 | U001 | ✅ PASS |
| 8 | 검색어 삭제 시 | 전체 목록 복원 | 5행 복원 | ✅ PASS |

## 4. 발견 결함

| ID | 내용 | 심각도 | 담당 | 상태 |
|----|------|:------:|:----:|:----:|
| BUG-1 | 대시보드 `GET /`가 **500 Internal Server Error**를 반환해 화면이 표시되지 않음 | 높음 (배포 차단) | BE | 수정 완료 · 재검증 PASS |

**BUG-1 상세**

- 재현: `pip install -r requirements.txt`로 설치한 뒤 `uvicorn app.main:app` 실행 → `http://localhost:8000` 접속하면 500
- 원인: `requirements.txt`에 버전 고정이 없어 Starlette 1.x가 설치된다. 이 버전에는 `templates.TemplateResponse("index.html", {"request": request})` 구형 호출 방식이 없어 `TypeError: unhashable type: 'dict'`가 발생한다. API(`/api/subscribers`)는 정상이라 BE의 curl 확인만으로는 드러나지 않았다.
- 조치: `app/main.py`를 `templates.TemplateResponse(request, "index.html")`로 수정 (`e7142f4`)
- 재검증: API-06, UI-01~25 전부 PASS
- 영향: Render는 배포할 때마다 최신 패키지를 설치하므로, 수정하지 않았다면 배포 서비스도 같은 문제를 겪었을 것이다.

## 5. 테스트 유효성 확인 (대조군)

테스트가 실제 결함을 잡아내는지 일부러 결함을 넣어 확인했다. 확인 후 원래 코드로 되돌렸다.

| 대조군 | 결과 |
|------|------|
| `main.py` 수정 전 원본 | API-06, UI-01 FAIL → 이후 UI 항목은 "미실행"으로 차단, 종료 코드 1 |
| `app.js`에서 상태 필터 조건 제거 | UI-07, 08, 11, 17, 18 FAIL (5건), 종료 코드 1 |

## 6. 범위 외 참고사항 (결함 아님)

- 행을 클릭해도 선택 강조와 가전 조회가 일어나지 않는다. `selectSubscriber()`가 아직 비어 있기 때문이며 요구사항 #2 범위다. `renderSubscribers()`의 `selected` 클래스 로직 자체는 UI-21에서 정상 동작을 확인했다.
- 상태 Badge 색상이 적용되지 않는다. `badgeClass()`가 요구사항 #3 범위로 미구현 상태다.
- 권고: 같은 종류의 문제가 다시 생기지 않도록 `requirements.txt`에 검증한 버전을 고정할 것을 검토한다 (PM 판단).
