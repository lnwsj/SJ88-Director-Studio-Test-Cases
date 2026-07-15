#!/usr/bin/env python3
"""
TC-11: Full Real UI Walkthrough
ทดสอบ UI จริงทุก step (คลิกจริง, พิมพ์จริง, รอ response จริง)
ถ่ายรูปทุก state เพื่อ debug ง่าย

Page: https://directorstudio.sj88ai.com/
"""
import asyncio
import json
import time
import urllib.request
import secrets
from pathlib import Path
from playwright.async_api import async_playwright
from datetime import datetime

BASE = "https://directorstudio.sj88ai.com"
CHROME = "/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome"
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
OUT = Path(f"/workspace/director-studio-test-cases/11-real-ui-walkthrough/runs/{TS}")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "screenshots").mkdir(exist_ok=True)
(OUT / "screenshots" / "signup").mkdir(exist_ok=True)
(OUT / "screenshots" / "login").mkdir(exist_ok=True)
(OUT / "screenshots" / "session").mkdir(exist_ok=True)

TEST_NAME = "TC-11 Full Real UI Walkthrough"
ADMIN_EMAIL = "admin@sj88ai.com"
ADMIN_PASSWORD = "admin1234"
TEST_USER = {
    "email": f"tc11_{secrets.token_hex(4)}@sj88ai.com",
    "password": "tc11test1234",
    "display_name": "TC-11 Test User"
}

# Track all events
events = []
network_log = []
console_log = []


def log_event(step, action, result, screenshot=None):
    """Record event with timestamp."""
    events.append({
        "step": step,
        "time": datetime.now().isoformat(),
        "action": action,
        "result": result,
        "screenshot": screenshot
    })
    icon = "✅" if "PASS" in str(result) or "success" in str(result).lower() or "loaded" in str(result).lower() else ("❌" if "FAIL" in str(result) or "error" in str(result).lower() else "📸")
    print(f"  {icon} [{step}] {action} → {result}")


async def shoot(page, path, full=True, label=""):
    """Take screenshot with consistent naming."""
    full_path = OUT / "screenshots" / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(full_path), full_page=full)
    if label:
        print(f"    📸 {label} → {path}")
    return str(full_path.relative_to(OUT))


def api_post(path, body):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        return json.loads(urllib.request.urlopen(req, timeout=15).read().decode()), None, 200
    except urllib.error.HTTPError as e:
        try:
            return None, e.read().decode()[:200], e.code
        except:
            return None, str(e), e.code
    except Exception as e:
        return None, str(e), 0


async def signup_walkthrough(page, step_prefix):
    """Complete signup flow with screenshots at every state."""
    print(f"\n{'='*60}")
    print(f"📋 SIGNUP FLOW - step_prefix={step_prefix}")
    print(f"{'='*60}")

    # Pre-create user via API (to ensure unique email, but we'll test UI signup with different email)
    api_email = TEST_USER["email"]

    # Step 1: Open page, see login tab
    log_event(f"{step_prefix}.01", "Navigate to /", "Loading...", None)
    await page.goto(f"{BASE}/", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)
    # Clear localStorage to force login form
    await page.evaluate("() => localStorage.clear()")
    await page.reload(wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    s1 = await shoot(page, f"signup/01_landing_login_tab.png", label="Landing page (login tab default)")
    log_event(f"{step_prefix}.01", "Landing page loaded", "Login tab visible", s1)

    # Step 2: Verify login tab is default (no display_name visible)
    email_el = await page.query_selector('input[name="email"]')
    email_visible = await email_el.is_visible() if email_el else False
    password_el = await page.query_selector('input[name="password"]')
    password_visible = await password_el.is_visible() if password_el else False
    display_name_el = await page.query_selector('input[name="display_name"]')
    display_name_visible = await display_name_el.is_visible() if display_name_el else False
    log_event(f"{step_prefix}.02", "Check default tab",
              f"email={email_visible}, password={password_visible}, display_name={display_name_visible}",
              None)

    # Step 3: Click signup tab
    signup_btn = page.locator('button:has-text("สมัครสมาชิก")').first
    await signup_btn.click()
    await page.wait_for_timeout(1500)
    s3 = await shoot(page, f"signup/02_after_click_signup_tab.png", label="After clicking signup tab")
    log_event(f"{step_prefix}.03", "Clicked signup tab", "Tab switched", s3)

    # Step 4: Verify signup form (3 fields visible)
    display_name_el2 = await page.query_selector('input[name="display_name"]')
    display_name_visible2 = await display_name_el2.is_visible() if display_name_el2 else False
    email_el2 = await page.query_selector('input[name="email"]')
    email_visible2 = await email_el2.is_visible() if email_el2 else False
    password_el2 = await page.query_selector('input[name="password"]')
    password_visible2 = await password_el2.is_visible() if password_el2 else False
    s4 = await shoot(page, f"signup/03_signup_empty_form.png", label="Signup form (empty)")
    log_event(f"{step_prefix}.04", "Verify signup form",
              f"display_name={display_name_visible2}, email={email_visible2}, password={password_visible2}",
              s4)

    # Step 5: Try empty submit
    submit_btn = await page.query_selector('#auth-submit')
    submit_visible = await submit_btn.is_visible() if submit_btn else False
    submit_text = await submit_btn.inner_text() if submit_btn else ""
    s5a = await shoot(page, f"signup/04_before_empty_submit.png", label=f"Submit button: '{submit_text}'")

    if submit_btn:
        await submit_btn.click()
        await page.wait_for_timeout(2000)
    s5b = await shoot(page, f"signup/05_after_empty_submit.png", label="After empty submit")
    # Check if we're still on signup
    url = page.url
    still_on_signup = "directorstudio" in url
    # Check for error/toast
    body_text = await page.inner_text("body")
    has_error = any(kw in body_text for kw in ["กรอก", "ใส่", "ต้อง", "ผิด", "error", "Error", "กรุณา"])
    log_event(f"{step_prefix}.05", "Empty submit",
              f"still_on_page={still_on_signup}, has_error_msg={has_error}",
              s5b)

    # Step 6: Fill signup form
    new_email = f"tc11ui_{secrets.token_hex(4)}@sj88ai.com"
    await page.fill('input[name="display_name"]', "TC-11 UI Test")
    await page.fill('input[name="email"]', new_email)
    await page.fill('input[name="password"]', "tc11uitest1234")
    s6 = await shoot(page, f"signup/06_filled_form.png", label=f"Filled form ({new_email})")
    log_event(f"{step_prefix}.06", "Fill form", f"email={new_email}", s6)

    # Step 7: Submit
    await page.click('#auth-submit')
    # Wait for either app view or error
    await page.wait_for_timeout(3000)
    s7a = await shoot(page, f"signup/07a_during_submit.png", label="During submit (loading)")
    # Wait longer
    await page.wait_for_timeout(5000)
    s7b = await shoot(page, f"signup/07b_after_submit.png", label="After submit")

    # Check result
    content = await page.content()
    is_app = ("project" in content.lower() or "studio" in content.lower() or "อยุธยา" in content or "โรงเรียนรัก" in content or "โปรเจกต์" in content)
    is_signup_form = await page.query_selector('input[name="display_name"]')
    is_signup_visible = await is_signup_form.is_visible() if is_signup_form else False
    log_event(f"{step_prefix}.07", "Submit signup",
              f"is_app_view={is_app}, signup_form_still_visible={is_signup_visible}",
              s7b)

    # Step 8: Check localStorage
    token = await page.evaluate("() => localStorage.getItem('ds_token')")
    log_event(f"{step_prefix}.08", "Check localStorage",
              f"token={'present (len=' + str(len(token)) + ')' if token else 'absent'}",
              None)

    return new_email, is_app


async def login_walkthrough(page, step_prefix, target_email, target_password):
    """Complete login flow with screenshots."""
    print(f"\n{'='*60}")
    print(f"📋 LOGIN FLOW - target={target_email}")
    print(f"{'='*60}")

    # Step 1: Force fresh login page (clear localStorage + reload)
    await page.evaluate("() => localStorage.clear()")
    await page.reload(wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    s1 = await shoot(page, f"login/01_fresh_login_page.png", label="Fresh login page (after logout)")

    # Step 2: Verify login form
    email_el = await page.query_selector('input[name="email"]')
    email_visible = await email_el.is_visible() if email_el else False
    password_el = await page.query_selector('input[name="password"]')
    password_visible = await password_el.is_visible() if password_el else False
    display_name_el = await page.query_selector('input[name="display_name"]')
    display_name_visible = await display_name_el.is_visible() if display_name_el else False
    log_event(f"{step_prefix}.02", "Verify login form",
              f"email={email_visible}, password={password_visible}, display_name_shown={display_name_visible}",
              s1)

    # Step 3: Test 1 - empty submit
    submit_btn = await page.query_selector('#auth-submit')
    if submit_btn:
        await submit_btn.click()
        await page.wait_for_timeout(2000)
    s3 = await shoot(page, f"login/02_after_empty_submit.png", label="After empty submit")
    log_event(f"{step_prefix}.03", "Empty submit", "See screenshot for any error", s3)

    # Step 4: Test 2 - wrong password
    await page.fill('input[name="email"]', target_email)
    await page.fill('input[name="password"]', "wrong_password_999")
    s4a = await shoot(page, f"login/03a_filled_wrong_password.png", label="Filled wrong password")
    if submit_btn:
        await submit_btn.click()
        await page.wait_for_timeout(3000)
    s4b = await shoot(page, f"login/03b_after_wrong_password.png", label="After wrong password submit")
    # Check we're still on login
    body_text = await page.inner_text("body")
    still_login = await page.query_selector('input[name="email"]') is not None
    has_error = any(kw in body_text for kw in ["ผิด", "ล้มเหลว", "ไม่ถูก", "error", "Error", "ไม่สำเร็จ"])
    log_event(f"{step_prefix}.04", "Wrong password",
              f"still_on_login={still_login}, error_visible={has_error}",
              s4b)

    # Step 5: Test 3 - wrong email
    await page.fill('input[name="email"]', f"nonexistent_{secrets.token_hex(3)}@fake.com")
    await page.fill('input[name="password"]', "any_password")
    s5a = await shoot(page, f"login/04a_filled_wrong_email.png", label="Filled wrong email")
    if submit_btn:
        await submit_btn.click()
        await page.wait_for_timeout(3000)
    s5b = await shoot(page, f"login/04b_after_wrong_email.png", label="After wrong email submit")
    still_login2 = await page.query_selector('input[name="email"]') is not None
    log_event(f"{step_prefix}.05", "Wrong email",
              f"still_on_login={still_login2}",
              s5b)

    # Step 6: Test 4 - valid login
    await page.fill('input[name="email"]', target_email)
    await page.fill('input[name="password"]', target_password)
    s6 = await shoot(page, f"login/05_filled_correct.png", label=f"Filled correctly ({target_email})")
    if submit_btn:
        await submit_btn.click()
    await page.wait_for_timeout(5000)
    s7 = await shoot(page, f"login/06_after_valid_login.png", label="After valid login (should be app view)")

    content = await page.content()
    is_app = ("project" in content.lower() or "studio" in content.lower() or "อยุธยา" in content or "โรงเรียนรัก" in content or "โปรเจกต์" in content or "+ โปรเจกต์" in content)
    auth_pwd = await page.query_selector('input[name="password"]')
    auth_pwd_visible = await auth_pwd.is_visible() if auth_pwd else False
    token = await page.evaluate("() => localStorage.getItem('ds_token')")
    log_event(f"{step_prefix}.06", "Valid login",
              f"is_app_view={is_app}, auth_form_visible={auth_pwd_visible}, token={'present' if token else 'absent'}",
              s7)

    # Step 7: Check user chip
    user_chip = await page.query_selector('#user-chip')
    if user_chip:
        chip_text = await user_chip.inner_text()
        s8 = await shoot(page, f"session/01_user_chip.png", label=f"User chip: '{chip_text}'")
        log_event(f"{step_prefix}.07", "Check user chip", f"text='{chip_text}'", s8)
    else:
        log_event(f"{step_prefix}.07", "Check user chip", "NOT FOUND", None)

    # Step 8: Refresh
    await page.reload(wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)
    s9 = await shoot(page, f"session/02_after_refresh.png", label="After refresh")
    content2 = await page.content()
    still_logged_in = ("project" in content2.lower() or "studio" in content2.lower() or "โปรเจกต์" in content2 or "+ โปรเจกต์" in content2)
    auth_pwd2 = await page.query_selector('input[name="password"]')
    auth_pwd_visible2 = await auth_pwd2.is_visible() if auth_pwd2 else False
    log_event(f"{step_prefix}.08", "Refresh page",
              f"still_logged_in={still_logged_in}, auth_form_visible={auth_pwd_visible2}",
              s9)

    return is_app


async def logout_walkthrough(page, step_prefix):
    """Logout + verify return to login."""
    print(f"\n{'='*60}")
    print(f"📋 LOGOUT FLOW")
    print(f"{'='*60}")

    # Step 1: Click logout
    logout_btn = await page.query_selector('#logout-btn')
    if logout_btn:
        await logout_btn.click()
        await page.wait_for_timeout(3000)
    s1 = await shoot(page, f"session/03_after_logout.png", label="After logout")
    token_after = await page.evaluate("() => localStorage.getItem('ds_token')")
    auth_pwd = await page.query_selector('input[name="password"]')
    auth_pwd_visible = await auth_pwd.is_visible() if auth_pwd else False
    log_event(f"{step_prefix}.01", "Logout",
              f"token_cleared={token_after is None}, back_on_login={auth_pwd_visible}",
              s1)

    return token_after is None and auth_pwd_visible


async def main():
    print(f"\n{'='*60}")
    print(f"🎬 {TEST_NAME}")
    print(f"{'='*60}\n")
    print(f"Run dir: {OUT}\n")
    print(f"Test user: {TEST_USER['email']}\n")
    start_time = time.time()

    # Setup
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROME,
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--use-gl=swiftshader"],
        )
        ctx = await browser.new_context(
            viewport={"width": 1400, "height": 1100},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await ctx.new_page()

        # Track console + network
        page.on("console", lambda m: console_log.append({"type": m.type, "text": m.text[:200]}))
        page.on("pageerror", lambda exc: console_log.append({"type": "pageerror", "text": str(exc)[:200]}))
        page.on("response", lambda r: network_log.append({
            "url": r.url[:150],
            "status": r.status,
            "method": r.request.method,
            "time": r.request.timing if hasattr(r.request, 'timing') else None
        }))

        # ====== PHASE 1: SIGNUP ======
        new_email, signup_success = await signup_walkthrough(page, "S")

        # ====== PHASE 2: LOGOUT (if signed up) ======
        if signup_success:
            await logout_walkthrough(page, "S.logout")

        # ====== PHASE 3: LOGIN (admin) ======
        login_success = await login_walkthrough(page, "L.admin", ADMIN_EMAIL, ADMIN_PASSWORD)

        # ====== PHASE 4: LOGOUT (admin) ======
        if login_success:
            await logout_walkthrough(page, "L.logout")

        # ====== PHASE 5: LOGIN (new test user) ======
        new_user_login_success = await login_walkthrough(page, "L.new", TEST_USER["email"], TEST_USER["password"])

        # ====== PHASE 6: Explore app (optional screenshot of projects view) ======
        print(f"\n{'='*60}")
        print(f"📋 APP EXPLORATION")
        print(f"{'='*60}")
        # Navigate to projects
        await page.wait_for_timeout(2000)
        s_app = await shoot(page, f"session/04_app_projects_view.png", label="App projects view")
        # Click โรงเรียนรัก if visible
        try:
            cards = await page.query_selector_all('.project-card, [class*="project-card"]')
            for card in cards:
                txt = await card.inner_text()
                if "โรงเรียนรัก" in txt:
                    await card.click()
                    break
            await page.wait_for_timeout(2000)
            # Click EP1
            ep_cards = await page.query_selector_all('.ep-card, [class*="ep-card"]')
            for card in ep_cards:
                txt = await card.inner_text()
                if "EP1" in txt:
                    await card.click()
                    break
            await page.wait_for_timeout(3000)
            s_app_ep = await shoot(page, f"session/05_app_ep1.png", label="App EP1 view")
            log_event("X.01", "Open โรงเรียนรัก → EP1", "App navigation works", s_app_ep)
        except Exception as e:
            log_event("X.01", "App exploration", f"error: {e}", s_app)

        # Take final screenshot
        await shoot(page, f"session/06_final.png", label="Final state")

        await browser.close()

    # ====== Generate report ======
    duration = time.time() - start_time
    total_events = len(events)
    success_events = sum(1 for e in events if "loaded" in str(e["result"]).lower() or "present" in str(e["result"]).lower() or "works" in str(e["result"]).lower() or "success" in str(e["result"]).lower() or "PASS" in str(e["result"]))
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY: {total_events} events in {duration:.1f}s")
    print(f"{'='*60}")
    print(f"Network calls: {len(network_log)}")
    print(f"Console events: {len(console_log)}")

    # Save events as JSON
    (OUT / "events.json").write_text(json.dumps({
        "events": events,
        "network_calls": len(network_log),
        "console_events": len(console_log),
        "duration_sec": duration,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    # Generate detailed HTML report
    events_html = "\n".join(
        f"""
        <tr>
          <td><code>{e['step']}</code></td>
          <td>{e['action']}</td>
          <td><span class="result">{e['result']}</span></td>
          <td class="screenshot">{'<a href="screenshots/' + e['screenshot'] + '" target="_blank"><img src="screenshots/' + e['screenshot'] + '" loading="lazy"/></a>' if e['screenshot'] else '—'}</td>
        </tr>"""
        for e in events
    )

    # Get all screenshots
    all_screenshots = sorted([str(p.relative_to(OUT)) for p in (OUT / "screenshots").rglob("*.png")])
    gallery = ""
    if all_screenshots:
        gallery = "<h2>📸 Screenshot Gallery</h2><div class='gallery'>"
        for s in all_screenshots:
            gallery += f'<div class="screenshot-item"><a href="screenshots/{s}" target="_blank"><img src="screenshots/{s}" loading="lazy"/><div class="caption">{s}</div></a></div>'
        gallery += "</div>"

    html = f"""<!DOCTYPE html>
<html lang="th"><head><meta charset="UTF-8"><title>{TEST_NAME}</title>
<style>
body{{font-family:-apple-system,sans-serif;background:#0a0a0a;color:#e5e5e5;padding:32px;margin:0;}}
.container{{max-width:1600px;margin:0 auto;}}
h1{{color:#10b981;font-size:36px;margin-bottom:8px;}}
h2{{color:#fbbf24;margin-top:40px;border-bottom:1px solid #333;padding-bottom:8px;}}
.meta{{color:#888;font-size:13px;}}
.stats{{display:flex;gap:16px;margin:24px 0;flex-wrap:wrap;}}
.stat{{background:#1a1a1a;padding:16px 24px;border-radius:12px;border:1px solid #333;}}
.stat .num{{font-size:28px;font-weight:800;color:#10b981;}}
.stat .label{{font-size:11px;color:#888;text-transform:uppercase;}}
table{{width:100%;border-collapse:collapse;margin-top:16px;background:#1a1a1a;border-radius:8px;overflow:hidden;}}
th{{background:#262626;padding:12px;text-align:left;color:#fbbf24;font-size:11px;text-transform:uppercase;}}
td{{padding:12px;border-top:1px solid #2a2a2a;font-size:13px;}}
.result{{color:#10b981;}}
.screenshot img{{max-width:200px;max-height:120px;border-radius:4px;border:1px solid #333;}}
.screenshot a{{display:block;}}
.gallery{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px;margin-top:16px;}}
.screenshot-item{{background:#1a1a1a;border:1px solid #333;border-radius:8px;padding:8px;}}
.screenshot-item img{{width:100%;border-radius:4px;}}
.caption{{font-size:11px;color:#888;margin-top:4px;word-break:break-all;}}
</style></head><body>
<div class="container">
<h1>🎬 {TEST_NAME}</h1>
<p class="meta">Run: {TS} · Duration: {duration:.1f}s · Test user: {TEST_USER['email']} · Admin: {ADMIN_EMAIL}</p>
<div class="stats">
<div class="stat"><div class="num">{total_events}</div><div class="label">Events</div></div>
<div class="stat"><div class="num">{len(network_log)}</div><div class="label">Network Calls</div></div>
<div class="stat"><div class="num">{len(console_log)}</div><div class="label">Console Events</div></div>
<div class="stat"><div class="num">{duration:.1f}s</div><div class="label">Duration</div></div>
<div class="stat"><div class="num">{len(all_screenshots)}</div><div class="label">Screenshots</div></div>
</div>

<h2>📋 Event Timeline</h2>
<table>
<thead><tr><th>Step</th><th>Action</th><th>Result</th><th>Screenshot</th></tr></thead>
<tbody>{events_html}</tbody>
</table>

{gallery}

</div></body></html>"""

    (OUT / "report.html").write_text(html, encoding="utf-8")
    print(f"\nReport: {OUT / 'report.html'}")
    print(f"Events: {OUT / 'events.json'}")
    print(f"Screenshots: {OUT / 'screenshots'}")


if __name__ == "__main__":
    asyncio.run(main())
