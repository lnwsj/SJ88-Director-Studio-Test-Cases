#!/usr/bin/env python3
"""
TC-01a: Steps 1-4 DEEP Test
- 50+ assertions across 4 steps
- Screenshot every step
- Detailed HTML report
- Test data verification (refs, scenes, dialogue)
"""
import asyncio
from playwright.async_api import async_playwright
import json
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = "https://directorstudio.sj88ai.com"
CHROME = "/root/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome"
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
OUT = Path(f"/workspace/director-studio-test-cases/01-video-generation/runs/deep-steps-1-4-{TS}")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "screenshots").mkdir(exist_ok=True)

assertions = []
network = []
start_time = time.time()


def assert_eq(step, substep, name, expected, actual, screenshot=None, notes=""):
    status = "PASS" if expected == actual else "FAIL"
    entry = {
        "step": step, "substep": substep, "name": name,
        "expected": str(expected), "actual": str(actual),
        "status": status, "screenshot": screenshot, "notes": notes,
    }
    assertions.append(entry)
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} [{step}.{substep}] {name}: expected={expected}, actual={actual}")
    if notes:
        print(f"      notes: {notes}")
    return status == "PASS"


def assert_contains(step, substep, name, expected_substr, actual_str, screenshot=None, notes=""):
    status = "PASS" if expected_substr in str(actual_str) else "FAIL"
    entry = {
        "step": step, "substep": substep, "name": name,
        "expected": f"contains '{expected_substr}'", "actual": str(actual_str)[:200],
        "status": status, "screenshot": screenshot, "notes": notes,
    }
    assertions.append(entry)
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} [{step}.{substep}] {name}: contains '{expected_substr}'")
    return status == "PASS"


async def shoot(page, name):
    path = OUT / "screenshots" / f"{name}.png"
    await page.screenshot(path=str(path), full_page=False)
    return f"screenshots/{name}.png"


async def shoot_full(page, name):
    path = OUT / "screenshots" / f"{name}.png"
    await page.screenshot(path=str(path), full_page=True)
    return f"screenshots/{name}.png"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROME, headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--use-gl=swiftshader"]
        )
        ctx = await browser.new_context(
            viewport={"width": 1400, "height": 1100},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await ctx.new_page()
        page.on("response", lambda r: network.append({
            "ts": time.time() - start_time, "method": r.request.method,
            "url": r.url, "status": r.status
        }) if "/api/" in r.url else None)
        page.on("pageerror", lambda exc: print(f"  [PAGEERROR] {exc}"))

        # Get Bearer token (login first)
        print(f"\n{'='*70}\nSTEP 1: Login Page\n{'='*70}")
        await page.goto(f"{BASE}/")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)
        s1 = await shoot(page, "01-login-initial")

        assert_eq(1, 1, "URL", f"{BASE}/", page.url, s1)
        assert_contains(1, 1, "Title", "Director Studio", await page.title(), s1)
        assert_eq(1, 1, "Email input visible", True, await page.is_visible('input[type="email"]'), s1)
        assert_eq(1, 1, "Email input type", "email", await page.get_attribute('input[type="email"]', 'type'), s1)
        assert_eq(1, 1, "Password input visible", True, await page.is_visible('input[type="password"]'), s1)
        assert_eq(1, 1, "Password input type", "password", await page.get_attribute('input[type="password"]', 'type'), s1)
        assert_eq(1, 1, "Submit button visible", True, await page.is_visible('button[type="submit"]'), s1)

        await page.fill('input[type="email"]', "admin@sj88ai.com")
        await page.fill('input[type="password"]', "admin1234")
        s1b = await shoot(page, "01-login-filled")
        assert_eq(1, 2, "Email field accepts text", "admin@sj88ai.com",
                  await page.input_value('input[type="email"]'), s1b)
        assert_eq(1, 2, "Password field accepts text", "admin1234",
                  await page.input_value('input[type="password"]'), s1b)

        # STEP 2: Login
        print(f"\n{'='*70}\nSTEP 2: Submit Login\n{'='*70}")
        net_before = len(network)
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        s2a = await shoot(page, "02-after-submit")
        s2b = await shoot_full(page, "02-projects-list")

        new_calls = network[net_before:]
        login_call = next((n for n in new_calls if "/api/auth/login" in n["url"]), None)
        me_call = next((n for n in new_calls if "/api/auth/me" in n["url"]), None)
        projects_call = next((n for n in new_calls if "/api/projects" == n["url"].replace(BASE, "").split("?")[0]), None)
        assert_eq(2, 1, "POST /api/auth/login status", 200,
                  login_call["status"] if login_call else None, s2a)
        assert_eq(2, 1, "GET /api/auth/me status", 200,
                  me_call["status"] if me_call else None, s2a)
        assert_eq(2, 1, "GET /api/projects status", 200,
                  projects_call["status"] if projects_call else None, s2a)

        nav_text = await page.text_content('nav') or ""
        admin_visible = "Admin" in nav_text or await page.is_visible('text=Admin')
        assert_eq(2, 2, "Admin badge visible", True, admin_visible, s2b)
        assert_eq(2, 2, "Email form hidden", True,
                  not await page.is_visible('input[type="email"]'), s2b)
        project_cards = await page.query_selector_all('[class*="project"]')
        assert_eq(2, 2, "Project cards present", True, len(project_cards) > 0, s2b)

        # Get token + project list via urllib (Playwright request returns string)
        token = await page.evaluate("() => localStorage.getItem('ds_token')")
        req2 = urllib.request.Request(f"{BASE}/api/projects", headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req2) as r2:
            projects_data = json.loads(r2.read().decode())
        print(f"  Projects: {[p['name'] for p in projects_data]}")
        target_project = next((p for p in projects_data if p["name"] == "โรงเรียนรัก"), None)
        assert_contains(2, 2, "โรงเรียนรัก in project list", "โรงเรียนรัก",
                        [p["name"] for p in projects_data], s2b)

        # STEP 3: Open โรงเรียนรัก
        print(f"\n{'='*70}\nSTEP 3: Open โรงเรียนรัก\n{'='*70}")
        pid = target_project["id"] if target_project else None
        print(f"  Project ID: {pid}")
        s3a = await shoot(page, "03a-before-click")
        romrak_card = await page.query_selector('text=โรงเรียนรัก')
        assert_eq(3, 1, "โรงเรียนรัก card visible", True, romrak_card is not None, s3a)

        await page.click('text=โรงเรียนรัก')
        await page.wait_for_timeout(3000)
        s3b = await shoot_full(page, "03b-project-view")

        # Project name appears anywhere on page
        page_text = await page.text_content('body') or ""
        assert_contains(3, 2, "โรงเรียนรัก shown on page", "โรงเรียนรัก", page_text, s3b)
        assert_eq(3, 2, "Back link visible", True, await page.is_visible('text=กลับ'), s3b)
        assert_eq(3, 2, "EP1 visible", True, await page.is_visible('text=วันแรกที่โรงเรียน'), s3b)
        assert_eq(3, 2, "+ Episode ใหม่ button", True, await page.is_visible('text=+ Episode ใหม่'), s3b)
        assert_eq(3, 2, "✨ Generate Episode (AI) button", True,
                  await page.is_visible('text=✨ Generate Episode'), s3b)
        assert_eq(3, 2, "Seed EP1-3 button removed", False,
                  await page.is_visible('text=Seed EP1-3'), s3b, "Confirmed removed")

        # STEP 4: EP1 + Veo Tab
        print(f"\n{'='*70}\nSTEP 4: EP1 + Veo Tab\n{'='*70}")
        await page.click('text=วันแรกที่โรงเรียน')
        await page.wait_for_timeout(3000)
        s4a = await shoot_full(page, "04a-modal-script")

        # 4.1 Modal
        body_text = await page.text_content('body') or ""
        assert_contains(4, 1, "Modal title", "วันแรกที่โรงเรียน", body_text, s4a)
        assert_eq(4, 1, "บท tab visible", True, await page.is_visible('button:has-text("บท")'), s4a)
        assert_eq(4, 1, "Veo tab visible", True, await page.is_visible('button:has-text("Veo")'), s4a)
        assert_eq(4, 1, "วิดีโอ tab visible", True, await page.is_visible('button:has-text("วิดีโอ")'), s4a)

        # 4.2 Script Tab data via API
        req3 = urllib.request.Request(f"{BASE}/api/projects/{pid}", headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req3) as r3:
            project_data = json.loads(r3.read().decode())
        ep1 = project_data["data"]["episodes"][0]
        s4b = await shoot_full(page, "04b-script-default")
        assert_eq(4, 2, "EP1 has 10 scenes", 10, len(ep1["scenes"]), s4b)
        assert_contains(4, 2, "EP1 has logline", "มิ้นท์", ep1.get("episode_logline", ""), s4b)
        chars = set(ep1.get("characters_in_ep", []))
        assert_eq(4, 2, "EP1 chars: mint,phom,peach", True,
                  chars >= {"mint", "phom", "peach"}, s4b)
        # Verify dialogue has Thai
        has_thai = any(any(ord(c) >= 0x0E00 for c in d.get("line", ""))
                      for s in ep1["scenes"] for d in s.get("dialogue", []))
        assert_eq(4, 2, "Thai dialogue in scenes", True, has_thai, s4b)
        has_mood = all(s.get("emotional_beat") for s in ep1["scenes"])
        assert_eq(4, 2, "All scenes have emotional_beat", True, has_mood, s4b)

        # 4.3 Switch to Veo tab
        await page.click('button:has-text("Veo")')
        await page.wait_for_timeout(2000)
        s4c = await shoot_full(page, "04c-veo-tab")
        body_text2 = await page.text_content('body') or ""
        assert_eq(4, 3, "Veo Prompts (10) header", True, "Veo Prompts (10)" in body_text2, s4c)
        assert_eq(4, 3, "Duration 0.0-8 shown", True, "0.0-8" in body_text2, s4c)
        veo_config = ep1.get("veo_config", {})
        assert_eq(4, 3, "veo_config.duration = 8s", "8s", veo_config.get("duration"), s4c)
        assert_eq(4, 3, "veo_config.aspect = 9:16", "9:16", veo_config.get("aspect"), s4c)

        # 4.4 Veo prompts detail
        timeline = ep1.get("timeline", [])
        assert_eq(4, 4, "timeline has 10 entries", 10, len(timeline), s4c)
        s1_veo = timeline[0] if timeline else {}
        assert_eq(4, 4, "S01_01 has t", "0.0-8", s1_veo.get("t"), s4c)
        assert_eq(4, 4, "S01_01 has refs", True, len(s1_veo.get("reference_image", [])) > 0, s4c)
        assert_eq(4, 4, "S01_01 has prompt (long)", True, len(s1_veo.get("prompt", "")) > 50, s4c)
        assert_eq(4, 4, "S01_01 has vo (Thai)", True,
                  any(ord(c) >= 0x0E00 for c in s1_veo.get("vo", "")), s4c)
        assert_eq(4, 4, "S01_01 has audio_cue", True,
                  len(s1_veo.get("audio_cue", "")) > 0, s4c)
        thai_scenes = sum(1 for c in timeline if any(ord(x) >= 0x0E00 for x in c.get("vo", "")))
        assert_eq(4, 4, "Thai VO in all 10 clips", 10, thai_scenes, s4c)

        # Get visible scene detail
        await page.wait_for_timeout(1000)
        s4d = await shoot(page, "04d-veo-scene-1")
        first_vo = ""
        first_audio = ""
        try:
            items = await page.query_selector_all('.veo-item')
            if items:
                vo_el = await items[0].query_selector('[class*="vo"]')
                if vo_el:
                    first_vo = (await vo_el.text_content()) or ""
                audio_el = await items[0].query_selector('[class*="audio"]')
                if audio_el:
                    first_audio = (await audio_el.text_content()) or ""
        except Exception as e:
            print(f"      [veo selector] {e}")""
        assert_contains(4, 4, "Scene 1 VO rendered", "มิ้นท์", first_vo, s4d)
        assert_contains(4, 4, "Scene 1 Audio rendered", "morning", first_audio, s4d)
        assert_eq(4, 4, "Generate Video button visible", True,
                  await page.is_visible('button:has-text("Generate Video")'), s4d)

        # 4.5 Project refs
        refs = project_data["data"].get("refs", [])
        assert_eq(4, 5, "Project has 3 refs", 3, len(refs), s4c)
        slots = [r.get("slot") for r in refs]
        assert_eq(4, 5, "Ref slots: ref1, ref2, ref3", True,
                  set(slots) >= {"ref1", "ref2", "ref3"}, s4c)
        ref_paths = [r.get("url") for r in refs if r.get("url", "").startswith("/opt/")]
        for rp in ref_paths:
            exists = os.path.exists(rp)
            print(f"      ref {os.path.basename(rp)}: exists={exists}")
        assert_eq(4, 5, "All ref files exist on disk", True,
                  all(os.path.exists(rp) for rp in ref_paths), s4c)

        veo_assets = ep1.get("veo_assets", {})
        assert_eq(4, 5, "veo_assets has 3 refs", 3, len(veo_assets), s4c)

        # Final overview
        s_overview = await shoot_full(page, "99-final-overview")

        await browser.close()
    return network


if __name__ == "__main__":
    print(f"📁 Output: {OUT}")
    network = asyncio.run(main())
    elapsed = time.time() - start_time

    passed = sum(1 for a in assertions if a["status"] == "PASS")
    failed = sum(1 for a in assertions if a["status"] == "FAIL")
    total = len(assertions)

    print(f"\n{'='*70}")
    print(f"📊 TC-01a (Steps 1-4 DEEP): {passed}/{total} PASS, {failed} FAIL")
    print(f"⏱️  Elapsed: {elapsed:.1f}s")
    print(f"📡 Network calls: {len(network)}")
    print(f"📸 Screenshots: {OUT}/screenshots/")
    print(f"{'='*70}")

    with open(OUT / "results.json", "w") as f:
        json.dump({
            "test": "TC-01a Steps 1-4 Deep",
            "started": datetime.fromtimestamp(start_time).isoformat(),
            "elapsed_sec": elapsed,
            "total_assertions": total,
            "passed": passed,
            "failed": failed,
            "assertions": assertions,
            "network": network,
        }, f, indent=2, ensure_ascii=False)

    # HTML report
    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>TC-01a Deep Report</title>
<style>
body { font-family: -apple-system, sans-serif; max-width: 1400px; margin: 0 auto; padding: 20px; background: #0a0a14; color: #e0e0e0; }
h1 { color: #fbbf24; }
h2 { color: #60a5fa; border-bottom: 1px solid #333; padding-bottom: 8px; margin-top: 32px; }
.summary { display: flex; gap: 16px; margin: 16px 0; }
.box { background: #1a1a2e; padding: 16px; border-radius: 8px; flex: 1; text-align: center; }
.num { font-size: 36px; font-weight: bold; }
.lbl { color: #888; font-size: 12px; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }
th { background: #2a2a3e; padding: 8px; text-align: left; color: #fbbf24; }
td { padding: 6px 8px; border-bottom: 1px solid #222; vertical-align: top; }
tr.PASS td { background: rgba(16, 185, 129, 0.05); }
tr.FAIL td { background: rgba(239, 68, 68, 0.05); }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }
.badge.PASS { background: #065f46; color: #6ee7b7; }
.badge.FAIL { background: #7f1d1d; color: #fca5a5; }
.screenshot { max-width: 100%; border-radius: 4px; border: 1px solid #333; margin: 8px 0; }
.network { background: #000; padding: 12px; border-radius: 4px; font-family: monospace; font-size: 11px; max-height: 400px; overflow: auto; }
.network .ok { color: #6ee7b7; }
.network .err { color: #fca5a5; }
.step-section { background: #1a1a2e; border-radius: 8px; padding: 20px; margin: 16px 0; border-left: 4px solid #60a5fa; }
</style></head>
<body>
<h1>🧪 TC-01a: Steps 1-4 Deep Test</h1>
<p><strong>Started:</strong> """ + datetime.fromtimestamp(start_time).isoformat() + """</p>
<p><strong>Elapsed:</strong> """ + f"{elapsed:.1f}s" + """</p>

<div class="summary">
    <div class="box"><div class="num" style="color:#10b981">""" + str(passed) + """</div><div class="lbl">PASSED</div></div>
    <div class="box"><div class="num" style="color:#ef4444">""" + str(failed) + """</div><div class="lbl">FAILED</div></div>
    <div class="box"><div class="num">""" + str(total) + """</div><div class="lbl">TOTAL</div></div>
    <div class="box"><div class="num">""" + str(len(network)) + """</div><div class="lbl">API CALLS</div></div>
</div>

<h2>📋 Assertions by Step</h2>
<table>
<thead><tr><th>Step</th><th>Sub</th><th>Name</th><th>Expected</th><th>Actual</th><th>Status</th></tr></thead>
<tbody>
"""
    for a in assertions:
        html += f"""<tr class="{a['status']}">
    <td>{a['step']}</td>
    <td>{a['substep']}</td>
    <td>{a['name']}</td>
    <td><code>{a['expected']}</code></td>
    <td><code>{a['actual'][:150]}</code></td>
    <td><span class="badge {a['status']}">{a['status']}</span></td>
</tr>
"""
    html += "</tbody></table>"

    for step_num in sorted(set(a["step"] for a in assertions)):
        step_asserts = [a for a in assertions if a["step"] == step_num]
        html += f'<div class="step-section">\n<h2>Step {step_num}</h2>\n'
        html += f'<p>{len(step_asserts)} assertions</p>\n'
        screenshots = list(set(a["screenshot"] for a in step_asserts if a.get("screenshot")))
        for s in screenshots:
            html += f'<img class="screenshot" src="{s}" />\n'
        html += '</div>\n'

    html += '<h2>📡 Network Calls</h2><div class="network">'
    for n in network:
        cls = "ok" if 200 <= n["status"] < 300 else "err"
        html += f'<div class="{cls}">[{n["ts"]:.1f}s] {n["status"]} {n["method"]} {n["url"]}</div>\n'
    html += '</div>'

    html += "</body></html>"

    with open(OUT / "report.html", "w") as f:
        f.write(html)

    print(f"\n✅ Report: {OUT}/report.html")
    sys.exit(0 if failed == 0 else 1)
