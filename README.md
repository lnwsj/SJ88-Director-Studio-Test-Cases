# Director Studio · Test Cases

**Last updated:** 2026-07-13
**Tester:** Playwright + Chromium (real Chrome binary, not headless shell)

## 📁 Folder Structure

```
director-studio-test-cases/
├── README.md
├── INDEX.md
│
├── 01-video-generation/           ← ⭐ TC-01 (4/5 PASS, 1 blocked by IP ban)
│   ├── TC-01-video-generation.md  ← Spec (ละเอียด)
│   ├── test_full.py               ← Playwright + Chrome
│   ├── test_ui_video_gen.py       ← Simpler version
│   ├── LOCAL_RUNNER.md            ← วิธีรันที่เครื่อง local
│   ├── TEST_AT_HOME.md            ← Manual test
│   └── runs/
│       └── 20260713_232507/       ← Latest run
│           ├── report.html        ← ⭐ HTML report (เปิดดูได้)
│           ├── results.json       ← Raw data
│           └── screenshots/       ← 11 รูป
│
├── 02-script-generation/          ← ยังไม่เขียน
├── 03-veo-prompt-generation/      ← ยังไม่เขียน
├── 04-refs-management/            ← ยังไม่เขียน
├── 05-projects-crud/              ← ยังไม่เขียน
├── 06-auth-tenant/                ← ยังไม่เขียน
├── 07-jobs-async/                 ← ยังไม่เขียน
└── 08-share-analytics/            ← ยังไม่เขียน
```

## 📊 Status

| TC | Test | Status | Last Run | Notes |
|----|------|--------|----------|-------|
| 01 | Video Generation | 🟡 4/5 | 2026-07-13 23:25 | Step 5: VPS IP banned by Cloudflare |

## 🛠️ Tools

- **Playwright + Chromium-1223** (real Chrome binary)
- **urllib** for API-only tests
- **paramiko** for SSH to VPS

## 🎯 How Each TC Works

1. **Spec (TC-XX-name.md)** — objective, pre-conditions, steps, expected vs actual
2. **Test script (test_*.py)** — automated execution
3. **Run output** — saved to `runs/YYYYMMDD_HHMMSS/`
4. **HTML report** — visual summary with screenshots + network log
5. **Screenshots** — at least 1 per step (some have 2-3)
6. **Network log** — every API call captured

## 📋 TC-01 Detailed Results

**Test: Generate Video via UI**

| Step | Status | Detail |
|------|--------|--------|
| 1. Login page | ✅ | Form loaded |
| 2. Submit form | ✅ | Logged in |
| 3. Open โรงเรียนรัก | ✅ | EP1 visible |
| 4. EP1 + Veo tab | ✅ | 10 prompts shown |
| 5. Generate Video | ❌ | Cloudflare 1010 (VPS IP) |

**See full HTML report:** `01-video-generation/runs/20260713_232507/report.html`

## ⚠️ Known Issue: Cloudflare IP Ban

VPS IP `5.83.147.61` ถูก Cloudflare 1010 ban (IP-level, not JWT)
- Local test (จากเครื่อง user) ไม่โดน
- ดูวิธีรันที่ `01-video-generation/LOCAL_RUNNER.md`

## 🔗 Related
- **Project:** https://directorstudio.sj88ai.com/
- **Admin:** `admin@sj88ai.com` / `admin1234`
- **Test projects:** โรงเรียนรัก, อยุธยา
- **Live Demo:** https://directorstudio.sj88ai.com/wow/
- **Sales:** https://directorstudio.sj88ai.com/sales/
