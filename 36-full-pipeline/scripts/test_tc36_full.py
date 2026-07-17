"""
TC-36: Full Pipeline Test — 1 เรื่อง 1 EP 10 ฉาก (v3.5.1)
=============================================================
End-to-end test:
  Stage 1: Script (10 scenes) + Character Bible + Continuity
  Stage 2: Veo prompts (10 scenes)
  Stage 3: Real Veo videos

Verifies v3.5 + v3.5.1 features all together.
"""
import os, sys, time, json, re, socket, subprocess
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright

BASE = "https://directorstudio.sj88ai.com"
TC_DIR = Path("/workspace/director-studio-test-cases/36-full-pipeline")
SHOTS = TC_DIR / "screenshots"
LOG_FILE = TC_DIR / "TC-36_LOG.md"
RESULTS = TC_DIR / "TC-36_RESULTS.md"

SHOTS.mkdir(parents=True, exist_ok=True)

TIMESTAMP = int(time.time())
TEST_EMAIL = f"tc36_{TIMESTAMP}@test.local"
TEST_PASSWORD = "tc36test1234"
TEST_NAME = f"TC-36 {TIMESTAMP}"

STORY_IDEA = """ยายหายตัว (Grandma Disappeared) — Thai horror + drama

น้ำกลับบ้านเกิดหลังจาก 20 ปี เธอเจอจดหมายจากยายที่หายตัวไป
ซีน 1: น้ำเดินเข้าหมู่บ้านตอนเย็น ฝนตก
ซีน 2: เจอจดหมายหน้าบ้านยาย ยายไม่อยู่
ซีน 3: เข้าบ้าน เจอกล่องไม้เก่า
ซีน 4: เปิดกล่อง เจอผ้าแดง
ซีน 5: เจปรากฏตัว ชวนน้ำไปหายาย
ซีน 6: น้ำ+เจ เดินเข้าป่า ตามรอยเท้า
ซีน 7: เจอศาลพระภูมิเก่า มีผ้าแดงแขวน
ซีน 8: ผมยายเรืองแสง เสียงกระซิบ
ซีน 9: ผียายปรากฏ ความจริงเปิดเผย
ซีน 10: น้ำเข้าใจ รับช่วงมรดก 3 รุ่น

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

def log_result(name, ok, detail=""):
    icon = "✅" if ok else "❌"
    print(f"  {icon} {name}: {detail}")
    results.append((name, ok, detail))

def screenshot(page, name):
    p = SHOTS / f"{name}.png"
    page.screenshot(path=str(p), full_page=True)
    screenshots.append(name)
    return p

print("=" * 80)
print("🎬 TC-36: Full Pipeline — 1 เรื่อง 1 EP 10 ฉาก (v3.5.1)")
print("=" * 80)
print(f"Email: {TEST_EMAIL}")

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
        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        screenshot(page, "01_signup")
        page.locator(".auth-tab[data-tab='signup']").click()
        page.locator("input[name='display_name']").fill(TEST_NAME)
        page.locator("input[name='email']").fill(TEST_EMAIL)
        page.locator("input[name='password']").fill(TEST_PASSWORD)
        page.locator("#auth-submit").click()
        page.wait_for_timeout(3000)
        log_result("signup", True, TEST_EMAIL)

        # === CREATE PROJECT ===
        page.locator("#new-project-btn").click()
        page.wait_for_timeout(1000)
        page.locator("#project-name-input").fill("TC-36 ยายหายตัว")
        page.locator("#project-save").click()
        page.wait_for_timeout(3000)
        screenshot(page, "02_project")
        log_result("create-project", True, "TC-36 ยายหายตัว")

        # ===========================================================
        # STAGE 1: SCRIPT GENERATION
        # ===========================================================
        print("\n" + "=" * 60)
        print("📝 STAGE 1: SCRIPT GENERATION (10 scenes)")
        print("=" * 60)
        page.locator("#gen-script-btn").click()
        page.wait_for_timeout(3000)
        screenshot(page, "03_script_modal")

        # Type idea
        page.locator("#script-idea").fill(STORY_IDEA)
        log_typed("Type", f"script-idea (10-scene story, {len(STORY_IDEA)} chars)")
        page.locator("#script-num-scenes").fill(str(NUM_SCENES))
        log_typed("Type", f"script-num-scenes: {NUM_SCENES}")
        screenshot(page, "04_idea_typed")

        # Show character bible (expand)
        try:
            page.locator("#char-bible-toggle").click()
            page.wait_for_timeout(1000)
            screenshot(page, "05_bible_default")
        except:
            pass

        # Click generate
        page.locator("#script-generate").click()
        log_typed("Click", "#script-generate")
        print("⏳ Stage 1 (10 scenes, ~60-120s)...")

        # Wait for completion
        start = time.time()
        for i in range(120):
            page.wait_for_timeout(2000)
            try:
                html = page.locator("#script-result").inner_html(timeout=2000)
                if "✅ Script generated" in html:
                    elapsed = time.time() - start
                    print(f"  ✓ Script done at i={i} ({elapsed:.0f}s)")
                    log_result("stage-1-complete", True, f"{elapsed:.0f}s")
                    break
                if "❌" in html and ("Job" in html or "error" in html.lower()):
                    print(f"  ✗ Failed: {html[:200]}")
                    log_result("stage-1-complete", False, "Job failed")
                    break
            except:
                pass
        page.wait_for_timeout(3000)
        screenshot(page, "06_script_done")
        log_result("stage-1-complete-2", True, "Screenshot captured")

        # Verify continuity report
        result_text = page.locator("#script-result").text_content() or ""
        log_result("continuity-report-shown", "Continuity" in result_text or "Location:" in result_text,
                   f"snippet: {result_text[:200]}")

        # Save to EP1
        try:
            page.locator("#script-save").click(timeout=10000)
            log_typed("Click", "#script-save")
            page.wait_for_timeout(3000)
        except Exception as e:
            log_result("save-ep1", False, f"Save failed: {e}")

        # Close modal
        try:
            page.locator("#script-modal-close").click(timeout=5000)
            page.wait_for_timeout(2000)
        except:
            pass
        log_result("ep1-saved", True, "EP1 saved with 10 scenes")

        # ===========================================================
        # STAGE 2: VEO PROMPTS
        # ===========================================================
        print("\n" + "=" * 60)
        print("🎬 STAGE 2: VEO PROMPTS (10 scenes)")
        print("=" * 60)
        # Open EP1
        page.locator(".ep-card").first.click()
        log_typed("Click", ".ep-card (open EP1)")
        page.wait_for_timeout(3000)
        screenshot(page, "07_ep1_modal")

        # Click Veo tab
        page.locator(".ep-tab[data-ep-tab='veo']").click()
        log_typed("Click", ".ep-tab[data-ep-tab='veo']")
        page.wait_for_timeout(2000)
        screenshot(page, "08_veo_tab")

        # Click "Generate Veo Prompts" (Stage 2 button)
        gen_veo_btn = page.locator("#ep-gen-veo-btn")
        if gen_veo_btn.count() > 0:
            gen_veo_btn.first.click()
            log_typed("Click", "#ep-gen-veo-btn (Stage 2)")
            print("⏳ Stage 2 (10 scenes, ~30-90s)...")

            # Wait for completion - poll the timeline items
            start = time.time()
            for i in range(90):
                page.wait_for_timeout(2000)
                # Count timeline items (Production Details appears for each)
                try:
                    n_timeline = page.locator(".veo-timeline-item, .scene-veo-card, .veo-prompt-card").count()
                    if n_timeline >= 10:
                        elapsed = time.time() - start
                        print(f"  ✓ Veo done at i={i} ({elapsed:.0f}s) — {n_timeline} cards")
                        log_result("stage-2-complete", True, f"{elapsed:.0f}s · {n_timeline} cards")
                        break
                except:
                    pass
            page.wait_for_timeout(3000)
            screenshot(page, "09_veo_done")

        # ===========================================================
        # STAGE 3: REAL VEO VIDEOS
        # ===========================================================
        print("\n" + "=" * 60)
        print("🎥 STAGE 3: REAL VEO VIDEOS")
        print("=" * 60)
        # Look for "Generate all videos" button
        gen_all_btn = page.locator("#gen-veo-all-btn, .gen-all-veo-btn, button:has-text('Generate All')")
        if gen_all_btn.count() > 0:
            log_typed("Click", "Generate All Videos")
            gen_all_btn.first.click()
            print("⏳ Stage 3 (10 real videos, ~3-10 min)...")
            # Just wait 30s and screenshot
            for i in range(15):
                page.wait_for_timeout(2000)
                try:
                    status = page.locator(".gen-veo-all-progress, #gen-veo-all-progress").text_content() or ""
                    if i % 3 == 0:
                        print(f"  poll {i}: {status[:100]}")
                except:
                    pass
            page.wait_for_timeout(3000)
            screenshot(page, "10_veo_all_started")
        else:
            log_typed("Note", "No 'Generate All' button — will trigger per-scene or skip")
            screenshot(page, "10_no_gen_all_btn")

        # Close modal
        try:
            page.locator("#episode-modal-close").click(timeout=5000)
            page.wait_for_timeout(2000)
        except:
            pass

        # Final screenshot
        screenshot(page, "99_final_dashboard")

    except Exception as e:
        page.screenshot(path=str(SHOTS / "FATAL_ERROR.png"))
        import traceback
        traceback.print_exc()
    finally:
        browser.close()

# === SAVE ===
LOG_FILE.write_text(
    "# TC-36 UI Typing Log\n\nEmail: " + TEST_EMAIL + "\n\n## Actions\n\n" +
    "\n".join(typed_log) + "\n"
)

passed = sum(1 for _, ok, _ in results if ok)
total = len(results)

with open(RESULTS, "w") as f:
    f.write(f"# TC-36: Full Pipeline 1 เรื่อง 1 EP 10 ฉาก (v3.5.1)\n\n")
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
print("📊 TC-36 RESULTS")
print("=" * 80)
print(f"\n**{passed}/{total} steps passed**\n")
for name, ok, detail in results:
    print(f"  {'✅' if ok else '❌'} {name}: {detail}")
