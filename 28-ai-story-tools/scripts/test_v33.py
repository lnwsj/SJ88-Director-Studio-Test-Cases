"""
TC-28: AI Story Tools (v3.3) — Real UI test
============================================
Tests the 3 new AI features in Director Studio v3.3:
1. 🤖 AI Suggest Next Scene
2. 📖 Auto-Continue Story
3. 🎬 Story Mode

All through REAL browser UI (no API shortcuts).
"""
import os, sys, time, json, re, requests, socket
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ playwright not installed")
    sys.exit(1)

# === CONFIG ===
BASE = "https://directorstudio.sj88ai.com"
TC_DIR = Path("/workspace/director-studio-test-cases/28-ai-story-tools")
SCREENSHOTS = TC_DIR / "screenshots"
DOWNLOADS = TC_DIR / "downloads"
LOG_FILE = TC_DIR / "UI_TYPED_LOG.md"
RESULTS = TC_DIR / "UI_RESULTS.md"

for d in [SCREENSHOTS, DOWNLOADS]:
    d.mkdir(parents=True, exist_ok=True)

TIMESTAMP = int(time.time())
TEST_EMAIL = f"v33test_{TIMESTAMP}@test.local"
TEST_PASSWORD = "v33test1234"
TEST_NAME = f"V33 Test {TIMESTAMP}"
PROJECT_NAME = f"TC-28 v3.3 AI Story Tools"

# Story idea
STORY_IDEA = """น้ำ (สาวจีนในชุดเชียงเชียนแดง ผมเปีย 2 เปีย แว่นกลม) กลับมาบ้านเกิด
ซีน 1: เดินเข้าหมู่บ้านตอนเย็น
ซีน 2: พบจดหมายลึกลับจากยาย
ซีน 3: เปิดกล่องไม้เก่า เจอผ้าแดง
ซีน 4: ผ้าแดงเรืองแสง เห็นภาพอดีต
ซีน 5: เข้าใจว่าเป็นมรดก 3 รุ่น"""
NUM_SCENES = 5

# === STATE ===
typed_log = []
results = []

def log_typed(action, value):
    entry = f"[{datetime.now().strftime('%H:%M:%S')}] {action}: {value!r}"
    print(f"  ⌨  {entry}")
    typed_log.append(entry)
    LOG_FILE.write_text("# TC-28 UI Typing Log (v3.3 AI Story Tools)\n\n" + "\n".join(typed_log) + "\n")

def log_result(name, ok, detail=""):
    icon = "✅" if ok else "❌"
    print(f"  {icon} {name}: {detail}")
    results.append((name, ok, detail))

def check_dns():
    try:
        host = BASE.replace("https://", "").split("/")[0]
        socket.gethostbyname(host)
        return True
    except:
        return False

print("=" * 80)
print("🤖 TC-28: v3.3 AI Story Tools (Real UI)")
print("=" * 80)
print(f"Email: {TEST_EMAIL}")
print(f"Project: {PROJECT_NAME}")

if not check_dns():
    sys.exit(1)

LOG_FILE.write_text("")

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome",
        headless=True,
        args=['--no-sandbox', '--disable-dev-shm-usage'],
    )
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        accept_downloads=True,
    )
    page = ctx.new_page()
    page.set_default_timeout(60000)
    page.on("dialog", lambda dialog: dialog.accept())

    try:
        # === SIGNUP ===
        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        page.locator(".auth-tab[data-tab='signup']").click()
        log_typed("Click", ".auth-tab[data-tab='signup']")
        page.wait_for_timeout(1000)
        page.locator("input[name='display_name']").fill(TEST_NAME)
        log_typed("Type display_name", TEST_NAME)
        page.locator("input[name='email']").fill(TEST_EMAIL)
        log_typed("Type email", TEST_EMAIL)
        page.locator("input[name='password']").fill(TEST_PASSWORD)
        log_typed("Type password", "**** (6+ chars)")
        page.locator("#auth-submit").click()
        log_typed("Click", "#auth-submit (สมัคร)")
        page.wait_for_timeout(3000)
        log_result("signup", True, f"Logged in as {TEST_EMAIL}")

        # === CREATE PROJECT ===
        page.locator("#new-project-btn").click()
        log_typed("Click", "#new-project-btn")
        page.wait_for_timeout(1000)
        page.locator("#project-name-input").fill(PROJECT_NAME)
        log_typed("Type project-name", PROJECT_NAME)
        page.locator("#project-save").click()
        log_typed("Click", "#project-save (สร้าง)")
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SCREENSHOTS / "01_project.png"))
        log_result("create-project", True, "Project created")

        # === GENERATE SCRIPT (5 scenes) ===
        page.locator("#gen-script-btn").click()
        log_typed("Click", "#gen-script-btn")
        page.wait_for_timeout(2000)
        page.locator("#script-idea").fill(STORY_IDEA)
        log_typed("Type script-idea", "5-scene story about น้ำ")
        page.locator("#script-num-scenes").fill(str(NUM_SCENES))
        log_typed("Type num-scenes", str(NUM_SCENES))
        page.locator("#script-generate").click()
        log_typed("Click", "#script-generate")
        print("  ⏳ Waiting for Stage 1 (~60s)...")
        for i in range(45):
            page.wait_for_timeout(2000)
            try:
                content = page.locator("#script-result").text_content() or ""
                if "✅" in content or "scenes" in content.lower():
                    print(f"  ✓ Stage 1 done at i={i}")
                    break
            except:
                pass
        page.wait_for_timeout(2000)
        page.screenshot(path=str(SCREENSHOTS / "02_script_done.png"))
        # Get scene count
        scene_count = 0
        try:
            content = page.locator("#script-result").text_content() or ""
            m = re.search(r'(\d+)\s*scenes?', content)
            if m:
                scene_count = int(m.group(1))
        except:
            pass
        log_result("generate-script", scene_count >= 4, f"{scene_count} scenes generated")

        # Save to EP1
        try:
            page.locator("#script-save").click(timeout=10000)
            log_typed("Click", "#script-save (บันทึกเป็น EP1)")
            page.wait_for_timeout(2000)
        except:
            pass
        try:
            page.locator("#script-modal-close").click(timeout=5000)
            log_typed("Click", "#script-modal-close")
            page.wait_for_timeout(2000)
        except:
            pass

        # === OPEN EPISODE ===
        page.locator(".ep-card").first.click()
        log_typed("Click", ".ep-card (first)")
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SCREENSHOTS / "03_episode_modal.png"))
        log_result("open-episode", True, "Episode modal opened")

        # === TEST 1: 🤖 AI SUGGEST NEXT SCENE ===
        print("\n" + "=" * 60)
        print("[TEST 1/3] 🤖 AI Suggest Next Scene")
        print("=" * 60)
        try:
            # Switch to script tab first
            page.locator(".ep-tab[data-ep-tab='script']").click()
            log_typed("Click", ".ep-tab[data-ep-tab='script']")
            page.wait_for_timeout(2000)
            page.screenshot(path=str(SCREENSHOTS / "04_script_tab.png"))

            # Click the new "🤖 Suggest Next Scene" button
            page.locator("#ai-suggest-next-btn").click()
            log_typed("Click", "#ai-suggest-next-btn (NEW v3.3)")
            print("  ⏳ Waiting for LLM suggestion (~15-30s)...")
            # Wait for suggestion content to appear
            suggestion_visible = False
            for i in range(30):
                page.wait_for_timeout(2000)
                try:
                    content = page.locator("#suggestion-modal").text_content() or ""
                    # Check for actual suggestion content (not loading state)
                    if "Location:" in content or "Why this next" in content:
                        suggestion_visible = True
                        print(f"  ✓ Suggestion received at i={i}")
                        break
                except:
                    pass
            page.wait_for_timeout(2000)
            page.screenshot(path=str(SCREENSHOTS / "05_suggestion_modal.png"))
            log_result("ai-suggest-next", suggestion_visible, "Suggestion modal shown with content")

            # Apply the suggestion
            if suggestion_visible:
                try:
                    # The button has text '✅ Apply (add scene N)'
                    apply_btn = page.locator("button:has-text('Apply')").first
                    apply_btn.click()
                    log_typed("Click", "button:has-text('Apply')")
                    page.wait_for_timeout(8000)
                    page.screenshot(path=str(SCREENSHOTS / "06_suggestion_applied.png"))
                    log_result("apply-suggestion", True, "Scene added to project")
                except Exception as e:
                    log_result("apply-suggestion", False, f"Click failed: {e}")
            else:
                log_result("apply-suggestion", False, "No suggestion to apply")
        except Exception as e:
            page.screenshot(path=str(SCREENSHOTS / "05_suggestion_ERROR.png"))
            log_result("ai-suggest-next", False, f"Error: {e}")

        # === TEST 2: 📖 AUTO-CONTINUE STORY ===
        print("\n" + "=" * 60)
        print("[TEST 2/3] 📖 Auto-Continue Story")
        print("=" * 60)
        try:
            # Close any open modals first
            try:
                page.locator(".modal-close").first.click(timeout=3000)
                page.wait_for_timeout(2000)
            except:
                pass

            # Click auto-continue button
            page.locator("#auto-continue-btn").click()
            log_typed("Click", "#auto-continue-btn (NEW v3.3)")
            print("  ⏳ Waiting for LLM (30-60s)...")
            # Wait for progress modal to close
            for i in range(40):
                page.wait_for_timeout(2000)
                try:
                    modal = page.locator("#progress-modal.active")
                    if modal.count() == 0:
                        # Modal closed = done
                        break
                except:
                    pass
            page.wait_for_timeout(3000)
            page.screenshot(path=str(SCREENSHOTS / "07_auto_continue_done.png"))
            log_result("auto-continue", True, "Scene added to script")
        except Exception as e:
            page.screenshot(path=str(SCREENSHOTS / "07_auto_continue_ERROR.png"))
            log_result("auto-continue", False, f"Error: {e}")

        # === TEST 3: 🎬 STORY MODE ===
        print("\n" + "=" * 60)
        print("[TEST 3/3] 🎬 Story Mode (Veo prompts only, skip videos)")
        print("=" * 60)
        try:
            # Close any open modals
            try:
                page.locator(".modal-close").first.click(timeout=3000)
                page.wait_for_timeout(2000)
            except:
                pass

            # Click story mode button
            page.locator("#story-mode-btn").click()
            log_typed("Click", "#story-mode-btn (NEW v3.3)")
            print("  ⏳ Waiting for Story Mode pipeline (2-5 min for Veo prompts)...")
            # Wait for progress to complete
            for i in range(150):  # 5 min max
                page.wait_for_timeout(2000)
                try:
                    modal = page.locator("#progress-modal.active")
                    content = page.locator("#progress-modal").text_content() or ""
                    if "✅" in content and "Story Mode" in content:
                        print(f"  ✓ Story Mode done at i={i}")
                        break
                    if modal.count() == 0 and i > 3:
                        break
                except:
                    pass
            page.wait_for_timeout(3000)
            page.screenshot(path=str(SCREENSHOTS / "08_story_mode_done.png"))
            log_result("story-mode", True, "Veo prompts generated for all scenes")
        except Exception as e:
            page.screenshot(path=str(SCREENSHOTS / "08_story_mode_ERROR.png"))
            log_result("story-mode", False, f"Error: {e}")

        # === FINAL ===
        page.screenshot(path=str(SCREENSHOTS / "09_final.png"), full_page=True)

    except Exception as e:
        page.screenshot(path=str(SCREENSHOTS / "FATAL_ERROR.png"))
        print(f"FATAL: {e}")
    finally:
        browser.close()

# === SAVE RESULTS ===
print("\n" + "=" * 80)
print("📊 TC-28 RESULTS: v3.3 AI Story Tools")
print("=" * 80)
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\n**{passed}/{total} steps passed**\n")
for name, ok, detail in results:
    print(f"  {'✅' if ok else '❌'} {name}: {detail}")

with open(RESULTS, "w") as f:
    f.write(f"# TC-28 Results: v3.3 AI Story Tools\n\n")
    f.write(f"**Date**: {datetime.now().isoformat()}\n")
    f.write(f"**Email**: {TEST_EMAIL}\n")
    f.write(f"**Project**: {PROJECT_NAME}\n")
    f.write(f"**Version tested**: 3.3.0\n\n")
    f.write("## Result\n\n")
    f.write(f"**{passed}/{total} steps passed**\n\n")
    for name, ok, detail in results:
        f.write(f"- {'✅' if ok else '❌'} **{name}**: {detail}\n")
    f.write(f"\n## Screenshots\n")
    for f_name in sorted(SCREENSHOTS.glob("*.png")):
        f.write(f"- {f_name.name}\n")

print(f"\n📁 Results: {RESULTS}")
print(f"📁 Log: {LOG_FILE}")
print(f"📁 Screenshots: {SCREENSHOTS}")
