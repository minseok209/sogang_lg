# requirement_3 테스트 설계서 (TE) · 작업 배분 (PM)

| 항목 | 내용 |
|------|------|
| 대상 요구사항 | `requirement_3.md` — 상태 기반 Badge + GitHub Actions CI + Render CD |
| 기준 코드 | `main` `17145de` |
| 브랜치 | `feature/status-badge-ci` → PR → `main` |
| 작성자 | 최민석 (PM / TE) |
| 자동화 | `tests/req3_e2e_test.py` (19건), `.github/workflows/ci.yml` |

## 1. 작업 배분 (PM)

| 담당 | 작업 | 파일 | 상태 |
|------|------|------|:----:|
| FE | `badgeClass()` 상태별 클래스 매핑 | `app/static/app.js` | 대기 (현재 항상 `"badge"` 반환) |
| PM | GitHub Actions CI 설정 | `.github/workflows/ci.yml` | 작성 완료 |
| PM | Render Web Service 생성 및 Auto-Deploy 연결 | Render Dashboard | PM 본인 계정으로 진행 |
| BE | 추가 구현 없음. CI 실패 시 API 원인 분석 지원 | — | — |
| TE | Badge 시나리오 작성, CI·배포 검증, 최종 Report (#1~#3) | `tests/` | 시나리오·스크립트 완료 |

FE는 `feature/status-badge-ci` 브랜치에 `badgeClass()`를 커밋한다. PR의 CI가 초록색이 되면 merge한다.

## 2. 상태 Badge 테스트 (Part A)

### 판정 방식

- 클래스: `badgeClass()`가 요구사항 문서의 매핑 표와 정확히 같은 클래스를 반환하는지 본다. 예를 들어 Standby는 `status-standby`가 아니라 `status-paused`여야 한다.
- 색상: 화면에 실제로 렌더링된 배경색(computed `background-color`)이 `style.css`에 정의된 색과 같은지 본다.

| 색 | CSS 클래스 | 배경색 | 대상 값 |
|----|-----------|--------|--------|
| 초록 | `status-active` | `#dcfce7` | Active, Online, Normal |
| 파랑 | `status-paused` | `#e0e7ff` | Paused, Standby |
| 빨강 | `status-expired` | `#fee2e2` | Expired, Error, Warning |
| 회색 | `status-offline` | `#e5e7eb` | Offline |
| 노랑 | `status-on` | `#fef3c7` | On, Cleaning |
| 연회색 | `status-off` | `#f3f4f6` | Off |

### 테스트 케이스

| TC | 요구사항 TE # | 시나리오 | 기대 결과 |
|----|:----:|---------|----------|
| FN-01 | — | `badgeClass()`에 상태 값 12종 입력 | 매핑 표와 일치 |
| FN-02 | — | 대소문자가 다른 값 (ACTIVE, online, warning) | 같은 클래스 |
| FN-03 | — | Unknown, 빈 문자열, null | `"badge"` |
| UI-01 | 1 | 구독 상태 Active (U001, U002, U004) | 초록 |
| UI-02 | 2 | 구독 상태 Paused (U003) | 파랑 |
| UI-03 | 3 | 구독 상태 Expired (U005) | 빨강 |
| UI-04 | 4 | 가전 상태 Online | 초록 |
| UI-05 | 5 | 가전 상태 Offline (D002) | 회색 |
| UI-06 | 6 | 가전 상태 Error (D006) | 빨강 |
| UI-07 | — | 가전 상태 Standby (D008) | 파랑 |
| UI-08 | 7 | D001 Power On | 노랑 |
| UI-09 | 8 | D001 Health Normal | 초록 |
| UI-10 | 9 | D006 Health Warning | 빨강 |
| UI-11 | — | D006 Power Error | 빨강 |
| UI-12 | — | D002 Power Off | 연회색 |
| UI-13 | — | D007 Power Cleaning | 노랑 |
| UI-14 | — | D004 Power Standby | 파랑 |
| UI-15 | — | 매핑 대상인데 기본 `badge`로 남은 곳 | 0건 |
| UI-16 | — | 실행 중 JS 오류 | 0건 |

더미 데이터에 있는 상태 값 12종(구독 3, 가전 4, 전원 5, 건강 2. 중복 포함)이 화면에서 모두 한 번 이상 검증된다.

## 3. CI 검증 (Part B)

`ci.yml`은 요구사항 문서의 단계(문법 검사 → 서버 기동 → health/API curl)에 TE 자동 검증을 추가했다. 그래서 화면 기능이 망가져도 CI가 실패한다.

| 단계 | 내용 |
|------|------|
| 1~6 | 요구사항 문서 그대로 + `GET /` 확인 추가 (BUG-1 같은 화면 오류 감지) |
| 7 | Playwright + Chromium 설치 |
| 8~10 | 요구사항 #1 (템플릿 17 + E2E 33), #2 (E2E 38), #3 (Badge 19) |
| 11 | `tests/reports/`를 Artifact(`te-reports`)로 업로드 (실패해도 업로드) |
| 12 | (선택) `RENDER_DEPLOY_HOOK_URL` Secret이 등록돼 있으면 main push 성공 시 Render 배포 |

| TC | 요구사항 TE # | 시나리오 | 기대 결과 | 확인 방법 |
|----|:----:|---------|----------|------|
| CI-01 | 10 | PR 생성 / main push | Actions에서 CI 자동 실행 | Actions 탭, PR Checks |
| CI-02 | 11 | health 체크 | 초록 체크 | 5단계 로그 |
| CI-03 | 12 | API 3종 + 대시보드 | 모두 200 | 6단계 로그 |
| CI-04 | — | TE 자동 검증 #1~#3 | 전부 PASS | 8~10단계 로그, `te-reports` Artifact |
| CI-05 | — | badgeClass 미구현 상태의 PR | **CI 실패** (배포 차단 동작 확인) | 10단계 FAIL |

## 4. 배포 검증 (Part C)

| TC | 요구사항 TE # | 시나리오 | 기대 결과 |
|----|:----:|---------|----------|
| CD-01 | 13 | `https://<서비스>.onrender.com/health` | `{"status":"ok"}` |
| CD-02 | 13 | 배포 URL에서 #1~#3 E2E 실행 (아래 명령) | 전부 PASS |
| CD-03 | — | main merge 후 Render Events | 자동 재배포 기록 |

```bash
python tests/req1_e2e_test.py --base-url https://<서비스>.onrender.com
python tests/req2_e2e_test.py --base-url https://<서비스>.onrender.com
python tests/req3_e2e_test.py --base-url https://<서비스>.onrender.com
```

Render 무료 인스턴스는 쉬고 있다가 깨어나는 데 시간이 걸린다. 첫 요청은 `/health`를 먼저 열어서 서버를 깨운 뒤 실행한다.

## 5. 스크립트 사전 검증

| 대상 코드 | 결과 |
|------|------|
| 현재 `main` (`badgeClass` 미구현) | PASS 2 / FAIL 17. 기대대로 실패 |
| 요구사항 문서대로 만든 참조 `badgeClass()` (커밋 안 함) | **PASS 19 / FAIL 0** |
| 참조 구현 적용 상태에서 요구사항 #1·#2 E2E | 33/33, 38/38 PASS (회귀 없음) |
