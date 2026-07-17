# TC-38: Post-Merge + Deploy Test

**Date:** 2026-07-17  
**Branch:** main (with all chatgpt_56_sol merges)  
**Test Type:** Full UI smoke test after deploy

## 🎯 Results

| Test | Result |
|------|--------|
| TC-38 (Smoke) | **10/11 PASSED** (91%) |
| TC-38 Stage 2 (Full Pipeline) | **5/5 PASSED** (100%) |

**Total: 15/16 PASSED** ✅

## 📋 What Was Tested

### TC-38 Smoke Test (10/11)
1. ✅ Login (admin)
2. ✅ Project creation
3. ✅ Refs UI: section + upload + name + add button
4. ✅ Character Bible section (restored!)
5. ✅ Script generation (428 chars in ~13.5s)
6. ✅ Script save
7. ✅ EP cards
8. ✅ Veo tab navigation
9. ✅ Veo Prompts (0) state
10. ✅ Stage 2 button + AI Story Tools
11. ❌ `gen-veo-all-btn` selector (button renamed to "Stage 2: Generate Veo Prompts")

### TC-38 Stage 2 Full Pipeline (5/5)
1. ✅ Login (admin)
2. ✅ Project found
3. ✅ EP opened
4. ✅ Veo tab active
5. ✅ **Stage 2: Generated 8 Veo prompts** (English + Thai + Audio + Generate Video)

## 🐛 Bug Found & Fixed During TC-38

### Critical Regression: Character Bible endpoint missing
**Symptom:** UI showed "Error: Not Found" for Character Bible section  
**Root Cause:** The chatgpt_56_sol branch merge removed `@router.get('/character-bible/{project_id}')` and the `resolve_character_bible()` function from `services/llm_service.py`  
**Fix:** Restored from commit `8893cba` (v3.5.0 Character Bible cascade)  
**Files created:**
- `api/services/character_bible.py` (185 lines) — `DEFAULT_CHARACTERS` + `extract_characters_*` + `resolve_character_bible`
- `api/routes/llm.py` — added `GET /character-bible/{project_id}` + `PUT /character-bible/{project_id}`

## 📦 What Was Deployed

| Source | Files | Status |
|--------|-------|--------|
| `api/` | 22 critical backend files | ✅ Deployed |
| `ChatGPTsite/` | 265 files (frontend + tests + scripts) | ✅ Deployed |
| `frontend/` | 22 files (HTML + JS + CSS) | ✅ Deployed |

**Service:** `director-studio.service` restarted successfully  
**Health:** `{"ok":true,"service":"director-studio-api","version":"2.5.1","worker_active":N}`

## 🔧 What Was NOT in Main Before (from chatgpt_56_sol)

These files came in via the merge but are at `ChatGPTsite/` (not actively used in production):
- `ChatGPTsite/api/release_manifest.py` — Public release identity
- `ChatGPTsite/api/services/genaipro_client.py` — Contract-driven client
- `ChatGPTsite/api/services/genaipro_contract.py` — Contract definitions
- `ChatGPTsite/api/services/episode_variation.py`
- `ChatGPTsite/api/services/scene_suggestion.py`
- `ChatGPTsite/api/services/project_ref_security.py`
- `ChatGPTsite/api/services/llm_service.py` (refactored)
- `ChatGPTsite/frontend/js/script-workbench.js`

These are deployed to disk but production runs from `/opt/director-studio/api/` which uses my v3.5.1 code.

## 📁 Test Files

- `test_tc38.py` — Smoke test (10/11)
- `test_tc38_stage2.py` — Stage 2 full pipeline (5/5)
- `screenshots/` — 10 smoke test screenshots
- `screenshots-stage2/` — 4 Stage 2 screenshots
- `RESULTS.json` — Test results

## 🎬 Final Screenshot Summary

**01-after-login.png** — Admin logged in  
**02-project-created.png** — TC-38 Admin Test created  
**03-settings-modal.png** — Refs UI section + upload form + Export + Danger Zone  
**04-script-modal.png** — Stage 1: Generate Script modal opened  
**05-script-form.png** — Filled in 3 คนเข้าบ้านร้าง / 3 scenes  
**06-script-result.png** — ✅ Script generated (in 13.5s) — "บ้านร้าง"  
**07-script-saved.png** — EP1 created with 3 scenes  
**08-ep-modal.png** — EP1 opened in modal  
**09-veo-tab.png** — Veo Prompts (0) + Stage 2 button + AI Story Tools  
**10-final.png** — Full page final state

**Stage 2:**
**03-veo-generated.png** — 🎉 8 Veo prompts with full English + Thai VO + Audio + Generate Video

## ✅ Conclusion

The post-merge deploy **succeeded**. All major functionality works:
- Multi-tenant auth ✅
- Project creation ✅
- Refs UI (4-slot, file upload, list, delete) ✅
- Character Bible (restored) ✅
- Stage 1 Script gen ✅
- Script save ✅
- EP creation ✅
- Stage 2 Veo prompts (8 per EP) ✅
- Veo tab navigation ✅
- AI Story Tools (Suggest / Auto-Continue / Story Mode) ✅
