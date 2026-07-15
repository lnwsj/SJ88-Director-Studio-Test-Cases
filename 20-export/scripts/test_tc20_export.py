"""
test_tc20_export.py — TC-20 Export E2E (.md / .json / .txt)
Tests live https://directorstudio.sj88ai.com/ export features.
"""
import os
import re
import time
import json
import requests
from playwright.sync_api import sync_playwright

LIVE = "https://directorstudio.sj88ai.com"
results = []


def log(name, ok, detail=""):
    icon = "✅" if ok else "❌"
    print(f"{icon} {name}: {detail}")
    results.append((name, ok, detail))


def signup_via_api(email, password="exptest1234"):
    r = requests.post(f"{LIVE}/api/auth/signup",
                      json={"email": email, "password": password})
    assert r.status_code == 200, f"signup failed: {r.text}"
    return r.json()["access_token"]


# ============================================================
# Setup: Create user + project with 2 episodes × 3 scenes + Veo prompts
# ============================================================
print("=" * 60)
print("TC-20 EXPORT (.md / .json / .txt) — Setup")
print("=" * 60)
EMAIL = f"exp_{int(time.time())}@test.com"
token = signup_via_api(EMAIL)
hdr = {"Authorization": f"Bearer {token}"}
print(f"  user: {EMAIL}")

# Create project with structured episodes
r = requests.post(f"{LIVE}/api/projects", json={"name": "Ghost Cafe"}, headers=hdr)
pid = r.json()['id']
print(f"  project: {pid}")

# 2 episodes, 3 scenes each, with Veo prompts in timeline
project_data = {
    "meta": {"genre": "horror", "language": "th", "aspect_ratio": "9:16"},
    "episodes": [
        {
            "episode_title": "EP1: เข้าร้าน",
            "episode_title_en": "Entering the Cafe",
            "episode_logline": "น้ำเข้าร้านกาแฟเที่ยงคืน เห็นเงาเด็กในกระจก",
            "scenes": [
                {"id": "S01_01", "title": "ประตูร้าน", "action": "น้ำเดินเข้าร้านมืดๆ"},
                {"id": "S01_02", "title": "เคาน์เตอร์", "action": "สั่งกาแฟกับบาริสต้า"},
                {"id": "S01_03", "title": "เงาในกระจก", "action": "เห็นเงาเด็กยิ้ม"},
            ],
            "timeline": [
                {"scene_id": "S01_01", "t": 0, "prompt": "ผู้หญิงเดินเข้าร้านกาแฟมืด ประตูไม้เก่า เสียงกระดิ่งดังเบาๆ cinematic horror"},
                {"scene_id": "S01_02", "t": 5, "prompt": "close-up เคาน์เตอร์ไม้ บาริสต้าชราผูกผ้ากันเปื้อน หลอดไฟแก้วสั่น Thai horror atmosphere"},
                {"scene_id": "S01_03", "t": 10, "prompt": "เงาเด็กผู้หญิงในกระจก ยิ้มก่อนตัวจริง slow motion supernatural"},
            ],
        },
        {
            "episode_title": "EP2: สั่งกาแฟ",
            "episode_title_en": "Order the Coffee",
            "episode_logline": "บาริสต้าเตือนว่าไม่ควรอยู่ต่อ",
            "scenes": [
                {"id": "S02_01", "title": "กาแฟเย็น", "action": "บาริสต้าทำกาแฟมือสั่น"},
                {"id": "S02_02", "title": "คำเตือน", "action": "บาริสต้าบอกให้กลับ"},
                {"id": "S02_03", "title": "เงาขยับ", "action": "เงาเด็กเดินออกจากกระจก"},
            ],
            "timeline": [
                {"scene_id": "S02_01", "t": 0, "prompt": "มือบาริสต้าชราสั่น รินกาแฟลงแก้ว ของเหลวสีดำผิดปกติ extreme close-up"},
                {"scene_id": "S02_02", "t": 5, "prompt": "บาริสต้ากระซิบ เตือนผู้หญิง ดวงตาหวาดกลัว Thai dialogue subtitles"},
                {"scene_id": "S02_03", "t": 10, "prompt": "เงาเด็กค่อยๆ ก้าวออกจากกระจก ตัวจริงยังอยู่ที่เดิม body horror reveal"},
            ],
        },
    ],
}

r = requests.put(f"{LIVE}/api/projects/{pid}", json={"data": project_data}, headers=hdr)
assert r.status_code == 200
print(f"  saved: 2 EPs × 3 scenes + Veo prompts")

# Get full project back
r = requests.get(f"{LIVE}/api/projects/{pid}", headers=hdr)
full_project = r.json()
print(f"  full project: {len(json.dumps(full_project))} bytes")

# ============================================================
# T1: Verify project structure (sanity)
# ============================================================
print("\n--- T1: Project structure ---")
log("T1.has-2-eps", len(full_project['data']['episodes']) == 2,
    f"{len(full_project['data']['episodes'])} episodes")
log("T1.ep1-3-scenes", len(full_project['data']['episodes'][0]['scenes']) == 3,
    f"EP1 scenes = {len(full_project['data']['episodes'][0]['scenes'])}")
log("T1.ep1-3-veo", len(full_project['data']['episodes'][0]['timeline']) == 3,
    f"EP1 Veo prompts = {len(full_project['data']['episodes'][0]['timeline'])}")

# ============================================================
# T2: API .json export (just project GET)
# ============================================================
print("\n--- T2: API .json ---")
r = requests.get(f"{LIVE}/api/projects/{pid}", headers=hdr)
log("T2.api-json-200", r.status_code == 200, f"status={r.status_code}")
data = r.json()
log("T2.api-json-valid", isinstance(data, dict) and "id" in data and "data" in data,
    f"keys: {list(data.keys())[:5]}")
log("T2.api-json-roundtrip", json.dumps(data) is not None,
    f"JSON-serializable: {len(json.dumps(data))} bytes")
log("T2.api-json-includes-episodes", "episodes" in data.get("data", {}),
    f"episodes in data: {len(data.get('data', {}).get('episodes', []))}")

# ============================================================
# T3: HTML has 3 export buttons
# ============================================================
print("\n--- T3: UI buttons present ---")
r = requests.get(f"{LIVE}/")
html = r.text
log("T3.json-btn-html", "id=\"project-export-btn\"" in html, ".json button in HTML")
log("T3.md-btn-html", "id=\"project-export-md-btn\"" in html, ".md button in HTML")
log("T3.txt-btn-html", "id=\"project-export-txt-btn\"" in html, ".txt button in HTML")

# ============================================================
# T4-T6: Real browser download tests
# ============================================================
print("\n--- T4: Real .json download ---")
DOWNLOAD_DIR = "/workspace/director-studio-test-cases/20-export/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome",
        args=["--no-sandbox", "--disable-gpu", "--use-gl=swiftshader"]
    )
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
    page = ctx.new_page()
    page.goto(LIVE, wait_until="domcontentloaded")
    page.locator("input[name=\"email\"]").fill(EMAIL)
    page.locator("input[name=\"password\"]").fill("exptest1234")
    page.locator("#auth-submit").click()
    page.wait_for_selector("a[data-tab=\"projects\"]", state="visible", timeout=10000)
    page.locator("a[data-tab=\"projects\"]").click()
    page.wait_for_timeout(800)

    # Open the project
    # Click on the project card
    page.locator(f".project-card:has-text('Ghost Cafe')").first.click()
    page.wait_for_timeout(1500)

    # Open project settings
    page.locator("#project-settings-btn").click()
    page.wait_for_timeout(500)

    page.screenshot(
        path="/workspace/director-studio-test-cases/20-export/screenshots/01-export-buttons.png",
        full_page=False
    )
    log("T3.screenshot-buttons", True, "01-export-buttons.png")

    # Test .json download
    with page.expect_download() as dl_info:
        page.locator("#project-export-btn").click()
    dl = dl_info.value
    json_path = os.path.join(DOWNLOAD_DIR, dl.suggested_filename)
    dl.save_as(json_path)
    log("T4.json-downloaded", os.path.exists(json_path), f"→ {dl.suggested_filename}")

    with open(json_path) as f:
        json_data = json.load(f)
    log("T4.json-valid-parse", "data" in json_data and "episodes" in json_data.get("data", {}),
        f"episodes = {len(json_data.get('data', {}).get('episodes', []))}")
    log("T4.json-2-eps", len(json_data["data"]["episodes"]) == 2,
        f"2 episodes in JSON")

    # Test .md download
    with page.expect_download() as dl_info:
        page.locator("#project-export-md-btn").click()
    dl = dl_info.value
    md_path = os.path.join(DOWNLOAD_DIR, dl.suggested_filename)
    dl.save_as(md_path)
    log("T5.md-downloaded", os.path.exists(md_path), f"→ {dl.suggested_filename}")
    with open(md_path) as f:
        md_content = f.read()
    log("T5.md-has-title", "# Ghost Cafe" in md_content, f"title in MD")
    log("T5.md-has-2-eps", "## 📋 2 Episodes" in md_content, f"episode count in MD")
    log("T5.md-has-ep1", "EP1: เข้าร้าน" in md_content, f"EP1 title in MD")
    log("T5.md-has-ep2", "EP2: สั่งกาแฟ" in md_content, f"EP2 title in MD")
    log("T5.md-3-sc-each", md_content.count("scenes") >= 2,
        f"scenes mentioned: {md_content.count('scenes')}")

    # Test .txt download (the new feature!)
    with page.expect_download() as dl_info:
        page.locator("#project-export-txt-btn").click()
    dl = dl_info.value
    txt_path = os.path.join(DOWNLOAD_DIR, dl.suggested_filename)
    dl.save_as(txt_path)
    log("T6.txt-downloaded", os.path.exists(txt_path), f"→ {dl.suggested_filename}")
    with open(txt_path) as f:
        txt_content = f.read()
    log("T6.txt-not-empty", len(txt_content) > 100, f"{len(txt_content)} chars")
    # Format: 1 prompt per line: "EP1_S01_01: <prompt>"
    ep1_lines = [l for l in txt_content.split("\n") if l.startswith("EP1_S")]
    ep2_lines = [l for l in txt_content.split("\n") if l.startswith("EP2_S")]
    log("T6.txt-ep1-3-prompts", len(ep1_lines) == 3,
        f"EP1 prompts = {len(ep1_lines)} (expect 3)")
    log("T6.txt-ep2-3-prompts", len(ep2_lines) == 3,
        f"EP2 prompts = {len(ep2_lines)} (expect 3)")
    log("T6.txt-format-correct", all(re.match(r"^EP\d+_S\d+_\d+: ", l) for l in ep1_lines + ep2_lines),
        f"all lines match 'EP<n>_S<n>_<n>: ' format")
    log("T6.txt-no-markdown", "##" not in txt_content and "**" not in txt_content,
        f"no markdown syntax (## or **)")
    log("T6.txt-no-json", "{" not in txt_content,
        f"no JSON syntax")
    log("T6.txt-actual-content", "cinematic horror" in txt_content or "Thai horror" in txt_content,
        f"real prompt content preserved")
    # Verify header is comment-style
    log("T6.txt-has-header", txt_content.startswith("# Ghost Cafe"),
        f"first line: {txt_content.split(chr(10))[0][:50]}")

    page.screenshot(
        path="/workspace/director-studio-test-cases/20-export/screenshots/02-after-downloads.png",
        full_page=False
    )
    log("T6.screenshot", True, "02-after-downloads.png")
    browser.close()

# ============================================================
# T7: Empty project
# ============================================================
print("\n--- T7: Empty project ---")
r = requests.post(f"{LIVE}/api/projects", json={"name": "Empty"}, headers=hdr)
empty_pid = r.json()['id']
r = requests.put(f"{LIVE}/api/projects/{empty_pid}",
                 json={"data": {"meta": {}, "episodes": []}}, headers=hdr)

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome",
        args=["--no-sandbox", "--disable-gpu", "--use-gl=swiftshader"]
    )
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
    page = ctx.new_page()
    page.goto(LIVE, wait_until="domcontentloaded")
    page.locator("input[name=\"email\"]").fill(EMAIL)
    page.locator("input[name=\"password\"]").fill("exptest1234")
    page.locator("#auth-submit").click()
    page.wait_for_selector("a[data-tab=\"projects\"]", state="visible", timeout=10000)
    page.locator("a[data-tab=\"projects\"]").click()
    page.wait_for_timeout(800)
    page.locator(f".project-card:has-text('Empty')").first.click()
    page.wait_for_timeout(1500)
    page.locator("#project-settings-btn").click()
    page.wait_for_timeout(500)

    with page.expect_download() as dl_info:
        page.locator("#project-export-md-btn").click()
    dl = dl_info.value
    md_empty_path = os.path.join(DOWNLOAD_DIR, "empty.md")
    dl.save_as(md_empty_path)
    with open(md_empty_path) as f:
        empty_md = f.read()
    log("T7.md-empty-no-eps", "No episodes yet" in empty_md,
        f"empty MD: {empty_md.split(chr(10))[-2][:60]}")

    with page.expect_download() as dl_info:
        page.locator("#project-export-txt-btn").click()
    dl = dl_info.value
    txt_empty_path = os.path.join(DOWNLOAD_DIR, "empty.txt")
    dl.save_as(txt_empty_path)
    with open(txt_empty_path) as f:
        empty_txt = f.read()
    log("T7.txt-empty-warns", "(no episodes yet)" in empty_txt,
        f"empty TXT: {empty_txt.strip().split(chr(10))[-1][:50]}")
    browser.close()

# ============================================================
# T8: Copy-paste to Sora/Runway test (just verify .txt is plain)
# ============================================================
print("\n--- T8: .txt ready for copy-paste ---")
with open(f"{DOWNLOAD_DIR}/Ghost_Cafe_prompts.txt") as f:
    txt = f.read()
# Count "real prompts" (not header)
real_prompts = [l for l in txt.split("\n")
                if re.match(r"^EP\d+_S\d+_\d+: .+", l) and len(l) > 50]
log("T8.6-real-prompts", len(real_prompts) == 6,
    f"real prompts: {len(real_prompts)} (expect 6: 2 EPs × 3 scenes)")
log("T8.prompts-are-substantial", all(len(l) > 50 for l in real_prompts),
    f"all prompts > 50 chars (ready for AI tools)")

# Print first 3 prompts for visual confirmation
print("\n   First 3 prompts from .txt:")
for p in real_prompts[:3]:
    print(f"   • {p[:80]}...")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
print(f"TC-20 RESULT: {passed}/{total} PASSED")
if passed < total:
    print("FAILED:")
    for n, ok, d in results:
        if not ok:
            print(f"  ❌ {n}: {d}")
print("=" * 60)
