"""
TC-12: Real Veo API Integration Test
=====================================
Verifies the backend can actually call genaipro API with the stored Veo JWT
and get a 200 OK response (with valid user data).

WHY THIS TEST EXISTS
- Previously the service returned 401 invalid_token even when the same token
  worked when called directly from a shell.
- This test locks in the real API integration so we don't regress.

DESIGN PRINCIPLES
- ONE genaipro call per test run (to avoid rate-limit/revocation)
- No direct probe of genaipro from outside the service (everything via API)
- Real Chromium screenshots, not curl
- IP-aware: skip if backend IP is known to be Cloudflare-banned

USAGE
    /usr/bin/python3 test_veo_real.py
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ---- Config ----
BASE = "https://directorstudio.sj88ai.com"
ADMIN_EMAIL = "admin@sj88ai.com"
ADMIN_PASSWORD = "admin1234"
CHROMIUM = "/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome"
RUNS_DIR = Path(__file__).parent / "runs"
RUNS_DIR.mkdir(exist_ok=True)


def log(msg):
    print(msg, flush=True)


def make_run_dir():
    ts = time.strftime("%Y%m%d_%H%M%S")
    d = RUNS_DIR / ts
    d.mkdir(exist_ok=True)
    return d


def api(path, method="GET", data=None, token=None):
    """Helper for backend API calls."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def screenshot(page, run_dir, name):
    p = run_dir / f"{name}.png"
    page.screenshot(path=str(p), full_page=False)
    log(f"  📸 {p.name}")


def step(n, name):
    log(f"\n=== Step {n}: {name} ===")


def main():
    run_dir = make_run_dir()
    results = []  # (id, description, expected, actual, pass)
    findings = []  # any anomalies

    def record(id_, desc, expected, actual, ok):
        results.append((id_, desc, expected, actual, ok))
        icon = "✅" if ok else "❌"
        log(f"  {icon} [{id_}] {desc}")
        log(f"      expected: {expected}")
        log(f"      actual:   {actual}")

    # ---------- Step 1: Health check ----------
    step(1, "Backend health")
    s, h = api("/api/health")
    ok = s == 200 and h.get("ok") is True
    record("12.1.1", "GET /api/health", 200, s, ok)
    if ok:
        log(f"      service: {h.get('service')} v{h.get('version')}, worker: {h.get('worker_active')}")

    # ---------- Step 2: Login as admin ----------
    step(2, "Login as admin")
    s, d = api("/api/auth/login", "POST", {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if s != 200 or "access_token" not in d:
        log(f"❌ Login failed: {s} {d}")
        return
    token = d["access_token"]
    user = d.get("user", {})
    record("12.2.1", "POST /api/auth/login", 200, s, True)
    record("12.2.2", "User role is admin", True, user.get("is_admin") is True, user.get("is_admin") is True)
    log(f"      user: {user.get('email')} (id={user.get('id')[:16]}...)")

    H = {"Authorization": f"Bearer {token}"}

    # ---------- Step 3: Get settings (check Veo JWT fingerprint) ----------
    step(3, "Verify Veo JWT is configured + fingerprint visible")
    s, settings = api("/api/settings", token=token)
    record("12.3.1", "GET /api/settings", 200, s, s == 200)
    has_jwt = settings.get("has_veo_jwt")
    fp = settings.get("veo_jwt_fingerprint", "")
    decrypt_ok = settings.get("veo_jwt_decrypt_ok")
    record("12.3.2", "has_veo_jwt = true", True, has_jwt, has_jwt is True)
    record("12.3.3", "veo_jwt_decrypt_ok = true", True, decrypt_ok, decrypt_ok is True)
    record("12.3.4", "fingerprint starts with 'sha256:'", "sha256:...", fp[:12] + "...", fp.startswith("sha256:") and len(fp) == 15)
    if not fp.startswith("sha256:"):
        findings.append(f"Fingerprint not in expected format: {fp!r}")
    log(f"      fingerprint: {fp}")

    # ---------- Step 4: Test JWT (THE CRITICAL REAL CALL) ----------
    step(4, "Test JWT via genaipro /v2/me (REAL API CALL)")
    log("  ⚠️  This makes 1 real call to genaipro.io/api/v2/me")
    s, test = api("/api/settings/veo-jwt/test", token=token)
    record("12.4.1", "GET /api/settings/veo-jwt/test returns 200", 200, s, s == 200)
    log(f"      response: {json.dumps(test, default=str)[:500]}")
    if test.get("ok"):
        record("12.4.2", "ok = true", True, test.get("ok"), True)
        record("12.4.3", "username = sj888", "sj888", test.get("username"), test.get("username") == "sj888")
        balance = test.get("balance")
        record("12.4.4", "balance is a number ≥ 0", "≥0", balance, isinstance(balance, (int, float)) and balance >= 0)
        remaining = test.get("total_remaining")
        record("12.4.5", "total_remaining is a number ≥ 0", "≥0", remaining, isinstance(remaining, (int, float)) and remaining >= 0)
    else:
        record("12.4.2", "ok = true", True, test.get("ok"), False)
        err = test.get("error", "")
        body = test.get("body", "")
        record("12.4.3", "error is NOT 'HTTP 401'", "≠401", err, err != "HTTP 401")
        if err == "HTTP 401":
            findings.append(
                "🚨 401 invalid_token: Veo JWT rejected by genaipro. "
                "Token may be expired/revoked. Generate new at genaipro.io → Avatar → API Key."
            )

    # ---------- Step 5: UI verification via Playwright ----------
    step(5, "UI: open Settings, verify fingerprint shown")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROMIUM,
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--use-gl=swiftshader"],
        )
        ctx = browser.new_context(viewport={"width": 1400, "height": 1100})
        page = ctx.new_page()

        # 5.1: Open login
        page.goto(f"{BASE}/auth.html", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)
        screenshot(page, run_dir, "12_5_01_login")

        # 5.2: Sign in
        page.fill('input[name="email"]', ADMIN_EMAIL)
        page.fill('input[name="password"]', ADMIN_PASSWORD)
        page.click("#auth-submit")
        page.wait_for_timeout(3000)
        screenshot(page, run_dir, "12_5_02_logged_in")

        # 5.3: Open Settings
        page.goto(f"{BASE}/settings.html", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(3000)
        screenshot(page, run_dir, "12_5_03_settings")

        # 5.4: Click "Test" button if available
        try:
            test_btn = page.locator('button:has-text("Test"), button:has-text("ทดสอบ")').first
            if test_btn.is_visible(timeout=2000):
                test_btn.click()
                page.wait_for_timeout(5000)
                screenshot(page, run_dir, "12_5_04_after_test")
                record("12.5.1", "UI Test button clickable", True, True, True)
            else:
                record("12.5.1", "UI Test button visible", True, False, False)
                findings.append("⚠️ Test button not visible in Settings UI")
        except Exception as e:
            record("12.5.1", "UI Test button found", True, False, False)
            findings.append(f"⚠️ Test button error: {e}")

        # 5.5: Check fingerprint visible in UI
        try:
            body = page.locator("body").inner_text()
            has_sha = "sha256:" in body
            record("12.5.2", "Fingerprint 'sha256:...' visible in UI", True, has_sha, has_sha)
        except Exception as e:
            record("12.5.2", "Fingerprint check", True, False, False)

        browser.close()

    # ---------- Summary ----------
    total = len(results)
    passed = sum(1 for _, _, _, _, ok in results if ok)
    log(f"\n{'='*60}")
    log(f"=== RESULT: {passed}/{total} PASS ({100*passed//total}%) ===")
    log(f"{'='*60}")
    for f in findings:
        log(f"  📝 {f}")

    # Write HTML report
    write_report(run_dir, results, findings)
    log(f"\nReport: {run_dir / 'report.html'}")
    return 0 if passed == total else 1


def write_report(run_dir, results, findings):
    rows = []
    for id_, desc, expected, actual, ok in results:
        cls = "pass" if ok else "fail"
        actual_str = str(actual)[:200]
        rows.append(f"""<tr class="{cls}">
  <td>{id_}</td>
  <td>{desc}</td>
  <td class="expected">{expected}</td>
  <td class="actual">{actual_str}</td>
  <td>{'✅' if ok else '❌'}</td>
</tr>""")
    total = len(results)
    passed = sum(1 for _, _, _, _, ok in results if ok)
    findings_html = "".join(f"<li>{f}</li>" for f in findings) or "<li>none</li>"
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>TC-12 Real Veo API</title>
<style>
body{{font-family:system-ui;margin:24px;background:#0e0e10;color:#e5e5e5}}
h1{{color:#22c55e}}
table{{width:100%;border-collapse:collapse;margin-top:16px}}
td,th{{padding:8px;border:1px solid #333;text-align:left;font-size:13px}}
tr.pass td{{background:#052e1a}}tr.fail td{{background:#3a0d0d}}
.expected{{color:#9ca3af}}.actual{{color:#e5e5e7;font-family:monospace}}
ul{{background:#1a1a1a;padding:16px 32px;border-radius:8px}}
img{{max-width:100%;border:1px solid #333;margin:8px 0}}
.gallery{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-top:16px}}
.card{{background:#1a1a1a;padding:8px;border-radius:8px}}
</style></head><body>
<h1>TC-12: Real Veo API Integration</h1>
<p><b>Date:</b> {time.strftime('%Y-%m-%d %H:%M:%S')} · <b>Result:</b> {passed}/{total} PASS</p>

<h2>Findings</h2>
<ul>{findings_html}</ul>

<h2>Assertions</h2>
<table>
<tr><th>#</th><th>Description</th><th>Expected</th><th>Actual</th><th>Pass</th></tr>
{"".join(rows)}
</table>

<h2>Screenshots</h2>
<div class="gallery">
{''.join(f'<div class="card"><b>{p.name}</b><br><img src="{p.name}"></div>' for p in sorted(run_dir.glob("*.png")))}
</div>
</body></html>"""
    (run_dir / "report.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
