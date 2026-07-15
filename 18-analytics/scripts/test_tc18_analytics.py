"""
test_tc18_analytics.py — TC-18 Analytics E2E
Tests live https://directorstudio.sj88ai.com/ analytics dashboard:
- Empty state (new user)
- Populated state (user with projects + jobs)
- 7-day chart bars
- Veo success rate %
- Per-user isolation
"""
import re
import time
import requests
from playwright.sync_api import sync_playwright

LIVE = "https://directorstudio.sj88ai.com"
results = []


def log(name, ok, detail=""):
    icon = "✅" if ok else "❌"
    print(f"{icon} {name}: {detail}")
    results.append((name, ok, detail))


def signup_via_api(email, password="testtest123"):
    r = requests.post(f"{LIVE}/api/auth/signup",
                      json={"email": email, "password": password})
    if r.status_code != 200:
        raise AssertionError(f"signup failed: {r.text}")
    return r.json()["access_token"]


# ============================================================
# Test 1: Analytics tab exists in nav + loads without error
# ============================================================
print("=" * 60)
print("TC-18 ANALYTICS — Setup")
print("=" * 60)
EMAIL_NEW = f"an_new_{int(time.time())}@test.com"
EMAIL_POP = f"an_pop_{int(time.time())}@test.com"
EMAIL_ISO = f"an_iso_{int(time.time())}@test.com"

new_token = signup_via_api(EMAIL_NEW)
print(f"  new user: {EMAIL_NEW}")

# Create populated user with projects
pop_token = signup_via_api(EMAIL_POP)
pop_hdr = {"Authorization": f"Bearer {pop_token}"}
for i in range(3):
    r = requests.post(f"{LIVE}/api/projects", json={"name": f"Test-Proj-{i}"}, headers=pop_hdr)
    assert r.status_code == 200
# Create 1 project with episodes
p = requests.post(f"{LIVE}/api/projects", json={"name": "With-Episodes"}, headers=pop_hdr).json()
requests.put(f"{LIVE}/api/projects/{p['id']}",
             json={"data": {"episodes": [{"title": "EP1"}, {"title": "EP2"}]}},
             headers=pop_hdr)
# Submit a job (script_gen)
r = requests.post(f"{LIVE}/api/jobs", json={"type": "script_gen", "input": {}}, headers=pop_hdr)
print(f"  populated user: {EMAIL_POP} (4 projects, 2 episodes, 1 job)")

# Isolation user
iso_token = signup_via_api(EMAIL_ISO)
iso_hdr = {"Authorization": f"Bearer {iso_token}"}
# Create 1 project
requests.post(f"{LIVE}/api/projects", json={"name": "Iso-Proj"}, headers=iso_hdr)
print(f"  isolation user: {EMAIL_ISO} (1 project)")

# ============================================================
# Test 2: API returns expected structure
# ============================================================
print("\n--- Test 2: API structure (populated user) ---")
r = requests.get(f"{LIVE}/api/analytics/me", headers=pop_hdr)
log("T2.api-200", r.status_code == 200, f"status={r.status_code}")
body = r.json()
log("T2.has-projects", "projects" in body and "total" in body["projects"],
    f"projects.total = {body['projects'].get('total')}")
log("T2.has-jobs", "jobs" in body and "total" in body["jobs"],
    f"jobs.total = {body['jobs'].get('total')}")
log("T2.has-veo", "veo_tasks" in body and "success_rate" in body["veo_tasks"],
    f"veo_tasks.success_rate = {body['veo_tasks'].get('success_rate')}")
log("T2.has-credits", "credits" in body and "estimated_used" in body["credits"],
    f"credits.estimated_used = {body['credits'].get('estimated_used')}")
log("T2.has-7-days", "last_7_days" in body and len(body["last_7_days"]) == 7,
    f"last_7_days has {len(body.get('last_7_days', []))} days (expect 7)")
log("T2.4-projects-count", body["projects"]["total"] >= 4,
    f"projects.total = {body['projects']['total']} (≥4 expected)")
log("T2.2-episodes-count", body["projects"]["episodes"] >= 2,
    f"episodes = {body['projects']['episodes']} (≥2 expected)")

# ============================================================
# Test 3: API requires auth (no token)
# ============================================================
print("\n--- Test 3: API auth required ---")
r = requests.get(f"{LIVE}/api/analytics/me")
log("T3.no-auth-401", r.status_code == 401, f"no token → {r.status_code} (expect 401)")

# ============================================================
# Test 4: Per-user isolation (API level)
# ============================================================
print("\n--- Test 4: Per-user isolation (API) ---")
r_pop = requests.get(f"{LIVE}/api/analytics/me", headers=pop_hdr).json()
r_iso = requests.get(f"{LIVE}/api/analytics/me", headers=iso_hdr).json()
log("T4.pop-4+", r_pop["projects"]["total"] >= 4,
    f"pop projects = {r_pop['projects']['total']} (≥4)")
log("T4.iso-1", r_iso["projects"]["total"] == 1,
    f"iso projects = {r_iso['projects']['total']} (expect 1)")
log("T4.iso-no-leak", r_iso["projects"]["total"] < r_pop["projects"]["total"],
    f"iso ({r_iso['projects']['total']}) < pop ({r_pop['projects']['total']}) → no leak")

# ============================================================
# Test 5: 7-day chart structure
# ============================================================
print("\n--- Test 5: 7-day chart structure ---")
days = body["last_7_days"]
log("T5.7-days", len(days) == 7, f"{len(days)} days")
labels = [d["day"] for d in days]
log("T5.day-labels", all(isinstance(d, str) and len(d) <= 5 for d in labels),
    f"labels: {labels}")
log("T5.day-counts", all(isinstance(d["count"], int) and d["count"] >= 0 for d in days),
    f"all counts are non-negative ints")
total_7d = sum(d["count"] for d in days)
log("T5.pop-7d-includes-job", total_7d >= 1,
    f"7-day total = {total_7d} (≥1 from the job we created)")

# ============================================================
# Test 6: UI - empty state (new user)
# ============================================================
print("\n--- Test 6: UI - empty state ---")
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome",
        args=["--no-sandbox", "--disable-gpu", "--use-gl=swiftshader"]
    )
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(LIVE, wait_until="domcontentloaded")
    page.locator("input[name=\"email\"]").fill(EMAIL_NEW)
    page.locator("input[name=\"password\"]").fill("testtest123")
    page.locator("#auth-submit").click()
    page.wait_for_selector("a[data-tab=\"projects\"]", state="visible", timeout=10000)
    page.locator("a[data-tab=\"analytics\"]").click()
    page.wait_for_timeout(2000)  # let API load

    quota_items = page.locator(".quota-item").count()
    log("T6.quota-items", quota_items == 8, f"{quota_items} quota items (expect 8: 2 rows × 4 items)")

    # Empty state: top project should be null
    top_project = page.locator("p.muted:has-text('Top project')").count()
    log("T6.no-top-project", top_project == 0,
        f"top project shown? {top_project} (expect 0 for empty)")

    # Take screenshot of empty state
    page.screenshot(path="/workspace/director-studio-test-cases/18-analytics/screenshots/01-empty-state.png", full_page=False)
    log("T6.screenshot-empty", True, "01-empty-state.png")
    browser.close()

# ============================================================
# Test 7: UI - populated state (chart bars)
# ============================================================
print("\n--- Test 7: UI - populated state ---")
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome",
        args=["--no-sandbox", "--disable-gpu", "--use-gl=swiftshader"]
    )
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(LIVE, wait_until="domcontentloaded")
    page.locator("input[name=\"email\"]").fill(EMAIL_POP)
    page.locator("input[name=\"password\"]").fill("testtest123")
    page.locator("#auth-submit").click()
    page.wait_for_selector("a[data-tab=\"projects\"]", state="visible", timeout=10000)
    page.locator("a[data-tab=\"analytics\"]").click()
    page.wait_for_timeout(2000)

    chart_bars = page.locator(".chart-bar-wrap").count()
    log("T7.7-chart-bars", chart_bars == 7, f"{chart_bars} chart bars (expect 7)")

    # Top project should be shown
    top_project_visible = page.locator("p.muted:has-text('Top project')").is_visible()
    log("T7.top-project-shown", top_project_visible, f"top project visible = {top_project_visible}")

    # Quota values: at least one should be > 0 (projects=4, episodes=2, jobs=1)
    quota_values = page.locator(".quota-value").all_text_contents()
    log("T7.has-non-zero-values", any(v.strip() not in ("0", "0%", "0.0", "—") for v in quota_values),
        f"quota values: {quota_values}")

    # Take screenshot
    page.screenshot(path="/workspace/director-studio-test-cases/18-analytics/screenshots/02-populated.png", full_page=False)
    log("T7.screenshot-populated", True, "02-populated.png")

    # Scroll to see chart
    page.locator(".chart-wrap").scroll_into_view_if_needed()
    page.screenshot(path="/workspace/director-studio-test-cases/18-analytics/screenshots/03-chart-detail.png", full_page=False)
    log("T7.screenshot-chart", True, "03-chart-detail.png")
    browser.close()

# ============================================================
# Test 8: UI - per-user isolation (visible)
# ============================================================
print("\n--- Test 8: UI - per-user isolation ---")
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome",
        args=["--no-sandbox", "--disable-gpu", "--use-gl=swiftshader"]
    )
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(LIVE, wait_until="domcontentloaded")
    page.locator("input[name=\"email\"]").fill(EMAIL_ISO)
    page.locator("input[name=\"password\"]").fill("testtest123")
    page.locator("#auth-submit").click()
    page.wait_for_selector("a[data-tab=\"projects\"]", state="visible", timeout=10000)
    page.locator("a[data-tab=\"analytics\"]").click()
    page.wait_for_timeout(2000)

    # Iso user has 1 project, 0 jobs
    # Should NOT see "4 projects" or "1 job" (pop user's data)
    quota_values_iso = page.locator(".quota-value").all_text_contents()
    log("T8.iso-projects-1", any("1" in v and "Projects" in page.locator(".quota-label").nth(i).text_content()
                                   for i, v in enumerate(quota_values_iso)),
        f"iso quota values: {quota_values_iso}")

    # Pop user had 4 projects — iso should NOT show 4
    has_four = any("4" in v for v in quota_values_iso)
    log("T8.iso-no-pop-data", not has_four,
        f"iso shows '4'? {has_four} (expect False)")

    page.screenshot(path="/workspace/director-studio-test-cases/18-analytics/screenshots/04-isolation.png", full_page=False)
    log("T8.screenshot-iso", True, "04-isolation.png")
    browser.close()

# ============================================================
# Test 9: Veo success rate (formula: completed + succeeded / total * 100)
# ============================================================
print("\n--- Test 9: Veo success rate formula ---")
r = requests.get(f"{LIVE}/api/analytics/me", headers=pop_hdr).json()
vt = r["veo_tasks"]
if vt["total"] > 0:
    expected = round(vt["success"] / vt["total"] * 100, 1)
else:
    expected = 0
log("T9.success-rate-formula", vt["success_rate"] == expected,
    f"success_rate = {vt['success_rate']} (computed: {expected})")

# ============================================================
# Test 10: Credits estimation (Veo=1, LLM=0.1)
# ============================================================
print("\n--- Test 10: Credits estimation ---")
r = requests.get(f"{LIVE}/api/analytics/me", headers=pop_hdr).json()
cr = r["credits"]
log("T10.llm-credits-≥0.1", cr["llm_credits"] >= 0.1,
    f"llm_credits = {cr['llm_credits']} (≥0.1 from 1 job)")
log("T10.total-≥llm", cr["estimated_used"] >= cr["llm_credits"],
    f"total {cr['estimated_used']} ≥ llm {cr['llm_credits']}")
log("T10.veo+llm=total", abs(cr["estimated_used"] - (cr["veo_credits"] + cr["llm_credits"])) < 0.1,
    f"veo {cr['veo_credits']} + llm {cr['llm_credits']} = total {cr['estimated_used']}")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
print(f"TC-18 RESULT: {passed}/{total} PASSED")
if passed < total:
    print("FAILED:")
    for n, ok, d in results:
        if not ok:
            print(f"  ❌ {n}: {d}")
print("=" * 60)
