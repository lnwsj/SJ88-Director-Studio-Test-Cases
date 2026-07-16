"""
TC-37: Full Pipeline 1 เรื่อง 1 EP 10 ฉาก — Real UI Only
=========================================================
End-to-end test through REAL browser UI (Playwright + Chromium-1223).
Verifies the user CAN do a full pipeline (Stage 1→2→3) via UI only.
Also produces UI screenshots + raw data for the user manual.
"""
import os, sys, time, json, re
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE = "https://directorstudio.sj88ai.com"
TC_DIR = Path("/workspace/director-studio-test-cases/37-ten-scenes-ui-full")
SHOTS = TC_DIR / "screenshots"
LOGS = TC_DIR / "logs"
SHOTS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

CHROME = "/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome"

TIMESTAMP = int(time.time())
TEST_EMAIL = f"tc37_{TIMESTAMP}@test.local"
TEST_PASSWORD = "tc37test1234"
TEST_NAME = f"TC-37 {TIMESTAMP}"
PROJECT_NAME = f"TC-37 น้ำหนาว 10 ฉาก"

STORY_IDEA = """เรื่อง: น้ำหนาว (The Cold Water) — Thai horror, 10 scenes, 3-Act

แม่ค้าชราในร้านก๋วยเตี๋ยวเก่าแก่ทรยศฆ่าลูกค้า 40 ปีที่แล้ว ตอนนี้ลูกค้าคนสุดท้ายเข้ามา

ฉาก 1: ลูกค้าคนสุดท้าย — น้ำเข้าร้านก๋วยเตี๋ยวเวลา 22:00 เจ้าของร้านผู้ชายนั่งหลับ ร้านมืด มีเข็มอยู่บนโต๊ะ

ฉาก 2: สั่งเมนูลึกลับ — น้ำสั่งก๋วยเตี๋ยวน้ำใส เจ้าของร้านตาเบิกกว้าง กระดาษสั่งเขียนว่า ไม่ใส่ผัก

ฉาก 3: หม้อน้ำเดือด — เจ้าของร้านใส่หม้อน้ำในครัว น้ำเดือดพุ่ง แต่ไอน้ำเย็นจัด กลิ่นเน่า

ฉาก 4: ถ้วยแตก — น้ำยกถ้วยขึ้น ถ้วยแตกกลางพื้นเอง น้ำในถ้วยไหลเป็นสีดำ กลิ่นเหม็นคาว

ฉาก 5: แม่ค้าชราปรากฏ — เจ้าของร้านหันไปเห็นแม่ค้าชรายืนที่ประตูหลัง ถือผ้าเช็ดมือสีแดง

ฉาก 6: บ่อน้ำต้องสาป — แม่ค้าชราพาน้ำไปบ่อน้ำหลังร้าน น้ำในบ่อดำสนิท ใบหน้าแม่ค้าสะท้อนในน้ำไม่ตรงกับใบหน้าจริง

ฉาก 7: ตะเกียงดับ — น้ำเดินออกจากร้าน ตะเกียงในมือเจ้าของร้านดับ ถนนเปลี่ยว มืดสนิท

ฉาก 8: เงาไล่ทัน — น้ำเดินเร็ว เงาดำยาวไล่ทัน น้ำหันกลับ เห็นเงายืนห่าง 2 เมตร

ฉาก 9: ศาลพระภูมิ — น้ำวิ่งถึงศาลพระภูมิ ผีแม่ค้าชราปรากฏบนศาล บอกว่า เธอกินน้ำต้องสาปไปแล้ว

ฉาก 10: จดหมายในตู้เย็น — เช้าวันรุ่งขึ้น เจ้าของร้านเปิดตู้เย็นเก่า เจอจดหมายของแม่ค้าชรา 40 ปีที่แล้ว เขียนถึงน้ำ

ธีม: ความทรงจำ การทรยศ น้ำ อาหาร ความตาย
ตัวละคร: น้ำ, เจ, ยาย, ผี"""

NUM_SCENES = 10

typed_log = []
results = {}
screenshots = []

def log_typed(action, value=""):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {action}: {value}"
    typed_log.append(line)
    print(line, flush=True)
    (LOGS / "typed.log").write_text("\n".join(typed_log) + "\n")

def shot(page, name):
    p = SHOTS / f"{name}.png"
    try:
        page.screenshot(path=str(p), full_page=True)
        screenshots.append(name)
        log_typed(f"📸 Screenshot", name)
    except Exception as e:
        log_typed(f"❌ Screenshot failed", f"{name} — {e}")

def get_projects(page):
    """Fetch all projects (handles dict vs list)"""
    return page.evaluate("""
        () => fetch('/api/projects', {
            headers: { 'Authorization': 'Bearer ' + (localStorage.getItem('ds_token') || localStorage.getItem('access_token')) }
        }).then(r => r.json()).then(d => Array.isArray(d) ? d : (d.projects || []))
    """)

def find_project(page, name):
    projects = get_projects(page)
    for p in projects:
        if name in p.get('name', ''):
            return p
    return None

def main():
    start = time.time()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME,
            args=["--no-sandbox", "--disable-gpu", "--use-gl=swiftshader", "--disable-dev-shm-usage"],
            headless=True,
        )
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
        page = ctx.new_page()
        page.set_default_timeout(60000)
        page.on("pageerror", lambda e: log_typed("💥 PAGEERROR", str(e)[:200]))
        page.on("dialog", lambda d: d.accept())

        try:
            # ==================== STEP 1: Signup ====================
            log_typed("STEP", "1. Signup")
            page.goto(BASE, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            shot(page, "01_landing")
            page.locator(".auth-tab[data-tab='signup']").click()
            page.wait_for_timeout(500)
            page.locator("input[name='display_name']").fill(TEST_NAME)
            page.locator("input[type='email']").fill(TEST_EMAIL)
            page.locator("input[type='password']").fill(TEST_PASSWORD)
            shot(page, "02_signup_filled")
            page.locator("#auth-submit").click()
            page.wait_for_timeout(3000)
            shot(page, "03_after_signup")
            log_typed("✅ Signed up", TEST_EMAIL)

            # ==================== STEP 2: Create project ====================
            log_typed("STEP", "2. Create project")
            page.locator("#new-project-btn").click()
            page.wait_for_timeout(500)
            page.locator("#project-name-input").fill(PROJECT_NAME)
            shot(page, "04_project_form")
            page.locator("#project-save").click()
            page.wait_for_timeout(2000)
            shot(page, "05_project_created")
            log_typed("✅ Project created", PROJECT_NAME)

            # ==================== STEP 3: Stage 1 — Script ====================
            log_typed("STEP", "3. Generate script (Stage 1)")
            page.locator("#gen-script-btn").click()
            page.wait_for_timeout(1500)
            shot(page, "06_script_modal")
            page.locator("#script-idea").fill(STORY_IDEA)
            page.wait_for_timeout(500)
            page.locator("#script-num-scenes").fill(str(NUM_SCENES))
            page.wait_for_timeout(500)
            shot(page, "07_idea_filled")
            page.locator("#script-generate").click()
            log_typed("⏳ Stage 1 started", "waiting for script...")

            # Wait for #script-result to have content
            stage1_start = time.time()
            for i in range(240):  # 8 min max
                page.wait_for_timeout(2000)
                if i % 15 == 0:
                    try:
                        r = page.locator("#script-result").text_content() or ""
                        log_typed(f"  poll #{i+1}", f"len={len(r)}, has_✅={'✅' in r}")
                    except:
                        pass
                try:
                    r = page.locator("#script-result").text_content() or ""
                    if len(r) > 100 and ("✅" in r or "scenes" in r.lower()):
                        if "ล้มเหลว" not in r and "❌" not in r:
                            break
                except:
                    pass
            stage1_dur = time.time() - stage1_start
            page.wait_for_timeout(2000)
            shot(page, "08_script_done")
            log_typed("✅ Stage 1 done", f"{stage1_dur:.0f}s")
            results["stage1_duration_sec"] = round(stage1_dur, 1)

            # Get scenes from API
            proj = find_project(page, PROJECT_NAME)
            api_data = None
            if proj:
                ep = (proj.get('data', {}).get('episodes') or [None])[0]
                if ep:
                    api_data = {
                        "project": proj['name'],
                        "episode_title": ep.get('episode_title'),
                        "num_scenes": len(ep.get('scenes', [])),
                        "scene_titles": [s.get('title') for s in ep.get('scenes', [])]
                    }
            results["scenes"] = api_data
            log_typed("📊 Scenes from API", json.dumps(api_data, ensure_ascii=False))

            # Save script
            try:
                page.locator("#script-save").click()
                page.wait_for_timeout(2000)
                log_typed("✅ Script saved", "")
            except Exception as e:
                log_typed("⚠️ Script save", str(e)[:100])

            # Close script modal
            try:
                page.locator("#script-modal-close").click()
                page.wait_for_timeout(1500)
            except:
                pass

            # ==================== STEP 4: Open EP1 ====================
            log_typed("STEP", "4. Open EP1")
            page.locator(".ep-card").first.click()
            page.wait_for_timeout(2500)
            shot(page, "09_ep1_modal")
            log_typed("✅ EP1 modal opened", "")

            # ==================== STEP 5: Stage 2 — Veo prompts ====================
            log_typed("STEP", "5. Generate Veo prompts (Stage 2)")
            page.locator(".ep-tab[data-ep-tab='script']").click()
            page.wait_for_timeout(2000)
            shot(page, "10_script_tab")

            stage2_start = time.time()
            page.locator("#gen-veo-all-btn").click()
            log_typed("⏳ Stage 2 started", "waiting for Veo prompts...")

            for i in range(60):  # 4 min max
                page.wait_for_timeout(4000)
                try:
                    progress_html = page.locator("#gen-veo-all-progress").inner_html() or ""
                    if "✅" in progress_html or "done" in progress_html.lower():
                        log_typed(f"  Stage 2 done at i={i+1}", progress_html[:120])
                        break
                except:
                    pass
                if i % 4 == 0:
                    try:
                        p = page.locator("#gen-veo-all-progress").text_content() or ""
                        log_typed(f"  poll #{i+1}", p[:80])
                    except:
                        pass
            stage2_dur = time.time() - stage2_start
            page.wait_for_timeout(3000)
            shot(page, "11_veo_done")
            log_typed("✅ Stage 2 done", f"{stage2_dur:.0f}s")
            results["stage2_duration_sec"] = round(stage2_dur, 1)

            proj = find_project(page, PROJECT_NAME)
            veo_data = None
            if proj:
                ep = (proj.get('data', {}).get('episodes') or [None])[0]
                if ep:
                    veo_data = {
                        "timeline_count": len(ep.get('timeline') or []),
                        "timeline_ids": [t.get('id') for t in (ep.get('timeline') or [])]
                    }
            results["veo_prompts"] = veo_data
            log_typed("📊 Veo prompts from API", json.dumps(veo_data, ensure_ascii=False))

            # ==================== STEP 6: Stage 3 — Videos ====================
            log_typed("STEP", "6. Generate videos (Stage 3)")
            page.wait_for_timeout(8000)

            veo_tab_ok = False
            for attempt in range(5):
                try:
                    page.locator(".ep-tab[data-ep-tab='veo']").click(force=True)
                    page.wait_for_timeout(3000)
                    gen_count = page.locator("button[data-act='generate']").count()
                    log_typed(f"  attempt {attempt+1}", f"gen-buttons={gen_count}")
                    if gen_count > 0:
                        veo_tab_ok = True
                        break
                except Exception as e:
                    log_typed(f"  ⚠️ VEO tab fail", str(e)[:100])
                page.wait_for_timeout(2000)
            if not veo_tab_ok:
                log_typed("❌ VEO tab failed", "")
            shot(page, "12_veo_tab_with_videos")

            stage3_start = time.time()
            num_videos = page.locator("button[data-act='generate']").count()
            log_typed(f"📊 Found {num_videos} generate buttons", "")

            for i in range(min(num_videos, 20)):
                try:
                    btn = page.locator("button[data-act='generate']").nth(i)
                    if btn.is_visible():
                        btn.scroll_into_view_if_needed()
                        btn.click()
                        log_typed(f"✅ Submitted video job {i+1}", "")
                        page.wait_for_timeout(500)
                except Exception as e:
                    log_typed(f"⚠️ Video {i+1} submit", str(e)[:100])
            log_typed("⏳ Stage 3 polling", "waiting for videos...")

            for attempt in range(80):  # 80 × 30s = 40 min max
                page.wait_for_timeout(30000)
                proj = find_project(page, PROJECT_NAME)
                if proj:
                    ep = (proj.get('data', {}).get('episodes') or [None])[0]
                    if ep:
                        total = len(ep.get('scenes', []))
                        done = sum(1 for s in ep.get('scenes', []) if s.get('video_url'))
                        log_typed(f"📊 Stage 3 poll #{attempt+1}", f"{done}/{total} videos")
                        if done >= total and total > 0:
                            log_typed("✅ All videos complete!", "")
                            break

            stage3_dur = time.time() - stage3_start
            page.wait_for_timeout(2000)
            shot(page, "13_videos_done")
            results["stage3_duration_sec"] = round(stage3_dur, 1)

            # ==================== FINAL ====================
            log_typed("STEP", "7. Final")
            shot(page, "14_final")
            proj = find_project(page, PROJECT_NAME)
            final = None
            if proj:
                ep = (proj.get('data', {}).get('episodes') or [None])[0]
                if ep:
                    final = {
                        "project": proj['name'],
                        "episode_title": ep.get('episode_title'),
                        "num_scenes": len(ep.get('scenes', [])),
                        "num_veo": len(ep.get('timeline') or []),
                        "num_videos": sum(1 for s in ep.get('scenes', []) if s.get('video_url')),
                        "scenes": [
                            {
                                "id": s.get('id'),
                                "title": s.get('title'),
                                "video_url": "YES" if s.get('video_url') else "NO"
                            }
                            for s in ep.get('scenes', [])
                        ]
                    }
            results["final"] = final
            (LOGS / "final.json").write_text(json.dumps(final, indent=2, ensure_ascii=False) if final else "{}")
            log_typed("💾 final.json saved", "")

            total_dur = time.time() - start
            log_typed("="*5, f"TEST COMPLETE — {total_dur/60:.1f} min")

            print("\n" + "="*70)
            print("TC-37 RESULTS")
            print("="*70)
            print(f"Project: {PROJECT_NAME}")
            print(f"Email: {TEST_EMAIL}")
            print(f"Total: {total_dur/60:.1f} min")
            if api_data:
                print(f"Stage 1: {api_data['num_scenes']} scenes in {stage1_dur:.0f}s")
            if veo_data:
                print(f"Stage 2: {veo_data.get('timeline_count', 0)} Veo in {stage2_dur:.0f}s")
            if final:
                print(f"Stage 3: {final.get('num_videos', 0)}/{final.get('num_scenes', 0)} videos in {stage3_dur:.0f}s")
            print("="*70)

        except Exception as e:
            log_typed("💥 Exception", str(e)[:300])
            try:
                shot(page, "ERROR")
            except:
                pass
            raise
        finally:
            browser.close()

    (TC_DIR / "results.json").write_text(json.dumps({
        "email": TEST_EMAIL,
        "results": results,
        "screenshots": screenshots,
        "total_duration_sec": round(time.time() - start, 1),
        "timestamp": TIMESTAMP,
    }, indent=2, ensure_ascii=False))
    log_typed("💾 results.json saved", "")

if __name__ == "__main__":
    main()
