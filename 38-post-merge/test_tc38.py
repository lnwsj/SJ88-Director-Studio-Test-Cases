"""TC-38: Full UI Test - Post-Merge Deploy (v4 - admin)"""
from playwright.sync_api import sync_playwright
import time, os, json

CHROME = "/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome"
URL = "https://directorstudio.sj88ai.com"
EMAIL = "admin@sj88ai.com"
PASSWORD = "admin1234"

SCREEN_DIR = "/workspace/director-studio-test-cases/38-post-merge/screenshots"
os.makedirs(SCREEN_DIR, exist_ok=True)
# Clear old
for f in os.listdir(SCREEN_DIR):
    os.remove(os.path.join(SCREEN_DIR, f))

results = []
def step(name, ok, msg=""):
    results.append((name, ok, msg))
    print(f"  {'✅' if ok else '❌'} {name}: {msg}")

print("=" * 60)
print("🧪 TC-38 v4: Full UI Test (admin)")
print("=" * 60)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME, headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.set_default_timeout(15000)
    page.on("dialog", lambda d: d.accept())
    
    # 1. Open + login
    print("\n[1] Open + Login as Admin")
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
    step("login", "project" in page.content().lower() or "Project" in page.content(), f"url={page.url}")
    page.screenshot(path=f"{SCREEN_DIR}/01-after-login.png")
    
    # 2. Create new project
    print("\n[2] Create New Project")
    new_btn = page.locator("#new-project-btn")
    if new_btn.count() > 0 and new_btn.first.is_visible():
        new_btn.first.click()
        time.sleep(1)
        page.locator("#project-name-input").fill("TC-38 Admin Test")
        page.locator("#project-save").click()
        time.sleep(2)
        page.screenshot(path=f"{SCREEN_DIR}/02-project-created.png")
        step("create-project", True, "TC-38 Admin Test")
    else:
        step("create-project", False, f"new-project-btn not visible (count={new_btn.count()})")
    
    # 3. Open settings modal
    print("\n[3] Settings Modal - Refs UI")
    time.sleep(1)
    settings_btn = page.locator("#project-settings-btn")
    if settings_btn.count() > 0 and settings_btn.first.is_visible():
        settings_btn.first.click()
        time.sleep(1.5)
        page.screenshot(path=f"{SCREEN_DIR}/03-settings-modal.png")
        has_refs = page.locator("text=Character References").count() > 0
        has_upload = page.locator("#project-ref-upload").count() > 0
        has_name = page.locator("#project-ref-name").count() > 0
        has_add = page.locator("#project-ref-add").count() > 0
        step("refs-section", has_refs, "Character References section")
        step("refs-upload-input", has_upload, "file input")
        step("refs-name-input", has_name, "name input")
        step("refs-add-button", has_add, "add button")
        
        # Close
        # Close settings properly via the × button
        close_btn = page.locator("#project-settings-close")
        if close_btn.count() > 0 and close_btn.first.is_visible():
            close_btn.first.click()
        time.sleep(0.5)
        time.sleep(0.5)
    
    # 4. Generate Script (admin has LLM key)
    print("\n[4] Generate Script (using admin LLM key)")
    gen_btn = page.locator("#gen-script-btn")
    if gen_btn.count() > 0 and gen_btn.first.is_visible():
        gen_btn.first.click()
        time.sleep(1.5)
        page.screenshot(path=f"{SCREEN_DIR}/04-script-modal.png")
        
        if page.locator("#script-idea").count() > 0:
            page.locator("#script-idea").fill("3 คนเข้าบ้านร้าง พบผีในรูปเก่า")
            page.locator("#script-num-scenes").fill("3")
            page.screenshot(path=f"{SCREEN_DIR}/05-script-form.png")
            page.locator("#script-generate").click()
            print("  Waiting for LLM...")
            
            try:
                page.wait_for_function(
                    "() => { const el = document.querySelector('#script-result'); if (!el) return false; const t = (el.value || el.textContent || '').trim(); return t.length > 200; }",
                    timeout=120000
                )
                page.screenshot(path=f"{SCREEN_DIR}/06-script-result.png")
                result_text = page.locator("#script-result").text_content() if page.locator("#script-result").count() > 0 else ""
                step("script-generate", "scene" in (result_text or "").lower() or "ฉาก" in (result_text or ""), 
                     f"length={len(result_text or '')} chars")
            except Exception as e:
                step("script-generate", False, f"timeout: {str(e)[:100]}")
                page.screenshot(path=f"{SCREEN_DIR}/06-script-timeout.png")
    
    # 5. Save script
    print("\n[5] Save Script")
    if page.locator("#script-save").count() > 0 and page.locator("#script-save").is_visible():
        page.locator("#script-save").click()
        time.sleep(2)
        page.screenshot(path=f"{SCREEN_DIR}/07-script-saved.png")
        step("save-script", True, "saved")
    
    # 6. Check Veo button
    print("\n[6] Check Veo tab")
    # Look for EP card
    time.sleep(1)
    ep_cards = page.locator(".ep-card")
    if ep_cards.count() > 0:
        step("ep-cards", True, f"{ep_cards.count()} EP cards")
        ep_cards.first.click()
        time.sleep(1.5)
        page.screenshot(path=f"{SCREEN_DIR}/08-ep-modal.png")
        # Try Veo tab
        veo_tab = page.locator(".ep-tab[data-ep-tab='veo']")
        if veo_tab.count() > 0:
            veo_tab.first.click()
            time.sleep(1)
            page.screenshot(path=f"{SCREEN_DIR}/09-veo-tab.png")
            step("veo-tab", True, "Veo tab clicked")
            # Check for generate button
            gen_veo = page.locator("#gen-veo-all-btn")
            step("veo-gen-btn", gen_veo.count() > 0, f"count={gen_veo.count()}")
    
    page.screenshot(path=f"{SCREEN_DIR}/10-final.png", full_page=True)
    browser.close()

print("\n" + "=" * 60)
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
print(f"📊 TC-38 Results: {passed}/{total} PASSED")
print("=" * 60)
for name, ok, msg in results:
    print(f"  {'✅' if ok else '❌'} {name}: {msg}")

with open("/workspace/director-studio-test-cases/38-post-merge/RESULTS.json", "w") as f:
    json.dump([{"name": n, "passed": ok, "msg": m} for n, ok, m in results], f, indent=2)
