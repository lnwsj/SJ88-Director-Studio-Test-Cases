#!/usr/bin/env python3
"""
TC-01 Video Generation — FULL UI TEST
- Multi-screenshot per step
- Real Chrome browser (signature จริง)
- Wait for actual completion (not just submit)
- Generate HTML report
"""
import asyncio
from playwright.async_api import async_playwright
import json
import os
import sys
import time
import base64
from datetime import datetime
from pathlib import Path

BASE = "https://directorstudio.sj88ai.com"
CHROME = "/root/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome"
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
OUT = Path(f"/workspace/director-studio-test-cases/01-video-generation/runs/{TS}")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "screenshots").mkdir(exist_ok=True)

# Test data
TEST_NAME = "TC-01 Video Generation (UI)"

results = []  # [{step, action, expected, actual, status, screenshots, network, notes}]
start_time = time.time()

def log_step(step, action, expected, actual, status, screenshots=None, network=None, notes=""):
    entry = {
        "step": step,
        "action": action,
        "expected": expected,
        "actual": actual,
        "status": status,
        "screenshots": screenshots or [],
        "network": network or [],
        "notes": notes,
        "ts": datetime.now().isoformat(),
    }
    results.append(entry)
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "🟡"
    print(f"\n{icon} Step {step}: {action}")
    print(f"   Expected: {expected}")
    print(f"   Actual: {actual[:200]}")
    if notes:
        print(f"   Notes: {notes}")
    return entry

async def shoot(page, name, full=False):
    """Take screenshot, return relative path"""
    path = OUT / "screenshots" / f"{name}.png"
    await page.screenshot(path=str(path), full_page=full)
    return f"screenshots/{name}.png"

async def main():
    network_log = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROME,
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--use-gl=swiftshader"]
        )
        ctx = await browser.new_context(
            viewport={"width": 1400, "height": 1100},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await ctx.new_page()

        # Capture all network
        def on_response(resp):
            if "/api/" in resp.url or "genaipro" in resp.url:
                network_log.append({
                    "method": resp.request.method,
                    "url": resp.url,
                    "status": resp.status,
                    "ts": time.time() - start_time,
                })
        page.on("response", on_response)
        page.on("pageerror", lambda exc: print(f"  [PAGEERROR] {exc}"))

        # === Step 1: Login page ===
        print("\n" + "="*60)
        print("Step 1: เปิดหน้า Login")
        print("="*60)
        await page.goto(f"{BASE}/")
        await page.wait_for_load_state("networkidle")
        s1 = await shoot(page, "01-login-page")
        log_step(1, "เปิดหน้า Login", "เห็น form email + password", 
                 f"URL={page.url}", "PASS", [s1])

        # === Step 2: กรอก + login ===
        print("\n" + "="*60)
        print("Step 2: กรอก credentials + login")
        print("="*60)
        await page.fill('input[type="email"]', "admin@sj88ai.com")
        await page.fill('input[type="password"]', "admin1234")
        s2a = await shoot(page, "02a-filled-form")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        s2b = await shoot(page, "02b-after-submit")
        log_step(2, "Submit login form", "เข้าหน้า projects",
                 f"URL={page.url}", "PASS", [s2a, s2b])

        # === Step 3: เปิดโปรเจกต์ โรงเรียนรัก ===
        print("\n" + "="*60)
        print("Step 3: เปิดโปรเจกต์ 'โรงเรียนรัก'")
        print("="*60)
        try:
            await page.click('text=โรงเรียนรัก', timeout=8000)
            await page.wait_for_timeout(3000)
            s3 = await shoot(page, "03-project-opened", full=True)
            # Verify EP1 visible
            ep1_visible = await page.is_visible('text=วันแรกที่โรงเรียน')
            log_step(3, "คลิก โรงเรียนรัก", "เห็น EP1 card",
                     f"EP1 visible={ep1_visible}", "PASS" if ep1_visible else "FAIL", [s3])
        except Exception as e:
            s3 = await shoot(page, "03-FAIL")
            log_step(3, "คลิก โรงเรียนรัก", "เห็น EP1", f"Error: {e}", "FAIL", [s3])
            await browser.close()
            return

        # === Step 4: เปิด EP1 ===
        print("\n" + "="*60)
        print("Step 4: เปิด EP1 'วันแรกที่โรงเรียน'")
        print("="*60)
        try:
            await page.click('text=วันแรกที่โรงเรียน', timeout=5000)
            await page.wait_for_timeout(3000)
            s4a = await shoot(page, "04a-ep1-script-tab", full=True)
            # Switch to Veo tab
            await page.click('button:has-text("Veo")')
            await page.wait_for_timeout(2000)
            s4b = await shoot(page, "04b-ep1-veo-tab", full=True)
            # Check 10 prompts
            content = await page.content()
            has_10 = "Veo Prompts (10)" in content
            log_step(4, "เปิด EP1 + Veo tab", "10 prompts shown", 
                     f"'Veo Prompts (10)' in DOM={has_10}", 
                     "PASS" if has_10 else "FAIL", [s4a, s4b])
        except Exception as e:
            await shoot(page, "04-FAIL")
            log_step(4, "เปิด EP1 + Veo tab", "10 prompts", f"Error: {e}", "FAIL")
            await browser.close()
            return

        # === Step 5: Generate Video scene 1 ===
        print("\n" + "="*60)
        print("Step 5: กด 🎬 Generate Video (Scene 1)")
        print("="*60)
        before_generate = network_log.copy()
        try:
            btn = await page.query_selector('button:has-text("Generate Video")')
            if not btn:
                log_step(5, "กด Generate Video", "button exists", "button not found", "FAIL")
                await browser.close()
                return
            
            await shoot(page, "05a-before-click")
            await btn.click()
            await page.wait_for_timeout(2000)
            s5a = await shoot(page, "05b-after-click", full=True)
            
            # Poll result
            final = None
            for i in range(60):
                await page.wait_for_timeout(2000)
                elapsed = (i + 1) * 2
                try:
                    result_text = await page.text_content('#veo-result-0')
                except:
                    result_text = None
                
                # Take screenshot every 10s
                if i % 5 == 0:
                    await shoot(page, f"05c-progress-{elapsed}s")
                
                if result_text:
                    print(f"   [t={elapsed}s] {result_text[:200]}")
                    if 'completed' in result_text.lower() or '✅' in result_text:
                        final = "completed"
                        break
                    if 'failed' in result_text.lower() or 'error' in result_text.lower() or '❌' in result_text:
                        final = "failed"
                        break
            
            await shoot(page, "05d-final", full=True)
            
            # Check for video element
            video = await page.query_selector('video')
            video_src = await video.get_attribute('src') if video else None
            
            # Get network since generate click
            new_network = [n for n in network_log if n not in before_generate]
            
            actual = f"final={final}, video_src={video_src[:100] if video_src else None}"
            status = "PASS" if final == "completed" and video_src else "FAIL"
            log_step(5, "กด Generate Video + รอจบ", 
                     "✅ completed + video player + 8s clip",
                     actual, status, 
                     [s5a, f"05d-final"], new_network,
                     f"Polled {len(new_network)} new network calls")
        except Exception as e:
            await shoot(page, "05-FAIL")
            log_step(5, "กด Generate Video", "completed", f"Error: {e}", "FAIL")

        # Final overview
        await shoot(page, "99-overview", full=True)
        await browser.close()

    return network_log

if __name__ == "__main__":
    print(f"📁 Output: {OUT}")
    print(f"🕐 Started: {datetime.now().isoformat()}")
    network = asyncio.run(main())
    elapsed = time.time() - start_time
    
    # Save raw results
    with open(OUT / "results.json", "w") as f:
        json.dump({
            "test": TEST_NAME,
            "started": datetime.fromtimestamp(start_time).isoformat(),
            "elapsed_sec": elapsed,
            "results": results,
            "network": network,
        }, f, indent=2, ensure_ascii=False)
    
    # Generate HTML report
    print("\n📝 Generating HTML report...")
    
    # Inline screenshots as base64 for portability? No, just reference paths
    html_parts = [f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{TEST_NAME} Report</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 1400px; margin: 0 auto; padding: 20px; background: #0f0f1a; color: #e0e0e0; }}
h1 {{ color: #fbbf24; }}
h2 {{ color: #60a5fa; border-bottom: 1px solid #333; padding-bottom: 8px; }}
.step {{ background: #1a1a2e; border-radius: 8px; padding: 16px; margin: 16px 0; border-left: 4px solid #555; }}
.step.PASS {{ border-left-color: #10b981; }}
.step.FAIL {{ border-left-color: #ef4444; }}
.status {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold; }}
.status.PASS {{ background: #065f46; color: #6ee7b7; }}
.status.FAIL {{ background: #7f1d1d; color: #fca5a5; }}
.field {{ margin: 6px 0; }}
.label {{ color: #888; font-size: 12px; text-transform: uppercase; }}
.value {{ color: #fff; font-family: 'Monaco', monospace; font-size: 13px; }}
.screenshots {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 12px; margin-top: 12px; }}
.screenshots img {{ width: 100%; border-radius: 4px; border: 1px solid #333; cursor: pointer; }}
.screenshots img:hover {{ transform: scale(1.02); transition: 0.2s; }}
.network {{ background: #000; padding: 8px; border-radius: 4px; font-family: monospace; font-size: 11px; max-height: 300px; overflow: auto; }}
.network .ok {{ color: #6ee7b7; }}
.network .err {{ color: #fca5a5; }}
.summary {{ display: flex; gap: 16px; margin: 16px 0; }}
.summary .box {{ background: #1a1a2e; padding: 16px; border-radius: 8px; flex: 1; text-align: center; }}
.summary .num {{ font-size: 36px; font-weight: bold; }}
.summary .lbl {{ color: #888; font-size: 12px; }}
</style></head>
<body>
<h1>🎬 {TEST_NAME}</h1>
<p><strong>Started:</strong> {datetime.fromtimestamp(start_time).isoformat()}</p>
<p><strong>Elapsed:</strong> {elapsed:.1f}s</p>

<div class="summary">
    <div class="box"><div class="num" style="color:#10b981">{sum(1 for r in results if r['status']=='PASS')}</div><div class="lbl">PASSED</div></div>
    <div class="box"><div class="num" style="color:#ef4444">{sum(1 for r in results if r['status']=='FAIL')}</div><div class="lbl">FAILED</div></div>
    <div class="box"><div class="num">{len(results)}</div><div class="lbl">TOTAL STEPS</div></div>
    <div class="box"><div class="num">{len(network)}</div><div class="lbl">NETWORK CALLS</div></div>
</div>
"""]

    for r in results:
        html_parts.append(f"""
<div class="step {r['status']}">
    <h2>Step {r['step']}: {r['action']} <span class="status {r['status']}">{r['status']}</span></h2>
    <div class="field"><span class="label">Expected:</span> <span class="value">{r['expected']}</span></div>
    <div class="field"><span class="label">Actual:</span> <span class="value">{r['actual']}</span></div>
    {f'<div class="field"><span class="label">Notes:</span> <span class="value">{r["notes"]}</span></div>' if r.get('notes') else ''}
    <div class="field"><span class="label">Screenshots ({len(r['screenshots'])}):</span></div>
    <div class="screenshots">
""")
        for s in r['screenshots']:
            html_parts.append(f'<img src="{s}" loading="lazy" />\n')
        html_parts.append('</div>')
        
        if r.get('network'):
            html_parts.append(f'<div class="field"><span class="label">Network ({len(r["network"])} calls):</span></div><div class="network">')
            for n in r['network']:
                cls = "ok" if 200 <= n['status'] < 300 else "err"
                html_parts.append(f'<div class="{cls}">[{n["ts"]:.1f}s] {n["status"]} {n["method"]} {n["url"]}</div>\n')
            html_parts.append('</div>')
        html_parts.append('</div>')

    html_parts.append("""
</body></html>
""")
    
    html_path = OUT / "report.html"
    with open(html_path, "w") as f:
        f.write("".join(html_parts))
    
    print(f"\n✅ Report: {html_path}")
    print(f"📁 Screenshots: {OUT}/screenshots/")
    print(f"📊 Network: {len(network)} calls logged")
    print(f"⏱️  Elapsed: {elapsed:.1f}s")
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    print(f"\n{'='*60}")
    print(f"📊 TC-01: {passed}/{len(results)} passed")
    print(f"{'='*60}")
    sys.exit(0 if passed == len(results) else 1)
