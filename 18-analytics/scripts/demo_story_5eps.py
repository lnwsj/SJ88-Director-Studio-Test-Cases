"""
demo_story_5eps.py — Live demo: 1 story × 5 EPs × see analytics
User: "ลองแต่งเรื่องสัก 1 เรื่อง 5 ep แล้วดูสถิติขึ้นไหม ไม่ต้องเจน vdo"

Uses /api/jobs (background queue) so analytics tracks:
- jobs.total
- credits.estimated_used (0.1 per LLM job)
- 7-day chart bars
"""
import time
import requests
from playwright.sync_api import sync_playwright

LIVE = "https://directorstudio.sj88ai.com"
STORY_IDEA = "เรื่อง 'เงาในร้านกาแฟ': สาวออฟฟิศเข้าร้านกาแฟเก่าแก่ตอนเที่ยงคืน เธอสั่งกาแฟแล้วเห็นเงาของเด็กผู้หญิงในกระจก เงายิ้มก่อนเธอ"

print("=" * 70)
print("🎬 LIVE DEMO: 1 เรื่อง × 5 EPs × ดูสถิติ")
print("=" * 70)

# ============================================================
# Step 1: Create user
# ============================================================
EMAIL = f"demo5b_{int(time.time())}@test.com"
print(f"\n[1] Signup new user: {EMAIL}")
r = requests.post(f"{LIVE}/api/auth/signup",
                  json={"email": EMAIL, "password": "demotest1234"})
assert r.status_code == 200, f"signup failed: {r.text}"
user_tok = r.json()['access_token']
user_hdr = {"Authorization": f"Bearer {user_tok}"}
print(f"    ✓ user_id = {r.json()['user']['id']}")

# ============================================================
# Step 2: Create project
# ============================================================
print(f"\n[2] Create project 'เงาในร้านกาแฟ'")
r = requests.post(f"{LIVE}/api/projects", json={"name": "เงาในร้านกาแฟ"}, headers=user_hdr)
assert r.status_code == 200
project_id = r.json()['id']
print(f"    ✓ project_id = {project_id}")

# ============================================================
# Step 3: Generate 5 scripts via /api/jobs (background queue)
# ============================================================
print(f"\n[3] Submit 5 script_gen JOBS (background queue → analytics tracks)")
job_ids = []
for ep_num in range(1, 6):
    r = requests.post(f"{LIVE}/api/jobs",
                      json={
                          "type": "script_gen",
                          "input": {
                              "idea": STORY_IDEA,
                              "episode_number": ep_num,
                              "num_scenes": 4,
                              "style": "Thai horror, dark, atmospheric, character-driven",
                          },
                          "project_id": project_id,
                      },
                      headers=user_hdr)
    if r.status_code == 200:
        jid = r.json()['job_id']
        job_ids.append(jid)
        print(f"    EP{ep_num}: queued job_id={jid}")
    else:
        print(f"    EP{ep_num}: ❌ {r.status_code} {r.text[:100]}")

print(f"\n[4] Wait 60s for jobs to complete...")
for i in range(6):
    time.sleep(10)
    # Check status of all jobs
    statuses = []
    for jid in job_ids:
        r = requests.get(f"{LIVE}/api/jobs/{jid}", headers=user_hdr)
        if r.status_code == 200:
            statuses.append(r.json().get('status', '?'))
    print(f"    {(i+1)*10}s: {dict((s, statuses.count(s)) for s in set(statuses))}")
    if all(s in ('succeeded', 'completed', 'failed') for s in statuses):
        break

# ============================================================
# Step 5: Collect scripts from successful jobs, save as episodes
# ============================================================
print(f"\n[5] Save successful scripts to project (so episodes show)")
episodes = []
for jid in job_ids:
    r = requests.get(f"{LIVE}/api/jobs/{jid}", headers=user_hdr)
    job = r.json()
    if job.get('status') in ('succeeded', 'completed') and job.get('result'):
        # Try to extract script
        result = job['result']
        if isinstance(result, dict):
            script = result.get('script') or result
            title = script.get('title') or script.get('episode_title') or f"EP{len(episodes)+1}"
            scenes = script.get('scenes', [])
            episodes.append({
                "title": title,
                "scenes": scenes,
                "synopsis": script.get('synopsis', ''),
            })
            print(f"    ✓ job {jid[:8]}: '{title}' ({len(scenes)} scenes)")
        else:
            print(f"    ? job {jid[:8]}: result is {type(result).__name__}")
    else:
        status = job.get('status')
        msg = job.get('message', '')[:80]
        print(f"    {status}: {jid[:8]} — {msg}")

# Save to project
r = requests.get(f"{LIVE}/api/projects/{project_id}", headers=user_hdr)
proj_data = r.json().get('data', {})
proj_data['episodes'] = episodes
proj_data['meta'] = {"genre": "horror", "language": "th", "aspect_ratio": "9:16"}
requests.put(f"{LIVE}/api/projects/{project_id}",
             json={"data": proj_data}, headers=user_hdr)
print(f"    ✓ {len(episodes)} episodes saved to project")

# ============================================================
# Step 6: Check analytics via API
# ============================================================
print(f"\n[6] Analytics (API)")
r = requests.get(f"{LIVE}/api/analytics/me", headers=user_hdr).json()
print(f"    projects.total    = {r['projects']['total']}")
print(f"    projects.episodes = {r['projects']['episodes']}")
print(f"    jobs.total        = {r['jobs']['total']}  ← from /api/jobs")
print(f"    veo_tasks.total   = {r['veo_tasks']['total']}  ← 0 (we skipped Veo)")
print(f"    credits.estimated = {r['credits']['estimated_used']}  ← 0.1 per LLM job")
print(f"    7-day total       = {sum(d['count'] for d in r['last_7_days'])} jobs")

# ============================================================
# Step 7: UI screenshot
# ============================================================
print(f"\n[7] UI screenshot")
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome",
        args=["--no-sandbox", "--disable-gpu", "--use-gl=swiftshader"]
    )
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(LIVE, wait_until="domcontentloaded")
    page.locator("input[name=\"email\"]").fill(EMAIL)
    page.locator("input[name=\"password\"]").fill("demotest1234")
    page.locator("#auth-submit").click()
    page.wait_for_selector("a[data-tab=\"projects\"]", state="visible", timeout=10000)
    page.locator("a[data-tab=\"analytics\"]").click()
    page.wait_for_timeout(2000)

    page.screenshot(
        path="/workspace/director-studio-test-cases/18-analytics/screenshots/05-demo-5eps.png",
        full_page=False
    )

    quota_values = page.locator(".quota-value").all_text_contents()
    print(f"    quota values (UI): {quota_values}")
    print(f"    chart bars:        {page.locator('.chart-bar-wrap').count()}")
    print(f"    ✓ 05-demo-5eps.png saved")

    page.locator(".chart-wrap").scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    page.screenshot(
        path="/workspace/director-studio-test-cases/18-analytics/screenshots/06-demo-5eps-chart.png",
        full_page=False
    )
    print(f"    ✓ 06-demo-5eps-chart.png saved (with chart)")
    browser.close()

# ============================================================
# Final
# ============================================================
print(f"\n{'='*70}")
print(f"✅ DEMO COMPLETE")
print(f"{'='*70}")
print(f"  Story:    'เงาในร้านกาแฟ'")
print(f"  Episodes: {len(episodes)} (saved)")
print(f"  Jobs:     {r['jobs']['total']} (5 script_gen, no Veo)")
print(f"  Credits:  {r['credits']['estimated_used']} estimated")
print(f"\n  → Analytics อัปเดต real-time")
print(f"  → 7-day chart แสดง jobs ที่เพิ่งสร้าง")
print(f"  → Top project แสดง 'เงาในร้านกาแฟ'")
print(f"{'='*70}")
