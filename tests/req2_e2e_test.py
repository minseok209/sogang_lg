"""
requirement_2 API + 실제 브라우저(E2E) 검증 스크립트  (TE)

가전 목록 / 사용 현황 / 주간 사용량 Bar Chart 를 검증합니다.
실제 Chromium 으로 대시보드를 열어 FE 의 app.js 가 그리는 화면을 확인합니다.

실행 방법
--------
    # 프로젝트 루트에서 (최초 1회)
    pip install -r tests/requirements-te.txt
    python -m playwright install chromium

    python tests/req2_e2e_test.py            # 서버 자동 기동 후 검증
    python tests/req2_e2e_test.py --headed   # 브라우저 화면을 띄워서 검증
    python tests/req2_e2e_test.py --base-url https://<배포 URL>   # 배포 후 검증

결과
----
    tests/reports/req2_e2e_report.md
    판정: PASS / FAIL / BLOCKED (선행 기능 미구현으로 실행 불가)
    종료 코드: 0 = 전부 PASS, 1 = FAIL 또는 BLOCKED 있음
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
REPORT_PATH = os.path.join(REPORT_DIR, "req2_e2e_report.md")
SHOT_DIR = os.path.join(REPORT_DIR, "screenshots")

os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 기대 결과의 기준 데이터 (더미 데이터는 수정하지 않는다)
from app.data.dummy_data import subscribers as SUBSCRIBERS  # noqa: E402
from app.data.dummy_data import devices_by_user as DEVICES  # noqa: E402
from app.data.dummy_data import usage_by_device as USAGE  # noqa: E402

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DEVICE_FIELDS = ["deviceId", "type", "model", "location", "status", "lastSeen"]
USAGE_FIELDS = ["deviceId", "deviceName", "powerStatus", "lastUsedAt", "totalUsageHours",
                "weeklyUsageCount", "healthStatus", "remark", "weeklyUsageTrend"]

results = []  # (TC ID, 구분, 시나리오, 기대 결과, 실제 결과, 판정)


def record(tc_id, layer, scenario, expected, actual, status):
    results.append((tc_id, layer, scenario, expected, str(actual), status))
    print(f"  [{status}] {tc_id}  {scenario}  → {actual}")


def check(tc_id, layer, scenario, expected, actual, passed):
    record(tc_id, layer, scenario, expected, actual, "PASS" if passed else "FAIL")


def block(tc_id, layer, scenario, expected, reason):
    record(tc_id, layer, scenario, expected, reason, "BLOCKED")


def device_ids(user_id, pred=lambda d: True):
    return [d["deviceId"] for d in DEVICES[user_id] if pred(d)]


# =============================================================================
# HTTP / 서버 유틸
# =============================================================================
def http(url, timeout=5):
    """(status, content_type, json 또는 None). 연결 실패 시 (None, '', None)."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read().decode("utf-8")
            st, ct = r.status, r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        body, st, ct = e.read().decode("utf-8", "replace"), e.code, e.headers.get("Content-Type", "")
    except Exception:
        return None, "", None
    try:
        return st, ct, json.loads(body)
    except json.JSONDecodeError:
        return st, ct, None


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
        if http(base + "/health", timeout=1)[0] == 200:
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
# 1) API 검증  (BE: app/api/subscribers.py, app/api/devices.py)
#    반환값: usage API 가 동작하는지 여부 (UI 사용 현황 검증의 선행 조건)
# =============================================================================
def run_api_tests(base):
    print("\n[API 검증]")

    # ---- 가전 목록 API -------------------------------------------------------
    st, ct, data = http(base + "/api/subscribers/U001/devices")
    ids = [d.get("deviceId") for d in data] if isinstance(data, list) else data
    check("API-01", "API", "GET /api/subscribers/U001/devices (TE-1)", "200 + 가전 2개 [D001, D002]",
          f"status={st}, {ids}", st == 200 and ids == ["D001", "D002"])

    st, ct, data = http(base + "/api/subscribers/U005/devices")
    check("API-02", "API", "가전 없는 사용자 U005 (TE-2)", "200 + []", f"status={st}, {data}",
          st == 200 and data == [])

    st, ct, data = http(base + "/api/subscribers/U999/devices")
    check("API-03", "API", "존재하지 않는 사용자 U999 (TE-3)", "404", f"status={st}", st == 404)

    mismatch = []
    for u in SUBSCRIBERS:
        st, _, data = http(base + f"/api/subscribers/{u['userId']}/devices")
        if st != 200 or data != DEVICES[u["userId"]]:
            mismatch.append(f"{u['userId']}(status={st})")
    check("API-04", "API", "전체 사용자 가전 목록 값/필드", "5명 모두 기준 데이터와 일치 (필드 6개)",
          "일치" if not mismatch else f"불일치: {mismatch}", not mismatch)

    counts = {u["userId"]: (u["deviceCount"], len(DEVICES[u["userId"]])) for u in SUBSCRIBERS}
    bad = {k: v for k, v in counts.items() if v[0] != v[1]}
    check("API-05", "API", "deviceCount 와 실제 가전 수 일치", "5명 모두 일치",
          "일치" if not bad else f"(deviceCount, 실제) {bad}", not bad)

    # ---- 사용 현황 API -------------------------------------------------------
    st, ct, data = http(base + "/api/devices/D001/usage")
    usage_ok = st == 200 and isinstance(data, dict)
    check("API-06", "API", "GET /api/devices/D001/usage (TE-8)", "200 + 사용 현황 JSON",
          f"status={st}, {str(data)[:60]}", usage_ok and "json" in ct)

    missing = [k for k in USAGE_FIELDS if not isinstance(data, dict) or k not in data]
    check("API-07", "API", "사용 현황 필드 9개 + 값 일치", "기준 데이터 D001 과 동일",
          "일치" if data == USAGE["D001"] else f"누락={missing}" if missing else "값 불일치",
          data == USAGE["D001"])

    st, ct, data = http(base + "/api/devices/D999/usage")
    check("API-08", "API", "존재하지 않는 디바이스 D999 (TE-9)", "404", f"status={st}, body={data}", st == 404)

    mismatch = []
    for dev_id, expected in USAGE.items():
        st, _, data = http(base + f"/api/devices/{dev_id}/usage")
        trend = data.get("weeklyUsageTrend") if isinstance(data, dict) else None
        if st != 200 or data != expected or not (isinstance(trend, list) and len(trend) == 7):
            mismatch.append(f"{dev_id}(status={st})")
    check("API-09", "API", "전체 디바이스 8개 사용 현황", "8개 모두 일치 + 주간 데이터 7개",
          "일치" if not mismatch else f"불일치: {mismatch}", not mismatch)

    # ---- 회귀 (요구사항 #1) --------------------------------------------------
    st, _, data = http(base + "/api/subscribers")
    check("API-10", "API", "회귀: GET /api/subscribers", "200 + 5명",
          f"status={st}, {len(data) if isinstance(data, list) else data}명",
          st == 200 and data == SUBSCRIBERS)

    return usage_ok


# =============================================================================
# 2) UI 검증  (FE: app/static/app.js) — 실제 Chromium
# =============================================================================
VISIBLE_ROWS_JS = """sel => [...document.querySelectorAll(sel + ' tr')]
    .filter(r => r.getClientRects().length)
    .map(r => (r.cells[0]?.innerText || '').trim())"""


def run_ui_tests(base, headed, usage_ok):
    from playwright.sync_api import sync_playwright

    print("\n[UI 검증 - Chromium]")
    page_errors = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not headed)
        ctx = browser.new_context(viewport={"width": 1280, "height": 1000})
        ctx.set_default_timeout(5000)

        # ---------- 공통 동작 ----------
        def rows(p, sel):
            return p.evaluate(VISIBLE_ROWS_JS, sel)

        def wait_rows(p, sel, expected, timeout=3000):
            """sel 의 화면 행 ID 가 expected 가 될 때까지 대기 후 실제 값 반환."""
            try:
                p.wait_for_function(
                    "([sel, exp]) => JSON.stringify((" + VISIBLE_ROWS_JS + ")(sel)) === JSON.stringify(exp)",
                    arg=[sel, expected], timeout=timeout)
            except Exception:
                pass
            return rows(p, sel)

        def open_dashboard():
            p = ctx.new_page()
            p.on("pageerror", lambda e: page_errors.append(str(e)))
            p.goto(base + "/")
            wait_rows(p, "#subscriber-body", [u["userId"] for u in SUBSCRIBERS])
            return p

        def pick_user(p, user_id):
            p.locator("#subscriber-body tr", has_text=user_id).click()
            return wait_rows(p, "#device-body", device_ids(user_id))

        def pick_device(p, device_id):
            p.locator("#device-body tr", has_text=device_id).click()
            try:
                p.wait_for_function(
                    "id => !document.getElementById('usage-detail').classList.contains('hidden') && "
                    "document.getElementById('usage-info').innerText.includes(id)", arg=device_id, timeout=3000)
            except Exception:
                pass

        def device_panel_text(p):
            return p.evaluate("document.getElementById('device-table').closest('section').innerText")

        def is_visible(p, el_id):
            return p.evaluate(f"!!document.getElementById('{el_id}').getClientRects().length")

        def chart_state(p):
            return p.evaluate("""() => {
                const c = (typeof Chart !== 'undefined') ? Chart.getChart('usageChart') : null;
                return c ? {type: c.config.type, labels: c.data.labels, data: c.data.datasets[0]?.data,
                            count: Object.keys(Chart.instances).length} : null; }""")

        def shot(p, tc_id):
            os.makedirs(SHOT_DIR, exist_ok=True)
            p.screenshot(path=os.path.join(SHOT_DIR, f"req2_{tc_id}.png"), full_page=True)

        def ui(tc_id, scenario, expected, fn):
            """fn(page) -> (actual, passed). 실패/예외 시 화면 캡처."""
            p = open_dashboard()
            try:
                actual, passed = fn(p)
            except Exception as e:
                actual, passed = f"{type(e).__name__}: {str(e).splitlines()[0][:120]}", False
            if not passed:
                shot(p, tc_id)
            check(tc_id, "UI", scenario, expected, actual, passed)
            p.close()

        def filter_case(user_id, steps, expected_ids):
            """사용자 선택 후 가전 검색/필터 조작 → 화면 행 비교."""
            def fn(p):
                pick_user(p, user_id)
                for kind, value in steps:
                    if kind == "search":
                        p.fill("#device-search", value)
                    else:
                        p.select_option("#device-status-filter", value)
                actual = wait_rows(p, "#device-body", expected_ids)
                return actual or "0행", actual == expected_ids
            return fn

        # ---------- 초기 화면 ----------
        def ui00(p):
            st = {"가전 안내문구 표시": is_visible(p, "device-empty"),
                  "가전 Table 숨김": not is_visible(p, "device-table"),
                  "사용현황 안내문구 표시": is_visible(p, "usage-empty"),
                  "사용현황 상세 숨김": not is_visible(p, "usage-detail")}
            return st, all(st.values())
        ui("UI-00", "초기 화면 (구독자 선택 전)", "안내문구만 표시, 가전 Table·사용현황 상세 숨김", ui00)

        # ---------- 가전 목록 (4.3 + 4.4) ----------
        def ui01(p):
            actual = pick_user(p, "U001")
            return (f"{actual}, 안내문구 숨김={not is_visible(p, 'device-empty')}",
                    actual == ["D001", "D002"] and not is_visible(p, "device-empty"))
        ui("UI-01", "U001 클릭 시 가전 Table 표시 (TE-4)", "D001, D002 표시", ui01)

        def ui02(p):
            pick_user(p, "U003")
            cells = p.evaluate("""() => [...document.querySelectorAll('#device-body tr')]
                .map(r => [...r.cells].map(c => c.innerText.trim()))""")
            expected = [[d[k] for k in ["deviceId", "type", "model", "location", "status"]] for d in DEVICES["U003"]]
            badges = p.evaluate("""() => [...document.querySelectorAll('#device-body tr')]
                .map(r => !!r.cells[4]?.querySelector('span.badge'))""")
            return ("일치" if cells == expected and all(badges) else f"{cells}, badge={badges}",
                    cells == expected and all(badges))
        ui("UI-02", "가전 컬럼 순서/값 + status badge", "ID/Type/Model/Location/Status(badge) 일치", ui02)

        def ui03(p):
            pick_user(p, "U002")
            sel = p.evaluate("() => [...document.querySelectorAll('#subscriber-body tr.selected')]"
                             ".map(r => r.cells[0].innerText.trim())")
            return sel, sel == ["U002"]
        ui("UI-03", "클릭한 구독자 행 선택 표시", "U002 1행만 selected", ui03)

        def ui04(p):
            p.locator("#subscriber-body tr", has_text="U005").click()
            p.wait_for_timeout(500)
            text = device_panel_text(p)
            visible = rows(p, "#device-body")
            return (f"행={visible}, 'No registered devices' 표시={'No registered devices' in text}",
                    "No registered devices" in text and not visible)
        ui("UI-04", "U005(가전 없음) 클릭 시 안내 메시지 (TE-5)", '"No registered devices" 표시, 행 없음', ui04)

        ui("UI-05", '가전 검색 "TV" (TE-6)', "U001: D001 (TV)",
           filter_case("U001", [("search", "TV")], ["D001"]))
        ui("UI-06", '가전 필터 "Online" (TE-7)', "U003: D004, D005",
           filter_case("U003", [("status", "Online")], device_ids("U003", lambda d: d["status"] == "Online")))
        ui("UI-07", '모델명 검색 "whisen" (대소문자 무시)', "U003: D005",
           filter_case("U003", [("search", "whisen")], ["D005"]))
        ui("UI-08", '위치 검색 "Home"', "U003: D006",
           filter_case("U003", [("search", "Home")], ["D006"]))
        ui("UI-09", '상태 텍스트 검색 "error"', "U003: D006",
           filter_case("U003", [("search", "error")], ["D006"]))
        ui("UI-10", '디바이스 ID 검색 "D005"', "U003: D005",
           filter_case("U003", [("search", "D005")], ["D005"]))
        ui("UI-11", '필터 "Offline"', "U001: D002",
           filter_case("U001", [("status", "Offline")], ["D002"]))
        ui("UI-12", '필터 "Standby"', "U004: D008",
           filter_case("U004", [("status", "Standby")], ["D008"]))
        ui("UI-13", '필터 "Error"', "U003: D006",
           filter_case("U003", [("status", "Error")], ["D006"]))
        ui("UI-14", '검색 "LG" + 필터 "Online" 동시 적용', "U003: D004, D005",
           filter_case("U003", [("search", "LG"), ("status", "Online")], ["D004", "D005"]))
        ui("UI-15", '필터 해제 + 검색어 삭제 시 복원', "U003: D004, D005, D006",
           filter_case("U003", [("status", "Error"), ("search", "Styler"), ("status", ""), ("search", "")],
                       device_ids("U003")))

        def ui16(p):
            pick_user(p, "U001")
            p.select_option("#device-status-filter", "Error")
            p.wait_for_timeout(300)
            text = device_panel_text(p)
            return (f"행={rows(p, '#device-body')}, 'No devices matched' 표시={'No devices matched' in text}",
                    "No devices matched" in text and not rows(p, "#device-body"))
        ui("UI-16", "필터 결과 없음 (U001 + Error)", '"No devices matched" 표시, 행 없음', ui16)

        def ui17(p):
            first = pick_user(p, "U001")
            second = pick_user(p, "U003")
            return f"U001={first} → U003={second}", first == ["D001", "D002"] and second == device_ids("U003")
        ui("UI-17", "다른 구독자 클릭 시 가전 목록 교체", "U001 목록 → U003 목록으로 교체", ui17)

        def ui18(p):
            pick_user(p, "U003")
            p.evaluate("window.__noReload = true")
            p.click("#device-search")
            p.keyboard.type("Sty", delay=50)
            actual = wait_rows(p, "#device-body", ["D006"])
            same = p.evaluate("window.__noReload === true")
            return f'"Sty"→{actual}, 페이지 유지={same}', actual == ["D006"] and same
        ui("UI-18", "가전 검색 실시간 반영 (키 입력)", "입력 즉시 D006, 새로고침 없음", ui18)

        # ---------- 사용 현황 + 차트 (4.5 + 4.6) ----------
        usage_cases = [
            ("UI-19", "D001 클릭 시 사용 현황 표시 (TE-10)", "8개 항목 값 표시, 안내문구 숨김"),
            ("UI-20", "Power / Health Status badge", "두 값 모두 span.badge"),
            ("UI-21", "D001 클릭 시 Bar Chart (TE-11)", f"bar, {DAYS}, {USAGE['D001']['weeklyUsageTrend']}"),
            ("UI-22", "선택한 가전 행 선택 표시", "D001 1행만 selected"),
            ("UI-23", "다른 가전 클릭 시 차트 갱신 (TE-12)", "D002 데이터로 교체, 차트 1개만 존재"),
            ("UI-24", "구독자 변경 시 사용 현황 초기화", "usage-empty 표시, usage-detail 숨김, 내용 비움"),
        ]
        ui01_ok = any(r[0] == "UI-01" and r[5] == "PASS" for r in results)
        if not usage_ok or not ui01_ok:
            reason = "선행 조건 API-06(usage API) 실패" if not usage_ok else "선행 조건 UI-01(가전 목록 화면) 실패"
            for tc_id, sc, exp in usage_cases:
                block(tc_id, "UI", sc, exp, f"BLOCKED — {reason}")
        else:
            def ui19(p):
                pick_user(p, "U001")
                pick_device(p, "D001")
                info = p.evaluate("document.getElementById('usage-info').innerText")
                u = USAGE["D001"]
                values = [u[k] for k in USAGE_FIELDS if k != "weeklyUsageTrend"]
                missing = [v for v in values if str(v) not in info]
                shown = is_visible(p, "usage-detail") and not is_visible(p, "usage-empty")
                return (f"누락 값={missing}, 상세 표시={shown}", not missing and shown)
            ui("UI-19", *usage_cases[0][1:], ui19)

            def ui20(p):
                pick_user(p, "U001")
                pick_device(p, "D001")
                badges = p.evaluate("() => [...document.querySelectorAll('#usage-info span.badge')]"
                                    ".map(b => b.innerText.trim())")
                return badges, "On" in badges and "Normal" in badges
            ui("UI-20", *usage_cases[1][1:], ui20)

            def ui21(p):
                pick_user(p, "U001")
                pick_device(p, "D001")
                c = chart_state(p)
                ok = bool(c) and c["type"] == "bar" and c["labels"] == DAYS \
                    and c["data"] == USAGE["D001"]["weeklyUsageTrend"]
                return c or "차트 없음", ok
            ui("UI-21", *usage_cases[2][1:], ui21)

            def ui22(p):
                pick_user(p, "U001")
                pick_device(p, "D001")
                sel = p.evaluate("() => [...document.querySelectorAll('#device-body tr.selected')]"
                                 ".map(r => r.cells[0].innerText.trim())")
                return sel, sel == ["D001"]
            ui("UI-22", *usage_cases[3][1:], ui22)

            def ui23(p):
                pick_user(p, "U001")
                pick_device(p, "D001")
                pick_device(p, "D002")
                c = chart_state(p)
                ok = bool(c) and c["data"] == USAGE["D002"]["weeklyUsageTrend"] and c["count"] == 1
                return c or "차트 없음", ok
            ui("UI-23", *usage_cases[4][1:], ui23)

            def ui24(p):
                pick_user(p, "U001")
                pick_device(p, "D001")
                pick_user(p, "U002")
                p.wait_for_timeout(300)
                info = p.evaluate("document.getElementById('usage-info').innerText.trim()")
                st = {"usage-empty 표시": is_visible(p, "usage-empty"),
                      "usage-detail 숨김": not is_visible(p, "usage-detail"), "내용 비움": info == ""}
                return st, all(st.values())
            ui("UI-24", *usage_cases[5][1:], ui24)

        # ---------- 응답 지연 ----------
        def ui27():
            p = ctx.new_page()
            p.on("pageerror", lambda e: page_errors.append(str(e)))
            # U003 가전 조회만 1.5초 지연시켜 "조회 중" 상태를 재현
            p.add_init_script("""const of = window.fetch; window.fetch = async (u, o) => {
                if (String(u).includes('/subscribers/U003/')) await new Promise(r => setTimeout(r, 1500));
                return of(u, o); };""")
            p.goto(base + "/")
            wait_rows(p, "#subscriber-body", [u["userId"] for u in SUBSCRIBERS])
            pick_user(p, "U001")
            p.locator("#subscriber-body tr", has_text="U003").click()
            p.wait_for_timeout(200)
            loading = rows(p, "#device-body")
            final = wait_rows(p, "#device-body", device_ids("U003"))
            passed = loading == [] and final == device_ids("U003")
            if not passed:
                shot(p, "UI-27")
            check("UI-27", "UI", "가전 조회 지연 중 이전 사용자 목록 제거",
                  "조회 중 0행 → 완료 후 U003 목록", f"조회 중={loading} → 완료 후={final}", passed)
            p.close()
        ui27()

        # ---------- 회귀 / 공통 ----------
        def ui25(p):
            p.fill("#subscriber-search", "Kim")
            actual = wait_rows(p, "#subscriber-body", ["U001"])
            return actual, actual == ["U001"]
        ui("UI-25", '회귀: 구독자 검색 "Kim" (요구사항 #1)', "U001", ui25)

        check("UI-26", "UI", "전체 실행 중 브라우저 JS 오류", "pageerror 0건",
              f"{len(page_errors)}건 {sorted(set(page_errors))[:3]}", not page_errors)

        browser.close()


# =============================================================================
# Report
# =============================================================================
MARK = {"PASS": "✅ PASS", "FAIL": "❌ FAIL", "BLOCKED": "⛔ BLOCKED"}


def render_report(base, commit):
    total = len(results)
    cnt = {k: sum(1 for r in results if r[5] == k) for k in MARK}
    lines = [
        "# requirement_2 API + 브라우저(E2E) 자동 검증 Report",
        "",
        "| 항목 | 내용 |",
        "|------|------|",
        "| **프로젝트** | webOS Subscription Management Dashboard |",
        "| **검증 대상** | requirement_2.md (가전 목록 + 사용 현황 + 차트) |",
        f"| **검증 일시** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |",
        f"| **대상 URL** | {base} |",
        f"| **대상 커밋** | `{commit}` |",
        "| **작성자** | 최민석 (PM / TE) |",
        "| **도구** | Python urllib (API), Playwright Chromium (UI) |",
        "",
        f"**총 {total}건 — PASS {cnt['PASS']} / FAIL {cnt['FAIL']} / BLOCKED {cnt['BLOCKED']}"
        f" — Pass Rate {(cnt['PASS'] / total * 100) if total else 0:.1f}%**",
        "",
        "| TC ID | 구분 | 테스트 시나리오 | 기대 결과 | 실제 결과 | 판정 |",
        "|:-----:|:----:|----------------|-----------|-----------|:----:|",
    ]
    for tc, layer, sc, exp, act, st in results:
        cell = lambda v: str(v).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {tc} | {layer} | {cell(sc)} | {cell(exp)} | {cell(act)} | {MARK[st]} |")
    lines += ["", "> 본 Report 는 `tests/req2_e2e_test.py` 로 생성되었습니다. "
              "실패 시 화면 캡처는 `tests/reports/screenshots/req2_*.png` 에 저장됩니다."]
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return cnt, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", help="이미 떠 있는 서버/배포 URL (없으면 로컬 서버 자동 기동)")
    ap.add_argument("--headed", action="store_true", help="브라우저 화면 표시")
    args = ap.parse_args()

    print("=" * 60)
    print(" requirement_2 API + E2E 검증")
    print("=" * 60)

    proc = None
    try:
        if args.base_url:
            base = args.base_url.rstrip("/")
        else:
            proc, base = start_server()
        print(f"[대상] {base}")
        usage_ok = run_api_tests(base)
        try:
            run_ui_tests(base, args.headed, usage_ok)
        except ImportError:
            check("UI-00", "UI", "Playwright 설치 여부", "설치됨",
                  "미설치: pip install -r tests/requirements-te.txt", False)
        except Exception as e:
            check("UI-ERR", "UI", "UI 검증 실행 중단", "정상 실행", f"{type(e).__name__}: {e}"[:200], False)
    finally:
        stop_server(proc)

    cnt, total = render_report(base, git_commit() if not args.base_url else "배포 서버 (PM 확인)")
    print("\n" + "=" * 60)
    print(f" 결과: PASS {cnt['PASS']} / FAIL {cnt['FAIL']} / BLOCKED {cnt['BLOCKED']} (총 {total})")
    print(f" Report 저장: {os.path.relpath(REPORT_PATH, PROJECT_ROOT)}")
    print("=" * 60)
    return 0 if cnt["PASS"] == total else 1


if __name__ == "__main__":
    sys.exit(main())
