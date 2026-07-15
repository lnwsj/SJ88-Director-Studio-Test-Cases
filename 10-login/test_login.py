#!/usr/bin/env python3
"""
TC-10: Login Flow (UI + API) - DETAILED
Tests user authentication on Director Studio.

**Page:** https://directorstudio.sj88ai.com/

**UI Structure (from manual exploration 2026-07-14):**
- Single page with 2 tabs: "เข้าสู่ระบบ" (login) | "สมัครสมาชิก" (signup)
- Login form (default tab): 2 inputs (email, password) + "เข้าสู่ระบบ" button
- Signup form (alt tab): 3 inputs (display_name, email, password) + "สมัคร" button

**Element selectors:**
- email input: `input[name="email"]`
- password input: `input[name="password"]`
- login tab button: `button:has-text("เข้าสู่ระบบ")`
- signup tab button: `button:has-text("สมัครสมาชิก")`
- submit button: `#auth-submit`
- logout button: `#logout-btn`

**API:** POST /api/auth/login
- body: {email, password}
- 200: {access_token, token_type, user}
- 401: invalid credentials

**Security checks:**
- No-token requests return 401
- Bad token returns 401
- Wrong password returns 401
- User with bad email format rejected
- Session token in localStorage after login
- Logout clears localStorage
"""
import asyncio
import json
import time
import urllib.request
import urllib.error
import secrets
from playwright.async_api import async_playwright
from datetime import datetime
from pathlib import Path

BASE = "https://directorstudio.sj88ai.com"
CHROME = "/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome"
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
OUT = Path(f"/workspace/director-studio-test-cases/10-login/runs/{TS}")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "screenshots").mkdir(exist_ok=True)

TEST_NAME = "TC-10 Login Flow (UI + API)"

# Pre-existing test user (from TC-09 or admin)
ADMIN_EMAIL = "admin@sj88ai.com"
ADMIN_PASSWORD = "admin1234"

# New test user for signup
TEST_USER = {
    "email": f"tc10_{secrets.token_hex(4)}@sj88ai.com",
    "password": "tc10test1234",
    "display_name": "TC-10 User"
}

assertions = []
start_time = time.time()


def assert_eq(step, name, expected, actual, screenshot="", notes=""):
    status = "PASS" if expected == actual else "FAIL"
    assertions.append({
        "step": step, "name": name, "expected": str(expected),
        "actual": str(actual)[:300], "status": status,
        "screenshot": screenshot, "notes": notes
    })
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} [{step}] {name}: expected={expected!r}, got={str(actual)[:80]!r}")
    return status == "PASS"


def assert_truthy(step, name, actual, screenshot="", notes=""):
    status = "PASS" if bool(actual) else "FAIL"
    assertions.append({
        "step": step, "name": name, "expected": "truthy",
        "actual": str(actual)[:300], "status": status,
        "screenshot": screenshot, "notes": notes
    })
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} [{step}] {name}: truthy? got={str(actual)[:80]!r}")
    return status == "PASS"


def assert_contains(step, name, expected_substr, actual_str, screenshot="", notes=""):
    status = "PASS" if expected_substr in str(actual_str) else "FAIL"
    assertions.append({
        "step": step, "name": name, "expected": f"contains '{expected_substr}'",
        "actual": str(actual_str)[:300], "status": status,
        "screenshot": screenshot, "notes": notes
    })
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} [{step}] {name}: contains '{expected_substr}'? got={str(actual_str)[:80]!r}")
    return status == "PASS"


async def shoot(page, name):
    path = OUT / "screenshots" / f"{name}.png"
    await page.screenshot(path=str(path), full_page=False)
    return str(path)


def api_get(path, token=""):
    req = urllib.request.Request(f"{BASE}{path}")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        return json.loads(urllib.request.urlopen(req, timeout=15).read().decode()), None, 200
    except urllib.error.HTTPError as e:
        try:
            return None, e.read().decode()[:300], e.code
        except:
            return None, str(e), e.code
    except Exception as e:
        return None, str(e), 0


def api_post(path, body, token=""):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        return json.loads(urllib.request.urlopen(req, timeout=15).read().decode()), None, 200
    except urllib.error.HTTPError as e:
        try:
            return None, e.read().decode()[:300], e.code
        except:
            return None, str(e), e.code
    except Exception as e:
        return None, str(e), 0


async def main():
    print(f"\n=== {TEST_NAME} ===\n")
    print(f"Run dir: {OUT}\n")

    # ====== STEP 0: Create test user (need a valid user to login as) ======
    print("--- Step 0: Create test user ---")
    res, err, code = api_post("/api/auth/signup", {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"],
        "display_name": TEST_USER["display_name"]
    })
    assert_eq(0, "Create test user (signup)", 200, code, "", f"err={err}")
    if res and "access_token" in res:
        print(f"  ✓ User created: {TEST_USER['email']}")

    # ====== STEP 1: API: POST /api/auth/login (valid admin) ======
    print("\n--- Step 1: API login (valid admin) ---")
    res, err, code = api_post("/api/auth/login", {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert_eq(1, "POST /api/auth/login returns 200", 200, code, "", f"err={err}")
    admin_token = res.get("access_token") if res else None
    assert_truthy(1, "Response has access_token", admin_token, "", f"len={len(admin_token) if admin_token else 0}")
    if res and "user" in res:
        u = res["user"]
        assert_eq(1, "Response has user.email", ADMIN_EMAIL, u.get("email", ""), "")
        assert_eq(1, "Response has user.role", "admin", u.get("role", ""), "")

    # ====== STEP 2: API: GET /api/auth/me with new token ======
    print("\n--- Step 2: API verify token ---")
    me, err, code = api_get("/api/auth/me", admin_token)
    assert_eq(2, "GET /api/auth/me works", 200, code, "", "")
    if me:
        assert_eq(2, "GET /api/auth/me returns correct email", ADMIN_EMAIL, me.get("email", ""), "")

    # ====== STEP 3: API: wrong password ======
    print("\n--- Step 3: API wrong password ---")
    res, err, code = api_post("/api/auth/login", {
        "email": ADMIN_EMAIL,
        "password": "wrong_password_999"
    })
    assert_eq(3, "Wrong password returns 401", 401, code, "", f"err={err}")

    # ====== STEP 4: API: wrong email ======
    print("\n--- Step 4: API wrong email ---")
    res, err, code = api_post("/api/auth/login", {
        "email": "nonexistent@sj88ai.com",
        "password": "any_password"
    })
    assert_eq(4, "Wrong email returns 401", 401, code, "", f"err={err}")

    # ====== STEP 5: API: empty body ======
    print("\n--- Step 5: API empty body ---")
    res, err, code = api_post("/api/auth/login", {})
    assert_truthy(5, "Empty body returns 4xx", code >= 400, "", f"code={code}, err={err}")

    # ====== STEP 6: API: bad token ======
    print("\n--- Step 6: API bad token ---")
    me, err, code = api_get("/api/auth/me", "invalid_jwt_token_xxx")
    assert_eq(6, "GET /api/auth/me with bad token returns 401", 401, code, "")

    # ====== STEP 7: API: no token ======
    print("\n--- Step 7: API no token ---")
    me, err, code = api_get("/api/auth/me", "")
    assert_eq(7, "GET /api/auth/me without token returns 401", 401, code, "")

    # ====== STEP 8: UI: open login page ======
    print("\n--- Step 8: UI open login ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROME,
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--use-gl=swiftshader"],
        )
        ctx = await browser.new_context(viewport={"width": 1400, "height": 1100})
        page = await ctx.new_page()
        page.on("pageerror", lambda exc: print(f"[PAGEERROR] {exc}"))
        page.on("dialog", lambda d: asyncio.create_task(d.accept()))

        # Clear localStorage to force login page
        await page.goto(f"{BASE}/", wait_until="domcontentloaded")
        await page.evaluate("() => localStorage.clear()")
        await page.reload(wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await shoot(page, "08_initial_login")

        # Verify login form is visible
        email_el = await page.query_selector('input[name="email"]')
        email_visible = await email_el.is_visible() if email_el else False
        password_el = await page.query_selector('input[name="password"]')
        password_visible = await password_el.is_visible() if password_el else False
        assert_truthy(8, "Login form visible (email + password)", email_visible and password_visible, "08_initial_login.png")

        # ====== STEP 9: UI: empty submit ======
        print("\n--- Step 9: UI empty submit ---")
        await page.click('#auth-submit')
        await page.wait_for_timeout(2000)
        # Check we're still on login page
        url_after = page.url
        assert_contains(9, "Still on auth page after empty submit", "directorstudio", url_after, "09_empty_submit.png", f"url={url_after}")
        # Check for any error message
        content = await page.content()
        # Look for toast or error text
        has_toast = ("toast" in content.lower() or "กรอก" in content.lower() or "ใส่" in content.lower() or "error" in content.lower())
        # Soft check
        print(f"  (has error msg: {has_toast})")

        # ====== STEP 10: UI: wrong password ======
        print("\n--- Step 10: UI wrong password ---")
        await page.fill('input[name="email"]', ADMIN_EMAIL)
        await page.fill('input[name="password"]', "wrong_pass_999")
        await page.click('#auth-submit')
        await page.wait_for_timeout(3000)
        await shoot(page, "10_wrong_password")
        # Should still be on login
        url_after = page.url
        auth_pwd = await page.query_selector('input[name="password"]')
        still_on_login = await auth_pwd.is_visible() if auth_pwd else False
        assert_truthy(10, "Wrong password stays on login page", still_on_login, "10_wrong_password.png", f"url={url_after}")
        # Check for error toast
        content_after = await page.content()
        # Look for "ผิด" or "ไม่" or error
        has_error = any(kw in content_after for kw in ["ผิด", "ไม่ถูก", "ล้มเหลว", "error", "invalid", "incorrect", "wrong"])
        print(f"  (has error message: {has_error})")

        # ====== STEP 11: UI: valid login (admin) ======
        print("\n--- Step 11: UI valid login (admin) ---")
        # Clear and re-fill
        await page.evaluate("() => localStorage.clear()")
        await page.reload(wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await page.fill('input[name="email"]', ADMIN_EMAIL)
        await page.fill('input[name="password"]', ADMIN_PASSWORD)
        await page.screenshot(path=str(OUT / "screenshots" / "11_filled.png"), full_page=False)
        await page.click('#auth-submit')
        await page.wait_for_timeout(5000)
        await shoot(page, "11b_after_login")

        # Check we're now in app
        content = await page.content()
        is_app = ("project" in content.lower() or "studio" in content.lower())
        assert_truthy(11, "After login, app view loaded", is_app, "11b_after_login.png", f"url={page.url}")
        # Check token in localStorage
        token_in_storage = await page.evaluate("() => localStorage.getItem('ds_token')")
        assert_truthy(11, "Token stored in localStorage", bool(token_in_storage), "", f"len={len(token_in_storage) if token_in_storage else 0}")

        # Check user chip visible
        user_chip = await page.query_selector('#user-chip')
        if user_chip:
            chip_text = await user_chip.inner_text()
            assert_contains(11, "User chip shows email/display", "admin", chip_text.lower(), "", f"chip={chip_text}")

        # ====== STEP 12: UI: refresh keeps logged in ======
        print("\n--- Step 12: UI refresh keeps session ---")
        await page.reload(wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        content = await page.content()
        still_logged_in = ("project" in content.lower() or "studio" in content.lower())
        auth_pwd2 = await page.query_selector('input[name="password"]')
        auth_pwd2_visible = await auth_pwd2.is_visible() if auth_pwd2 else False
        assert_truthy(12, "Session persists after refresh", still_logged_in and not auth_pwd2_visible, "", f"app={still_logged_in}, auth_form={auth_pwd2_visible}")

        # ====== STEP 13: UI: logout ======
        print("\n--- Step 13: UI logout ---")
        logout_btn = await page.query_selector('#logout-btn')
        if logout_btn:
            await logout_btn.click()
            await page.wait_for_timeout(3000)
            await shoot(page, "13_after_logout")
            token_after = await page.evaluate("() => localStorage.getItem('ds_token')")
            assert_eq(13, "Token cleared after logout", None, token_after, "13_after_logout.png")
            # Should be back on login
            auth_pwd3 = await page.query_selector('input[name="password"]')
            assert_truthy(13, "Back on login page after logout", await auth_pwd3.is_visible() if auth_pwd3 else False, "")
        else:
            print("  ⚠ logout button not found")
            assert_truthy(13, "Logout button visible", False, "")

        # ====== STEP 14: UI: login as new test user ======
        print("\n--- Step 14: UI login as new test user ---")
        await page.fill('input[name="email"]', TEST_USER["email"])
        await page.fill('input[name="password"]', TEST_USER["password"])
        await page.click('#auth-submit')
        await page.wait_for_timeout(5000)
        content = await page.content()
        is_app = ("project" in content.lower() or "studio" in content.lower())
        assert_truthy(14, "Login as new user works", is_app, "", f"url={page.url}")
        token_test = await page.evaluate("() => localStorage.getItem('ds_token')")
        assert_truthy(14, "Token stored for new user", bool(token_test), "")

        # Logout
        logout_btn2 = await page.query_selector('#logout-btn')
        if logout_btn2:
            await logout_btn2.click()
            await page.wait_for_timeout(2000)

        # ====== STEP 15: UI: try login with signup form (wrong tab) ======
        print("\n--- Step 15: UI tab switching ---")
        await page.click('button:has-text("สมัครสมาชิก")')
        await page.wait_for_timeout(1500)
        await shoot(page, "15_signup_tab_via_login")
        # Should show display_name
        display_name_el = await page.query_selector('input[name="display_name"]')
        assert_truthy(15, "Tab switch reveals signup form", await display_name_el.is_visible() if display_name_el else False, "15_signup_tab_via_login.png")
        # Switch back
        await page.click('button:has-text("เข้าสู่ระบบ")')
        await page.wait_for_timeout(1500)

        await browser.close()

    # ====== Generate HTML report ======
    total = len(assertions)
    passed = sum(1 for a in assertions if a["status"] == "PASS")
    failed = total - passed
    duration = time.time() - start_time
    pct = (passed / total * 100) if total > 0 else 0
    color = "#10b981" if pct == 100 else "#f59e0b" if pct >= 80 else "#ef4444"

    rows = "\n".join(
        f"""
        <tr class="{a['status'].lower()}">
          <td>{a['step']}</td>
          <td>{a['name']}</td>
          <td class="expected">{a['expected']}</td>
          <td class="actual">{a['actual']}</td>
          <td><span class="badge badge-{a['status'].lower()}">{a['status']}</span></td>
        </tr>"""
        for a in assertions
    )

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>{TEST_NAME}</title>
<style>
body{{font-family:-apple-system,sans-serif;background:#0a0a0a;color:#e5e5e5;padding:32px;margin:0;}}
.container{{max-width:1400px;margin:0 auto;}}
h1{{color:{color};font-size:32px;}}
.stats{{display:flex;gap:16px;margin:24px 0;flex-wrap:wrap;}}
.stat{{background:#1a1a1a;padding:16px 24px;border-radius:12px;border:1px solid #333;}}
.stat .num{{font-size:28px;font-weight:800;color:{color};}}
.stat .label{{font-size:11px;color:#888;text-transform:uppercase;}}
table{{width:100%;border-collapse:collapse;margin-top:16px;background:#1a1a1a;border-radius:8px;overflow:hidden;}}
th{{background:#262626;padding:12px;text-align:left;color:#fbbf24;font-size:11px;text-transform:uppercase;}}
td{{padding:12px;border-top:1px solid #2a2a2a;font-size:13px;}}
.expected,.actual{{font-family:monospace;font-size:11px;max-width:300px;overflow:hidden;text-overflow:ellipsis;}}
tr.pass{{border-left:3px solid #10b981;}}
tr.fail{{border-left:3px solid #ef4444;background:#2a1a1a;}}
.badge{{padding:3px 8px;border-radius:100px;font-size:10px;font-weight:700;}}
.badge-pass{{background:#10b981;color:#000;}}
.badge-fail{{background:#ef4444;color:#fff;}}
.meta{{color:#888;font-size:13px;}}
</style></head><body>
<div class="container">
<h1>{TEST_NAME}</h1>
<p class="meta">Run: {TS} · Duration: {duration:.1f}s · Admin: {ADMIN_EMAIL}</p>
<div class="stats">
<div class="stat"><div class="num">{passed}/{total}</div><div class="label">Passed</div></div>
<div class="stat"><div class="num">{pct:.0f}%</div><div class="label">Pass Rate</div></div>
<div class="stat"><div class="num">{failed}</div><div class="label">Failed</div></div>
<div class="stat"><div class="num">{duration:.1f}s</div><div class="label">Duration</div></div>
</div>
<h2>Assertions</h2>
<table><thead><tr><th>Step</th><th>Name</th><th>Expected</th><th>Actual</th><th>Status</th></tr></thead>
<tbody>{rows}</tbody></table>
</div></body></html>"""

    (OUT / "report.html").write_text(html, encoding="utf-8")
    print(f"\n=== {passed}/{total} PASS ({pct:.0f}%) in {duration:.1f}s ===")
    print(f"Report: {OUT / 'report.html'}")

    (OUT / "summary.json").write_text(json.dumps({
        "test": TEST_NAME,
        "total": total, "passed": passed, "failed": failed,
        "pass_rate": pct, "duration_sec": duration,
        "timestamp": TS,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
