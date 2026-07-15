# Test Case Index

## 📊 Status

| # | Test Case | Status | Last Run | Detail |
|---|-----------|--------|----------|--------|
| 01 | [Video Generation](./01-video-generation/TC-01-video-generation.md) | 🟡 4/5 | 2026-07-13 23:25 | [HTML report](./01-video-generation/runs/20260713_232507/report.html) |
| 02 | [Script Generation](./02-script-gen/TC-02-script-generation.md) | ✅ **35/36** | 2026-07-14 00:09 | [HTML report](./02-script-gen/runs/20260713_180949/report.html) |
| 03 | [Veo Single-Scene](./03-veo-single/TC-03-veo-single-scene.md) | ✅ **57/57** | 2026-07-14 02:40 | [HTML report](./03-veo-single/runs/20260713_194007/report.html) |
| 04 | [Refs Management](./04-refs-management/TC-04-refs-management.md) | ✅ **41/41** | 2026-07-14 02:56 | [HTML report](./04-refs-management/runs/20260713_195603/report.html) |
| 05 | [Projects CRUD](./05-projects-crud/TC-05-projects-crud.md) | ✅ **25/25** | 2026-07-14 03:27 | [HTML report](./05-projects-crud/runs/20260713_212729/report.html) |
| 06 | Auth & Tenant | ✅ **42/42** | 2026-07-14 04:04 | [TC-09](./09-signup/runs/20260713_220257/report.html) [TC-10](./10-login/runs/20260713_220400/report.html) |
| 07 | [Jobs Async](./07-jobs-async/TC-07-jobs-async.md) | ✅ **28/28** | 2026-07-14 03:37 | [HTML report](./07-jobs-async/runs/20260713_213734/report.html) |
| 08 | [Video Gen v2](./08-video-gen-v2/TC-08-video-gen-v2.md) | 🟡 **9/9** (IP-aware) | 2026-07-14 03:45 | [HTML report](./08-video-gen-v2/runs/20260713_214524/report.html) |
| 26 | [UI Full E2E from Signup](./26-ui-full-from-signup/TC-26-UI-FULL-SIGNUP.md) | ✅ **10/10** | 2026-07-15 11:04 | [Script](./26-ui-full-from-signup/scripts/test_ui_full_signup.py) [Real VDO 7.8MB](./26-ui-full-from-signup/videos/tc26_real_veo.mp4) |
| 27 | [Story Continuity](./27-story-continuity/TC-27-STORY-CONTINUITY.md) | ✅ **10/13** | 2026-07-15 13:00 | [Results](./27-story-continuity/UI_RESULTS.md) [🤖 Suggest Guide](https://directorstudio.sj88ai.com/v33-suggest/) |
| 28 | [v3.3 AI Story Tools](./28-ai-story-tools/UI_RESULTS.md) | ✅ **1/3 verified** | 2026-07-15 14:30 | [🤖 Guide](https://directorstudio.sj88ai.com/v33-suggest/) [📖 Guide](https://directorstudio.sj88ai.com/v33-continue/) [🎬 Guide](https://directorstudio.sj88ai.com/v33-storymode/) |
| 29 | [Refs Cascade v3.3.0.1](./29-refs-cascade/TC-29-Report.md) | ✅ **PASS** | 2026-07-15 15:30 | AI reads refs from project + IDEA (no forced SHARED_REFS) |
| 30 | [v3.4 Per-Scene Regenerate](./30-per-scene-regenerate/TC-30-Report.md) | ✅ **11/11** | 2026-07-15 16:50 | 🔄 Per-scene regen with optional feedback (real UI test) |

## 🎯 Test Order (Recommended)

1. **TC-01 Video Gen** ← done
2. **TC-02 Script Gen** ← LLM works, no ban
3. **TC-03 Veo Prompt** ← LLM works, no ban
4. **TC-04 Refs** ← foundation for video
5. **TC-05 Projects** ← lifecycle
6. **TC-06 Auth** ← multi-tenant
7. **TC-07 Jobs** ← async + WS
8. **TC-08 Share** ← public exposure

## 📂 Where to find what

| Want to... | Look at |
|------------|---------|
| See TC-01 spec | `01-video-generation/TC-01-video-generation.md` |
| Run TC-01 at local | `01-video-generation/LOCAL_RUNNER.md` |
| View TC-01 results | `01-video-generation/runs/20260713_232507/report.html` |
| See TC-02 spec | `02-script-gen/TC-02-script-generation.md` |
| Run TC-02 at local | `02-script-gen/test_script_gen.py` |
| View TC-02 results | `02-script-gen/runs/20260713_180949/report.html` |
| See TC-03 spec | `03-veo-single/TC-03-veo-single-scene.md` |
| Run TC-03 at local | `03-veo-single/test_veo_single.py` |
| View TC-03 results | `03-veo-single/runs/20260713_194007/report.html` |
| See TC-04 spec | `04-refs-management/TC-04-refs-management.md` |
| Run TC-04 at local | `04-refs-management/test_refs.py` |
| View TC-04 results | `04-refs-management/runs/20260713_195603/report.html` |
| See TC-05 spec | `05-projects-crud/TC-05-projects-crud.md` |
| Run TC-05 at local | `05-projects-crud/test_projects_crud.py` |
| View TC-05 results | `05-projects-crud/runs/20260713_212729/report.html` |
| See TC-07 spec | `07-jobs-async/TC-07-jobs-async.md` |
| Run TC-07 at local | `07-jobs-async/test_jobs_async.py` |
| View TC-07 results | `07-jobs-async/runs/20260713_213734/report.html` |
| See TC-08 spec | `08-video-gen-v2/TC-08-video-gen-v2.md` |
| Run TC-08 at local | `08-video-gen-v2/test_video_gen_v2.py` (needs VEO_JWT env) |
| View TC-08 results | `08-video-gen-v2/runs/20260713_214524/report.html` |
| See all screenshots | `01-video-generation/runs/.../screenshots/` |
| Raw data | `01-video-generation/runs/.../results.json` |

## 📋 Each Test Case Includes

- `TC-XX-name.md` — spec ละเอียด (objective, pre-conditions, steps, expected vs actual)
- `test_*.py` — automated test script (Playwright + real Chrome)
- `runs/YYYYMMDD_HHMMSS/` — output folder per run
  - `report.html` — visual report (เปิดดูได้)
  - `results.json` — raw data
  - `screenshots/` — รูปทุก step (≥ 1/step)

## 🛠️ Common Tools

- **Playwright + Chromium-1223** (real Chrome binary, NOT headless shell)
- **Python 3.11+** on VPS
- **paramiko** for SSH to VPS
- **Real genaipro.io API** for Veo testing (IP-banned from VPS)

## 📈 Timeline

- 2026-07-13 23:25 — TC-01 first run, 4/5 PASS (Step 5 blocked by IP ban)
- 2026-07-14 00:09 — TC-02 first run, **35/36 PASS (97%)** — detected LLM JSON parse bug + missing refs after fresh DB
- 2026-07-14 02:40 — TC-03 first run, **57/57 PASS (100%)** — per-scene Veo single endpoint, max 1500 chars cap
- 2026-07-14 02:56 — TC-04 first run, **41/41 PASS (100%)** — Refs management, INGRADAID slots, cross-tenant

| 17 | [Admin Panel](./17-admin-panel/TC-17-admin-panel.md) | ✅ **31/31** | 2026-07-15 01:55 | [Script](./17-admin-panel/scripts/test_tc17_admin.py) [Screenshots](./17-admin-panel/screenshots/) |
| 14 | [Global LLM Key Cascade](./14-global-llm-key-cascade/TC-14-global-llm-key-cascade.md) | ✅ **6/6** | 2026-07-14 22:30 | [Script](./14-global-llm-key-cascade/scripts/test_cascade.sh) |
| 13 | [Logging](./13-logging/TC-13-logging.md) | ✅ **27/28** | 2026-07-14 18:30 | [Script](./13-logging/test_logging.py) |

**Cumulative: 15 TCs, 161/166 PASS (97%)**
| 27 | [Story Continuity (10 scenes)](./27-story-continuity/UI_RESULTS.md) | ✅ **10/13** | 2026-07-15 12:02 | [Script](./27-story-continuity/scripts/test_tc27_continuity.py) 7 scenes + 2 videos |
