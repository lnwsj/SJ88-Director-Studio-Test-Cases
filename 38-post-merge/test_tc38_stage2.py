"""TC-38 v2: Test Stage 2 (Veo gen) to verify full pipeline"""
from playwright.sync_api import sync_playwright
import time, os, json

CHROME = "/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome"
URL = "https://directorstudio.sj88ai.com"
EMAIL = "admin@sj88ai.com"
PASSWORD = "admin1234"

SCREEN_DIR = "/workspace/director-studio-test-cases/38-post-merge/screenshots-stage2"
os.makedirs(SCREEN_DIR, exist_ok=True)
for f in os.listdir(SCREEN_DIR):
    os.remove(os.path.join(SCREEN_DIR, f))

results = []
def step(name, ok, msg=""):
    results.append((name, ok, msg))
    print(f"  {'✅' if ok else '❌'} {name}: {msg}")

print("=" * 60)
print("🧪 TC-38 Stage 2: Full Pipeline Test")
print("=" * 60)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME, headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.set_default_timeout(15000)
    page.on("dialog", lambda d: d.accept())
    
    # 1. Login
    print("\n[1] Login")
    page.goto(URL, wait_until="domcontentloaded")
    time.sleep(2)
    try:
        page.locator(".auth-tab[data-tab='login']").click()
        time.sleep(0.5)
    except: pass
    page.locator("input[type='email']").fill(EMAIL)
    page.locator("input[type='password']").fill(PASSWORD)
    page.locator("#auth-submit").click()
    time.sleep(3)
    step("login", "project" in page.content().lower(), f"url={page.url}")
    
    # 2. Find/create project with existing EP
    print("\n[2] Find or Create Test Project")
    # Use the existing TC-38 Admin Test project that has 1 EP
    # Click on it
    proj_cards = page.locator(".project-card")
    if proj_cards.count() == 0:
        # Maybe we're already in the project - look for project name
        if "TC-38 Admin Test" in page.content():
            step("project-found", True, "TC-38 Admin Test already open")
        else:
            step("project-found", False, "no project card, not in project")
            browser.close()
            exit(1)
    else:
        # Find the TC-38 project
        for i in range(proj_cards.count()):
            txt = proj_cards.nth(i).text_content()
            if "TC-38" in txt:
                proj_cards.nth(i).click()
                time.sleep(2)
                step("project-found", True, f"opened TC-38 project")
                break
    
    # 3. Open EP
    print("\n[3] Open EP")
    ep_cards = page.locator(".ep-card")
    if ep_cards.count() > 0:
        ep_cards.first.click()
        time.sleep(1.5)
        page.screenshot(path=f"{SCREEN_DIR}/01-ep-modal.png")
        step("ep-opened", True, "EP opened")
    else:
        step("ep-opened", False, f"no EP cards: {ep_cards.count()}")
        browser.close()
        exit(1)
    
    # 4. Click Veo tab
    print("\n[4] Click Veo tab")
    veo_tab = page.locator(".ep-tab[data-ep-tab='veo']")
    if veo_tab.count() > 0:
        veo_tab.first.click()
        time.sleep(1)
        page.screenshot(path=f"{SCREEN_DIR}/02-veo-tab.png")
        step("veo-tab", True, "Veo tab active")
    
    # 5. Generate Veo Prompts
    print("\n[5] Stage 2: Generate Veo Prompts")
    # The button is "Stage 2: Generate Veo Prompts"
    stage2_btn = page.locator("button:has-text('Stage 2: Generate')")
    if stage2_btn.count() > 0:
        stage2_btn.first.click()
        print("  Waiting for LLM...")
        # Wait for prompts to be generated
        try:
            page.wait_for_function(
                "() => { const el = document.querySelector('.veo-prompts-list, .veo-prompt-item, [class*=\"veo\"]'); if (el) return true; const all = document.querySelectorAll('*'); for (const e of all) { if (e.textContent && e.textContent.includes('Scene 1') && e.children.length === 0) return true; } return false; }",
                timeout=120000
            )
            time.sleep(2)
            page.screenshot(path=f"{SCREEN_DIR}/03-veo-generated.png")
            step("veo-generated", True, "Veo prompts generated")
        except Exception as e:
            step("veo-generated", False, f"timeout: {str(e)[:80]}")
            page.screenshot(path=f"{SCREEN_DIR}/03-veo-timeout.png")
    
    # 6. Final state
    page.screenshot(path=f"{SCREEN_DIR}/04-final.png", full_page=True)
    
    browser.close()

print("\n" + "=" * 60)
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
print(f"📊 TC-38 Stage 2 Results: {passed}/{total} PASSED")
print("=" * 60)
for name, ok, msg in results:
    print(f"  {'✅' if ok else '❌'} {name}: {msg}")
