#!/usr/bin/env python3
"""
TC-01: Video Generation via UI (Playwright + Chromium)

Test นี้ simulate user จริงๆ — เปิด Chrome, login, navigate, กดปุ่ม
ใช้ browser signature จริง → Cloudflare ไม่บล็อก (ถ้า JWT ใช้ได้)

⚠️ MUST run on same machine as Chrome (uses local Chrome binary)
"""
import asyncio
from playwright.async_api import async_playwright
import time
import json
import sys
import os

BASE = "https://directorstudio.sj88ai.com"
CHROME = "/root/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome"
# VPS: /opt/google/chrome/chrome

SCREENSHOTS = "/workspace/director-studio-test-cases/01-video-generation/screenshots"
os.makedirs(SCREENSHOTS, exist_ok=True)

async def main():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROME,
            headless=True,  # No display, but uses real Chrome binary
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--use-gl=swiftshader",
            ]
        )
        ctx = await browser.new_context(
            viewport={"width": 1400, "height": 1100},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await ctx.new_page()
        page.on("pageerror", lambda exc: print(f"  [PAGEERROR] {exc}"))
        page.on("console", lambda msg: print(f"  [console.{msg.type}] {msg.text}") if msg.type == "error" else None)

        # === Step 1: Login ===
        print("\n=== Step 1: Login ===")
        await page.goto(f"{BASE}/")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=f"{SCREENSHOTS}/01-login-page.png")
        await page.fill('input[type="email"]', "admin@sj88ai.com")
        await page.fill('input[type="password"]', "admin1234")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        await page.screenshot(path=f"{SCREENSHOTS}/02-after-login.png")
        url = page.url
        print(f"  URL after login: {url}")
        results.append(("Step 1: Login", "PASS" if "share" not in url else "FAIL", url))

        # === Step 2: เปิด Project โรงเรียนรัก ===
        print("\n=== Step 2: เปิดโปรเจกต์ โรงเรียนรัก ===")
        try:
            await page.click('text=โรงเรียนรัก', timeout=5000)
            await page.wait_for_timeout(3000)
            await page.screenshot(path=f"{SCREENSHOTS}/03-project-view.png")
            results.append(("Step 2: เปิดโปรเจกต์", "PASS", "clicked โรงเรียนรัก"))
        except Exception as e:
            results.append(("Step 2: เปิดโปรเจกต์", "FAIL", str(e)[:200]))
            await page.screenshot(path=f"{SCREENSHOTS}/03-fail.png")
            await browser.close()
            return results

        # === Step 3: เปิด EP1 ===
        print("\n=== Step 3: เปิด EP1 ===")
        try:
            await page.click('text=วันแรกที่โรงเรียน', timeout=5000)
            await page.wait_for_timeout(3000)
            await page.screenshot(path=f"{SCREENSHOTS}/04-ep1-opened.png")
            results.append(("Step 3: เปิด EP1", "PASS", "modal opened"))
        except Exception as e:
            results.append(("Step 3: เปิด EP1", "FAIL", str(e)[:200]))
            await browser.close()
            return results

        # === Step 4: ไป Veo tab ===
        print("\n=== Step 4: ไป Veo tab ===")
        try:
            await page.click('button:has-text("Veo")', timeout=5000)
            await page.wait_for_timeout(2000)
            await page.screenshot(path=f"{SCREENSHOTS}/05-veo-tab.png")
            # Check for Veo Prompts (10) text
            content = await page.content()
            if "Veo Prompts (10)" in content:
                results.append(("Step 4: Veo tab", "PASS", "10 prompts shown"))
            else:
                results.append(("Step 4: Veo tab", "FAIL", "no 10 prompts text"))
        except Exception as e:
            results.append(("Step 4: Veo tab", "FAIL", str(e)[:200]))
            await browser.close()
            return results

        # === Step 5: กด Generate Video scene 1 ===
        print("\n=== Step 5: กด Generate Video scene 1 ===")
        try:
            # Capture network for debugging
            network_log = []
            page.on("response", lambda resp: network_log.append((resp.status, resp.url)) if "/api/" in resp.url else None)

            btn = await page.query_selector('button:has-text("Generate Video")')
            if not btn:
                results.append(("Step 5: กด Generate Video", "FAIL", "button not found"))
                await browser.close()
                return results
            await btn.click()
            print("  Clicked! Polling result every 2s...")
            await page.screenshot(path=f"{SCREENSHOTS}/06-clicked-generate.png")

            # Wait + poll result
            final_status = None
            for i in range(60):  # 120s max
                await page.wait_for_timeout(2000)
                try:
                    result_text = await page.text_content('#veo-result-0')
                except:
                    result_text = None
                elapsed = (i + 1) * 2
                if result_text and ('completed' in result_text.lower() or 'failed' in result_text.lower() or 'error' in result_text.lower() or '%' in result_text or 'http' in result_text.lower()):
                    print(f"  [t={elapsed}s] {result_text[:200]}")
                if result_text and 'completed' in result_text.lower():
                    final_status = "completed"
                    break
                elif result_text and 'failed' in result_text.lower():
                    final_status = "failed"
                    break
                elif result_text and 'error' in result_text.lower():
                    final_status = "error"
                    break

            await page.screenshot(path=f"{SCREENSHOTS}/07-final-result.png", full_page=True)

            # Check for video element
            video_elem = await page.query_selector('video')
            video_src = None
            if video_elem:
                video_src = await video_elem.get_attribute('src')

            results.append(("Step 5: Generate Video", final_status or "TIMEOUT", f"video_src={video_src[:100] if video_src else None}"))

            # Save network log
            with open(f"{SCREENSHOTS}/network.json", "w") as f:
                json.dump(network_log, f, indent=2)
        except Exception as e:
            results.append(("Step 5: Generate Video", "FAIL", str(e)[:200]))
            await page.screenshot(path=f"{SCREENSHOTS}/05-fail.png")

        await browser.close()

    return results

if __name__ == "__main__":
    results = asyncio.run(main())
    print(f"\n{'='*60}")
    passed = sum(1 for _,s,_ in results if s == "PASS")
    print(f"📊 TC-01: {passed}/{len(results)} passed")
    print(f"{'='*60}")
    for name, status, msg in results:
        icon = "✅" if status == "PASS" else "❌"
        print(f"  {icon} {name}: {msg[:150]}")
    sys.exit(0 if passed == len(results) else 1)
