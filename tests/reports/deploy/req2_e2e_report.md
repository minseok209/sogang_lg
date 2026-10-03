# requirement_2 API + 브라우저(E2E) 자동 검증 Report

| 항목 | 내용 |
|------|------|
| **프로젝트** | webOS Subscription Management Dashboard |
| **검증 대상** | requirement_2.md (가전 목록 + 사용 현황 + 차트) |
| **검증 일시** | 2026-10-01 17:05:54 |
| **대상 URL** | https://sogang-lg-webos.onrender.com |
| **대상 커밋** | `1540daf` (Render 배포본, 앱 코드는 ed7bc9a와 동일) |
| **작성자** | 최민석 (PM / TE) |
| **도구** | Python urllib (API), Playwright Chromium (UI) |

**총 38건 — PASS 38 / FAIL 0 / BLOCKED 0 — Pass Rate 100.0%**

| TC ID | 구분 | 테스트 시나리오 | 기대 결과 | 실제 결과 | 판정 |
|:-----:|:----:|----------------|-----------|-----------|:----:|
| API-01 | API | GET /api/subscribers/U001/devices (TE-1) | 200 + 가전 2개 [D001, D002] | status=200, ['D001', 'D002'] | ✅ PASS |
| API-02 | API | 가전 없는 사용자 U005 (TE-2) | 200 + [] | status=200, [] | ✅ PASS |
| API-03 | API | 존재하지 않는 사용자 U999 (TE-3) | 404 | status=404 | ✅ PASS |
| API-04 | API | 전체 사용자 가전 목록 값/필드 | 5명 모두 기준 데이터와 일치 (필드 6개) | 일치 | ✅ PASS |
| API-05 | API | deviceCount 와 실제 가전 수 일치 | 5명 모두 일치 | 일치 | ✅ PASS |
| API-06 | API | GET /api/devices/D001/usage (TE-8) | 200 + 사용 현황 JSON | status=200, {'deviceId': 'D001', 'deviceName': 'LG OLED evo C4', 'powerS | ✅ PASS |
| API-07 | API | 사용 현황 필드 9개 + 값 일치 | 기준 데이터 D001 과 동일 | 일치 | ✅ PASS |
| API-08 | API | 존재하지 않는 디바이스 D999 (TE-9) | 404 | status=404, body={'detail': 'Device D999 not found'} | ✅ PASS |
| API-09 | API | 전체 디바이스 8개 사용 현황 | 8개 모두 일치 + 주간 데이터 7개 | 일치 | ✅ PASS |
| API-10 | API | 회귀: GET /api/subscribers | 200 + 5명 | status=200, 5명 | ✅ PASS |
| UI-00 | UI | 초기 화면 (구독자 선택 전) | 안내문구만 표시, 가전 Table·사용현황 상세 숨김 | {'가전 안내문구 표시': True, '가전 Table 숨김': True, '사용현황 안내문구 표시': True, '사용현황 상세 숨김': True} | ✅ PASS |
| UI-01 | UI | U001 클릭 시 가전 Table 표시 (TE-4) | D001, D002 표시 | ['D001', 'D002'], 안내문구 숨김=True | ✅ PASS |
| UI-02 | UI | 가전 컬럼 순서/값 + status badge | ID/Type/Model/Location/Status(badge) 일치 | 일치 | ✅ PASS |
| UI-03 | UI | 클릭한 구독자 행 선택 표시 | U002 1행만 selected | ['U002'] | ✅ PASS |
| UI-04 | UI | U005(가전 없음) 클릭 시 안내 메시지 (TE-5) | "No registered devices" 표시, 행 없음 | 행=[], 'No registered devices' 표시=True | ✅ PASS |
| UI-05 | UI | 가전 검색 "TV" (TE-6) | U001: D001 (TV) | ['D001'] | ✅ PASS |
| UI-06 | UI | 가전 필터 "Online" (TE-7) | U003: D004, D005 | ['D004', 'D005'] | ✅ PASS |
| UI-07 | UI | 모델명 검색 "whisen" (대소문자 무시) | U003: D005 | ['D005'] | ✅ PASS |
| UI-08 | UI | 위치 검색 "Home" | U003: D006 | ['D006'] | ✅ PASS |
| UI-09 | UI | 상태 텍스트 검색 "error" | U003: D006 | ['D006'] | ✅ PASS |
| UI-10 | UI | 디바이스 ID 검색 "D005" | U003: D005 | ['D005'] | ✅ PASS |
| UI-11 | UI | 필터 "Offline" | U001: D002 | ['D002'] | ✅ PASS |
| UI-12 | UI | 필터 "Standby" | U004: D008 | ['D008'] | ✅ PASS |
| UI-13 | UI | 필터 "Error" | U003: D006 | ['D006'] | ✅ PASS |
| UI-14 | UI | 검색 "LG" + 필터 "Online" 동시 적용 | U003: D004, D005 | ['D004', 'D005'] | ✅ PASS |
| UI-15 | UI | 필터 해제 + 검색어 삭제 시 복원 | U003: D004, D005, D006 | ['D004', 'D005', 'D006'] | ✅ PASS |
| UI-16 | UI | 필터 결과 없음 (U001 + Error) | "No devices matched" 표시, 행 없음 | 행=[], 'No devices matched' 표시=True | ✅ PASS |
| UI-17 | UI | 다른 구독자 클릭 시 가전 목록 교체 | U001 목록 → U003 목록으로 교체 | U001=['D001', 'D002'] → U003=['D004', 'D005', 'D006'] | ✅ PASS |
| UI-18 | UI | 가전 검색 실시간 반영 (키 입력) | 입력 즉시 D006, 새로고침 없음 | "Sty"→['D006'], 페이지 유지=True | ✅ PASS |
| UI-19 | UI | D001 클릭 시 사용 현황 표시 (TE-10) | 8개 항목 값 표시, 안내문구 숨김 | 누락 값=[], 상세 표시=True | ✅ PASS |
| UI-20 | UI | Power / Health Status badge | 두 값 모두 span.badge | ['On', 'Normal'] | ✅ PASS |
| UI-21 | UI | D001 클릭 시 Bar Chart (TE-11) | bar, ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], [2, 3, 1, 4, 2, 3, 3] | {'type': 'bar', 'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], 'data': [2, 3, 1, 4, 2, 3, 3], 'count': 1} | ✅ PASS |
| UI-22 | UI | 선택한 가전 행 선택 표시 | D001 1행만 selected | ['D001'] | ✅ PASS |
| UI-23 | UI | 다른 가전 클릭 시 차트 갱신 (TE-12) | D002 데이터로 교체, 차트 1개만 존재 | {'type': 'bar', 'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], 'data': [0, 1, 0, 1, 1, 0, 1], 'count': 1} | ✅ PASS |
| UI-24 | UI | 구독자 변경 시 사용 현황 초기화 | usage-empty 표시, usage-detail 숨김, 내용 비움 | {'usage-empty 표시': True, 'usage-detail 숨김': True, '내용 비움': True} | ✅ PASS |
| UI-27 | UI | 가전 조회 지연 중 이전 사용자 목록 제거 | 조회 중 0행 → 완료 후 U003 목록 | 조회 중=[] → 완료 후=['D004', 'D005', 'D006'] | ✅ PASS |
| UI-25 | UI | 회귀: 구독자 검색 "Kim" (요구사항 #1) | U001 | ['U001'] | ✅ PASS |
| UI-26 | UI | 전체 실행 중 브라우저 JS 오류 | pageerror 0건 | 0건 [] | ✅ PASS |

> 본 Report 는 `tests/req2_e2e_test.py` 로 생성되었습니다. 실패 시 화면 캡처는 `tests/reports/screenshots/req2_*.png` 에 저장됩니다.
