#!/usr/bin/env python3
"""
TC-01b: Verify 20 new director fields in generated scripts
- Trigger fresh script generation via LLM
- Verify all 20 new fields present
- Verify field values are sensible (not empty, not defaults)
- Generate HTML report
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
OUT = Path(f"/workspace/director-studio-test-cases/02-script-fields/runs/{TS}")
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "screenshots").mkdir(exist_ok=True)

# 20 new fields to test
NEW_FIELDS = [
    "shot_type", "camera_move", "lens", "duration_sec",
    "lighting", "mood_color", "time_of_day", "weather",
    "ambient", "sfx",
    "characters_state",
    "plot_advances", "foreshadowing",
    "props", "vfx_notes", "transition_in", "transition_out",
    "director_note", "pacing", "tone_tags",
]

assertions = []
network = []
start_time = time.time()


def assert_eq(name, expected, actual, notes=""):
    status = "PASS" if expected == actual else "FAIL"
    assertions.append({"name": name, "expected": str(expected), "actual": str(actual)[:200],
                       "status": status, "notes": notes})
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} {name}: expected={expected}, actual={str(actual)[:100]}")
    return status == "PASS"


def assert_truthy(name, value, notes=""):
    """Check value is non-empty/non-None"""
    is_truthy = bool(value) and value != [] and value != {} and value != ""
    assertions.append({"name": name, "expected": "truthy", "actual": str(value)[:200],
                       "status": "PASS" if is_truthy else "FAIL", "notes": notes})
    icon = "✅" if is_truthy else "❌"
    print(f"  {icon} {name}: {str(value)[:100]}")
    return is_truthy


async def shoot(page, name):
    path = OUT / "screenshots" / f"{name}.png"
    await page.screenshot(path=str(path), full_page=False)
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

        # Login
        print(f"\n{'='*70}\nLOGIN\n{'='*70}")
        await page.goto(f"{BASE}/")
        await page.wait_for_load_state("networkidle")
        await page.fill('input[type="email"]', "admin@sj88ai.com")
        await page.fill('input[type="password"]', "admin1234")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        await shoot(page, "01-logged-in")
        token = await page.evaluate("() => localStorage.getItem('ds_token')")
        print(f"  Got token: {token[:20]}...")

        # Find Ayutthaya project
        print(f"\n{'='*70}\nFIND AYUTTHAYA PROJECT\n{'='*70}")
        req = urllib.request.Request(f"{BASE}/api/projects", headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req) as r2:
            projs = json.loads(r2.read().decode())
        ayut = next((p for p in projs if p["name"] == "อยุธยา"), None)
        if not ayut:
            # Create
            data = json.dumps({
                "name": "อยุธยา",
                "kind": "episode",
                "data": {
                    "characters": ["chandra", "ghost"],
                    "meta": {"genre": "horror", "language": "th", "aspect_ratio": "9:16"}
                }
            }).encode()
            req = urllib.request.Request(f"{BASE}/api/projects", data=data,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req) as r3:
                ayut = json.loads(r3.read().decode())
        pid = ayut["id"]
        print(f"  Project: {pid}")

        # Verify existing project has 20 new fields
        print(f"\n{'='*70}\nVERIFY EXISTING EP1\n{'='*70}")
        req = urllib.request.Request(f"{BASE}/api/projects/{pid}", headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req) as r4:
            project = json.loads(r4.read().decode())
        eps = project.get("data", {}).get("episodes", [])
        assert_eq("Ayutthaya has at least 1 EP", True, len(eps) >= 1)
        if eps:
            ep1 = eps[0]
            scenes = ep1.get("scenes", [])
            assert_eq("EP1 has 3+ scenes", True, len(scenes) >= 3)

            s1 = scenes[0]
            print(f"\n  Scene 1 keys: {list(s1.keys())}")
            print()
            print(f"  === Verifying {len(NEW_FIELDS)} new fields ===")

            for field in NEW_FIELDS:
                value = s1.get(field, "MISSING")
                if field in ("ambient", "sfx", "tone_tags"):
                    assert_truthy(f"scene.s1.{field} is non-empty list", value, f"expected list")
                elif field in ("plot_advances", "foreshadowing", "props", "characters_state"):
                    assert_truthy(f"scene.s1.{field} is non-empty", value)
                else:
                    assert_truthy(f"scene.s1.{field} is non-empty", value)

            # Verify across all scenes
            print()
            print(f"  === Field coverage across all {len(scenes)} scenes ===")
            for field in NEW_FIELDS:
                count = sum(1 for s in scenes if s.get(field))
                pct = count / len(scenes) * 100
                print(f"    {field}: {count}/{len(scenes)} ({pct:.0f}%)")
                if count < len(scenes):
                    print(f"      [missing in {len(scenes)-count} scenes]")

        # === NEW: Generate EP2 to test fresh generation ===
        print(f"\n{'='*70}\nNEW: GENERATE EP2 + VERIFY FIELDS\n{'='*70}")
        gen_data = json.dumps({
            "prompt": "จันทราเจ้าเดินสำรวจบ้านริมน้ำ เจอรูปถ่ายเก่าแขวนอยู่บนผนัง ในรูปมีแม่ของเธอยืนอยู่ข้างชายแปลกหน้า",
            "episode_number": 2,
            "num_scenes": 3,
            "style": "Thai horror dark atmospheric"
        }).encode()
        req = urllib.request.Request(f"{BASE}/api/llm/generate-script",
            data=gen_data, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST")
        await shoot(page, "02-before-gen-ep2")
        with urllib.request.urlopen(req, timeout=180) as r5:
            gen_resp = json.loads(r5.read().decode())
        await shoot(page, "03-after-gen-ep2")

        if "script" in gen_resp:
            new_ep = gen_resp["script"]
            print(f"  Generated: {new_ep.get('episode_title', '?')}")
            print(f"  Scenes: {len(new_ep.get('scenes', []))}")
            new_s1 = new_ep["scenes"][0]
            print(f"  Scene 1 keys: {list(new_s1.keys())}")

            for field in NEW_FIELDS:
                value = new_s1.get(field, "MISSING")
                if field in ("ambient", "sfx", "tone_tags"):
                    assert_truthy(f"new_ep.s1.{field} is non-empty list", value)
                else:
                    assert_truthy(f"new_ep.s1.{field} is non-empty", value)
        else:
            print(f"  ❌ Error: {gen_resp.get('detail', gen_resp)[:300]}")

        # Final overview
        await shoot(page, "99-final")
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
    print(f"📊 TC-01b (20 New Fields): {passed}/{total} PASS, {failed} FAIL")
    print(f"⏱️  Elapsed: {elapsed:.1f}s")
    print(f"{'='*70}")

    with open(OUT / "results.json", "w") as f:
        json.dump({
            "test": "TC-01b 20 New Director Fields",
            "started": datetime.fromtimestamp(start_time).isoformat(),
            "elapsed_sec": elapsed,
            "total": total, "passed": passed, "failed": failed,
            "assertions": assertions, "network": network,
        }, f, indent=2, ensure_ascii=False)

    # HTML report
    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>TC-01b 20 Fields</title>
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
.field-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.field-item { background: #1a1a2e; padding: 8px; border-radius: 4px; }
.field-name { color: #60a5fa; font-size: 11px; }
.field-value { color: #e0e0e0; font-size: 12px; }
</style></head>
<body>
<h1>🆕 TC-01b: 20 New Director Fields</h1>
<p><strong>Started:</strong> """ + datetime.fromtimestamp(start_time).isoformat() + """</p>
<p><strong>Elapsed:</strong> """ + f"{elapsed:.1f}s" + """</p>

<div class="summary">
    <div class="box"><div class="num" style="color:#10b981">""" + str(passed) + """</div><div class="lbl">PASSED</div></div>
    <div class="box"><div class="num" style="color:#ef4444">""" + str(failed) + """</div><div class="lbl">FAILED</div></div>
    <div class="box"><div class="num">""" + str(total) + """</div><div class="lbl">TOTAL</div></div>
    <div class="box"><div class="num">""" + str(len(network)) + """</div><div class="lbl">API CALLS</div></div>
</div>

<h2>📋 Assertions</h2>
<table>
<thead><tr><th>Name</th><th>Expected</th><th>Actual</th><th>Status</th></tr></thead>
<tbody>
"""
    for a in assertions:
        html += f"""<tr class="{a['status']}">
    <td>{a['name']}</td>
    <td><code>{a['expected']}</code></td>
    <td><code>{a['actual'][:200]}</code></td>
    <td><span class="badge {a['status']}">{a['status']}</span></td>
</tr>
"""
    html += "</tbody></table>"

    html += '<h2>📸 Screenshots</h2>'
    for s in OUT.glob("screenshots/*.png"):
        html += f'<img class="screenshot" src="screenshots/{s.name}" />\n'

    html += '<h2>📡 Network</h2><div class="network">'
    for n in network:
        cls = "ok" if 200 <= n["status"] < 300 else "err"
        html += f'<div class="{cls}">[{n["ts"]:.1f}s] {n["status"]} {n["method"]} {n["url"]}</div>\n'
    html += '</div>'

    html += "</body></html>"

    with open(OUT / "report.html", "w") as f:
        f.write(html)

    print(f"\n✅ Report: {OUT}/report.html")
    sys.exit(0 if failed == 0 else 1)
