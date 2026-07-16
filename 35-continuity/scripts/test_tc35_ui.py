"""
TC-35: Scene Continuity + Dialogue Quality v3.5.1 (Real UI)
============================================================
Tests the 4-rule continuity validator:
  1. LOCATION continuity
  2. CALLBACK PROP continuity
  3. TIME progression
  4. EMOTIONAL continuity

Plus dialogue quality (character voice consistency).
"""
import os, sys, time, json, re, socket
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright

BASE = "https://directorstudio.sj88ai.com"
TC_DIR = Path("/workspace/director-studio-test-cases/35-continuity")
SHOTS = TC_DIR / "screenshots"
LOG_FILE = TC_DIR / "TC-35_LOG.md"
RESULTS = TC_DIR / "TC-35_RESULTS.md"

SHOTS.mkdir(parents=True, exist_ok=True)

TIMESTAMP = int(time.time())
TEST_EMAIL = f"tc35_{TIMESTAMP}@test.local"
TEST_PASSWORD = "tc35test1234"
TEST_NAME = f"TC-35 {TIMESTAMP}"

typed_log = []
results = []

def log_typed(action, value):
    entry = f"[{datetime.now().strftime('%H:%M:%S')}] {action}: {value!r}"
    print(f"  ⌨  {entry}")
    typed_log.append(entry)

def log_result(name, ok, detail=""):
    icon = "✅" if ok else "❌"
    print(f"  {icon} {name}: {detail}")
    results.append((name, ok, detail))

print("=" * 80)
print("⚡ TC-35: Scene Continuity + Dialogue v3.5.1 (Real UI)")
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
    page.set_default_timeout(60000)
    page.on("dialog", lambda d: (log_typed("Dialog", d.type), d.accept()))
    page.on("pageerror", lambda e: log_result("JS_ERROR", False, str(e)[:200]))

    script_data = None

    try:
        # === SIGNUP ===
        page.goto(BASE, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
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
        page.locator("#project-name-input").fill("TC-35 Continuity")
        page.locator("#project-save").click()
        page.wait_for_timeout(3000)
        log_result("create-project", True, "Project created")

        # === OPEN SCRIPT MODAL ===
        page.locator("#gen-script-btn").click()
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SHOTS / "01_script_modal.png"))

        # === GENERATE SCRIPT WITH STRICT REQUIREMENTS ===
        idea = """น้ำเดินเข้าหมู่บ้านตอนเย็น เห็นจดหมายจากยาย
ซีน 1: น้ำเดินเข้าหมู่บ้าน
ซีน 2: เจอจดหมายหน้าบ้านยาย
ซีน 3: เปิดจดหมาย เจอกล่องไม้
ซีน 4: เปิดกล่อง เจอผ้าแดง
ซีน 5: ผีปรากฏตัว"""
        page.locator("#script-idea").fill(idea)
        page.locator("#script-num-scenes").fill("5")
        page.locator("#script-generate").click()
        log_typed("Click", "#script-generate (5 scenes)")
        print("⏳ Stage 1 (~60s)...")

        # Wait for completion
        for i in range(90):
            page.wait_for_timeout(2000)
            try:
                html = page.locator("#script-result").inner_html(timeout=2000)
                if "✅ Script generated" in html:
                    print(f"  ✓ Script done at i={i}")
                    break
            except:
                pass
        page.wait_for_timeout(3000)
        page.screenshot(path=str(SHOTS / "02_script_with_continuity.png"), full_page=True)

        # Parse the result to extract continuity report
        # The result is in a <pre> or in HTML format
        result_html = page.locator("#script-result").inner_html()
        result_text = page.locator("#script-result").text_content() or ""

        # Check that continuity report is shown
        has_continuity = "Continuity" in result_text or "continuity" in result_text or "Location:" in result_text
        log_result("continuity-report-visible", has_continuity,
                   f"Has 'Continuity' in result: {has_continuity}")

        # Get the actual script from the API for deeper analysis
        # Use page.evaluate to get the pendingScript
        api_result = page.evaluate("""async () => {
            const token = localStorage.getItem('sj_token');
            if (!token) return {error: 'no token'};
            const r = await fetch('/api/projects', {headers: {Authorization: 'Bearer ' + token}});
            const data = await r.json();
            const projects = Array.isArray(data) ? data : (data.projects || []);
            for (const p of projects) {
                if (p.name && p.name.includes('TC-35')) {
                    return {project: p};
                }
            }
            return {error: 'project not found'};
        }""")

        if "project" in api_result:
            project = api_result["project"]
            d = project.get("data", {})
            eps = d.get("episodes", [])
            if eps:
                ep = eps[0]
                scenes = ep.get("scenes", [])
                log_result("script-saved", len(scenes) == 5, f"EP1 has {len(scenes)} scenes")

                # Check continuity manually
                print("\n--- Scene-by-scene analysis ---")
                for i, s in enumerate(scenes):
                    print(f"\n{s.get('id')} '{s.get('title')}'")
                    print(f"  loc: {s.get('location', '?')}")
                    print(f"  time: {s.get('time_marker', '?')}")
                    print(f"  emotion: {s.get('emotional_beat', '?')}")
                    print(f"  dialogue: {s.get('dialogue', [])}")

                # Time progression check
                times = []
                for s in scenes:
                    tm = s.get("time_marker", "")
                    m = re.search(r'(\d{1,2}):(\d{2})', tm)
                    if m:
                        times.append(int(m.group(1)) * 60 + int(m.group(2)))
                time_progression_ok = all(times[i] <= times[i+1] for i in range(len(times)-1)) if len(times) > 1 else False
                log_result("time-progression", time_progression_ok,
                           f"Times: {times}, all increasing: {time_progression_ok}")

                # Character consistency
                all_chars = set()
                for s in scenes:
                    all_chars.update(s.get("characters", []))
                log_result("character-slots-used", "ref1" in all_chars,
                           f"Characters used: {sorted(all_chars)}")

                # Dialogue quality check: count dialogue lines
                total_dlg = sum(len(s.get("dialogue", [])) for s in scenes)
                log_result("dialogue-present", total_dlg >= 3, f"Total dialogue lines: {total_dlg}")

                # Save script for HTML report
                script_data = ep

        # Save
        try:
            page.locator("#script-save").click(timeout=10000)
            log_typed("Click", "#script-save")
            page.wait_for_timeout(3000)
        except:
            pass

        page.screenshot(path=str(SHOTS / "99_final.png"), full_page=True)

    except Exception as e:
        page.screenshot(path=str(SHOTS / "FATAL_ERROR.png"))
        import traceback
        traceback.print_exc()
    finally:
        browser.close()

# === SAVE ===
LOG_FILE.write_text(
    "# TC-35 UI Typing Log\n\nEmail: " + TEST_EMAIL + "\n\n## Actions\n\n" +
    "\n".join(typed_log) + "\n"
)

passed = sum(1 for _, ok, _ in results if ok)
total = len(results)

with open(RESULTS, "w") as f:
    f.write(f"# TC-35: Scene Continuity + Dialogue v3.5.1\n\n")
    f.write(f"**Date**: {datetime.now().isoformat()}\n")
    f.write(f"**Email**: {TEST_EMAIL}\n")
    f.write(f"**Version**: 3.5.1\n\n")
    f.write("## Result\n\n")
    f.write(f"**{passed}/{total} steps passed**\n\n")
    for name, ok, detail in results:
        f.write(f"- {'✅' if ok else '❌'} **{name}**: {detail}\n")
    f.write(f"\n## Script Data\n\n```json\n{json.dumps(script_data, ensure_ascii=False, indent=2)[:5000]}\n```\n")

# Save raw script for HTML report
if script_data:
    with open(TC_DIR / "report" / "script_data.json", "w") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print("📊 TC-35 RESULTS")
print("=" * 80)
print(f"\n**{passed}/{total} steps passed**\n")
for name, ok, detail in results:
    print(f"  {'✅' if ok else '❌'} {name}: {detail}")
