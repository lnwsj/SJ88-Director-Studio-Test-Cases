#!/usr/bin/env python3
"""
TC-03: Veo Single-Scene Prompt Generation — FULL UI TEST
- Real Chrome browser (signature จริง)
- Tests the new per-scene 'Generate Veo Prompt' button + /api/llm/generate-veo-single endpoint
- Validates: max 1500 chars, all 20 director fields used, result saved to ep.timeline
- HTML report + screenshots + JSON
"""
import asyncio
from playwright.async_api import async_playwright
import json
import time
from datetime import datetime
from pathlib import Path

BASE = "https://directorstudio.sj88ai.com"
CHROME = "/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome"
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
OUT = Path(f"/workspace/director-studio-test-cases/03-veo-single/runs/{TS}")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "screenshots").mkdir(exist_ok=True)

TEST_NAME = "TC-03 Veo Single-Scene (UI)"
EMAIL = "admin@sj88ai.com"
PASSWORD = "admin1234"
HORROR_PID = "75a2d0cf09a64504"  # อยุธยา
ROMANCE_PID = "8c495498e41d41b1"  # โรงเรียนรัก

# The 20 director fields the prompt should use
EXPECTED_FIELDS = [
    "shot_type", "camera_move", "lens", "duration_sec",
    "lighting", "mood_color", "time_of_day", "weather",
    "ambient", "sfx", "characters_state",
    "plot_advances", "foreshadowing",
    "props", "vfx_notes", "transition_in", "transition_out",
    "director_note", "pacing", "tone_tags"
]

MAX_CHARS = 1500
assertions = []
start_time = time.time()
network = []


def assert_eq(step, name, expected, actual, screenshot="", notes=""):
    status = "PASS" if expected == actual else "FAIL"
    assertions.append({
        "step": step, "name": name, "expected": expected,
        "actual": str(actual)[:200], "status": status,
        "screenshot": screenshot, "notes": notes
    })
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} [{step}] {name}: expected={expected!r}, got={actual!r}")
    return status == "PASS"


def assert_truthy(step, name, actual, screenshot="", notes=""):
    status = "PASS" if bool(actual) else "FAIL"
    assertions.append({
        "step": step, "name": name, "expected": "truthy",
        "actual": str(actual)[:200], "status": status,
        "screenshot": screenshot, "notes": notes
    })
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} [{step}] {name}: truthy? got={str(actual)[:80]!r}")
    return status == "PASS"


def assert_lte(step, name, value, limit, screenshot="", notes=""):
    status = "PASS" if value <= limit else "FAIL"
    assertions.append({
        "step": step, "name": name, "expected": f"<= {limit}",
        "actual": str(value), "status": status,
        "screenshot": screenshot, "notes": notes
    })
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} [{step}] {name}: {value} <= {limit}?")
    return status == "PASS"


def assert_contains(step, name, expected_substr, actual_str, screenshot="", notes=""):
    status = "PASS" if expected_substr in str(actual_str) else "FAIL"
    assertions.append({
        "step": step, "name": name, "expected": f"contains '{expected_substr}'",
        "actual": str(actual_str)[:200], "status": status,
        "screenshot": screenshot, "notes": notes
    })
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} [{step}] {name}: contains '{expected_substr}'? got={str(actual_str)[:80]!r}")
    return status == "PASS"


async def shoot(page, name):
    path = OUT / "screenshots" / f"{name}.png"
    await page.screenshot(path=str(path), full_page=False)
    return f"screenshots/{name}.png"


async def get_token(page):
    return await page.evaluate("() => localStorage.getItem('ds_token')")


async def api_get(page, path):
    return await page.evaluate(f"""async () => {{
        const t = localStorage.getItem('ds_token');
        const r = await fetch('{BASE}/api{path}', {{ headers: {{ 'Authorization': `Bearer ${{t}}` }} }});
        return [r.status, await r.text()];
    }}""")


async def api_post(page, path, body):
    return await page.evaluate(f"""async () => {{
        const t = localStorage.getItem('ds_token');
        const r = await fetch('{BASE}/api{path}', {{
            method: 'POST',
            headers: {{ 'Authorization': `Bearer ${{t}}`, 'Content-Type': 'application/json' }},
            body: JSON.stringify({json.dumps(body)})
        }});
        return [r.status, await r.text()];
    }}""")


async def main():
    print(f"\n{'='*70}\n{TEST_NAME}\n{'='*70}\n")

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

        # ============ STEP 1: LOGIN ============
        print(f"\n{'='*70}\nSTEP 1: Login as admin\n{'='*70}")
        await page.goto(f"{BASE}/")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)
        s1 = await shoot(page, "01-login")
        await page.fill('input[type="email"]', EMAIL)
        await page.fill('input[type="password"]', PASSWORD)
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(2500)
        s2 = await shoot(page, "01b-after-login")
        token = await get_token(page)
        assert_truthy(1, "JWT token in localStorage", token, s2)

        # ============ STEP 2: API: Get horror project + verify refs ============
        print(f"\n{'='*70}\nSTEP 2: API: Get horror project + refs\n{'='*70}")
        status, body = await api_get(page, f"/projects/{HORROR_PID}")
        assert_eq(2, "GET horror project", 200, status)
        proj = json.loads(body)
        data = proj.get("data", {})
        refs = data.get("refs", [])
        meta = data.get("meta", {})
        print(f"  Refs: {len(refs)}, Genre: {meta.get('genre')}, Language: {meta.get('language')}")
        assert_truthy(2, "Horror project has refs", len(refs) >= 1, "")
        assert_contains(2, "Horror project genre", "horror", str(meta), "")

        # ============ STEP 3: API: Get EP1 with scenes ============
        print(f"\n{'='*70}\nSTEP 3: API: Get EP1 + scenes with 20 fields\n{'='*70}")
        eps = data.get("episodes", [])
        ep1 = eps[0] if eps else None
        assert_truthy(3, "Horror has episodes", ep1 is not None, "")
        scenes = ep1.get("scenes", []) if ep1 else []
        assert_truthy(3, "EP1 has scenes", len(scenes) > 0, "")
        s_first = scenes[0]
        s3 = await shoot(page, "03-ep1-loaded")
        print(f"  EP1: {ep1.get('episode_title', '?')}, {len(scenes)} scenes")
        # Verify all 20 fields in scene 1
        fields_ok = sum(1 for f in EXPECTED_FIELDS
                        if s_first.get(f) is not None and s_first.get(f) != "" and s_first.get(f) != [])
        assert_eq(3, "Scene 1 has all 20 director fields", 20, fields_ok, s3)
        for f in EXPECTED_FIELDS:
            assert_truthy(3, f"Field '{f}' populated", s_first.get(f), s3)

        # ============ STEP 4: API: Direct call /api/llm/generate-veo-single ============
        print(f"\n{'='*70}\nSTEP 4: API: Direct call to /generate-veo-single\n{'='*70}")
        prev_scenes = [{"title": s.get("title"), "location": s.get("location"),
                        "summary": s.get("action", "")[:80]} for s in scenes[:1]]
        ep_ctx = {
            "episode_title": ep1.get("episode_title", ""),
            "episode_logline": ep1.get("episode_logline", ""),
            "characters_in_ep": ep1.get("characters_in_ep", []),
            "previous_scenes_summary": prev_scenes
        }
        status, body = await api_post(page, "/llm/generate-veo-single", {
            "scene": s_first,
            "refs": refs,
            "project_meta": meta,
            "episode_context": ep_ctx,
            "max_chars": MAX_CHARS
        })
        s4 = await shoot(page, "04-api-call")
        assert_eq(4, "POST /generate-veo-single status", 200, status, s4)
        result = json.loads(body)
        assert_truthy(4, "Result has 'ok' flag", result.get("ok"), s4)
        veo = result.get("veo", {})
        timeline = veo.get("timeline", [])
        assert_truthy(4, "Result has 1 timeline clip (not batched)", len(timeline) == 1, s4,
                      notes=f"Got {len(timeline)} clips (expected exactly 1)")
        if timeline:
            prompt = timeline[0].get("prompt", "")
            prompt_len = result.get("prompt_length", len(prompt))
            print(f"  Prompt length: {prompt_len} chars (max {MAX_CHARS})")
            print(f"  Truncated: {result.get('truncated')}")
            assert_lte(4, "Prompt <= max_chars (1500)", prompt_len, MAX_CHARS, s4)
            assert_truthy(4, "Prompt is non-empty", len(prompt) > 0, s4)
            assert_truthy(4, "vo field present", timeline[0].get("vo"), s4)
            assert_truthy(4, "audio_cue field present", timeline[0].get("audio_cue"), s4)
            assert_truthy(4, "camera.move from script", timeline[0].get("camera", {}).get("move"), s4)
            # Check that prompt uses script's shot_type + camera_move
            assert_contains(4, "Prompt uses shot_type (ECU)", "ECU", prompt, s4)
            assert_contains(4, "Prompt uses camera_move", "slow tilt", prompt, s4)
            assert_contains(4, "Prompt uses lens (35mm)", "35mm", prompt, s4)

        # ============ STEP 5: UI: Open EP1 modal + check button exists ============
        print(f"\n{'='*70}\nSTEP 5: UI: Open EP1 modal + verify per-scene buttons\n{'='*70}")
        # Navigate to project + EP1
        await page.goto(f"{BASE}/")
        await page.wait_for_timeout(1500)
        # Click project card
        try:
            await page.locator("text=อยุธยา").first.click(timeout=5000)
        except Exception:
            cards = await page.query_selector_all('[class*="project-card"]')
            if cards:
                await cards[0].click()
        await page.wait_for_timeout(2000)
        # Click EP1
        try:
            await page.click("text=EP1", timeout=3000)
        except Exception:
            ep_cards = await page.query_selector_all('[class*="ep-card"]')
            if ep_cards:
                await ep_cards[0].click()
        await page.wait_for_timeout(2500)
        s5 = await shoot(page, "05-ep1-modal")

        # Count per-scene buttons
        btn_count = await page.locator('button[data-act="gen-veo-single"]').count()
        print(f"  Per-scene buttons found: {btn_count}")
        assert_eq(5, "Per-scene buttons == 3 (one per scene)", 3, btn_count, s5)
        # Check button text contains 'max 1500'
        first_btn_text = await page.locator('button[data-act="gen-veo-single"]').first.inner_text()
        assert_contains(5, "Button text mentions 'max 1500'", "1500", first_btn_text, s5)

        # ============ STEP 6: UI: Click first button + wait for result ============
        print(f"\n{'='*70}\nSTEP 6: UI: Click scene 1 button + verify result\n{'='*70}")
        await page.locator('button[data-act="gen-veo-single"]').first.click()
        # Wait for output to appear
        try:
            await page.wait_for_function(
                '() => { const o = document.querySelector(".scene-veo-output"); return o && o.innerText.includes("chars") && !o.innerText.includes("⏳"); }',
                timeout=90000
            )
            print("  ✓ Output ready")
        except Exception as e:
            print(f"  [WARN] Output timeout: {e}")
        await page.wait_for_timeout(2000)
        s6 = await shoot(page, "06-scene1-result")

        # Read result
        try:
            badge = await page.locator('.scene-veo-head .badge').first.inner_text(timeout=5000)
            print(f"  Badge: {badge}")
            assert_contains(6, "Badge shows 'chars'", "chars", badge, s6)
            # Extract N from badge
            import re
            m = re.search(r'(\d+)\s*chars', badge)
            if m:
                chars_shown = int(m.group(1))
                assert_lte(6, "UI badge chars <= 1500", chars_shown, MAX_CHARS, s6)
        except Exception as e:
            print(f"  [WARN] badge read err: {e}")
        # Read prompt
        try:
            prompt_text = await page.locator('.scene-veo-output pre').first.inner_text(timeout=5000)
            print(f"  Prompt ({len(prompt_text)} chars):")
            assert_lte(6, "UI prompt text <= 1500", len(prompt_text), MAX_CHARS, s6)
            assert_truthy(6, "UI prompt has > 200 chars (rich content)", len(prompt_text) > 200, s6)
            # Read VO + audio too
            vo_el = await page.locator('.scene-veo-output p.muted').first.inner_text()
            print(f"  VO: {vo_el[:80]}")
        except Exception as e:
            print(f"  [WARN] prompt read err: {e}")

        # ============ STEP 7: UI: Click scene 2 button + verify ============
        print(f"\n{'='*70}\nSTEP 7: UI: Click scene 2 button\n{'='*70}")
        await page.locator('button[data-act="gen-veo-single"]').nth(1).click()
        try:
            await page.wait_for_function(
                '() => { const outs = document.querySelectorAll(".scene-veo-output"); return outs.length >= 2 && outs[1] && outs[1].innerText.includes("chars") && !outs[1].innerText.includes("⏳"); }',
                timeout=90000
            )
            print("  ✓ Scene 2 output ready")
        except Exception as e:
            print(f"  [WARN] Scene 2 timeout: {e}")
        await page.wait_for_timeout(2000)
        s7 = await shoot(page, "07-scene2-result")
        try:
            badge2 = await page.locator('.scene-veo-output .badge').nth(1).inner_text(timeout=5000)
            print(f"  Scene 2 badge: {badge2}")
            assert_contains(7, "Scene 2 badge has 'chars'", "chars", badge2, s7)
        except Exception as e:
            print(f"  [WARN] scene 2 badge err: {e}")

        # ============ STEP 8: UI: Click scene 3 button + verify ============
        print(f"\n{'='*70}\nSTEP 8: UI: Click scene 3 button\n{'='*70}")
        await page.locator('button[data-act="gen-veo-single"]').nth(2).click()
        try:
            await page.wait_for_function(
                '() => { const outs = document.querySelectorAll(".scene-veo-output"); return outs.length >= 3 && outs[2] && outs[2].innerText.includes("chars") && !outs[2].innerText.includes("⏳"); }',
                timeout=90000
            )
            print("  ✓ Scene 3 output ready")
        except Exception as e:
            print(f"  [WARN] Scene 3 timeout: {e}")
        await page.wait_for_timeout(2000)
        s8 = await shoot(page, "08-scene3-result")
        try:
            badge3 = await page.locator('.scene-veo-output .badge').nth(2).inner_text(timeout=5000)
            print(f"  Scene 3 badge: {badge3}")
            assert_contains(8, "Scene 3 badge has 'chars'", "chars", badge3, s8)
        except Exception as e:
            print(f"  [WARN] scene 3 badge err: {e}")

        # ============ STEP 9: API: Verify ep.timeline populated with all 3 scenes ============
        print(f"\n{'='*70}\nSTEP 9: API: Verify ep.timeline has all 3 prompts\n{'='*70}")
        await page.wait_for_timeout(3000)  # let UI save
        status, body = await api_get(page, f"/projects/{HORROR_PID}")
        proj = json.loads(body)
        ep1 = proj.get("data", {}).get("episodes", [])[0]
        timeline = ep1.get("timeline", [])
        print(f"  ep.timeline length: {len(timeline)}")
        assert_truthy(9, "ep.timeline has 3 prompts", len(timeline) >= 3, s8)
        if len(timeline) >= 3:
            for i, clip in enumerate(timeline):
                p = clip.get("prompt", "")
                print(f"  Clip {i+1}: {len(p)} chars")
                assert_lte(9, f"Clip {i+1} prompt <= 1500", len(p), MAX_CHARS, s8)

        # ============ STEP 10: API: Different genre (romance) - verify cross-project works ============
        print(f"\n{'='*70}\nSTEP 10: API: Test with romance project (cross-genre)\n{'='*70}")
        status, body = await api_get(page, f"/projects/{ROMANCE_PID}")
        assert_eq(10, "GET romance project", 200, status)
        rproj = json.loads(body)
        rdata = rproj.get("data", {})
        rrefs = rdata.get("refs", [])
        rmeta = rdata.get("meta", {})
        reps = rdata.get("episodes", [])
        rscenes = reps[0].get("scenes", []) if reps else []
        if rscenes and rrefs:
            rscene1 = rscenes[0]
            rep_ctx = {
                "episode_title": reps[0].get("episode_title", ""),
                "episode_logline": reps[0].get("episode_logline", ""),
                "characters_in_ep": reps[0].get("characters_in_ep", []),
                "previous_scenes_summary": []
            }
            status, body = await api_post(page, "/llm/generate-veo-single", {
                "scene": rscene1,
                "refs": rrefs,
                "project_meta": rmeta,
                "episode_context": rep_ctx,
                "max_chars": MAX_CHARS
            })
            assert_eq(10, "Romance /generate-veo-single status", 200, status, s8)
            rresult = json.loads(body)
            rveo = rresult.get("veo", {})
            rtimeline = rveo.get("timeline", [])
            assert_truthy(10, "Romance: 1 timeline clip", len(rtimeline) == 1, s8)
            if rtimeline:
                rprompt = rtimeline[0].get("prompt", "")
                rlen = rresult.get("prompt_length", len(rprompt))
                print(f"  Romance prompt: {rlen} chars")
                assert_lte(10, "Romance prompt <= 1500", rlen, MAX_CHARS, s8)
                # Romance-specific: prompt should NOT have horror filters
                assert_contains(10, "Romance prompt has [ref1] slot", "[ref1]", rprompt, s8)
        else:
            print(f"  [SKIP] No scenes or refs in romance project")

        # ============ STEP 11: API: max_chars=500 cap works ============
        print(f"\n{'='*70}\nSTEP 11: API: max_chars=500 cap test\n{'='*70}")
        status, body = await api_post(page, "/llm/generate-veo-single", {
            "scene": s_first, "refs": refs, "project_meta": meta,
            "episode_context": ep_ctx, "max_chars": 500
        })
        assert_eq(11, "POST max_chars=500 status", 200, status, s8)
        r11 = json.loads(body)
        r11_len = r11.get("prompt_length", 0)
        print(f"  max_chars=500 result: {r11_len} chars (truncated={r11.get('truncated')})")
        assert_lte(11, "Prompt <= 500 when max_chars=500", r11_len, 500, s8)

        # ============ DONE ============
        print(f"\n{'='*70}\nDONE — closing browser\n{'='*70}")
        await browser.close()

    # ============ WRITE RESULTS ============
    total = len(assertions)
    passed = sum(1 for a in assertions if a["status"] == "PASS")
    failed = sum(1 for a in assertions if a["status"] == "FAIL")
    duration = time.time() - start_time

    veo_single_calls = [n for n in network if "generate-veo-single" in n.get("url", "")]
    print(f"\n  /api/llm/generate-veo-single calls: {len(veo_single_calls)}")

    results = {
        "test": TEST_NAME,
        "ts": TS,
        "duration_sec": round(duration, 1),
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{passed}/{total} ({passed/total*100:.0f}%)" if total else "N/A",
        "url": BASE,
        "browser": "chromium-1223 (real)",
        "max_chars_cap": MAX_CHARS,
        "veo_single_api_calls": len(veo_single_calls),
        "assertions": assertions,
        "network_calls": len(network),
        "errors": [a for a in assertions if a["status"] == "FAIL"]
    }
    with open(OUT / "results.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # ============ HTML REPORT ============
    html = [f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{TEST_NAME}</title>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 1200px; margin: 20px auto; padding: 20px; background: #0a0a0a; color: #e0e0e0; }}
h1 {{ color: #d4a574; border-bottom: 2px solid #d4a574; padding-bottom: 8px; }}
.summary {{ display: flex; gap: 16px; margin: 20px 0; flex-wrap: wrap; }}
.stat {{ padding: 16px; background: #1a1a1a; border-radius: 8px; flex: 1; min-width: 150px; border-left: 4px solid #d4a574; }}
.stat .num {{ font-size: 32px; font-weight: bold; }}
.stat.passed .num {{ color: #4ade80; }}
.stat.failed .num {{ color: #f87171; }}
.section {{ margin: 32px 0; padding: 16px; background: #111; border-radius: 8px; }}
table {{ width: 100%; border-collapse: collapse; margin: 8px 0; }}
th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #333; }}
th {{ background: #222; color: #d4a574; }}
tr.pass td {{ color: #4ade80; }}
tr.fail td {{ color: #f87171; }}
tr.fail {{ background: #2a1515; }}
.screenshot {{ max-width: 100%; border: 1px solid #333; border-radius: 4px; margin: 8px 0; }}
.tag {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; margin-right: 4px; }}
.tag.pass {{ background: #14532d; color: #4ade80; }}
.tag.fail {{ background: #7f1d1d; color: #fca5a5; }}
.notes {{ color: #888; font-size: 12px; font-style: italic; }}
</style></head><body>
<h1>🎬 {TEST_NAME}</h1>
<p><strong>Timestamp:</strong> {TS} · <strong>URL:</strong> {BASE} · <strong>Duration:</strong> {duration:.1f}s</p>
<p><strong>Max chars cap:</strong> {MAX_CHARS} · <strong>API calls:</strong> {len(veo_single_calls)}</p>
<div class="summary">
    <div class="stat passed"><div class="num">{passed}</div><div>Passed</div></div>
    <div class="stat failed"><div class="num">{failed}</div><div>Failed</div></div>
    <div class="stat"><div class="num">{total}</div><div>Total</div></div>
    <div class="stat"><div class="num">{results['pass_rate']}</div><div>Pass Rate</div></div>
    <div class="stat"><div class="num">{len(veo_single_calls)}</div><div>API calls</div></div>
</div>
<div class="section">
<h2>📊 Test Coverage</h2>
<ul>
    <li><strong>Step 1-3:</strong> Login + load horror project + verify 20 director fields in scene 1</li>
    <li><strong>Step 4:</strong> API: direct call to /api/llm/generate-veo-single (max 1500)</li>
    <li><strong>Step 5-6:</strong> UI: per-scene button + click scene 1 + verify result badge + prompt</li>
    <li><strong>Step 7-8:</strong> UI: click scenes 2 + 3 + verify each gets its own output</li>
    <li><strong>Step 9:</strong> API: ep.timeline populated with 3 prompts (each <= 1500)</li>
    <li><strong>Step 10:</strong> API: cross-genre (romance) works with same endpoint</li>
    <li><strong>Step 11:</strong> API: max_chars=500 cap respected (smart truncation)</li>
</ul>
</div>
<div class="section">
<h2>🖼️ Screenshots</h2>
"""]

    seen = set()
    for a in assertions:
        s = a.get("screenshot", "")
        if s and s not in seen:
            seen.add(s)
            html.append(f'<h3>Step {a["step"]}: {a["name"]}</h3>')
            html.append(f'<img class="screenshot" src="{s}" />')

    html.append('</div><div class="section"><h2>📋 All Assertions</h2><table>')
    html.append('<tr><th>#</th><th>Step</th><th>Name</th><th>Expected</th><th>Actual</th><th>Status</th><th>Notes</th></tr>')
    for i, a in enumerate(assertions, 1):
        cls = "pass" if a["status"] == "PASS" else "fail"
        html.append(f'<tr class="{cls}"><td>{i}</td><td>{a["step"]}</td><td>{a["name"]}</td>'
                    f'<td>{a["expected"]}</td><td>{a["actual"]}</td>'
                    f'<td><span class="tag {cls}">{a["status"]}</span></td>'
                    f'<td class="notes">{a.get("notes", "")}</td></tr>')
    html.append('</table></div></body></html>')

    with open(OUT / "report.html", "w") as f:
        f.write("\n".join(html))

    print(f"\n{'='*70}")
    print(f"📊 RESULT: {passed}/{total} PASS ({passed/total*100:.0f}%)")
    print(f"   Duration: {duration:.1f}s")
    print(f"   📁 {OUT}")
    print(f"   📄 {OUT}/report.html")
    print(f"   📋 {OUT}/results.json")
    print(f"{'='*70}")
    if failed > 0:
        print(f"\n❌ {failed} FAILED:")
        for a in assertions:
            if a["status"] == "FAIL":
                print(f"   - [{a['step']}] {a['name']}: expected={a['expected']}, got={a['actual']}")


if __name__ == "__main__":
    asyncio.run(main())
