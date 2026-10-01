# requirement_1 검증 Report (TE 실습)

| 항목 | 내용 |
|------|------|
| **프로젝트** | webOS Subscription Management Dashboard |
| **검증 대상** | requirement_1.md |
| **검증 일시** | 2026-10-01 16:28:50 |
| **작성자** | 최민석 (PM / TE) |

**총 17건 중 PASS 17 / FAIL 0 — Pass Rate 100.0%**

| TC ID | 테스트 시나리오 | 기대 결과 | 실제 결과 | 판정 |
|:-----:|----------------|-----------|-----------|:----:|
| DEV-01 | get_subscribers() 함수 직접 호출 | 5명 반환 | 5명 반환 | ✅ PASS |
| API-01 | GET /api/subscribers 호출 | 200 OK | status=200 | ✅ PASS |
| TE-1 | /api/subscribers 호출 | 5명의 사용자 목록 반환 | 5명 | ✅ PASS |
| TE-3 | 검색창에 "Kim" 입력 | Kim Minsoo만 표시 | 1명: ['Kim Minsoo'] | ✅ PASS |
| API-02 | 응답 항목별 필수 필드 포함 여부 | userId/name/plan/status/deviceCount 모두 존재 | 누락 없음 | ✅ PASS |
| API-03 | GET / 대시보드 페이지 응답 | 200 OK + Table(tbody) 존재 | status=200, subscriber-body 있음 | ✅ PASS |
| TE-2 | 대시보드 접속 시 Table 자동 표시 | 5명 목록 표시 | 초기 호출=O, API 호출=O, 표시 대상 5명 | ✅ PASS |
| TE-4 | 검색창에 "Premium" 입력 | Premium 플랜 사용자만 표시 | 2명: ['Kim Minsoo', 'Choi Sumin'] | ✅ PASS |
| TE-5 | 상태 필터 "Active" 선택 | Active 사용자만 표시 | 3명: ['Kim Minsoo', 'Lee Jiyoon', 'Choi Sumin'] | ✅ PASS |
| TE-6 | 상태 필터 "Expired" 선택 | Jung Hyerin만 표시 | 1명: ['Jung Hyerin'] | ✅ PASS |
| TE-7 | 검색 "Premium" + 필터 "Active" 동시 적용 | 두 조건 모두 만족하는 결과만 표시 | 2명: ['Kim Minsoo', 'Choi Sumin'] | ✅ PASS |
| TE-8 | 검색 "Kim" → 검색어 삭제 | 전체 목록(5명) 복원 | 검색 시 1명 → 삭제 후 5명 | ✅ PASS |
| TE-9 | 검색창에 ID "U003" 입력 | Park Junho만 표시 | 1명: ['Park Junho'] | ✅ PASS |
| TE-10 | 소문자 "kim minsoo" 입력 (대소문자 무시) | Kim Minsoo만 표시 | 1명: ['Kim Minsoo'] | ✅ PASS |
| TE-11 | 검색창에 상태 "paused" 입력 | Paused 사용자(Park Junho)만 표시 | 1명: ['Park Junho'] | ✅ PASS |
| TE-12 | 존재하지 않는 검색어 "zzz" 입력 | 0명 (빈 Table) | 0명 | ✅ PASS |
| TE-13 | 검색/필터 결과 실시간 반영 (이벤트 바인딩) | input/change 이벤트에 renderSubscribers 연결 | search(input)=O, filter(change)=O | ✅ PASS |

> 본 Report 는 `tests/req1_test_template.py` 로 생성되었습니다.
