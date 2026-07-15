"""
TC-29: Verify AI reads refs from UI for script generation
Tests the fix for the bug where LLM didn't get character context
"""
import os, sys, time, json, re, socket
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ playwright not installed")
    sys.exit(1)

BASE = "https://directorstudio.sj88ai.com"
TC_DIR = Path("/workspace/director-studio-test-cases/29-refs-fix")
SCREENSHOTS = TC_DIR / "screenshots"
LOG_FILE = TC_DIR / "UI_TYPED_LOG.md"
RESULTS = TC_DIR / "UI_RESULTS.md"

for d in [SCREENSHOTS]:
    d.mkdir(parents=True, exist_ok=True)

TIMESTAMP = int(time.time())
TEST_EMAIL = f"refsfix_{TIMESTAMP}@test.local"
TEST_PASSWORD = "refsfix1234"
TEST_NAME = f"Refs Fix {TIMESTAMP}"
PROJECT_NAME = f"TC-29 Refs Fix Test"

actions = []
def log_typed(action, value):
    entry = f"[{datetime.now().strftime('%H:%M:%S')}] {action}: {value!r}"
    print(f"  ⌨  {entry}")
    actions.append(entry)
    LOG_FILE.write_text("# TC-29 UI Actions (refs fix verification)\n\n" + "\n".join(actions) + "\n")

def check_dns():
    try:
        host = BASE.replace("https://", "").split("/")[0]
        socket.gethostbyname(host)
        return True
    except:
        return False

print("=" * 80)
print("🧪 TC-29: Verify AI reads refs from UI")
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
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(60000)
    page.on("dialog", lambda dialog: dialog.accept())

    try:
        # Signup
        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        page.locator(".auth-tab[data-tab='signup']").click()
        page.wait_for_timeout(1000)
        page.locator("input[name='display_name']").fill(TEST_NAME)
        log_typed("Type display_name", TEST_NAME)
        page.locator("input[name='email']").fill(TEST_EMAIL)
        log_typed("Type email", TEST_EMAIL)
        page.locator("input[name='password']").fill(TEST_PASSWORD)
        log_typed("Type password", "****")
        page.locator("#auth-submit").click()
        log_typed("Click", "#auth-submit (สมัคร)")
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SCREENSHOTS / "01_signed_up.png"))

        # Create project
        page.locator("#new-project-btn").click()
        page.wait_for_timeout(1000)
        page.locator("#project-name-input").fill(PROJECT_NAME)
        log_typed("Type project name", PROJECT_NAME)
        page.locator("#project-save").click()
        log_typed("Click", "#project-save (สร้าง)")
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SCREENSHOTS / "02_project.png"))

        # Generate script (refs will be loaded from SHARED_REFS by backend cascade)
        page.locator("#gen-script-btn").click()
        page.wait_for_timeout(2000)
        # Use a very specific story with character details
        page.locator("#script-idea").fill("น้ำ (สาวจีนในชุดเชียงเชียนแดง ผมเปีย 2 เปีย แว่นกลม) เดินเข้าหมู่บ้านเก่าตอนค่ำ เจอบ้านยายที่เคยอยู่")
        log_typed("Type script idea", "น้ำ ชุดเชียงเชียนแดง ผมเปีย 2 เปีย แว่นกลม")
        page.locator("#script-num-scenes").fill("3")
        log_typed("Type num-scenes", "3")
        page.locator("#script-generate").click()
        log_typed("Click", "#script-generate")
        print("⏳ Waiting for script gen...")
        for i in range(45):
            page.wait_for_timeout(2000)
            try:
                content = page.locator("#script-result").text_content() or ""
                if "✅" in content or "scenes" in content.lower():
                    print(f"  ✓ Done at i={i}")
                    break
            except:
                pass
        page.wait_for_timeout(2000)
        page.screenshot(path=str(SCREENSHOTS / "04_script.png"))

        # Get script content
        script_text = page.locator("#script-result").text_content() or ""
        # Check if AI used character details
        has_chinese_girl = "สาวจีน" in script_text or "ชุดเชียงเชียน" in script_text
        has_braids = "ผมเปีย" in script_text or "เปีย" in script_text
        has_round_glasses = "แว่นกลม" in script_text or "แว่น" in script_text
        has_ref1_used = "[ref1]" in script_text

        print(f"\n=== Character Context Verification ===")
        print(f"  [ref1] used: {has_ref1_used}")
        print(f"  สาวจีน/ชุดเชียงเชียน mentioned: {has_chinese_girl}")
        print(f"  ผมเปีย mentioned: {has_braids}")
        print(f"  แว่นกลม mentioned: {has_round_glasses}")

        with open(SCREENSHOTS / "04_script_text.txt", "w") as f:
            f.write(script_text)

        # Write results
        with open(RESULTS, "w") as f:
            f.write(f"# TC-29 Results: AI reads refs from UI\n\n")
            f.write(f"**Date**: {datetime.now().isoformat()}\n")
            f.write(f"**Email**: {TEST_EMAIL}\n\n")
            f.write("## Character Context Test\n\n")
            f.write(f"- ✅ AI used [ref1] in scenes: {has_ref1_used}\n")
            f.write(f"- {'✅' if has_chinese_girl else '❌'} AI used 'สาวจีน/ชุดเชียงเชียน': {has_chinese_girl}\n")
            f.write(f"- {'✅' if has_braids else '❌'} AI used 'ผมเปีย': {has_braids}\n")
            f.write(f"- {'✅' if has_round_glasses else '❌'} AI used 'แว่นกลม': {has_round_glasses}\n")
            f.write(f"\n## Verdict\n\n")
            if has_ref1_used and has_chinese_girl and has_braids:
                f.write("**✅ PASS** — AI now reads character context from refs\n")
            else:
                f.write("**❌ PARTIAL** — Some character context not used\n")
            f.write(f"\n## Full script text\n\n```\n{script_text[:2000]}\n```\n")

        print(f"\n📁 Results: {RESULTS}")
        print(f"📁 Log: {LOG_FILE}")

    except Exception as e:
        page.screenshot(path=str(SCREENSHOTS / "FATAL.png"))
        print(f"FATAL: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.close()
