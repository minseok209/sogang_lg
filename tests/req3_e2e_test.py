"""
requirement_3 상태 Badge 검증 스크립트  (TE)

badgeClass() 매핑 규칙과, 실제 화면(구독자 / 가전 / 사용 현황)의 badge 가
올바른 CSS 클래스와 "실제 렌더링 색상"으로 표시되는지 Chromium 으로 확인합니다.

실행 방법
--------
    pip install -r tests/requirements-te.txt
    python -m playwright install chromium

    python tests/req3_e2e_test.py
    python tests/req3_e2e_test.py --base-url https://<배포 URL>   # 배포 후 검증

결과
----
    tests/reports/req3_e2e_report.md
    종료 코드: 0 = 전부 PASS, 1 = FAIL 있음
"""

import argparse
import os
import sys
from datetime import datetime

# 서버 기동 / HTTP 유틸은 요구사항 #2 스크립트의 것을 재사용
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from req2_e2e_test import (  # noqa: E402
    PROJECT_ROOT, REPORT_DIR, SHOT_DIR, VISIBLE_ROWS_JS,
    SUBSCRIBERS, DEVICES, USAGE, start_server, stop_server, git_commit,
)

REPORT_PATH = os.path.join(REPORT_DIR, "req3_e2e_report.md")

# requirement_3.md 색상 매핑 표 (값 → (CSS 클래스, 색상 이름))
MAPPING = {
    "Active": "status-active", "Online": "status-active", "Normal": "status-active",
    "Paused": "status-paused", "Standby": "status-paused",
    "Expired": "status-expired", "Error": "status-expired", "Warning": "status-expired",
    "Offline": "status-offline",
    "On": "status-on", "Cleaning": "status-on",
    "Off": "status-off",
}
# style.css 의 실제 배경색 (computed style 기준)
COLOR = {
    "status-active": ("초록", "rgb(220, 252, 231)"),
    "status-paused": ("파랑", "rgb(224, 231, 255)"),
    "status-expired": ("빨강", "rgb(254, 226, 226)"),
    "status-offline": ("회색", "rgb(229, 231, 235)"),
    "status-on": ("노랑", "rgb(254, 243, 199)"),
    "status-off": ("연회색", "rgb(243, 244, 246)"),
}
COLOR_NAME = {rgb: name for name, rgb in COLOR.values()}

results = []  # (TC ID, 구분, 시나리오, 기대 결과, 실제 결과, 판정)


def check(tc_id, layer, scenario, expected, actual, passed):
    results.append((tc_id, layer, scenario, expected, str(actual), passed))
    print(f"  [{'PASS' if passed else 'FAIL'}] {tc_id}  {scenario}  → {actual}")


def expected_for(value):
    cls = MAPPING.get(value)
    return (f"badge {cls}", COLOR[cls][0]) if cls else ("badge", "기본")


def run_tests(base, headed):
    from playwright.sync_api import sync_playwright

    page_errors = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not headed)
        page = browser.new_page(viewport={"width": 1280, "height": 1000})
        page.set_default_timeout(5000)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(base + "/")
        page.wait_for_function("document.querySelectorAll('#subscriber-body tr').length === 5")

        # ------------------------------------------------------------------
        # 1) badgeClass() 함수 매핑 (요구사항 문서의 규칙 그대로)
        # ------------------------------------------------------------------
        print("\n[badgeClass() 매핑]")
        def expected_class(v):
            key = (v or "").capitalize()
            return f"badge {MAPPING[key]}" if key in MAPPING else "badge"

        groups = [
            ("FN-01", "상태 값 12종 매핑", "Active/Online/Normal→status-active … Off→status-off", list(MAPPING)),
            ("FN-02", "대소문자 무시 (ACTIVE, online, warning)", "각 값의 매핑 클래스", ["ACTIVE", "online", "warning"]),
            ("FN-03", "그 외 값 (Unknown, 빈 문자열, null)", '"badge"', ["Unknown", "", None]),
        ]
        for tc, scenario, expected, vals in groups:
            got = page.evaluate("vals => vals.map(v => badgeClass(v))", vals)
            wrong = [f"{v!r}→{g!r}" for v, g in zip(vals, got) if g != expected_class(v)]
            check(tc, "FN", scenario, expected, "전부 일치" if not wrong else wrong, not wrong)

        def badge_info(selector):
            """selector 에 해당하는 badge 들의 (텍스트, class, 배경색)."""
            return page.evaluate("""sel => [...document.querySelectorAll(sel)].map(b => [
                b.innerText.trim(), b.className, getComputedStyle(b).backgroundColor])""", selector)

        def verify(tc_id, scenario, items):
            """items: [(텍스트, class, 배경색)] → 텍스트별 기대 class/색상과 비교."""
            bad, shown = [], []
            for text, cls, bg in items:
                exp_cls, exp_color = expected_for(text)
                ok = cls == exp_cls and (exp_color == "기본" or COLOR_NAME.get(bg) == exp_color)
                shown.append(f"{text}={COLOR_NAME.get(bg, bg)}")
                if not ok:
                    bad.append(f"{text}: class={cls!r}, 색={COLOR_NAME.get(bg, bg)} (기대 {exp_cls}, {exp_color})")
            passed = bool(items) and not bad
            if not passed:
                os.makedirs(SHOT_DIR, exist_ok=True)
                page.screenshot(path=os.path.join(SHOT_DIR, f"req3_{tc_id}.png"), full_page=True)
            exp = ", ".join(sorted({f"{t}={expected_for(t)[1]}" for t, _, _ in items})) or "badge 존재"
            check(tc_id, "UI", scenario, exp, ", ".join(shown) if passed else (bad or "badge 없음"), passed)

        # ------------------------------------------------------------------
        # 2) 구독자 Table (TE #1~#3)
        # ------------------------------------------------------------------
        print("\n[구독자 상태 badge]")
        subs = badge_info("#subscriber-body span.badge")
        for tc, status in (("UI-01", "Active"), ("UI-02", "Paused"), ("UI-03", "Expired")):
            verify(tc, f"구독 상태 {status} (TE-{tc[-1]})", [i for i in subs if i[0] == status])

        # ------------------------------------------------------------------
        # 3) 가전 Table (TE #4~#6 + Standby)
        # ------------------------------------------------------------------
        print("\n[가전 상태 badge]")
        seen = {}
        for user in ("U001", "U003", "U004"):
            page.locator("#subscriber-body tr", has_text=user).click()
            page.wait_for_function("([sel, n]) => (" + VISIBLE_ROWS_JS + ")(sel).length === n",
                                   arg=["#device-body", len(DEVICES[user])])
            for item in badge_info("#device-body span.badge"):
                seen.setdefault(item[0], item)
        for tc, status, te in (("UI-04", "Online", "TE-4"), ("UI-05", "Offline", "TE-5"),
                               ("UI-06", "Error", "TE-6"), ("UI-07", "Standby", "보강")):
            verify(tc, f"가전 상태 {status} ({te})", [seen[status]] if status in seen else [])

        # ------------------------------------------------------------------
        # 4) 사용 현황 Power / Health (TE #7~#9 + 보강)
        # ------------------------------------------------------------------
        print("\n[사용 현황 badge]")
        owner = {d["deviceId"]: u for u, ds in DEVICES.items() for d in ds}

        def usage_badges(device_id):
            page.locator("#subscriber-body tr", has_text=owner[device_id]).click()
            page.locator("#device-body tr", has_text=device_id).click()
            page.wait_for_function(
                "id => !document.getElementById('usage-detail').classList.contains('hidden') && "
                "document.getElementById('usage-info').innerText.includes(id)", arg=device_id)
            return badge_info("#usage-info span.badge")

        cases = [
            ("UI-08", "D001", "powerStatus", "Power On (TE-7)"),
            ("UI-09", "D001", "healthStatus", "Health Normal (TE-8)"),
            ("UI-10", "D006", "healthStatus", "Health Warning (TE-9)"),
            ("UI-11", "D006", "powerStatus", "Power Error"),
            ("UI-12", "D002", "powerStatus", "Power Off"),
            ("UI-13", "D007", "powerStatus", "Power Cleaning"),
            ("UI-14", "D004", "powerStatus", "Power Standby"),
        ]
        cache = {}
        for tc, dev, field, scenario in cases:
            if dev not in cache:
                cache[dev] = usage_badges(dev)
            want = USAGE[dev][field]
            verify(tc, f"{dev} {scenario}", [i for i in cache[dev] if i[0] == want][:1])

        # ------------------------------------------------------------------
        # 5) 화면 전체 badge 누락 여부 + JS 오류
        # ------------------------------------------------------------------
        plain = [i[0] for i in badge_info("span.badge") if i[0] in MAPPING and i[1] == "badge"]
        check("UI-15", "UI", "매핑 대상 값이 기본 badge 로 남은 곳", "0건", plain or "0건", not plain)
        check("UI-16", "UI", "실행 중 브라우저 JS 오류", "pageerror 0건",
              f"{len(page_errors)}건 {page_errors[:3]}", not page_errors)
        browser.close()


def render_report(base, commit):
    total = len(results)
    passed = sum(1 for r in results if r[5])
    cell = lambda v: str(v).replace("|", "\\|").replace("\n", " ")
    lines = [
        "# requirement_3 상태 Badge 자동 검증 Report",
        "",
        "| 항목 | 내용 |",
        "|------|------|",
        "| **프로젝트** | webOS Subscription Management Dashboard |",
        "| **검증 대상** | requirement_3.md Part A (상태 기반 UI 표현) |",
        f"| **검증 일시** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |",
        f"| **대상 URL** | {base} |",
        f"| **대상 커밋** | `{commit}` |",
        "| **작성자** | 최민석 (PM / TE) |",
        "| **도구** | Playwright Chromium (class + computed background-color) |",
        "",
        f"**총 {total}건 중 PASS {passed} / FAIL {total - passed} — Pass Rate "
        f"{(passed / total * 100) if total else 0:.1f}%**",
        "",
        "| TC ID | 구분 | 테스트 시나리오 | 기대 결과 | 실제 결과 | 판정 |",
        "|:-----:|:----:|----------------|-----------|-----------|:----:|",
    ]
    for tc, layer, sc, exp, act, ok in results:
        lines.append(f"| {tc} | {layer} | {cell(sc)} | {cell(exp)} | {cell(act)} | "
                     f"{'✅ PASS' if ok else '❌ FAIL'} |")
    lines += ["", "> 본 Report 는 `tests/req3_e2e_test.py` 로 생성되었습니다."]
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
    print(" requirement_3 상태 Badge 검증")
    print("=" * 60)
    proc = None
    try:
        if args.base_url:
            base = args.base_url.rstrip("/")
        else:
            proc, base = start_server()
        print(f"[대상] {base}")
        try:
            run_tests(base, args.headed)
        except Exception as e:
            check("ERR", "UI", "검증 실행 중단", "정상 실행", f"{type(e).__name__}: {e}"[:200], False)
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
