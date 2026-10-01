# requirement_1 API + 브라우저(E2E) 자동 검증 Report

| 항목 | 내용 |
|------|------|
| **프로젝트** | webOS Subscription Management Dashboard |
| **검증 대상** | requirement_1.md |
| **검증 일시** | 2026-10-01 16:28:55 |
| **대상 URL** | http://127.0.0.1:51362 |
| **대상 커밋** | `e7142f4` |
| **작성자** | 최민석 (PM / TE) |
| **도구** | Python urllib (API), Playwright Chromium (UI) |

**총 33건 중 PASS 33 / FAIL 0 — Pass Rate 100.0%**

| TC ID | 구분 | 테스트 시나리오 | 기대 결과 | 실제 결과 | 판정 |
|:-----:|:----:|----------------|-----------|-----------|:----:|
| API-01 | API | GET /health | 200 + {"status":"ok"} | status=200, body={"status":"ok"} | ✅ PASS |
| API-02 | API | GET /api/subscribers 응답 코드/형식 | 200 + application/json | status=200, content-type=application/json | ✅ PASS |
| API-03 | API | 사용자 수 / ID 목록 | 5명 ['U001', 'U002', 'U003', 'U004', 'U005'] | 5명 ['U001', 'U002', 'U003', 'U004', 'U005'] | ✅ PASS |
| API-04 | API | 필수 필드 및 타입 | userId/name/plan/status=str, deviceCount=int | 이상 없음 | ✅ PASS |
| API-05 | API | 응답 값이 기준 데이터와 일치 | dummy_data.subscribers 와 동일 | 일치 | ✅ PASS |
| API-06 | API | GET / 대시보드 페이지 | 200 + 검색창/필터/Table 요소 존재 | status=200, 누락=[] | ✅ PASS |
| API-07 | API | 정적 파일 제공 (app.js, style.css) | 둘 다 200 | {'/static/app.js': 200, '/static/style.css': 200} | ✅ PASS |
| API-08 | API | POST /api/subscribers (허용되지 않은 메서드) | 405 | status=405 | ✅ PASS |
| UI-01 | UI | 대시보드 접속 시 Table 자동 표시 (TE-2) | 5행 자동 표시 | ['U001', 'U002', 'U003', 'U004', 'U005'] | ✅ PASS |
| UI-02 | UI | 컬럼 순서 및 셀 값 (deviceCount 0 포함) | ID/Name/Plan/Status/Devices 가 데이터와 일치 | 일치 | ✅ PASS |
| UI-03 | UI | Status 열이 badge(span) 로 렌더링 | 5행 모두 span.badge | ['Active', 'Active', 'Paused', 'Active', 'Expired'] | ✅ PASS |
| UI-04 | UI | 키 입력마다 실시간 반영 (페이지 새로고침 없음) | "Ki"→U001 / "Kim"→U001, 페이지 유지 | "Ki"→['U001'], "Kim"→['U001'], 페이지 유지=True | ✅ PASS |
| UI-05 | UI | 검색 "Kim" (TE-3) | U001 Kim Minsoo | ['U001'] | ✅ PASS |
| UI-06 | UI | 검색 "Premium" (TE-4) | ['U001', 'U004'] | ['U001', 'U004'] | ✅ PASS |
| UI-07 | UI | 필터 "Active" (TE-5) | ['U001', 'U002', 'U004'] | ['U001', 'U002', 'U004'] | ✅ PASS |
| UI-08 | UI | 필터 "Expired" (TE-6) | U005 Jung Hyerin | ['U005'] | ✅ PASS |
| UI-09 | UI | 검색 "Kim" + 필터 "Active" (TE-7) | ['U001'] | ['U001'] | ✅ PASS |
| UI-10 | UI | 검색 "Kim" 후 검색어 삭제 (TE-8) | 전체 5행 복원 | ['U001', 'U002', 'U003', 'U004', 'U005'] | ✅ PASS |
| UI-11 | UI | 필터 "Paused" | ['U003'] | ['U003'] | ✅ PASS |
| UI-12 | UI | 필터 "All Status" 로 복귀 | 전체 5행 | ['U001', 'U002', 'U003', 'U004', 'U005'] | ✅ PASS |
| UI-13 | UI | ID 검색 "U003" | ['U003'] | ['U003'] | ✅ PASS |
| UI-14 | UI | 상태 텍스트 검색 "paused" | ['U003'] | ['U003'] | ✅ PASS |
| UI-15 | UI | 대소문자 무시 "KIM" | ['U001'] | ['U001'] | ✅ PASS |
| UI-16 | UI | 부분 문자열 "min" | Kim Minsoo, Choi Sumin | ['U001', 'U004'] | ✅ PASS |
| UI-17 | UI | 검색 "Kim" + 필터 "Expired" (조건 불일치) | 0행 (빈 Table) | 0행 | ✅ PASS |
| UI-18 | UI | 필터 "Active" 유지 + 검색어 입력 후 삭제 | Active 3행 유지 | ['U001', 'U002', 'U004'] | ✅ PASS |
| UI-19 | UI | 없는 검색어 "zzz" | 0행 (빈 Table) | 0행 | ✅ PASS |
| UI-20 | UI | 검색 대상 외 필드 "Yonsei" (organization) | 0행 (검색 대상은 name/plan/status/userId) | 0행 | ✅ PASS |
| UI-21 | UI | selectedUserId 행에 selected 클래스 적용 | U002 1행만 selected | ['U002'] | ✅ PASS |
| UI-22 | UI | 행 클릭 시 selectSubscriber 호출 (오류 없음) | 클릭 시 JS 오류 없음 (선택 강조는 요구사항 #2 에서 완성) | 오류 없음 | ✅ PASS |
| UI-23 | UI | API 500 응답 시 화면 동작 | JS 예외 없이 빈 Table 유지 | 0행, pageerror=0 | ✅ PASS |
| UI-24 | UI | HTML 이 포함된 이름 렌더링 (XSS 방어) | 태그가 아닌 텍스트로 표시 | {'img': False, 'xss': False, 'text': '<img src=x onerror=window.__xss=1>'} | ✅ PASS |
| UI-25 | UI | 전체 실행 중 브라우저 JS 오류 | pageerror 0건 | 0건 [] | ✅ PASS |

> 본 Report 는 `tests/req1_e2e_test.py` 로 생성되었습니다. 실패 시 화면 캡처는 `tests/reports/screenshots/` 에 저장됩니다.
