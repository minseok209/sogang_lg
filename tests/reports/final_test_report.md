# 최종 검증 Report (요구사항 #1 ~ #3)

| 항목 | 내용 |
|------|------|
| 프로젝트 | webOS Subscription Management Dashboard |
| 팀 | PM / TE: 최민석 · BE: 하지훈 · FE: 이광수 |
| 저장소 | https://github.com/minseok209/sogang_lg |
| 배포 URL | https://sogang-lg-webos.onrender.com |
| 검증 대상 커밋 | `ed7bc9a` (PR #1 merge, 요구사항 #3 완료 시점 앱 코드) |
| 검증 일시 | 2026-10-01 |
| 작성자 | 최민석 (PM / TE) |

## 1. 종합 결과

| 검증 환경 | 요구사항 #1 | 요구사항 #2 | 요구사항 #3 | 합계 |
|------|:----:|:----:|:----:|:----:|
| 로컬 (macOS, Python 3.14) | 17 + 33 PASS | 38 PASS | 19 PASS | **107 / 107** |
| GitHub Actions CI (Ubuntu, Python 3.11) | 17 + 33 PASS | 38 PASS | 19 PASS | **107 / 107** |
| Render 배포 URL | 33 PASS | 38 PASS | 19 PASS | **90 / 90** |

배포 URL에서는 `req1_test_template.py`를 실행하지 않았다. 이 스크립트는 서버 함수를 직접 호출하는 방식이라 원격 서버를 대상으로 돌릴 수 없다.

**종합 판정: PASS. 요구사항 #1~#3의 완료 조건을 모두 충족한다.**

## 2. 요구사항별 완료 조건

| 요구사항 | 완료 조건 | 근거 | 판정 |
|------|------|------|:----:|
| #1 | 구독자 API, Table 자동 표시, 검색 4종, 필터 3종, 실시간 반영 | `req1_test_report.md` | ✅ |
| #2 | 가전 목록·사용 현황 API(404 포함), 가전 Table·검색·필터, 사용 현황, Bar Chart | `req2_test_report.md` | ✅ |
| #3 | 상태별 Badge 색상 (초록/파랑/빨강/회색 + 노랑/연회색) | `req3_e2e_report.md` (FN-01~03, UI-01~16) | ✅ |
| #3 | `.github/workflows/ci.yml` 설정 | `ci.yml` | ✅ |
| #3 | Push/PR 시 CI 자동 실행 | 실행 `36833284731` (PR), `36833587776`, `36833879456` (main push) | ✅ |
| #3 | CI에서 서버 기동 + API 테스트 통과 | 위 실행 로그의 health/API/TE 단계 | ✅ |
| #3 | Render Web Service와 GitHub 저장소 연결 | Render 앱을 `sogang_lg` 저장소에만 설치 | ✅ |
| #3 | main push/merge 시 자동 재배포 | Auto-Deploy: **After CI Checks Pass** (5장 참고) | ✅ |
| #3 | 배포 URL에서 전체 기능 동작 | `deploy/req1~3_e2e_report.md` (90/90) | ✅ |
| #3 | (선택) CI 통과 시에만 배포 | Deploy Hook 대신 Render의 After CI Checks Pass 사용 | ✅ |

## 3. 요구사항 #3 TE 시나리오 결과

| # | 테스트 시나리오 | 예상 결과 | 실제 결과 | 결과 |
|---|----------------|----------|-----------|:----:|
| 1 | Active 상태 구독자 확인 | 초록 badge | U001, U002, U004 `status-active` / `rgb(220, 252, 231)` | ✅ PASS |
| 2 | Paused 상태 구독자 확인 | 파랑 badge | U003 `status-paused` | ✅ PASS |
| 3 | Expired 상태 구독자 확인 | 빨강 badge | U005 `status-expired` | ✅ PASS |
| 4 | Online 상태 가전 확인 | 초록 badge | `status-active` | ✅ PASS |
| 5 | Offline 상태 가전 확인 | 회색 badge | D002 `status-offline` | ✅ PASS |
| 6 | Error 상태 가전 확인 | 빨강 badge | D006 `status-expired` | ✅ PASS |
| 7 | Power On 상태 확인 | 노랑 badge | D001 `status-on` | ✅ PASS |
| 8 | Health Normal 상태 확인 | 초록 badge | D001 `status-active` | ✅ PASS |
| 9 | Health Warning 상태 확인 | 빨강 badge | D006 `status-expired` | ✅ PASS |
| 10 | main push 시 CI 자동 실행 | Actions 탭에서 실행 확인 | push 2건 자동 실행 | ✅ PASS |
| 11 | CI에서 health 체크 통과 | 초록 체크마크 | success | ✅ PASS |
| 12 | CI에서 API 테스트 통과 | 3개 엔드포인트 모두 통과 | 3종 + 대시보드 `/` 200 | ✅ PASS |
| 13 | CI 통과 후 Render 배포 확인 | 배포 URL 접속 가능 | `/health` 200, E2E 90/90 | ✅ PASS |

보강 케이스(Standby·Off·Cleaning, 대소문자 무시, 미정의 값, 기본 badge 누락 0건)도 모두 PASS다.

## 4. 결함 이력

| ID | 요구사항 | 내용 | 담당 | 조치 |
|----|:----:|------|:----:|------|
| BUG-1 | #1 | 최신 Starlette에서 대시보드 `/` 500 에러 | BE 영역 | `e7142f4` 수정 |
| CSS-1 | #2 | `.usage-detail`이 `.hidden`을 덮어써 사용 현황 영역이 숨겨지지 않음 | FE | 사전 공유 → FE `bc6748e`에서 수정 |
| BUG-2 | #2 | 조회 중 이전 사용자의 가전이 남아 다른 사용자의 사용 현황이 표시됨 | FE 영역 | `1b74eca` 수정 + 회귀 테스트 UI-27 |

요구사항 #3에서는 결함이 발견되지 않았다. FE 이광수의 `badgeClass()`는 매핑 표와 정확히 일치했다.

BUG-1은 배포 환경에도 직접 영향이 있었다. Render 빌드 로그를 보면 배포할 때마다 최신 Starlette 1.7이 설치된다. 미리 고치지 않았다면 배포 서비스도 500 에러였을 것이다.

## 5. CI / CD 구성

```
PR 생성 또는 main push
  → GitHub Actions CI (약 1분)
      문법 검사 → 서버 기동 → /health, API 3종, / → TE E2E #1~#3 (Chromium) → Report Artifact
  → CI 통과 시에만 Render 배포 (Auto-Deploy: After CI Checks Pass)
  → 배포 URL에서 E2E 재실행 (--base-url)
```

| 항목 | 설정 |
|------|------|
| Render 서비스 | `sogang-lg-webos`, Python 3, Oregon, **Free** |
| Build / Start | `pip install -r requirements.txt` / `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check | `/health` |
| GitHub 연결 범위 | Render 앱을 `minseok209/sogang_lg` 하나에만 설치 (Only select repositories) |
| 첫 배포 | `1540daf`, 빌드 성공부터 live까지 약 1분 |
| 자동 재배포 확인 | `07aa007` push → CI success (17:08:38) → Render "New commit via Auto-Deploy"로 `07aa007` 배포 시작 (17:08) |

## 6. 남은 과제 (PM 권고)

| 항목 | 내용 |
|------|------|
| 의존성 버전 고정 | `requirements.txt`에 검증한 버전(fastapi 0.142.2, starlette 1.7.0, uvicorn 0.54.0, jinja2 3.1.6)을 고정해 BUG-1 같은 문제를 예방 |
| main 보호 규칙 | 직접 push 금지, CI 필수 체크, Approve 1명 이상 |
| Actions 버전 | Node.js 20 지원 종료 경고 → `actions/checkout`, `setup-python`, `upload-artifact` 최신 메이저로 업데이트 |
| 무료 인스턴스 | 쉬다가 깨어나는 데 50초 이상 걸릴 수 있음. 배포 후 검증할 때는 `/health`로 먼저 깨운 뒤 실행 |

## 7. 관련 문서

- 테스트 설계: `tests/req1_test_plan.md`, `tests/req2_test_plan.md`, `tests/req3_test_plan.md`
- 요구사항별 Report: `req1_test_report.md`, `req2_test_report.md`, `req3_e2e_report.md`
- 배포 URL 검증: `deploy/req1_e2e_report.md`, `deploy/req2_e2e_report.md`, `deploy/req3_e2e_report.md`
- PM/TE 요약: `req1_2_pm_te_summary.md`
- 마무리 체크리스트: `docs/wrapup_checklist.md`
