"""
requirement_1 API + 실제 브라우저(E2E) 검증 스크립트  (TE)

req1_test_template.py 는 검색/필터 규칙을 파이썬으로 "재현"해서 확인합니다.
이 스크립트는 실제 Chromium 으로 대시보드를 열고 FE 의 app.js 가
화면(Table)에 무엇을 그리는지 직접 확인합니다.

실행 방법
--------
    # 프로젝트 루트에서 (최초 1회)
    pip install -r tests/requirements-te.txt
    python -m playwright install chromium

    python tests/req1_e2e_test.py            # 서버 자동 기동 후 검증
    python tests/req1_e2e_test.py --headed   # 브라우저 화면을 띄워서 검증
    python tests/req1_e2e_test.py --base-url https://<배포 URL>   # 배포 후 검증

결과
----
    tests/reports/req1_e2e_report.md
    종료 코드: 0 = 전부 PASS, 1 = FAIL 있음  (CI 에서 배포 차단용으로 사용)
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR)
REPORT_DIR = os.path.join(THIS_DIR, "reports")
REPORT_PATH = os.path.join(REPORT_DIR, "req1_e2e_report.md")
SHOT_DIR = os.path.join(REPORT_DIR, "screenshots")

os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 기대 결과의 기준 데이터 (더미 데이터는 수정하지 않는다)
from app.data.dummy_data import subscribers as EXPECTED  # noqa: E402

ALL_IDS = [u["userId"] for u in EXPECTED]
FIELDS = ["userId", "name", "plan", "status", "deviceCount"]

results = []  # (TC ID, 구분, 시나리오, 기대 결과, 실제 결과, 판정)


def check(tc_id, layer, scenario, expected, actual, passed):
    results.append((tc_id, layer, scenario, expected, str(actual), passed))
    print(f"  [{'PASS' if passed else 'FAIL'}] {tc_id}  {scenario}  → {actual}")


def ids_where(pred):
    return [u["userId"] for u in EXPECTED if pred(u)]


# =============================================================================
# HTTP / 서버 유틸
# =============================================================================
def http(method, url, timeout=5):
    """(status, content_type, body_text). 연결 실패 시 (None, '', 오류메시지)."""
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", ""), e.read().decode("utf-8", "replace")
    except Exception as e:
        return None, "", str(e)


def start_server():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=PROJECT_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    for _ in range(40):
        if proc.poll() is not None:
            break
        if http("GET", base + "/health", timeout=1)[0] == 200:
            return proc, base
        time.sleep(0.5)
    proc.kill()
    raise RuntimeError("서버 기동 실패: requirements 설치 및 app/main.py 확인")


def stop_server(proc):
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def git_commit():
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True,
                                      stderr=subprocess.DEVNULL).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain", "app"], text=True,
                                        stderr=subprocess.DEVNULL).strip()
        return out + (" (+ app/ 미커밋 변경 포함)" if dirty else "")
    except Exception:
        return "unknown"


# =============================================================================
# 1) API 검증  (BE: app/api/subscribers.py, app/main.py)
# =============================================================================
def run_api_tests(base):
    print("\n[API 검증]")
    st, ct, body = http("GET", base + "/health")
    check("API-01", "API", "GET /health", '200 + {"status":"ok"}', f"status={st}, body={body[:40]}",
          st == 200 and body and json.loads(body).get("status") == "ok")

    st, ct, body = http("GET", base + "/api/subscribers")
    check("API-02", "API", "GET /api/subscribers 응답 코드/형식", "200 + application/json",
          f"status={st}, content-type={ct}", st == 200 and "json" in ct)
    try:
        data = json.loads(body)
    except Exception:
        data = None

    ok = isinstance(data, list) and sorted(u.get("userId") for u in data) == sorted(ALL_IDS)
    check("API-03", "API", "사용자 수 / ID 목록", f"5명 {ALL_IDS}",
          f"{len(data)}명 {[u.get('userId') for u in data]}" if isinstance(data, list) else "리스트 아님", ok)

    bad = []
    for u in data if isinstance(data, list) else []:
        for k in FIELDS:
            if k not in u:
                bad.append(f"{u.get('userId')}:{k} 누락")
        if not all(isinstance(u.get(k), str) for k in FIELDS[:-1]) or type(u.get("deviceCount")) is not int:
            bad.append(f"{u.get('userId')}: 타입 오류")
    check("API-04", "API", "필수 필드 및 타입", "userId/name/plan/status=str, deviceCount=int",
          "이상 없음" if ok and not bad else bad or "데이터 없음", ok and not bad)

    check("API-05", "API", "응답 값이 기준 데이터와 일치", "dummy_data.subscribers 와 동일",
          "일치" if data == EXPECTED else "불일치", data == EXPECTED)

    st, ct, body = http("GET", base + "/")
    need = ['id="subscriber-body"', 'id="subscriber-search"', 'id="subscriber-status-filter"']
    missing = [n for n in need if n not in body]
    check("API-06", "API", "GET / 대시보드 페이지", "200 + 검색창/필터/Table 요소 존재",
          f"status={st}, 누락={missing}" if st == 200 else f"status={st}: {body[:60]}",
          st == 200 and "html" in ct and not missing)

    sts = {p: http("GET", base + p)[0] for p in ("/static/app.js", "/static/style.css")}
    check("API-07", "API", "정적 파일 제공 (app.js, style.css)", "둘 다 200", sts,
          all(v == 200 for v in sts.values()))

    st, _, _ = http("POST", base + "/api/subscribers")
    check("API-08", "API", "POST /api/subscribers (허용되지 않은 메서드)", "405", f"status={st}", st == 405)


# =============================================================================
# 2) UI 검증  (FE: app/static/app.js)  — 실제 Chromium
# =============================================================================
VISIBLE_IDS_JS = """() => [...document.querySelectorAll('#subscriber-body tr')]
    .filter(r => r.getClientRects().length)
    .map(r => (r.cells[0]?.innerText || '').trim())"""


def run_ui_tests(base, headed):
    from playwright.sync_api import sync_playwright

    print("\n[UI 검증 - Chromium]")
    page_errors = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not headed)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        ctx.set_default_timeout(5000)

        def new_page(route=None):
            p = ctx.new_page()
            p.on("pageerror", lambda e: page_errors.append(str(e)))
            if route:
                p.route("**/api/subscribers", route)
            p.goto(base + "/")
            return p

        def visible_ids(p):
            return p.evaluate(VISIBLE_IDS_JS)

        def wait_ids(p, expected):
            """화면의 행 ID 가 기대값이 될 때까지 대기. 시간 초과 시 실제 값 반환."""
            try:
                p.wait_for_function(
                    "exp => JSON.stringify((" + VISIBLE_IDS_JS + ")().sort()) === JSON.stringify(exp)",
                    arg=sorted(expected), timeout=3000)
            except Exception:
                pass
            return visible_ids(p)

        def ui_case(tc_id, scenario, expected_ids, steps, expected_text=None):
            """steps: [("search", 값) | ("status", 값)] 를 순서대로 조작 후 화면 행 비교."""
            p = new_page()
            try:
                wait_ids(p, ALL_IDS)
                for kind, value in steps:
                    if kind == "search":
                        p.fill("#subscriber-search", value)
                    else:
                        p.select_option("#subscriber-status-filter", value)
                actual = wait_ids(p, expected_ids)
                passed = sorted(actual) == sorted(expected_ids)
                if not passed:
                    os.makedirs(SHOT_DIR, exist_ok=True)
                    p.screenshot(path=os.path.join(SHOT_DIR, f"{tc_id}.png"), full_page=True)
                check(tc_id, "UI", scenario, expected_text or (expected_ids or "0행 (빈 Table)"),
                      actual or "0행", passed)
            finally:
                p.close()

        # ---- 초기 표시 / 렌더링 ------------------------------------------------
        p = new_page()
        actual = wait_ids(p, ALL_IDS)
        check("UI-01", "UI", "대시보드 접속 시 Table 자동 표시 (TE-2)", "5행 자동 표시",
              actual, sorted(actual) == sorted(ALL_IDS))
        if sorted(actual) != sorted(ALL_IDS):
            os.makedirs(SHOT_DIR, exist_ok=True)
            p.screenshot(path=os.path.join(SHOT_DIR, "UI-01.png"), full_page=True)
            check("UI-XX", "UI", "UI-02 ~ UI-25", "실행", "미실행 — 선행 조건(UI-01) 실패로 차단", False)
            browser.close()
            return

        cells = p.evaluate("""() => [...document.querySelectorAll('#subscriber-body tr')]
            .map(r => [...r.cells].map(c => c.innerText.trim()))""")
        expected_cells = [[str(u[k]) for k in FIELDS] for u in EXPECTED]
        check("UI-02", "UI", "컬럼 순서 및 셀 값 (deviceCount 0 포함)",
              "ID/Name/Plan/Status/Devices 가 데이터와 일치",
              "일치" if cells == expected_cells else cells, cells == expected_cells)

        badges = p.evaluate("""() => [...document.querySelectorAll('#subscriber-body tr')]
            .map(r => r.cells[3]?.querySelector('span.badge')?.innerText.trim() || null)""")
        check("UI-03", "UI", "Status 열이 badge(span) 로 렌더링", "5행 모두 span.badge",
              badges, badges == [u["status"] for u in EXPECTED])

        # ---- 실시간 반영: 한 글자씩 입력 (새로고침 없이 갱신) --------------------
        p.evaluate("window.__noReload = true")
        p.click("#subscriber-search")
        p.keyboard.type("Ki", delay=50)
        mid = wait_ids(p, ids_where(lambda u: "ki" in u["name"].lower() or "ki" in u["plan"].lower()
                                    or "ki" in u["status"].lower() or "ki" in u["userId"].lower()))
        p.keyboard.type("m", delay=50)
        end = wait_ids(p, ["U001"])
        same_page = p.evaluate("window.__noReload === true")
        check("UI-04", "UI", "키 입력마다 실시간 반영 (페이지 새로고침 없음)",
              '"Ki"→U001 / "Kim"→U001, 페이지 유지',
              f'"Ki"→{mid}, "Kim"→{end}, 페이지 유지={same_page}',
              mid == ["U001"] and end == ["U001"] and same_page)
        p.close()

        # ---- 요구사항 문서 TE 시나리오 #3 ~ #8 --------------------------------
        ui_case("UI-05", '검색 "Kim" (TE-3)', ["U001"], [("search", "Kim")], "U001 Kim Minsoo")
        ui_case("UI-06", '검색 "Premium" (TE-4)', ids_where(lambda u: u["plan"] == "Premium"),
                [("search", "Premium")])
        ui_case("UI-07", '필터 "Active" (TE-5)', ids_where(lambda u: u["status"] == "Active"),
                [("status", "Active")])
        ui_case("UI-08", '필터 "Expired" (TE-6)', ["U005"], [("status", "Expired")], "U005 Jung Hyerin")
        ui_case("UI-09", '검색 "Kim" + 필터 "Active" (TE-7)', ["U001"],
                [("search", "Kim"), ("status", "Active")])
        ui_case("UI-10", '검색 "Kim" 후 검색어 삭제 (TE-8)', ALL_IDS,
                [("search", "Kim"), ("search", "")], "전체 5행 복원")

        # ---- 완료 조건 보강 (검색 기준 4종 / 필터 3종 / 조합) -----------------
        ui_case("UI-11", '필터 "Paused"', ["U003"], [("status", "Paused")])
        ui_case("UI-12", '필터 "All Status" 로 복귀', ALL_IDS,
                [("status", "Expired"), ("status", "")], "전체 5행")
        ui_case("UI-13", 'ID 검색 "U003"', ["U003"], [("search", "U003")])
        ui_case("UI-14", '상태 텍스트 검색 "paused"', ["U003"], [("search", "paused")])
        ui_case("UI-15", '대소문자 무시 "KIM"', ["U001"], [("search", "KIM")])
        ui_case("UI-16", '부분 문자열 "min"', ["U001", "U004"], [("search", "min")],
                "Kim Minsoo, Choi Sumin")
        ui_case("UI-17", '검색 "Kim" + 필터 "Expired" (조건 불일치)', [],
                [("search", "Kim"), ("status", "Expired")])
        ui_case("UI-18", '필터 "Active" 유지 + 검색어 입력 후 삭제', ids_where(lambda u: u["status"] == "Active"),
                [("status", "Active"), ("search", "Kim"), ("search", "")], "Active 3행 유지")
        ui_case("UI-19", '없는 검색어 "zzz"', [], [("search", "zzz")])
        ui_case("UI-20", '검색 대상 외 필드 "Yonsei" (organization)', [], [("search", "Yonsei")],
                "0행 (검색 대상은 name/plan/status/userId)")

        # ---- 선택 행 표시 로직 -------------------------------------------------
        p = new_page()
        wait_ids(p, ALL_IDS)
        p.evaluate("selectedUserId = 'U002'; renderSubscribers();")
        selected = p.evaluate("() => [...document.querySelectorAll('#subscriber-body tr.selected')]"
                              ".map(r => r.cells[0].innerText.trim())")
        check("UI-21", "UI", "selectedUserId 행에 selected 클래스 적용", "U002 1행만 selected",
              selected, selected == ["U002"])
        before = len(page_errors)
        p.locator("#subscriber-body tr", has_text="U003").click()
        p.wait_for_timeout(300)
        check("UI-22", "UI", "행 클릭 시 selectSubscriber 호출 (오류 없음)",
              "클릭 시 JS 오류 없음 (선택 강조는 요구사항 #2 에서 완성)",
              "오류 없음" if len(page_errors) == before else page_errors[before:],
              len(page_errors) == before)
        p.close()

        # ---- 예외 / 보안 -------------------------------------------------------
        p = new_page(lambda r: r.fulfill(status=500, body="error"))
        p.wait_for_timeout(500)
        rows = visible_ids(p)
        check("UI-23", "UI", "API 500 응답 시 화면 동작", "JS 예외 없이 빈 Table 유지",
              f"{len(rows)}행, pageerror={len(page_errors)}", rows == [] and not page_errors)
        p.close()

        xss = [{"userId": "U900", "name": "<img src=x onerror=window.__xss=1>", "plan": "Basic",
                "status": "Active", "deviceCount": 0}]
        p = new_page(lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(xss)))
        wait_ids(p, ["U900"])
        injected = p.evaluate("() => ({img: !!document.querySelector('#subscriber-body img'), "
                              "xss: window.__xss === 1, text: document.querySelector('#subscriber-body td:nth-child(2)')?.innerText})")
        check("UI-24", "UI", "HTML 이 포함된 이름 렌더링 (XSS 방어)", "태그가 아닌 텍스트로 표시",
              injected, not injected["img"] and not injected["xss"] and injected["text"] == xss[0]["name"])
        p.close()

        check("UI-25", "UI", "전체 실행 중 브라우저 JS 오류", "pageerror 0건",
              f"{len(page_errors)}건 {page_errors[:3]}", not page_errors)

        browser.close()


# =============================================================================
# Report
# =============================================================================
def render_report(base, commit):
    total = len(results)
    passed = sum(1 for r in results if r[5])
    lines = [
        "# requirement_1 API + 브라우저(E2E) 자동 검증 Report",
        "",
        "| 항목 | 내용 |",
        "|------|------|",
        "| **프로젝트** | webOS Subscription Management Dashboard |",
        "| **검증 대상** | requirement_1.md |",
        f"| **검증 일시** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |",
        f"| **대상 URL** | {base} |",
        f"| **대상 커밋** | `{commit}` |",
        "| **작성자** | 최민석 (PM / TE) |",
        "| **도구** | Python urllib (API), Playwright Chromium (UI) |",
        "",
        f"**총 {total}건 중 PASS {passed} / FAIL {total - passed} — Pass Rate "
        f"{(passed / total * 100) if total else 0:.1f}%**",
        "",
        "| TC ID | 구분 | 테스트 시나리오 | 기대 결과 | 실제 결과 | 판정 |",
        "|:-----:|:----:|----------------|-----------|-----------|:----:|",
    ]
    for tc, layer, sc, exp, act, ok in results:
        cell = lambda v: str(v).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {tc} | {layer} | {cell(sc)} | {cell(exp)} | {cell(act)} | "
                     f"{'✅ PASS' if ok else '❌ FAIL'} |")
    lines += ["", "> 본 Report 는 `tests/req1_e2e_test.py` 로 생성되었습니다. "
              "실패 시 화면 캡처는 `tests/reports/screenshots/` 에 저장됩니다."]
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return passed, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", help="이미 떠 있는 서버/배포 URL (없으면 로컬 서버 자동 기동)")
    ap.add_argument("--headed", action="store_true", help="브라우저 화면 표시")
    args = ap.parse_args()

    print("=" * 60)
    print(" requirement_1 API + E2E 검증")
    print("=" * 60)

    proc = None
    try:
        if args.base_url:
            base = args.base_url.rstrip("/")
        else:
            proc, base = start_server()
        print(f"[대상] {base}")
        run_api_tests(base)
        try:
            run_ui_tests(base, args.headed)
        except ImportError:
            check("UI-00", "UI", "Playwright 설치 여부", "설치됨",
                  "미설치: pip install -r tests/requirements-te.txt", False)
        except Exception as e:
            check("UI-ERR", "UI", "UI 검증 실행 중단", "정상 실행", f"{type(e).__name__}: {e}"[:200], False)
    finally:
        stop_server(proc)

    passed, total = render_report(base, git_commit() if not args.base_url else "배포 서버 (PM 확인)")
    print("\n" + "=" * 60)
    print(f" 결과: PASS {passed} / FAIL {total - passed} (총 {total})")
    print(f" Report 저장: {os.path.relpath(REPORT_PATH, PROJECT_ROOT)}")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
