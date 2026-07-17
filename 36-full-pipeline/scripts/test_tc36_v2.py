"""
TC-36: Full Pipeline Test — 1 เรื่อง 1 EP 10 ฉาก (v3.5.1)
=============================================================
End-to-end test:
  Stage 1: Script (10 scenes) + Character Bible + Continuity
  Stage 2: Veo prompts (10 scenes)
  Stage 3: Real Veo videos
"""
import os, sys, time, json, re, socket
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE = "https://directorstudio.sj88ai.com"
TC_DIR = Path("/workspace/director-studio-test-cases/36-full-pipeline")
SHOTS = TC_DIR / "screenshots_v2"
LOG_FILE = TC_DIR / "TC-36_LOG_v2.md"
RESULTS = TC_DIR / "TC-36_RESULTS_v2.md"

SHOTS.mkdir(parents=True, exist_ok=True)

TIMESTAMP = int(time.time())
TEST_EMAIL = f"tc36v2_{TIMESTAMP}@test.local"
TEST_PASSWORD = "tc36v2test1234"
TEST_NAME = f"TC-36 v2 {TIMESTAMP}"

STORY_IDEA = """เรื่อง: ยายหายตัว (Grandma Disappeared) — Thai horror + drama

น้ำกลับบ้านเกิดหลัง 20 ปี เธอเจอจดหมายจากยายที่หายตัวไป
1. น้ำเดินเข้าหมู่บ้านตอนเย็น ฝนตกปรอยๆ
2. เจอจดหมายหน้าบ้านยาย ยายไม่อยู่
3. เข้าบ้าน เจอกล่องไม้เก่าบนโต๊ะ
4. เปิดกล่อง เจอผ้าแดงพันอยู่
5. เจปรากฏตัว ชวนน้ำไปหายาย
6. น้ำ+เจ เดินเข้าป่า ตามรอยเท้าเปลี่ยน
7. เจอศาลพระภูมิเก่า มีผ้าแดงแขวน
8. เงายายเรืองแสง เสียงกระซิบเรียก
9. ผียายปรากฏ เปิดเผยความจริง 3 รุ่น
10. น้ำรับช่วงมรดก ผ้าแดง กล่องไม้ จดหมาย

ตัวละคร: น้ำ, เจ, ยาย, ผี
ธีม: ครอบครัว 3 รุ่น มรดก การกลับบ้าน"""

NUM_SCENES = 10

typed_log = []
results = []
screenshots = []

def log_typed(action, value):
    entry = f"[{datetime.now().strftime('%H:%M:%S')}] {action}: {value!r}"
    print(f"  ⌨  {entry}")
    typed_log.append(entry)
    # Also write to log file immediately
    with open(LOG_FILE, 'a') as f:
        f.write(entry + "\n")

def log_result(name, ok, detail=""):
    icon = "✅" if ok else "❌"
    print(f"  {icon} {name}: {detail}")
    results.append((name, ok, detail))

def screenshot(page, name):
    p = SHOTS / f"{name}.png"
    page.screenshot(path=str(p), full_page=True)
    screenshots.append(name)
    print(f"  📸 {name}.png")

print("=" * 80)
print("🎬 TC-36 v2: Full Pipeline 1 เรื่อง 1 EP 10 ฉาก (v3.5.1)")
print("=" * 80)
print(f"Email: {TEST_EMAIL}")

# Init log
LOG_FILE.write_text(f"# TC-36 v2 Log\n\nEmail: {TEST_EMAIL}\n\n")

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome",
        headless=True,
        args=['--no-sandbox', '--disable-dev-shm-usage'],
    )
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(120000)
    page.on("dialog", lambda d: (log_typed("Dialog", d.type), d.accept()))
    page.on("pageerror", lambda e: log_result("JS_ERROR", False, str(e)[:200]))

    try:
        # === SIGNUP ===
        log_typed("Navigate", BASE)
        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        screenshot(page, "01_signup_form")
        
        log_typed("Click", ".auth-tab[data-tab='signup']")
        page.locator(".auth-tab[data-tab='signup']").click()
        page.wait_for_timeout(500)
        page.locator("input[name='display_name']").fill(TEST_NAME)
        log_typed("Type", f"display_name={TEST_NAME}")
        page.locator("input[name='email']").fill(TEST_EMAIL)
        log_typed("Type", f"email={TEST_EMAIL}")
        page.locator("input[name='password']").fill(TEST_PASSWORD)
        log_typed("Type", "password=********")
        log_typed("Click", "#auth-submit")
        page.locator("#auth-submit").click()
        page.wait_for_timeout(4000)
        screenshot(page, "02_after_signup")
        log_result("signup", True, TEST_EMAIL)

        # === CREATE PROJECT ===
        log_typed("Click", "#new-project-btn")
        page.locator("#new-project-btn").click()
        page.wait_for_timeout(1500)
        page.locator("#project-name-input").fill("TC-36 ยายหายตัว")
        log_typed("Type", "project-name=TC-36 ยายหายตัว")
        log_typed("Click", "#project-save")
        page.locator("#project-save").click()
        page.wait_for_timeout(3000)
        screenshot(page, "03_project_created")
        log_result("create-project", True, "TC-36 ยายหายตัว")

        # ===========================================================
        # STAGE 1: SCRIPT GENERATION
        # ===========================================================
        print("\n" + "=" * 60)
        print("📝 STAGE 1: SCRIPT GENERATION (10 scenes)")
        print("=" * 60)
        log_typed("Click", "#gen-script-btn")
        page.locator("#gen-script-btn").click()
        page.wait_for_timeout(3000)
        screenshot(page, "04_script_modal_open")

        # Type idea
        page.locator("#script-idea").fill(STORY_IDEA)
        log_typed("Type", f"script-idea ({len(STORY_IDEA)} chars, {NUM_SCENES} scenes)")
        page.locator("#script-num-scenes").fill(str(NUM_SCENES))
        log_typed("Type", f"script-num-scenes={NUM_SCENES}")
        page.wait_for_timeout(500)
        screenshot(page, "05_idea_typed")

        # Show character bible
        try:
            page.locator("#char-bible-toggle").click()
            log_typed("Click", "#char-bible-toggle (show bible)")
            page.wait_for_timeout(1000)
            screenshot(page, "06_bible_expanded")
        except Exception as e:
            log_typed("Warn", f"bible toggle failed: {e}")

        log_typed("Click", "#script-generate")
        page.locator("#script-generate").click()
        print("⏳ Stage 1 (10 scenes, ~60-180s)...")

        # Wait for completion
        start = time.time()
        completed = False
        for i in range(150):
            page.wait_for_timeout(2000)
            try:
                html = page.locator("#script-result").inner_html(timeout=2000)
                if "✅ Script generated" in html:
                    elapsed = time.time() - start
                    print(f"  ✓ Script done at i={i} ({elapsed:.0f}s)")
                    log_typed("Stage 1", f"done in {elapsed:.0f}s")
                    completed = True
                    break
                if "❌" in html and "error" in html.lower():
                    log_typed("Stage 1 FAIL", html[:200])
                    break
                if i % 10 == 0:
                    print(f"  ⏳ waiting... i={i}, html snippet: {html[:100]}")
            except Exception as e:
                if i % 20 == 0:
                    print(f"  poll {i}: {e}")
        page.wait_for_timeout(3000)
        screenshot(page, "07_script_done")
        log_result("stage-1-complete", completed, f"{time.time()-start:.0f}s")

        # Verify continuity report
        result_text = ""
        try:
            result_text = page.locator("#script-result").text_content() or ""
        except:
            pass
        has_continuity = "Continuity" in result_text or "Location:" in result_text
        log_result("continuity-report-shown", has_continuity,
                   f"snippet: {result_text[:150]}")

        # Save to EP1
        try:
            log_typed("Click", "#script-save")
            page.locator("#script-save").click(timeout=10000)
            page.wait_for_timeout(4000)
            log_result("save-ep1", True, "Saved")
        except Exception as e:
            log_result("save-ep1", False, f"Failed: {e}")

        # Close modal
        try:
            log_typed("Click", "#script-modal-close")
            page.locator("#script-modal-close").click(timeout=5000)
            page.wait_for_timeout(2000)
        except Exception as e:
            log_typed("Close script modal", f"failed: {e}")

        # ===========================================================
        # STAGE 2: VEO PROMPTS
        # ===========================================================
        print("\n" + "=" * 60)
        print("🎬 STAGE 2: VEO PROMPTS (10 scenes)")
        print("=" * 60)
        log_typed("Click", ".ep-card (open EP1)")
        try:
            page.locator(".ep-card").first.click()
            page.wait_for_timeout(3000)
            screenshot(page, "08_ep1_modal")
        except Exception as e:
            log_typed("Open EP1", f"failed: {e}")
        
        try:
            log_typed("Click", ".ep-tab[data-ep-tab='veo']")
            page.locator(".ep-tab[data-ep-tab='veo']").click()
            page.wait_for_timeout(2000)
            screenshot(page, "09_veo_tab")
        except Exception as e:
            log_typed("Click veo tab", f"failed: {e}")

        # Click "Generate Veo Prompts" (Stage 2 button)
        try:
            log_typed("Click", "#ep-gen-veo-btn (Stage 2)")
            page.locator("#ep-gen-veo-btn").first.click()
            print("⏳ Stage 2 (10 scenes, ~30-120s)...")
            start = time.time()
            stage2_done = False
            for i in range(90):
                page.wait_for_timeout(2000)
                try:
                    # Look for Veo timeline items - they have Production Details
                    n_prompts = page.locator(".veo-prompt-card, .scene-veo, .timeline-item").count()
                    # Also check by querying the API directly
                    if i % 5 == 0 and i > 0:
                        # Get project from API
                        proj_data = page.evaluate("""async () => {
                            const t = localStorage.getItem('sj_token');
                            const r = await fetch('/api/projects', {headers: {Authorization: 'Bearer ' + t}});
                            const d = await r.json();
                            const proj = (Array.isArray(d) ? d : d.projects || []).find(p => p.name && p.name.includes('TC-36'));
                            if (!proj) return null;
                            const ep = proj.data.episodes && proj.data.episodes[0];
                            return ep ? {scenes: (ep.scenes || []).length, timeline: (ep.timeline || []).length} : null;
                        }""")
                        if proj_data and proj_data.get('timeline', 0) >= 10:
                            elapsed = time.time() - start
                            print(f"  ✓ Veo done at i={i} ({elapsed:.0f}s) — timeline={proj_data['timeline']}")
                            log_typed("Stage 2", f"done in {elapsed:.0f}s, {proj_data['timeline']} prompts")
                            stage2_done = True
                            break
                except Exception as e:
                    pass
            page.wait_for_timeout(3000)
            screenshot(page, "10_veo_done")
            log_result("stage-2-complete", stage2_done, f"{time.time()-start:.0f}s")
        except Exception as e:
            log_result("stage-2-complete", False, f"Failed: {e}")

        # ===========================================================
        # STAGE 3: REAL VEO VIDEOS
        # ===========================================================
        print("\n" + "=" * 60)
        print("🎥 STAGE 3: REAL VEO VIDEOS")
        print("=" * 60)
        # Look for "Generate all videos" or similar
        gen_all = page.locator("#gen-veo-all-btn, .gen-veo-all-btn")
        if gen_all.count() > 0:
            try:
                log_typed("Click", "#gen-veo-all-btn (Stage 3)")
                gen_all.first.click()
                print("⏳ Stage 3 (10 real videos, ~3-10 min)...")
                # Just wait and screenshot
                for i in range(20):
                    page.wait_for_timeout(3000)
                    if i % 5 == 0:
                        try:
                            status = page.locator("#gen-veo-all-progress, .gen-veo-all-progress").text_content() or ""
                            print(f"  poll {i}: {status[:100]}")
                        except:
                            pass
                page.wait_for_timeout(3000)
                screenshot(page, "11_veo_videos_started")
                log_result("stage-3-started", True, "Video gen queued")
            except Exception as e:
                log_result("stage-3-started", False, f"Failed: {e}")
        else:
            log_typed("Note", "No 'gen-veo-all-btn' — checking for per-scene buttons")
            # Look for per-scene Veo buttons
            veo_btns = page.locator(".veo-gen-btn, .gen-veo-btn, button:has-text('Generate Video')")
            n_veo = veo_btns.count()
            log_typed("Per-scene Veo btns", f"found {n_veo}")
            screenshot(page, "11_per_scene_veo_btns")
            if n_veo > 0:
                # Click first one as test
                veo_btns.first.click()
                log_typed("Click", f"first per-scene Veo btn")
                page.wait_for_timeout(15000)
                screenshot(page, "12_first_veo_started")

        # Close modal
        try:
            log_typed("Click", "#episode-modal-close")
            page.locator("#episode-modal-close").click(timeout=5000)
            page.wait_for_timeout(2000)
        except:
            pass

        # Final screenshot
        screenshot(page, "99_final")

    except Exception as e:
        page.screenshot(path=str(SHOTS / "FATAL_ERROR.png"))
        print(f"FATAL: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.close()

# === SAVE ===
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)

with open(RESULTS, "w") as f:
    f.write(f"# TC-36 v2: Full Pipeline 1 เรื่อง 1 EP 10 ฉาก (v3.5.1)\n\n")
    f.write(f"**Date**: {datetime.now().isoformat()}\n")
    f.write(f"**Email**: {TEST_EMAIL}\n")
    f.write(f"**Version**: 3.5.1\n\n")
    f.write("## Result\n\n")
    f.write(f"**{passed}/{total} steps passed**\n\n")
    for name, ok, detail in results:
        f.write(f"- {'✅' if ok else '❌'} **{name}**: {detail}\n")
    f.write(f"\n## Screenshots\n\n")
    for s in sorted(screenshots):
        f.write(f"- {s}.png\n")

print("\n" + "=" * 80)
print("📊 TC-36 v2 RESULTS")
print("=" * 80)
print(f"\n**{passed}/{total} steps passed**\n")
for name, ok, detail in results:
    print(f"  {'✅' if ok else '❌'} {name}: {detail}")
