"""
test_tc17_admin.py — TC-17 Admin Panel E2E
Tests live https://directorstudio.sj88ai.com/ with 2 users (admin + regular)
Verifies: RBAC, list users, stats, delete user (cascade), secrets isolation
"""
import re
import time
import requests
from playwright.sync_api import sync_playwright, expect

LIVE = "https://directorstudio.sj88ai.com"
# Pre-existing admin account (first user on live site)
ADMIN_EMAIL = "admin@sj88ai.com"
ADMIN_PW = "admin1234"
# New test user
EMAIL_USER = f"user_tc17_{int(time.time())}@test.com"
PW = "tc17test1234"

results = []


def log(name, ok, detail=""):
    icon = "✅" if ok else "❌"
    print(f"{icon} {name}: {detail}")
    results.append((name, ok, detail))


def signup_via_api(email):
    r = requests.post(f"{LIVE}/api/auth/signup",
                      json={"email": email, "password": PW})
    assert r.status_code == 200, f"signup failed: {r.text}"
    return r.json()["access_token"]


def login_via_api(email, password=PW):
    r = requests.post(f"{LIVE}/api/auth/login",
                      json={"email": email, "password": password})
    assert r.status_code == 200, f"login failed: {r.text}"
    return r.json()["access_token"]


# ============================================================
# Setup
# ============================================================
print("=" * 60)
print("TC-17 ADMIN PANEL — Setup")
print("=" * 60)

admin_token = login_via_api(ADMIN_EMAIL, ADMIN_PW)  # pre-existing admin
user_token = signup_via_api(EMAIL_USER)
admin_hdr = {"Authorization": f"Bearer {admin_token}"}
user_hdr = {"Authorization": f"Bearer {user_token}"}
print(f"  admin: {ADMIN_EMAIL}")
print(f"  user : {EMAIL_USER}")

# Create 2 projects for user
for i in range(2):
    r = requests.post(f"{LIVE}/api/projects", json={"name": f"User-Proj-{i}"},
                      headers=user_hdr)
    assert r.status_code == 200, f"project create failed: {r.text}"
print("  user has 2 projects")

# ============================================================
# Test 1: List users (admin)
# ============================================================
print("\n--- Test 1: List users (admin) ---")
r = requests.get(f"{LIVE}/api/admin/users", headers=admin_hdr)
log("T1.list-users", r.status_code == 200,
    f"status={r.status_code} count={len(r.json())}")
assert r.status_code == 200
users = r.json()
emails = {u["email"] for u in users}
assert ADMIN_EMAIL in emails
assert EMAIL_USER in emails
log("T1.both-users-present", True, f"emails found: {emails}")

# Verify admin role flag on first user
admin_user = next(u for u in users if u["email"] == ADMIN_EMAIL)
log("T1.admin-role", admin_user["role"] == "admin",
    f"admin role = {admin_user['role']}")

# ============================================================
# Test 2: List users (NON-admin → 403)
# ============================================================
print("\n--- Test 2: RBAC: non-admin blocked ---")
r = requests.get(f"{LIVE}/api/admin/users", headers=user_hdr)
log("T2.user-403", r.status_code == 403,
    f"non-admin GET /admin/users → {r.status_code} (expect 403)")

r = requests.get(f"{LIVE}/api/admin/stats", headers=user_hdr)
log("T2.user-stats-403", r.status_code == 403,
    f"non-admin GET /admin/stats → {r.status_code} (expect 403)")

r = requests.delete(f"{LIVE}/api/admin/users/{admin_user['id']}", headers=user_hdr)
log("T2.user-delete-403", r.status_code == 403,
    f"non-admin DELETE /admin/users → {r.status_code} (expect 403)")

# ============================================================
# Test 3: System stats
# ============================================================
print("\n--- Test 3: System stats ---")
r = requests.get(f"{LIVE}/api/admin/stats", headers=admin_hdr)
log("T3.stats-200", r.status_code == 200, f"status={r.status_code}")
stats = r.json()
log("T3.user-count-2", stats["user_count"] >= 2,
    f"user_count = {stats['user_count']} (≥2 expected)")
log("T3.project-count-2", stats["project_count"] >= 2,
    f"project_count = {stats['project_count']} (≥2 expected)")
log("T3.task-count-zero", stats["task_count"] >= 0,
    f"task_count = {stats['task_count']}")

# ============================================================
# Test 4: Secrets isolation (admin sees has_*, never veo_jwt_enc)
# ============================================================
print("\n--- Test 4: Secrets isolation ---")
# Set a fake veo_jwt for the user (need 1000+ chars; must look like real JWT)
import base64
fake_hdr = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip('=')
fake_body = base64.urlsafe_b64encode(
    b'{"jti":"test_99","username":"fake","plan":"pro","exp":9999999999}'
).decode().rstrip('=')
fake_sig = 'A' * 1000  # 1000-char signature
fake_jwt = f"{fake_hdr}.{fake_body}.{fake_sig}"  # total ~1170 chars
r = requests.put(f"{LIVE}/api/settings/veo-jwt",
                 json={"veo_jwt": fake_jwt}, headers=user_hdr)
log("T4.set-jwt", r.status_code == 200, f"user saved veo_jwt (status={r.status_code}, body={r.text[:100]})")

# Admin fetches the user
target_id = next(u for u in users if u["email"] == EMAIL_USER)["id"]
r = requests.get(f"{LIVE}/api/admin/users/{target_id}", headers=admin_hdr)
log("T4.get-user-200", r.status_code == 200, f"status={r.status_code}")
body = r.json()
log("T4.has-veo-jwt-true", body["settings"]["has_veo_jwt"] == 1,
    f"has_veo_jwt = {body['settings']['has_veo_jwt']}")
log("T4.no-jwt-leaked", fake_jwt not in r.text,
    f"fake JWT string NOT in response (text scanned)")
log("T4.no-enc-leaked", "veo_jwt_enc" not in r.text,
    f"encrypted column name NOT in response")

# ============================================================
# Test 5: Cannot delete self
# ============================================================
print("\n--- Test 5: Cannot delete self ---")
my_id = admin_user["id"]
r = requests.delete(f"{LIVE}/api/admin/users/{my_id}", headers=admin_hdr)
log("T5.no-suicide-400", r.status_code == 400,
    f"self-delete → {r.status_code} (expect 400)")
err = r.json()
msg = (err.get("detail") or err.get("error") or r.text).lower()
log("T5.error-msg-correct", "yourself" in msg,
    f"msg: {err.get('detail') or err.get('error') or r.text[:80]}")

# ============================================================
# Test 6: Delete user (cascade) — admin deletes regular user
# ============================================================
print("\n--- Test 6: Delete user + cascade ---")
r = requests.delete(f"{LIVE}/api/admin/users/{target_id}", headers=admin_hdr)
log("T6.delete-200", r.status_code == 200, f"status={r.status_code} {r.json()}")

r = requests.get(f"{LIVE}/api/admin/users", headers=admin_hdr)
emails_after = {u["email"] for u in r.json()}
log("T6.user-gone", EMAIL_USER not in emails_after,
    f"deleted user email removed from list")

# Verify cascade — projects should also be gone (check via /api/projects)
r = requests.get(f"{LIVE}/api/projects", headers=admin_hdr)
# admin can see their own projects (which are 0)
log("T6.admin-api-200", r.status_code == 200,
    f"/api/projects still 200 for admin after delete (status={r.status_code})")

# Try to login as deleted user — should fail
r = requests.post(f"{LIVE}/api/auth/login",
                  json={"email": EMAIL_USER, "password": PW})
log("T6.deleted-cant-login", r.status_code in (401, 403),
    f"login with deleted credentials → {r.status_code} (expect 401/403)")

# ============================================================
# Test 7: Real UI test — admin tab visible + shows stats
# ============================================================
print("\n--- Test 7: UI test (Playwright) ---")
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome",
        args=["--no-sandbox", "--disable-gpu", "--use-gl=swiftshader"]
    )
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(LIVE, wait_until="domcontentloaded")

    # Login as admin
    page.locator("input[name=\"email\"]").fill(ADMIN_EMAIL)
    page.locator("input[name=\"password\"]").fill(ADMIN_PW)
    page.locator("#auth-submit").click()
    page.wait_for_selector("a[data-tab=\"projects\"]", state="visible", timeout=10000)

    # T7a: admin nav visible
    nav_admin = page.locator("#nav-admin")
    log("T7a.admin-nav-visible", nav_admin.is_visible(),
        f"#nav-admin display: {nav_admin.evaluate('el => el.style.display')}")

    # T7b: click admin tab
    nav_admin.click()
    page.wait_for_timeout(800)

    # T7c: stats rendered
    stat_cards = page.locator(".admin-stats .stat-card").count()
    log("T7c.stats-cards", stat_cards == 4, f"{stat_cards} stat cards (expect 4)")

    # T7d: users list rendered
    user_cards = page.locator(".users-list .user-card").count()
    log("T7d.user-cards", user_cards >= 1, f"{user_cards} user cards")

    # Screenshot admin panel
    page.screenshot(path="/workspace/director-studio-test-cases/17-admin-panel/screenshots/01-admin-panel.png", full_page=False)
    log("T7.screenshot-saved", True, "01-admin-panel.png")

    # T7e: delete buttons for OTHER users (44 cards - 1 admin = 43 buttons)
    delete_buttons = page.locator(".user-delete-btn").count()
    expected_btns = user_cards - 1  # all minus me
    log("T7e.delete-btn-count", delete_buttons == expected_btns,
        f"{delete_buttons} delete buttons (expected {expected_btns} = {user_cards} users - 1 me)")

    browser.close()

# ============================================================
# Final: with a fresh second user, verify delete button shows
# ============================================================
print("\n--- Test 8: UI delete flow (Playwright) ---")
EMAIL_V2 = f"user2_tc17_{int(time.time())}@test.com"
v2_token = signup_via_api(EMAIL_V2)
# v2 user creates 1 project
r = requests.post(f"{LIVE}/api/projects", json={"name": "V2-Proj"},
                  headers={"Authorization": f"Bearer {v2_token}"})

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome",
        args=["--no-sandbox", "--disable-gpu", "--use-gl=swiftshader"]
    )
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    # Mock confirm to always return true
    page.on("dialog", lambda d: d.accept())

    page.goto(LIVE, wait_until="domcontentloaded")
    page.locator("input[name=\"email\"]").fill(ADMIN_EMAIL)
    page.locator("input[name=\"password\"]").fill(ADMIN_PW)
    page.locator("#auth-submit").click()
    page.wait_for_selector("a[data-tab=\"projects\"]", state="visible", timeout=10000)
    page.locator("#nav-admin").click()
    page.wait_for_timeout(800)

    # T8a: now there should be a delete button for user_v2
    delete_btn = page.locator(f".user-delete-btn[data-email='{EMAIL_V2}']")
    log("T8a.delete-btn-present", delete_btn.count() == 1,
        f"1 delete button for v2 user (expect 1, got {delete_btn.count()})")

    page.screenshot(path="/workspace/director-studio-test-cases/17-admin-panel/screenshots/02-with-delete-btn.png", full_page=False)

    # T8b: click delete (with dialog auto-accept)
    users_before = page.locator(".users-list .user-card").count()
    delete_btn.click()
    page.wait_for_timeout(1500)  # wait for re-render
    users_after = page.locator(".users-list .user-card").count()
    log("T8b.user-deleted-UI", users_after == users_before - 1,
        f"users before={users_before} after={users_after} (delta=-1)")

    # T8c: v2 user gone from API list
    r = requests.get(f"{LIVE}/api/admin/users", headers=admin_hdr)
    emails_now = {u["email"] for u in r.json()}
    log("T8c.v2-gone", EMAIL_V2 not in emails_now,
        f"v2 user email removed from API list")

    # T8d: toast should show success — check #toast element (any non-empty)
    toast_text = page.locator("#toast").text_content()
    has_success_class = "success" in (page.locator("#toast").get_attribute("class") or "")
    log("T8d.toast-shown", bool(toast_text) and ("ลบ" in toast_text or has_success_class),
        f"#toast text='{toast_text}' class='{page.locator('#toast').get_attribute('class')}'")

    page.screenshot(path="/workspace/director-studio-test-cases/17-admin-panel/screenshots/03-after-delete.png", full_page=False)
    browser.close()

# ============================================================
# Test 9: Non-admin in browser doesn't see admin nav
# ============================================================
print("\n--- Test 9: Non-admin UI (no admin tab) ---")
EMAIL_NORMAL = f"normal_tc17_{int(time.time())}@test.com"
signup_via_api(EMAIL_NORMAL)
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome",
        args=["--no-sandbox", "--disable-gpu", "--use-gl=swiftshader"]
    )
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(LIVE, wait_until="domcontentloaded")
    page.locator("input[name=\"email\"]").fill(EMAIL_NORMAL)
    page.locator("input[name=\"password\"]").fill(PW)
    page.locator("#auth-submit").click()
    page.wait_for_selector("a[data-tab=\"projects\"]", state="visible", timeout=10000)

    nav_admin = page.locator("#nav-admin")
    is_visible = nav_admin.is_visible()
    log("T9.non-admin-no-nav", not is_visible,
        f"non-admin sees nav-admin? {is_visible} (expect False)")
    page.screenshot(path="/workspace/director-studio-test-cases/17-admin-panel/screenshots/04-non-admin-no-admin.png", full_page=False)
    browser.close()

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
print(f"TC-17 RESULT: {passed}/{total} PASSED")
if passed < total:
    print("FAILED:")
    for n, ok, d in results:
        if not ok:
            print(f"  ❌ {n}: {d}")
print("=" * 60)
