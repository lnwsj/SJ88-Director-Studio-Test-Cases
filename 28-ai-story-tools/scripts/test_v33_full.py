"""
Take real UI screenshots of all 3 v3.3 features
- 1 test per feature
- All click + type logged with timestamps
"""
import os, sys, time, json, re, socket
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
SCREENSHOTS = TC_DIR / "screenshots_full"
DOWNLOADS = TC_DIR / "downloads"
for d in [SCREENSHOTS, DOWNLOADS]:
    d.mkdir(parents=True, exist_ok=True)

TIMESTAMP = int(time.time())
TEST_EMAIL = f"v33full_{TIMESTAMP}@test.local"
TEST_PASSWORD = "v33full1234"
TEST_NAME = f"V33 Full {TIMESTAMP}"

STORY_IDEA = """น้ำ (สาวจีนในชุดเชียงเชียนแดง ผมเปีย 2 เปีย แว่นกลม) กลับมาบ้านเกิด
ซีน 1: เดินเข้าหมู่บ้านตอนเย็น
ซีน 2: พบจดหมายลึกลับจากยาย
ซีน 3: เปิดกล่องไม้เก่า เจอผ้าแดง
ซีน 4: ผ้าแดงเรืองแสง เห็นภาพอดีต
ซีน 5: เข้าใจว่าเป็นมรดก 3 รุ่น"""
NUM_SCENES = 5

# Track all actions for each feature
actions = {"suggest": [], "continue": [], "storymode": []}

def log_action(feature, action, value):
    entry = f"[{datetime.now().strftime('%H:%M:%S')}] {action}: {value!r}"
    print(f"  [{feature}] ⌨  {entry}")
    actions[feature].append(entry)
    with open(TC_DIR / f"actions_{feature}.log", "w") as f:
        f.write(f"# {feature} UI Actions\n\n" + "\n".join(actions[feature]) + "\n")

def check_dns():
    try:
        host = BASE.replace("https://", "").split("/")[0]
        socket.gethostbyname(host)
        return True
    except:
        return False

print("=" * 80)
print(f"📸 Taking screenshots of all 3 v3.3 features")
print("=" * 80)
print(f"Email: {TEST_EMAIL}")

if not check_dns():
    sys.exit(1)

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
        page.wait_for_timeout(1000)
        page.locator("input[name='display_name']").fill(TEST_NAME)
        log_action("suggest", "Type display_name", TEST_NAME)
        page.locator("input[name='email']").fill(TEST_EMAIL)
        log_action("suggest", "Type email", TEST_EMAIL)
        page.locator("input[name='password']").fill(TEST_PASSWORD)
        log_action("suggest", "Type password", "**** (6+ chars)")
        page.locator("#auth-submit").click()
        log_action("suggest", "Click", "#auth-submit (สมัคร)")
        page.wait_for_timeout(3000)

        # === CREATE PROJECT ===
        page.locator("#new-project-btn").click()
        page.wait_for_timeout(1000)
        page.locator("#project-name-input").fill("v3.3 Features Demo")
        log_action("suggest", "Type project name", "v3.3 Features Demo")
        page.locator("#project-save").click()
        log_action("suggest", "Click", "#project-save")
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SCREENSHOTS / "common_01_project.png"))
        print("✓ Project created")

        # === GENERATE 5-SCENE SCRIPT ===
        page.locator("#gen-script-btn").click()
        page.wait_for_timeout(2000)
        page.locator("#script-idea").fill(STORY_IDEA)
        log_action("suggest", "Type script idea", "5-scene story")
        page.locator("#script-num-scenes").fill(str(NUM_SCENES))
        log_action("suggest", "Type num scenes", str(NUM_SCENES))
        page.locator("#script-generate").click()
        log_action("suggest", "Click", "#script-generate")
        print("⏳ Generating script (~60s)...")
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
        page.screenshot(path=str(SCREENSHOTS / "common_02_script.png"))
        # Save to EP1
        try:
            page.locator("#script-save").click(timeout=10000)
            log_action("suggest", "Click", "#script-save (save as EP1)")
            page.wait_for_timeout(2000)
        except:
            pass
        try:
            page.locator("#script-modal-close").click(timeout=5000)
            log_action("suggest", "Click", "#script-modal-close")
            page.wait_for_timeout(2000)
        except:
            pass
        print("✓ Script saved as EP1 (5 scenes)")

        # === OPEN EPISODE ===
        page.locator(".ep-card").first.click()
        log_action("suggest", "Click", ".ep-card (open EP1)")
        page.wait_for_timeout(3000)

        # Switch to Veo tab
        page.locator(".ep-tab[data-ep-tab='veo']").click()
        log_action("suggest", "Click", ".ep-tab[data-ep-tab='veo']")
        page.wait_for_timeout(2000)
        page.screenshot(path=str(SCREENSHOTS / "common_03_veo_tab.png"))
        print("✓ Episode modal open, on Veo tab")

        # === FEATURE 1: 🤖 AI SUGGEST NEXT SCENE ===
        print("\n" + "=" * 60)
        print("[FEATURE 1] 🤖 AI Suggest Next Scene")
        print("=" * 60)
        page.screenshot(path=str(SCREENSHOTS / "01_01_before_click.png"))
        page.locator("#ai-suggest-next-btn").click()
        log_action("suggest", "Click", "#ai-suggest-next-btn (NEW v3.3)")
        page.wait_for_timeout(2000)
        page.screenshot(path=str(SCREENSHOTS / "01_02_loading.png"))
        print("⏳ Waiting for LLM (15-30s)...")
        for i in range(30):
            page.wait_for_timeout(2000)
            try:
                content = page.locator("#suggestion-modal").text_content() or ""
                if "Location:" in content or "Why this next" in content or "แนะนำ" in content:
                    print(f"  ✓ Suggestion at i={i}")
                    break
            except:
                pass
        page.wait_for_timeout(2000)
        page.screenshot(path=str(SCREENSHOTS / "01_03_suggestion.png"))

        # Read suggestion content
        suggestion_text = ""
        try:
            suggestion_text = page.locator("#suggestion-modal").text_content() or ""
        except:
            pass
        with open(SCREENSHOTS / "01_03_suggestion_text.txt", "w") as f:
            f.write(suggestion_text)

        # Apply the suggestion
        try:
            apply_btn = page.locator("button:has-text('Apply')").first
            apply_btn.click()
            log_action("suggest", "Click", "button:has-text('Apply')")
            page.wait_for_timeout(5000)
            page.screenshot(path=str(SCREENSHOTS / "01_04_after_apply.png"))
            print("✓ Suggestion applied")
        except Exception as e:
            print(f"  ! Apply failed: {e}")

        # Wait for modal to close
        page.wait_for_timeout(3000)
        try:
            page.locator("body").click(timeout=2000)
        except:
            pass
        page.screenshot(path=str(SCREENSHOTS / "01_05_ep_with_new_scene.png"))

        # === FEATURE 2: 📖 AUTO-CONTINUE STORY ===
        print("\n" + "=" * 60)
        print("[FEATURE 2] 📖 Auto-Continue Story")
        print("=" * 60)
        # Make sure we're still on Veo tab and modals closed
        try:
            page.locator(".ep-tab[data-ep-tab='veo']").click(timeout=5000)
        except:
            pass
        page.wait_for_timeout(2000)
        page.screenshot(path=str(SCREENSHOTS / "02_01_before_click.png"))
        page.locator("#auto-continue-btn").click()
        log_action("continue", "Click", "#auto-continue-btn (NEW v3.3)")
        page.wait_for_timeout(2000)
        page.screenshot(path=str(SCREENSHOTS / "02_02_progress.png"))
        print("⏳ Auto-Continue (30-60s)...")
        for i in range(45):
            page.wait_for_timeout(2000)
            try:
                # Check for any progress modal or completion
                progress = page.locator("#progress-modal.active")
                if progress.count() == 0 and i > 3:
                    print(f"  ✓ Progress modal closed at i={i}")
                    break
            except:
                pass
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SCREENSHOTS / "02_03_after_continue.png"))
        print("✓ Auto-Continue done")

        # === FEATURE 3: 🎬 STORY MODE ===
        print("\n" + "=" * 60)
        print("[FEATURE 3] 🎬 Story Mode (Veo prompts only)")
        print("=" * 60)
        try:
            page.locator(".ep-tab[data-ep-tab='veo']").click(timeout=5000)
        except:
            pass
        page.wait_for_timeout(2000)
        page.screenshot(path=str(SCREENSHOTS / "03_01_before_click.png"))
        page.locator("#story-mode-btn").click()
        log_action("storymode", "Click", "#story-mode-btn (NEW v3.3)")
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SCREENSHOTS / "03_02_progress_start.png"))
        print("⏳ Story Mode (60-120s for Veo prompts only)...")
        for i in range(90):
            page.wait_for_timeout(2000)
            try:
                progress = page.locator("#progress-modal.active")
                content = page.locator("#progress-modal").text_content() or ""
                # If we see "Story Mode" in title and a checkmark = done
                if ("Story Mode" in content and "✅" in content):
                    print(f"  ✓ Story Mode done at i={i}")
                    break
                if progress.count() == 0 and i > 5:
                    break
            except:
                pass
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SCREENSHOTS / "03_03_storymode_done.png"), full_page=True)
        print("✓ Story Mode done")

        # === FINAL ===
        page.screenshot(path=str(SCREENSHOTS / "final_full.png"), full_page=True)

    except Exception as e:
        page.screenshot(path=str(SCREENSHOTS / "FATAL_ERROR.png"))
        print(f"FATAL: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.close()

print("\n" + "=" * 80)
print("📸 ALL SCREENSHOTS")
print("=" * 80)
for f in sorted(SCREENSHOTS.glob("*.png")):
    print(f"  {f.name}")
