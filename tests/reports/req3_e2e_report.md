# requirement_3 상태 Badge 자동 검증 Report

| 항목 | 내용 |
|------|------|
| **프로젝트** | webOS Subscription Management Dashboard |
| **검증 대상** | requirement_3.md Part A (상태 기반 UI 표현) |
| **검증 일시** | 2026-10-01 17:08:44 |
| **대상 URL** | http://127.0.0.1:55044 |
| **대상 커밋** | `07aa007` |
| **작성자** | 최민석 (PM / TE) |
| **도구** | Playwright Chromium (class + computed background-color) |

**총 19건 중 PASS 19 / FAIL 0 — Pass Rate 100.0%**

| TC ID | 구분 | 테스트 시나리오 | 기대 결과 | 실제 결과 | 판정 |
|:-----:|:----:|----------------|-----------|-----------|:----:|
| FN-01 | FN | 상태 값 12종 매핑 | Active/Online/Normal→status-active … Off→status-off | 전부 일치 | ✅ PASS |
| FN-02 | FN | 대소문자 무시 (ACTIVE, online, warning) | 각 값의 매핑 클래스 | 전부 일치 | ✅ PASS |
| FN-03 | FN | 그 외 값 (Unknown, 빈 문자열, null) | "badge" | 전부 일치 | ✅ PASS |
| UI-01 | UI | 구독 상태 Active (TE-1) | Active=초록 | Active=초록, Active=초록, Active=초록 | ✅ PASS |
| UI-02 | UI | 구독 상태 Paused (TE-2) | Paused=파랑 | Paused=파랑 | ✅ PASS |
| UI-03 | UI | 구독 상태 Expired (TE-3) | Expired=빨강 | Expired=빨강 | ✅ PASS |
| UI-04 | UI | 가전 상태 Online (TE-4) | Online=초록 | Online=초록 | ✅ PASS |
| UI-05 | UI | 가전 상태 Offline (TE-5) | Offline=회색 | Offline=회색 | ✅ PASS |
| UI-06 | UI | 가전 상태 Error (TE-6) | Error=빨강 | Error=빨강 | ✅ PASS |
| UI-07 | UI | 가전 상태 Standby (보강) | Standby=파랑 | Standby=파랑 | ✅ PASS |
| UI-08 | UI | D001 Power On (TE-7) | On=노랑 | On=노랑 | ✅ PASS |
| UI-09 | UI | D001 Health Normal (TE-8) | Normal=초록 | Normal=초록 | ✅ PASS |
| UI-10 | UI | D006 Health Warning (TE-9) | Warning=빨강 | Warning=빨강 | ✅ PASS |
| UI-11 | UI | D006 Power Error | Error=빨강 | Error=빨강 | ✅ PASS |
| UI-12 | UI | D002 Power Off | Off=연회색 | Off=연회색 | ✅ PASS |
| UI-13 | UI | D007 Power Cleaning | Cleaning=노랑 | Cleaning=노랑 | ✅ PASS |
| UI-14 | UI | D004 Power Standby | Standby=파랑 | Standby=파랑 | ✅ PASS |
| UI-15 | UI | 매핑 대상 값이 기본 badge 로 남은 곳 | 0건 | 0건 | ✅ PASS |
| UI-16 | UI | 실행 중 브라우저 JS 오류 | pageerror 0건 | 0건 [] | ✅ PASS |

> 본 Report 는 `tests/req3_e2e_test.py` 로 생성되었습니다.
