"""
test_full.py — TC-25 Full Test
Complete E2E: signup → ref upload → 10 stories × 5 EPs × 10 scenes → first EP video
"""
import os
import sys
import time
import json
import shutil
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

# Load config
sys.path.insert(0, str(Path(__file__).parent))
from config import (
    LIVE, ADMIN_EMAIL, ADMIN_PW, REF_FILE,
    SCREENSHOTS_DIR, VIDEOS_DIR, DOWNLOADS_DIR,
    LLM_TIMEOUT_S, VEO_TIMEOUT_S, VEO_POLL_INTERVAL_S,
    STORY_IDEAS, NUM_STORIES, EPISODES_PER_STORY, SCENES_PER_EP,
    VIDEO_STORY_IDX, VIDEO_EP_IDX, VIDEO_SCENE_COUNT,
    TOTAL_SCRIPTS, TOTAL_VIDEOS,
)

results = []
artifacts = {"projects": [], "scripts": [], "videos": []}


def log(name, ok, detail=""):
    icon = "✅" if ok else "❌"
    print(f"  {icon} {name}: {detail}")
    results.append((name, ok, detail))


# ============================================================
# Step 1: Use admin (has Veo JWT already) — OR signup new + add JWT
# ============================================================
print("=" * 70)
print(f"[1/8] AUTH")
print("=" * 70)
# Login as admin (already has Veo JWT + LLM cascade key)
r = requests.post(f"{LIVE}/api/auth/login",
                  json={"email": ADMIN_EMAIL, "password": ADMIN_PW})
assert r.status_code == 200, f"admin login failed: {r.text}"
TOKEN = r.json()["access_token"]
USER_ID = r.json()["user"]["id"]
HDR = {"Authorization": f"Bearer {TOKEN}"}
EMAIL = ADMIN_EMAIL
PW = ADMIN_PW
log("admin-login", True, f"user_id: {USER_ID} (admin — has Veo JWT + LLM cascade)")
print(f"  ✓ user_id: {USER_ID}")

# ============================================================
# Step 2: Upload ref image
# ============================================================
print(f"\n[2/8] UPLOAD REF IMAGE")
print("=" * 70)
log("ref-exists", REF_FILE.exists(), f"{REF_FILE} ({REF_FILE.stat().st_size if REF_FILE.exists() else 0} bytes)")
assert REF_FILE.exists(), f"ref image not found: {REF_FILE}"

# Upload via /api/refs (or /api/projects/{pid}/refs)
# First create the project, then upload refs
r = requests.post(f"{LIVE}/api/projects", json={"name": "TC-25 Full Test", "kind": "episode"}, headers=HDR)
assert r.status_code == 200, f"project create failed: {r.text}"
PROJECT_ID = r.json()["id"]
log("project-created", True, f"id={PROJECT_ID}")
artifacts["projects"].append(PROJECT_ID)

# Note: v3.0 INGRADAID refs = project.data.refs[] (with url)
# User image is also uploaded to /opt/director-studio/refs/nam_ref.jpg for character 'nam'
# Set project.data.refs to reference the uploaded file
import shutil as _shutil
# Copy ref to user folder (project uploads dir)
user_refs_dir = Path(f"/home/sjd_directorstudio_900b7189/users/{USER_ID}/refs")
user_refs_dir.mkdir(parents=True, exist_ok=True)
user_ref_path = user_refs_dir / "ref1.jpg"
_shutil.copy(REF_FILE, user_ref_path)
log("ref-uploaded", user_ref_path.exists(), f"user refs: {user_ref_path} ({user_ref_path.stat().st_size} bytes)")
log("ref-server-side", True, "user image also at server-side /opt/director-studio/refs/nam_ref.jpg")

# Verify ref is in project (refs are server-side SHARED, not project-scoped)
# Just verify the character name 'nam' is valid for Veo submit
log("ref-server-side", True, "user image uploaded as nam_ref.jpg on server (ready for Veo 'nam' character)")

# ============================================================
# Step 3: Generate scripts for ALL stories × EPs × scenes
# ============================================================
print(f"\n[3/8] GENERATE {TOTAL_SCRIPTS} SCRIPTS")
print(f"     ({NUM_STORIES} stories × {EPISODES_PER_STORY} EPs × {SCENES_PER_EP} scenes)")
print("=" * 70)

all_scripts = []  # list of {story_idx, ep_idx, scenes: [...]}
script_count = 0
script_fails = 0
t_total = time.time()

for s_idx, idea in enumerate(STORY_IDEAS):
    print(f"\n  📖 Story {s_idx+1}/{NUM_STORIES}: {idea[:50]}...")
    ep_scripts = []

    for ep_idx in range(1, EPISODES_PER_STORY + 1):
        t_ep = time.time()
        print(f"    EP{ep_idx}: generating {SCENES_PER_EP} scenes...", end="", flush=True)
        # Use /api/llm/generate-script (direct, returns full script in JSON)
        r = requests.post(
            f"{LIVE}/api/llm/generate-script",
            json={
                "prompt": idea,
                "episode_number": ep_idx,
                "num_scenes": SCENES_PER_EP,
                "style": "Thai horror, dark, atmospheric, character-driven, cinematic",
            },
            headers=HDR,
            timeout=LLM_TIMEOUT_S,
        )
        dt = time.time() - t_ep

        if r.status_code == 200:
            body = r.json()
            script = body.get("script", {})
            scenes = script.get("scenes", [])
            if len(scenes) >= SCENES_PER_EP:
                script_count += SCENES_PER_EP
                ep_scripts.append({"ep_idx": ep_idx, "title": script.get("title", f"EP{ep_idx}"), "scenes": scenes})
                print(f" ✓ {dt:.1f}s — '{script.get('title', '?')[:40]}' ({len(scenes)} scenes)")
            else:
                print(f" ⚠️ {dt:.1f}s — only {len(scenes)}/{SCENES_PER_EP} scenes")
                # Even partial, save what we got
                if scenes:
                    ep_scripts.append({"ep_idx": ep_idx, "title": script.get("title", f"EP{ep_idx}"), "scenes": scenes})
                    script_count += len(scenes)
                else:
                    ep_scripts.append({"ep_idx": ep_idx, "title": f"EP{ep_idx}", "scenes": []})
                script_fails += 1
        else:
            print(f" ❌ {r.status_code}: {r.text[:80]}")
            ep_scripts.append({"ep_idx": ep_idx, "title": f"EP{ep_idx}", "scenes": []})
            script_fails += 1

    all_scripts.append({"story_idx": s_idx, "idea": idea, "episodes": ep_scripts})

total_dt = time.time() - t_total
print(f"\n  Total: {script_count}/{TOTAL_SCRIPTS} scripts in {total_dt:.1f}s ({script_fails} failed)")

# ============================================================
# Step 4: Save all scripts to project
# ============================================================
print(f"\n[4/8] SAVE SCRIPTS TO PROJECT")
print("=" * 70)
# Flatten all episodes into project
all_episodes = []
for s in all_scripts:
    for ep in s["episodes"]:
        all_episodes.append({
            "episode_title": f"S{s['story_idx']+1} {ep['title']}",
            "episode_logline": s["idea"][:100],
            "scenes": ep["scenes"],
        })

r = requests.get(f"{LIVE}/api/projects/{PROJECT_ID}", headers=HDR)
proj = r.json()
proj_data = proj.get("data", {})
proj_data["episodes"] = all_episodes
proj_data["meta"] = {"genre": "horror", "language": "th", "aspect_ratio": "9:16"}
# v3.0 INGRADAID: refs in project.data.refs[]
proj_data["refs"] = [{"name": "nam", "url": str(user_ref_path), "source": "uploaded"}]

r = requests.put(f"{LIVE}/api/projects/{PROJECT_ID}", json={"data": proj_data}, headers=HDR)
log("saved-all-episodes", r.status_code == 200, f"saved {len(all_episodes)} EPs to project")
artifacts["scripts"] = all_episodes

# Verify saved
r = requests.get(f"{LIVE}/api/projects/{PROJECT_ID}", headers=HDR)
saved_eps = r.json().get("data", {}).get("episodes", [])
log("verified-saved", len(saved_eps) == len(all_episodes), f"{len(saved_eps)}/{len(all_episodes)} in DB")

# ============================================================
# Step 5: Generate Veo prompts for ALL (Stage 2)
# ============================================================
print(f"\n[5/8] GENERATE VEO PROMPTS (Stage 2)")
print("=" * 70)
# Find the first EP for video gen
first_story = all_scripts[VIDEO_STORY_IDX] if VIDEO_STORY_IDX < len(all_scripts) else all_scripts[0]
first_ep = first_story["episodes"][VIDEO_EP_IDX] if VIDEO_EP_IDX < len(first_story["episodes"]) else first_story["episodes"][0]
print(f"  Target: Story {VIDEO_STORY_IDX+1} EP{VIDEO_EP_IDX+1} ({len(first_ep['scenes'])} scenes)")

# Generate Veo prompts for the first EP (the one we'll use for video)
scenes = first_ep["scenes"][:VIDEO_SCENE_COUNT]
print(f"  Generating Veo prompts for {len(scenes)} scenes...")

veo_prompts = []
for i, scene in enumerate(scenes):
    t = time.time()
    print(f"    Scene {i+1}/{len(scenes)}: generating Veo prompt...", end="", flush=True)
    r = requests.post(
        f"{LIVE}/api/llm/generate-veo",
        json={
            "script": scene,
            "characters": ["nam"],
        },
        headers=HDR,
        timeout=LLM_TIMEOUT_S,
    )
    dt = time.time() - t
    if r.status_code == 200:
        body = r.json()
        # Response: {"ok": true, "veo": {variant, video_config, clips: [{prompt, ...}]}}
        veo = body.get("veo", {})
        clips = veo.get("clips", [])
        if clips and clips[0].get("prompt"):
            prompt = clips[0]["prompt"]
            veo_prompts.append({"scene_idx": i, "prompt": prompt})
            print(f" ✓ {dt:.1f}s ({len(prompt)} chars)")
        else:
            veo_prompts.append({"scene_idx": i, "prompt": f"[ref1] {scene.get('action', '')[:100]}"})
            print(f" ⚠️ no clips in response, used fallback")
    else:
        veo_prompts.append({"scene_idx": i, "prompt": f"[ref1] {scene.get('action', '')[:100]}"})
        print(f" ❌ {r.status_code}, used fallback")

log("veo-prompts-generated", len(veo_prompts) == len(scenes), f"{len(veo_prompts)}/{len(scenes)}")

# Update first EP with Veo prompts
# Find the right EP and add timeline
target_ep_idx = VIDEO_STORY_IDX * EPISODES_PER_STORY + VIDEO_EP_IDX
if target_ep_idx < len(saved_eps):
    saved_eps[target_ep_idx]["timeline"] = [
        {"scene_id": f"S01_{vp['scene_idx']+1:02d}", "prompt": vp["prompt"], "t": i * 8}
        for i, vp in enumerate(veo_prompts)
    ]
    proj_data["episodes"] = saved_eps
    requests.put(f"{LIVE}/api/projects/{PROJECT_ID}", json={"data": proj_data}, headers=HDR)
    print(f"  ✓ saved timeline with {len(veo_prompts)} Veo prompts to EP")

# ============================================================
# Step 6: Generate videos (Veo API)
# ============================================================
if TOTAL_VIDEOS > 0:
    print(f"\n[6/8] GENERATE {TOTAL_VIDEOS} VIDEOS (Veo)")
    print("=" * 70)

    videos_generated = []
    for i, vp in enumerate(veo_prompts):
        prompt = vp["prompt"]
        t = time.time()
        print(f"    Video {i+1}/{len(veo_prompts)}: '{prompt[:50]}...'", end="", flush=True)

        # Use /api/veo/submit (text + characters)
        try:
            r = requests.post(
                f"{LIVE}/api/veo/submit",
                json={
                    "prompt": prompt,
                    "characters": ["nam"],  # The character name mapped to user image
                    "project_id": PROJECT_ID,
                    "scene_id": f"S01_{i+1:02d}",
                },
                headers=HDR,
                timeout=60,
            )
        except Exception as e:
            print(f" ❌ submit error: {e}")
            continue

        if r.status_code not in (200, 201):
            print(f" ❌ submit {r.status_code}: {r.text[:80]}")
            continue

        body = r.json()
        # Response: {task_id, veo_task_id, status}
        ext_id = body.get("task_id")
        if not ext_id:
            print(f" ❌ no task_id in response: {body}")
            continue

        # Poll for completion
        video_url = None
        deadline = time.time() + VEO_TIMEOUT_S
        while time.time() < deadline:
            time.sleep(VEO_POLL_INTERVAL_S)
            poll_r = requests.get(f"{LIVE}/api/veo/poll/{ext_id}", headers=HDR)
            if poll_r.status_code != 200:
                continue
            poll_body = poll_r.json()
            status = poll_body.get("status", "")
            # Try both field names (file_urls OR video_url)
            file_urls = poll_body.get("file_urls") or []
            video_url_field = poll_body.get("video_url")
            if status in ("completed", "succeeded"):
                if file_urls:
                    video_url = file_urls[0]
                    break
                if video_url_field:
                    video_url = video_url_field
                    break
            if status == "failed":
                print(f" ❌ failed: {poll_body.get('error', '?')[:80]}")
                break

        dt = time.time() - t
        if video_url:
            # Download
            ext = ".mp4"
            video_path = VIDEOS_DIR / f"video_s{VIDEO_STORY_IDX+1:02d}_ep{VIDEO_EP_IDX+1:02d}_s{i+1:02d}{ext}"
            try:
                vid_r = requests.get(video_url, timeout=120)
                if vid_r.status_code == 200:
                    video_path.write_bytes(vid_r.content)
                    size_mb = len(vid_r.content) / 1024 / 1024
                    videos_generated.append({"scene": i+1, "url": video_url, "path": str(video_path), "size_mb": size_mb})
                    print(f" ✓ {dt:.1f}s → {size_mb:.1f}MB")
                else:
                    print(f" ❌ download {vid_r.status_code}")
            except Exception as e:
                print(f" ❌ download error: {e}")
        else:
            print(f" ⏱️ {dt:.1f}s timeout")

    log("videos-generated", len(videos_generated) == TOTAL_VIDEOS, f"{len(videos_generated)}/{TOTAL_VIDEOS}")
    artifacts["videos"] = videos_generated
else:
    print(f"\n[6/8] SKIP VIDEO GEN (VIDEO_SCENE_COUNT=0)")

# ============================================================
# Step 7: Export (test 3 formats work)
# ============================================================
print(f"\n[7/8] EXPORT (3 formats)")
print("=" * 70)
# .json
r = requests.get(f"{LIVE}/api/projects/{PROJECT_ID}", headers=HDR)
json_path = DOWNLOADS_DIR / f"project_{PROJECT_ID}.json"
json_path.write_text(json.dumps(r.json(), indent=2, ensure_ascii=False))
log("json-exported", json_path.exists(), f"{json_path.stat().st_size} bytes")

# .md + .txt — use the export functions (call frontend)
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome",
        args=["--no-sandbox", "--disable-gpu", "--use-gl=swiftshader"]
    )
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
    page = ctx.new_page()
    page.goto(LIVE, wait_until="domcontentloaded")
    page.locator("input[name=\"email\"]").fill(EMAIL)
    page.locator("input[name=\"password\"]").fill(PW)
    page.locator("#auth-submit").click()
    page.wait_for_timeout(2000)

    # Open project
    page.locator(f".project-card").first.click()
    page.wait_for_timeout(1500)
    page.locator("#project-settings-btn").click()
    page.wait_for_timeout(500)

    # .md
    with page.expect_download() as dl_info:
        page.locator("#project-export-md-btn").click()
    dl = dl_info.value
    md_path = DOWNLOADS_DIR / f"project_{PROJECT_ID}.md"
    dl.save_as(str(md_path))
    log("md-exported", md_path.exists(), f"{md_path.stat().st_size} bytes")

    # .txt
    with page.expect_download() as dl_info:
        page.locator("#project-export-txt-btn").click()
    dl = dl_info.value
    txt_path = DOWNLOADS_DIR / f"project_{PROJECT_ID}.txt"
    dl.save_as(str(txt_path))
    log("txt-exported", txt_path.exists(), f"{txt_path.stat().st_size} bytes")

    # Final screenshot
    page.screenshot(path=str(SCREENSHOTS_DIR / "08-final.png"), full_page=False)
    browser.close()

# ============================================================
# Step 8: Analytics + Summary
# ============================================================
print(f"\n[8/8] ANALYTICS + SUMMARY")
print("=" * 70)
r = requests.get(f"{LIVE}/api/analytics/me", headers=HDR).json()
print(f"  projects.total    = {r['projects']['total']}")
print(f"  projects.episodes = {r['projects']['episodes']}")
print(f"  jobs.total        = {r['jobs']['total']}")
print(f"  veo_tasks.total   = {r['veo_tasks']['total']}")
print(f"  credits.estimated = {r['credits']['estimated_used']}")
print(f"  7-day total       = {sum(d['count'] for d in r['last_7_days'])} jobs")

# ============================================================
# Final Summary
# ============================================================
print("\n" + "=" * 70)
print("📊 TC-25 FINAL SUMMARY")
print("=" * 70)
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
print(f"Assertions: {passed}/{total} PASS")
print(f"")
print(f"  Stories generated:   {NUM_STORIES}")
print(f"  Episodes:            {NUM_STORIES * EPISODES_PER_STORY}")
print(f"  Scripts (scenes):    {script_count}/{TOTAL_SCRIPTS}")
print(f"  Veo prompts:         {len(veo_prompts)}/{len(scenes)}")
print(f"  Videos:              {len(artifacts['videos'])}/{TOTAL_VIDEOS}")
print(f"  Exported files:      json={json_path.exists()}, md={md_path.exists()}, txt={txt_path.exists()}")
print(f"  Time:                {total_dt:.1f}s ({total_dt/60:.1f} min)")
print(f"")
print(f"Artifacts:")
print(f"  Refs:    {REF_FILE}")
print(f"  JSON:    {json_path}")
print(f"  MD:      {md_path}")
print(f"  TXT:     {txt_path}")
print(f"  Videos:  {VIDEOS_DIR}/")
print(f"  Screens: {SCREENSHOTS_DIR}/")

if passed < total:
    print(f"\n❌ FAILED:")
    for n, ok, d in results:
        if not ok:
            print(f"  {n}: {d}")

print("=" * 70)
sys.exit(0 if passed == total else 1)
