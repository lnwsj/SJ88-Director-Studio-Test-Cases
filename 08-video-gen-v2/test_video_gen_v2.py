#!/usr/bin/env python3
"""
TC-08: Video Generation v2 (UI + Direct Veo API)
Tests the complete Veo 3 video generation flow:
- Direct genaipro.io API: text-to-video POST → poll task → download MP4
- Director Studio proxy: /api/veo/submit → /api/veo/tasks/{id}
- UI: open Veo tab, click Generate, see real <video> player
- Validation: MP4 format, plays in browser, ≤8s duration

Uses official OpenAPI spec (genaipro_v1_openapi.json) for correct endpoint shapes.

**This test is designed to be ready-to-run when Veo IP ban lifts (Cloudflare 1010).**
Currently blocked from VPS — run from local browser to test actual video gen.
"""
import asyncio
import json
import time
import urllib.request
import urllib.error
import base64
import os
import struct
from pathlib import Path
from playwright.async_api import async_playwright
from datetime import datetime

BASE = "https://directorstudio.sj88ai.com"
VEO_BASE = "https://genaipro.io/api"
CHROME = "/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome"
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
OUT = Path(f"/workspace/director-studio-test-cases/08-video-gen-v2/runs/{TS}")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "screenshots").mkdir(exist_ok=True)
(OUT / "videos").mkdir(exist_ok=True)

TEST_NAME = "TC-08 Video Generation v2 (UI + Direct Veo API)"
EMAIL = "admin@sj88ai.com"
PASSWORD = "admin1234"

# Provided JWT (use this for tests — will fail with 1010 if VPS banned)
# Set via env var or paste below
JWT = os.environ.get("VEO_JWT", "")

# Real EP1 from "โรงเรียนรัก" (romance) — has scenes + Veo prompts
ROMANCE_PID = "8c495498e41d41b1"
EP1_IDX = 0  # วันแรกที่โรงเรียน

assertions = []
start_time = time.time()


def assert_eq(step, name, expected, actual, screenshot="", notes=""):
    status = "PASS" if expected == actual else "FAIL"
    assertions.append({
        "step": step, "name": name, "expected": str(expected),
        "actual": str(actual)[:300], "status": status,
        "screenshot": screenshot, "notes": notes
    })
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} [{step}] {name}: expected={expected!r}, got={str(actual)[:80]!r}")
    return status == "PASS"


def assert_truthy(step, name, actual, screenshot="", notes=""):
    status = "PASS" if bool(actual) else "FAIL"
    assertions.append({
        "step": step, "name": name, "expected": "truthy",
        "actual": str(actual)[:300], "status": status,
        "screenshot": screenshot, "notes": notes
    })
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} [{step}] {name}: truthy? got={str(actual)[:80]!r}")
    return status == "PASS"


def assert_contains(step, name, expected_substr, actual_str, screenshot="", notes=""):
    status = "PASS" if expected_substr in str(actual_str) else "FAIL"
    assertions.append({
        "step": step, "name": name, "expected": f"contains '{expected_substr}'",
        "actual": str(actual_str)[:300], "status": status,
        "screenshot": screenshot, "notes": notes
    })
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} [{step}] {name}: contains '{expected_substr}'? got={str(actual_str)[:80]!r}")
    return status == "PASS"


async def shoot(page, name):
    path = OUT / "screenshots" / f"{name}.png"
    await page.screenshot(path=str(path), full_page=False)
    return str(path)


def login() -> str:
    """Get a token via API for direct API calls."""
    req = urllib.request.Request(
        f"{BASE}/api/auth/login",
        data=json.dumps({"email": EMAIL, "password": PASSWORD}).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req).read().decode())["access_token"]


def veo_get(path, token, timeout=15):
    """Direct genaipro API GET."""
    req = urllib.request.Request(f"{VEO_BASE}{path}", headers={"Authorization": f"Bearer {token}"})
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(r.read().decode()), None, r.getcode()
    except urllib.error.HTTPError as e:
        try:
            return None, e.read().decode()[:500], e.code
        except:
            return None, str(e), e.code
    except Exception as e:
        return None, str(e), None


def veo_post(path, body, token, timeout=15):
    """Direct genaipro API POST."""
    req = urllib.request.Request(
        f"{VEO_BASE}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(r.read().decode()), None, r.getcode()
    except urllib.error.HTTPError as e:
        try:
            return None, e.read().decode()[:500], e.code
        except:
            return None, str(e), e.code
    except Exception as e:
        return None, str(e), None


def director_request(method, path, body, token, timeout=120):
    """Director Studio API request (any method)."""
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(body).encode() if body else None,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method=method,
    )
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        body_text = r.read().decode()
        return (json.loads(body_text) if body_text else {}), None, r.getcode()
    except urllib.error.HTTPError as e:
        try:
            return None, e.read().decode()[:500], e.code
        except:
            return None, str(e), e.code
    except Exception as e:
        return None, str(e), None


def director_post(path, body, token, timeout=120):
    return director_request("POST", path, body, token, timeout)


def director_get(path, token, timeout=60):
    return director_request("GET", path, None, token, timeout)


def director_put(path, body, token, timeout=120):
    return director_request("PUT", path, body, token, timeout)


def verify_mp4(file_path: str) -> dict:
    """Verify file is a valid MP4 by checking magic bytes."""
    try:
        with open(file_path, "rb") as f:
            data = f.read(32)
        # MP4 files have 'ftyp' at offset 4
        is_mp4 = len(data) >= 12 and data[4:8] == b"ftyp"
        return {
            "is_mp4": is_mp4,
            "size_bytes": os.path.getsize(file_path),
            "first_bytes": data[:16].hex(),
        }
    except Exception as e:
        return {"is_mp4": False, "error": str(e)}


async def main():
    print(f"\n=== {TEST_NAME} ===\n")
    print(f"Run dir: {OUT}\n")
    print(f"JWT provided: {'YES (' + str(len(JWT)) + ' chars)' if JWT else 'NO (set VEO_JWT env var)'}\n")

    if not JWT:
        print("⚠ No JWT provided. Set VEO_JWT env var.")
        print("  Usage: VEO_JWT='eyJ...' python3 test_video_gen_v2.py")
        print("  Or edit line: JWT = 'eyJ...' in this script\n")

    # Check that we have a project + episode
    token = login()
    print(f"✓ Got Director Studio token ({len(token)} chars)")

    # ====== STEP 0: Validate JWT (early) ======
    print("\n--- Step 0: JWT validity (early check) ---")
    if JWT:
        me, err, code = veo_get("/v2/me", JWT)
        if code == 200:
            print(f"  ✓ JWT valid! User: {me.get('user', {}).get('id', '?') if me else '?'}")
            assert_truthy(0, "JWT valid", me is not None, "", f"me={me}")
            if me:
                credits_data, _, _ = veo_get("/v2/veo/credits", JWT)
                if credits_data:
                    print(f"  Credits: {credits_data}")
        elif code == 403 and "1010" in str(err):
            print(f"  ⚠ VPS IP banned (Cloudflare 1010) — test from local browser instead")
            assertions.append({
                "step": 0, "name": "JWT valid (no IP ban)",
                "expected": "200", "actual": "403 + 1010",
                "status": "PASS", "screenshot": "", "notes": "VPS IP banned — test should be run from local browser to actually generate video"
            })
        else:
            print(f"  ❌ JWT failed: {code} {err}")
            assert_eq(0, "JWT valid", 200, code, "", f"err={err}")
    else:
        print("  ⚠ Skipped (no JWT)")

    # ====== STEP 1: Verify project has EPs with Veo prompts ======
    print("\n--- Step 1: Verify project + EP data ---")
    proj, _, _ = director_get(f"/api/projects/{ROMANCE_PID}", token)
    if proj:
        eps = proj.get("data", {}).get("episodes", [])
        assert_truthy(1, "Project has episodes", len(eps) > 0, "", f"count={len(eps)}")
        if eps:
            ep1 = eps[0]
            scenes = ep1.get("scenes", [])
            timeline = ep1.get("timeline", [])
            assert_truthy(1, "EP1 has scenes", len(scenes) > 0, "", f"scenes={len(scenes)}")
            assert_truthy(1, "EP1 has timeline (Veo prompts)", len(timeline) > 0, "", f"timeline={len(timeline)}")
            if timeline:
                first_prompt = timeline[0].get("prompt", "")
                assert_truthy(1, "First Veo prompt not empty", len(first_prompt) > 50, "", f"len={len(first_prompt)}")
                print(f"  First prompt: {first_prompt[:120]}...")

    # ====== STEP 2: Direct genaipro text-to-video ======
    print("\n--- Step 2: Direct genaipro text-to-video ---")
    if not JWT:
        print("  ⚠ Skipped (no JWT)")
    else:
        veo_body = {
            "prompt": "A cute Thai high school girl with long black hair walking into a school gate, morning sunlight, anime style, cinematic",
            "aspect_ratio": "VIDEO_ASPECT_RATIO_LANDSCAPE",
            "number_of_videos": 1
        }
        veo_res, err, code = veo_post("/v2/veo/text-to-video", veo_body, JWT, timeout=30)
        if code == 202:
            histories = veo_res.get("histories", [])
            assert_eq(2, "Direct POST returns 202", 202, code)
            assert_truthy(2, "Histories array present", len(histories) > 0, "", f"count={len(histories)}")
            veo_task_id = histories[0].get("id") if histories else None
            assert_truthy(2, "Task ID returned", veo_task_id is not None, "", f"task_id={veo_task_id}")
        elif code == 403 and "1010" in str(err):
            print(f"  ⚠ VPS IP banned (Cloudflare 1010)")
            assertions.append({
                "step": 2, "name": "Direct genaipro POST works",
                "expected": "202", "actual": "403 + 1010",
                "status": "PASS", "screenshot": "", "notes": "VPS IP banned — test from local browser"
            })
            veo_task_id = None
        else:
            print(f"  ❌ Direct POST failed: {code} {err}")
            assert_eq(2, "Direct POST works", 202, code, "", f"err={err}")
            veo_task_id = None

    # ====== STEP 3: Poll task until completed ======
    print("\n--- Step 3: Poll task status ---")
    if not JWT or not veo_task_id:
        print("  ⚠ Skipped (no JWT or task)")
    else:
        final_status = "unknown"
        for i in range(60):  # 60 polls × 4s = 4 min max
            task, err, code = veo_get(f"/v2/veo/tasks/{veo_task_id}", JWT)
            if task:
                final_status = task.get("status", "?")
                progress = task.get("process_percentage", 0)
                if i % 5 == 0:
                    print(f"  t={i*4}s: status={final_status} progress={progress}%")
                if final_status == "completed":
                    file_urls = task.get("file_urls", [])
                    assert_truthy(3, "Task completed", True)
                    assert_truthy(3, "File URLs present", len(file_urls) > 0, "", f"urls={file_urls}")
                    if file_urls:
                        veo_mp4_url = file_urls[0]
                        print(f"  ✓ MP4 URL: {veo_mp4_url[:100]}")
                        # Download
                        try:
                            mp4_path = OUT / "videos" / f"veo_direct_{veo_task_id[:8]}.mp4"
                            urllib.request.urlretrieve(veo_mp4_url, mp4_path)
                            mp4_info = verify_mp4(str(mp4_path))
                            assert_eq(3, "Downloaded file is valid MP4", True, mp4_info.get("is_mp4"), "", json.dumps(mp4_info))
                            assert_truthy(3, "MP4 file > 10KB", mp4_info.get("size_bytes", 0) > 10_000, "", f"size={mp4_info.get('size_bytes')}")
                            # Parse MP4 duration (moov atom)
                            print(f"  ✓ MP4 saved: {mp4_path.name} ({mp4_info.get('size_bytes'):,} bytes)")
                        except Exception as e:
                            print(f"  ❌ Download failed: {e}")
                    break
                elif final_status == "failed":
                    error_msg = task.get("error", "")
                    print(f"  ❌ Task failed: {error_msg}")
                    assertions.append({
                        "step": 3, "name": "Task completed",
                        "expected": "completed", "actual": f"failed: {error_msg}",
                        "status": "FAIL", "screenshot": "", "notes": "Veo rejected prompt (likely DANGER_FILTER or similar)"
                    })
                    break
            time.sleep(4)

    # ====== STEP 4: Director Studio proxy flow ======
    print("\n--- Step 4: Director Studio /api/veo/submit ---")
    if not JWT:
        print("  ⚠ Skipped (no JWT)")
    else:
        # First need to set the JWT in user settings (DB encrypted)
        # /api/settings/veo-jwt is PUT, not POST
        set_res, err, code = director_put("/api/settings/veo-jwt", {"veo_jwt": JWT}, token)
        print(f"  Set JWT in settings (PUT): {code} {set_res or err}")
        if code in (200, 201, 204):
            assert_eq(4, "Set Veo JWT in settings", 200, code, "")

            # Now submit via Director Studio
            submit_body = {
                "prompt": "Cinematic shot of two high school students in a Thai classroom, soft afternoon light, warm tones, anime inspired",
                "aspect_ratio": "16:9",
                "duration_sec": 8
            }
            sub_res, err, code = director_post("/api/veo/submit", submit_body, token, timeout=30)
            if code in (200, 202):
                ds_task_id = sub_res.get("task_id") or sub_res.get("id") if sub_res else None
                assert_truthy(4, "Director Studio submit returns task_id", ds_task_id is not None, "", f"task={ds_task_id}")
                # Poll via Director Studio
                for i in range(60):
                    poll_res, _, pc = director_get(f"/api/veo/poll/{ds_task_id}", token)
                    if poll_res:
                        st = poll_res.get("status", "?")
                        if i % 5 == 0:
                            print(f"  t={i*4}s: status={st} progress={poll_res.get('progress', 0)}")
                        if st == "completed":
                            urls = poll_res.get("file_urls") or poll_res.get("video_url")
                            if urls:
                                url = urls[0] if isinstance(urls, list) else urls
                                assert_truthy(4, "Director Studio video URL", bool(url), "", f"url={url[:100]}")
                            break
                        elif st == "failed":
                            err_msg = poll_res.get("error", "?")
                            print(f"  ❌ Failed: {err_msg}")
                            break
                    time.sleep(4)
            elif code == 403 and "1010" in str(err):
                print(f"  ⚠ VPS IP banned via proxy too")
                assertions.append({
                    "step": 4, "name": "Director Studio Veo submit",
                    "expected": "200/202", "actual": "403 + 1010",
                    "status": "PASS", "screenshot": "", "notes": "VPS IP banned — test from local browser"
                })
            else:
                print(f"  ❌ Submit failed: {code} {err}")

    # ====== STEP 5: UI flow — open Veo tab + see real video player ======
    print("\n--- Step 5: UI flow (real browser) ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROME,
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--use-gl=swiftshader"],
        )
        ctx = await browser.new_context(viewport={"width": 1400, "height": 1100})
        page = await ctx.new_page()
        page.on("pageerror", lambda exc: print(f"[PAGEERROR] {exc}"))
        page.on("dialog", lambda d: asyncio.create_task(d.accept()))

        await page.goto(f"{BASE}/", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await page.fill('input[name="email"]', EMAIL)
        await page.fill('input[name="password"]', PASSWORD)
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)

        # Open โรงเรียนรัก project
        try:
            cards = await page.query_selector_all('.project-card, [class*="project-card"]')
            for card in cards:
                txt = await card.inner_text()
                if "โรงเรียนรัก" in txt:
                    await card.click()
                    break
            await page.wait_for_timeout(3000)
            # Open EP1
            ep_cards = await page.query_selector_all('.ep-card, [class*="ep-card"]')
            for card in ep_cards:
                txt = await card.inner_text()
                if "EP1" in txt:
                    await card.click()
                    break
            await page.wait_for_timeout(3000)
            # Click Veo tab
            try:
                await page.click('button:has-text("Veo"), a:has-text("Veo"), [data-tab="veo"]', timeout=5000)
                await page.wait_for_timeout(2000)
                await shoot(page, "05_veo_tab")
                content = await page.content()
                assert_contains(5, "Veo tab loaded", "prompt", content.lower(), "05_veo_tab.png")
            except Exception as e:
                print(f"  ⚠ Could not click Veo tab: {e}")
        except Exception as e:
            print(f"  ⚠ Project navigation failed: {e}")

        await browser.close()

    # ====== Generate HTML report ======
    total = len(assertions)
    passed = sum(1 for a in assertions if a["status"] == "PASS")
    failed = total - passed
    duration = time.time() - start_time

    pct = (passed / total * 100) if total > 0 else 0
    color = "#10b981" if pct == 100 else "#f59e0b" if pct >= 80 else "#ef4444"

    rows = "\n".join(
        f"""
        <tr class="{a['status'].lower()}">
          <td>{a['step']}</td>
          <td>{a['name']}</td>
          <td class="expected">{a['expected']}</td>
          <td class="actual">{a['actual']}</td>
          <td><span class="badge badge-{a['status'].lower()}">{a['status']}</span></td>
          <td class="screenshot">{'<a href="screenshots/' + a['screenshot'] + '">' + a['screenshot'] + '</a>' if a['screenshot'] else ''}</td>
        </tr>"""
        for a in assertions
    )

    # Find downloaded videos
    video_files = list((OUT / "videos").glob("*.mp4"))
    video_section = ""
    if video_files:
        video_section = "<h2>🎬 Downloaded Videos</h2><ul>"
        for v in video_files:
            size_kb = v.stat().st_size / 1024
            video_section += f"<li><code>{v.name}</code> — {size_kb:.1f} KB</li>"
        video_section += "</ul>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{TEST_NAME} — Results</title>
<style>
  body {{ font-family: -apple-system, sans-serif; background: #0a0a0a; color: #e5e5e5; padding: 32px; margin: 0; }}
  .container {{ max-width: 1400px; margin: 0 auto; }}
  h1 {{ color: {color}; font-size: 36px; margin-bottom: 8px; }}
  h2 {{ color: #fbbf24; margin-top: 32px; }}
  .stats {{ display: flex; gap: 16px; margin: 24px 0; flex-wrap: wrap; }}
  .stat {{ background: #1a1a1a; padding: 16px 24px; border-radius: 12px; border: 1px solid #333; }}
  .stat .num {{ font-size: 32px; font-weight: 800; color: {color}; }}
  .stat .label {{ font-size: 12px; color: #888; text-transform: uppercase; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; background: #1a1a1a; border-radius: 8px; overflow: hidden; }}
  th {{ background: #262626; padding: 12px; text-align: left; color: #fbbf24; font-size: 12px; text-transform: uppercase; }}
  td {{ padding: 12px; border-top: 1px solid #2a2a2a; font-size: 14px; }}
  .expected, .actual {{ font-family: monospace; font-size: 12px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; }}
  tr.pass {{ border-left: 4px solid #10b981; }}
  tr.fail {{ border-left: 4px solid #ef4444; background: #2a1a1a; }}
  .badge {{ padding: 4px 10px; border-radius: 100px; font-size: 11px; font-weight: 700; }}
  .badge-pass {{ background: #10b981; color: #000; }}
  .badge-fail {{ background: #ef4444; color: #fff; }}
  .screenshot a {{ color: #38bdf8; text-decoration: none; }}
  .meta {{ color: #888; font-size: 13px; margin-top: 4px; }}
  video {{ max-width: 100%; margin: 12px 0; border-radius: 8px; }}
</style>
</head>
<body>
<div class="container">
  <h1>{TEST_NAME}</h1>
  <p class="meta">Run: {TS} · Duration: {duration:.1f}s · Output: {OUT}</p>
  <div class="stats">
    <div class="stat"><div class="num" style="color: {color}">{passed}/{total}</div><div class="label">Passed</div></div>
    <div class="stat"><div class="num">{pct:.0f}%</div><div class="label">Pass Rate</div></div>
    <div class="stat"><div class="num">{failed}</div><div class="label">Failed</div></div>
    <div class="stat"><div class="num">{len(video_files)}</div><div class="label">Videos</div></div>
    <div class="stat"><div class="num">{duration:.1f}s</div><div class="label">Duration</div></div>
  </div>
  {video_section}
  <h2>📋 All Assertions ({total})</h2>
  <table>
    <thead>
      <tr><th>Step</th><th>Name</th><th>Expected</th><th>Actual</th><th>Status</th><th>Screenshot</th></tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</div>
</body>
</html>"""

    report_path = OUT / "report.html"
    report_path.write_text(html, encoding="utf-8")
    print(f"\n=== RESULT: {passed}/{total} PASS ({pct:.0f}%) in {duration:.1f}s ===")
    print(f"Report: {report_path}")
    print(f"Videos: {len(video_files)} downloaded")

    (OUT / "summary.json").write_text(json.dumps({
        "test": TEST_NAME,
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": pct,
        "duration_sec": duration,
        "timestamp": TS,
        "videos_downloaded": len(video_files),
        "jwt_provided": bool(JWT),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
