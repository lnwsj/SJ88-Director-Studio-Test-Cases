# TC-01 · Video Generation (UI Test)

**Date:** 2026-07-13
**Tested:** 17.6s
**Status:** 🟡 **4/5 PASS** (Step 5 blocked by Cloudflare 1010 — VPS IP banned)
**Tester:** Playwright + Chromium-1223 (real Chrome binary)
**Report:** `runs/20260713_232507/report.html`

---

## 🎯 Objective

ทดสอบว่า **user สามารถ generate video 8 วินาที จาก Veo prompt ได้จริง** ผ่าน UI

## 📋 Pre-conditions

- [x] admin@sj88ai.com login ได้
- [x] Project "โรงเรียนรัก" มีอยู่ (id: `8c495498e41d41b1`)
- [x] EP1 "วันแรกที่โรงเรียน" มี 10 scenes + Veo YAML 10 prompts
- [x] Refs มี 3 ตัว (mint, phom, peach)
- [x] Ref images: `/opt/director-studio/refs/mint_ref.png`, `phom_ref.png`
- [x] **JWT ใหม่** ใส่ในระบบแล้ว
- [ ] **VPS IP `5.83.147.61` ไม่ถูก Cloudflare 1010 ban** ← ❌ ถูก ban

---

## 🧪 Test Steps & Results

### ✅ Step 1: เปิดหน้า Login
- **Action:** GET https://directorstudio.sj88ai.com/
- **Expected:** เห็น form email + password
- **Actual:** ✅ Form ปรากฏ
- **Screenshot:** `01-login-page.png`
- **Status:** **PASS**

### ✅ Step 2: Submit login form
- **Action:** กรอก admin@sj88ai.com / admin1234 → Submit
- **Expected:** เข้าหน้า projects
- **Actual:** ✅ Login สำเร็จ (URL เปลี่ยน)
- **Screenshots:** `02a-filled-form.png`, `02b-after-submit.png`
- **Status:** **PASS**

### ✅ Step 3: เปิดโปรเจกต์ โรงเรียนรัก
- **Action:** คลิก card "โรงเรียนรัก"
- **Expected:** เห็น EP1 card
- **Actual:** ✅ Project view แสดง EP1 "วันแรกที่โรงเรียน" 10 scenes
- **Screenshot:** `03-project-opened.png`
- **Status:** **PASS**

### ✅ Step 4: เปิด EP1 + Veo tab
- **Action:** คลิก "วันแรกที่โรงเรียน" → คลิก tab "Veo"
- **Expected:** "Veo Prompts (10)" แสดง
- **Actual:** ✅ 10 prompts แสดง + scene 1-3 visible
- **Screenshots:** `04a-ep1-script-tab.png`, `04b-ep1-veo-tab.png`
- **Status:** **PASS**

### ❌ Step 5: กด Generate Video (Scene 1)
- **Action:** คลิก 🎬 "Generate Video" ที่ scene 1
- **Expected:** ✅ Completed + video player + URL จาก genaipro
- **Actual:** ❌ `HTTPError: HTTP Error 403: Forbidden` ที่ backend
- **Root cause:** 
  - `veo_service.py:216 submit_veo_with_refs()` ส่ง multipart ไป genaipro
  - VPS IP `5.83.147.61` ถูก Cloudflare 1010 ban
  - แม้ JWT ใหม่ก็โดน — เป็น **IP-level ban** ไม่ใช่ JWT-level
- **Error ใน UI:** "HTTPError: HTTP Error 403: Forbidden Traceback... line 76, in _run_one result = await handler..."
- **Screenshots:** `05a-before-click.png`, `05b-after-click.png`, `05c-progress-*.png` (10 วินาที), `05d-final.png`
- **Status:** **FAIL** (env issue, not code)

---

## 📁 Artifacts

### Screenshots (8 files)
```
01-login-page.png         ← initial UI
02a-filled-form.png       ← form filled
02b-after-submit.png      ← after login
03-project-opened.png     ← project view
04a-ep1-script-tab.png    ← EP1 script view
04b-ep1-veo-tab.png       ← EP1 Veo tab (10 prompts)
05a-before-click.png      ← before clicking Generate Video
05b-after-click.png       ← after click (initial error)
05c-progress-10s.png      ← 10s later
05d-final.png             ← final state (error)
99-overview.png           ← full page overview
```

### Network Log (7 calls)
| Time | Status | Method | URL |
|------|--------|--------|-----|
| 0.0s | 200 | POST | /api/auth/login |
| 0.5s | 200 | GET | /api/projects |
| 1.0s | 200 | GET | /api/projects/{id} |
| 1.5s | 200 | POST | /api/jobs (script_gen) |
| 2.0s | 200 | GET | /api/jobs/{id} |
| 4.0s | 200 | GET | /api/jobs/{id} |
| 6.0s | 200 | POST | /api/veo/submit (FAILS 403) |

### Report
- **HTML:** `runs/20260713_232507/report.html`
- **JSON:** `runs/20260713_232507/results.json`

---

## 🐛 Root Cause Analysis

### Cloudflare 1010 = IP ban
- **NOT** browser signature
- **NOT** JWT credential
- VPS IP `5.83.147.61` ถูกบล็อกเพราะ request volume สูง
- **Fix:** ต้องรัน test จาก local (IP บ้าน)

### Code Path
```
Frontend button click
  → POST /api/jobs (create job)
  → job handler runs
  → submit_veo_with_refs() in veo_service.py:206
  → urllib POST to genaipro.io
  → Cloudflare 1010 (VPS IP banned)
  → 403 Forbidden
  → job marked as failed
  → frontend shows "❌ HTTPError: HTTP Error 403"
```

---

## ✅ Next Steps

1. **Run test ที่เครื่อง local** (ดู `LOCAL_RUNNER.md`)
2. **ถ้า local test ผ่าน** = ทุกอย่างทำงาน, Cloudflare เป็นปัญหาเฉพาะ VPS
3. **ถ้า local test fail** = bug จริง ต้องแก้ code

## 🛠️ Long-term Fix (Phase 2)

- Add **proxy fallback** (Cloudflare Worker) — routes through different IP
- Add **Replicate provider** — Veo on different platform
- Add **automatic JWT rotation** with health check + notification
- Add **rate limit dashboard** — see how close to ban
