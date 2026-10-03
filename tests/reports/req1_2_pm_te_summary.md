# 요구사항 #1 · #2 PM / TE 활동 요약 Report

| 항목 | 내용 |
|------|------|
| 작성자 | 최민석 (PM / TE) |
| 기간 | 2026-10-01 |
| 저장소 | https://github.com/minseok209/sogang_lg |
| 기준 커밋 | `8ef5473` (요구사항 #2 검증 완료 merge) |

## 1. 진행 흐름

| 단계 | 요구사항 #1 | 요구사항 #2 |
|------|------|------|
| 요구사항 배분 (PM) | BE: `GET /api/subscribers`<br>FE: Table + 검색/필터 | BE: 가전 목록·사용 현황 API<br>FE: 가전 Table, 사용 현황, 차트 |
| 개발 | BE `f2a9b4e`, FE `b02aae5` | BE `2256f30`, FE `bc6748e` |
| 테스트 설계 (TE) | `tests/req1_test_plan.md` | `tests/req2_test_plan.md` (개발 전에 작성) |
| 자동 검증 (TE) | 템플릿 17건 + E2E 33건 | E2E 38건 |
| 결함 수정 | BUG-1 (`e7142f4`) | CSS-1 (FE 수정), BUG-2 (`1b74eca`) |
| 최종 판정 | PASS → `main` 반영 (`125dec8`) | PASS → `main` 반영 (`8ef5473`) |

## 2. 검증 결과

| 요구사항 | 스크립트 | 결과 | 상세 Report |
|------|------|:----:|------|
| #1 | `tests/req1_test_template.py` | 17 / 17 PASS | `req1_report_template.md` |
| #1 | `tests/req1_e2e_test.py` | 33 / 33 PASS | `req1_e2e_report.md`, `req1_test_report.md` |
| #2 | `tests/req2_e2e_test.py` | 38 / 38 PASS | `req2_e2e_report.md`, `req2_test_report.md` |

요구사항 #2 검증 시점에 요구사항 #1 스크립트도 다시 실행해 회귀가 없음을 확인했다.

## 3. 발견 결함과 조치

| ID | 요구사항 | 내용 | 발견 방법 | 조치 |
|----|:----:|------|------|------|
| BUG-1 | #1 | 대시보드 `/`가 500 에러. 최신 Starlette 1.x에서 구형 `TemplateResponse` 호출 방식이 제거됨 | 자동 테스트 (API-06) | `app/main.py` 한 줄 수정 |
| CSS-1 | #2 | `.usage-detail`이 `.hidden`을 덮어써 사용 현황 영역이 숨겨지지 않음 (스켈레톤 CSS) | 개발 전 참조 구현으로 스크립트를 검증하다가 발견 | FE에 사전 공유 → FE가 수정 |
| BUG-2 | #2 | 구독자를 바꾼 직후 조회 중에 이전 사용자의 가전이 남아, 다른 사용자의 사용 현황이 표시됨 | FE 코드 리뷰 + 응답 지연 재현 | `app.js` 5줄 수정 + 회귀 테스트 UI-27 추가 |

세 건 모두 API를 curl로 확인하는 것만으로는 드러나지 않았다. 실제 브라우저로 화면을 검증해서 찾았다.

## 4. TE 산출물

| 파일 | 내용 |
|------|------|
| `tests/req1_test_plan.md`, `tests/req2_test_plan.md` | 구현 코드를 분석해 도출한 테스트 설계서 |
| `tests/req1_test_template.py` | 학생용 템플릿의 TODO 완성 (TE 시나리오 #1~#8 + 보강) |
| `tests/req1_e2e_test.py`, `tests/req2_e2e_test.py` | Playwright Chromium 기반 API + UI 자동 검증 |
| `tests/reports/` | 자동 생성 Report와 최종 검증 Report |
| `tests/requirements-te.txt` | 테스트용 의존성 (playwright) |

테스트 스크립트를 만들 때 지킨 원칙은 다음과 같다.

- 실제 화면 기준으로 판정한다. Python으로 필터 규칙을 다시 구현한 결과는 FE 검증의 근거로 쓰지 않는다.
- 선행 조건이 실패하면 이후 항목은 PASS로 세지 않고 BLOCKED 또는 미실행으로 기록한다.
- FAIL이 하나라도 있으면 종료 코드 1을 반환한다. 그래서 CI에서 그대로 쓸 수 있다.
- 결함을 일부러 넣은 대조군으로 테스트가 실제로 결함을 잡는지 확인한다.

## 5. PM 관점 개선 사항

| 항목 | 현황 | 다음 조치 |
|------|------|------|
| 브랜치 전략 | BE와 FE가 `main`에 직접 push함 (요구사항 #2 문서는 feature 브랜치 → PR 방식) | 요구사항 #3부터 PR + CI 통과 후 merge |
| 자동 CI | 없음 (로컬에서 수동 실행) | 요구사항 #3에서 GitHub Actions에 TE 스크립트 연결 |
| 의존성 버전 | `requirements.txt`에 버전 고정이 없음 (BUG-1의 원인) | 고정 여부 검토 |
| 배포 | 미진행 | 요구사항 #3에서 Render 연결 후 배포 URL로 E2E 재실행 (`--base-url`) |
