# TC-03: Veo Single-Scene Prompt Generation (UI)

## Status: ✅ **57/57 PASS (100%)**

## What This Test Covers
End-to-end test of the **per-scene Veo prompt generator** (commit `e32028d`).
- New endpoint: `POST /api/llm/generate-veo-single`
- New UI: per-scene "🎬 Generate Veo Prompt (1 scene, max 1500 chars)" button
- Hard cap: 1500 chars per prompt (configurable)
- Smart truncation: cuts at last period before limit

## Test Flow (11 Steps)

| # | Step | What |
|---|------|------|
| 1 | Login | Auth as admin, get JWT |
| 2 | Get horror project | API: verify refs + meta |
| 3 | Verify 20 fields | All 20 director fields present in scene 1 |
| 4 | API direct call | POST /generate-veo-single, expect 1 clip (not batched) |
| 5 | UI buttons | Verify 3 per-scene buttons + text "max 1500" |
| 6 | Click scene 1 | UI click → wait → verify badge + prompt |
| 7 | Click scene 2 | UI click → wait → verify result |
| 8 | Click scene 3 | UI click → wait → verify result |
| 9 | Verify ep.timeline | API: all 3 prompts saved, each <= 1500 |
| 10 | Cross-genre (romance) | Same endpoint, different genre, works |
| 11 | max_chars=500 cap | Smart truncation works |

## Results

### ✅ 57/57 PASS (100%)

| Step | What | Result |
|------|------|--------|
| 1-2 | Login + project | ✅ PASS |
| 3 | 20 fields in scene | ✅ **20/20 PASS** |
| 4 | API direct call | ✅ 909 chars, 1 clip |
| 5 | UI buttons | ✅ **3 buttons, "max 1500" text** |
| 6 | Scene 1 UI | ✅ **827 chars** |
| 7 | Scene 2 UI | ✅ **1102 chars** |
| 8 | Scene 3 UI | ✅ **1023 chars** |
| 9 | ep.timeline 3 clips | ✅ **827, 1102, 1023 chars** (all ≤ 1500) |
| 10 | Romance cross-genre | ✅ 786 chars |
| 11 | max_chars=500 cap | ✅ 483 chars (truncated) |

### Verified Lengths
| Project | Scene | Length | Truncated |
|---------|-------|--------|-----------|
| Horror | S01_01 (การตื่นในความมืด) | 827 chars | ❌ no |
| Horror | S01_02 (เงาของแม่) | 1102 chars | ❌ no |
| Horror | S01_03 (ข้อเสนอจากเบื้องบน) | 1023 chars | ❌ no |
| Romance | S01_01 (โรงเรียนรัก) | 786 chars | ❌ no |
| Horror (cap test) | S01_01 (max=500) | 483 chars | ✅ yes |

All within 1500 hard cap. Average ~950 chars per prompt.

## How to Run

```bash
cd /workspace/director-studio-test-cases/03-veo-single
python3 test_veo_single.py
```

Output:
- `runs/<timestamp>/report.html` — full report with screenshots
- `runs/<timestamp>/results.json` — machine-readable
- `runs/<timestamp>/screenshots/*.png` — 8 screenshots

## Key Test Patterns

### 1. Smart Truncation Detection
When `max_chars=500`, the system prompt asks LLM to write ~500 chars.
If LLM overshoots, `safe_truncate` cuts at last `.` before limit.
Test checks `truncated=True` flag + actual length.

### 2. Per-Scene UI Button Detection
```js
document.querySelectorAll('button[data-act="gen-veo-single"]')
```
Returns N buttons (one per scene).

### 3. Wait for Output Ready
Poll `.scene-veo-output` for text containing "chars" but NOT "⏳":
```js
await page.wait_for_function(
  '() => { const o = document.querySelector(".scene-veo-output"); 
           return o && o.innerText.includes("chars") && !o.innerText.includes("⏳"); }',
  timeout=90000
);
```

### 4. Cross-Genre Same Endpoint
Romance project uses same `/api/llm/generate-veo-single` endpoint.
Backend `load_project_refs` + `project_meta` drive the genre-specific
persona, mood, lighting, and filters.

## What This Test Validates
- ✅ New endpoint `/api/llm/generate-veo-single` works
- ✅ Hard cap 1500 chars respected
- ✅ Per-scene UI button (one per scene) renders + wired
- ✅ Click → API → save to `ep.timeline[idx]` flow
- ✅ Badge shows correct char count
- ✅ All 20 director fields used in prompt
- ✅ Cross-genre (horror + romance) supported
- ✅ Smart truncation (max_chars=500 → 483 chars)
- ✅ Shot type + camera move + lens propagated from script

## What This Test Does NOT Cover
- Batched "Generate All" button (not yet implemented)
- Caching (same scene → return cached prompt)
- Video generation from Veo prompt (covered in TC-01)
- Multiple languages (only th tested)

## Screenshot Index (Latest Run)
1. `01-login.png` — Login page
2. `01b-after-login.png` — After login
3. `03-ep1-loaded.png` — EP1 modal with scenes
4. `04-api-call.png` — Direct API call state
5. `05-ep1-modal.png` — EP1 with 3 yellow buttons visible
6. `06-scene1-result.png` — Scene 1 with ✓ 827 chars badge
7. `07-scene2-result.png` — Scene 2 with ✓ 1102 chars badge
8. `08-scene3-result.png` — Scene 3 with ✓ 1023 chars badge + toast

## Test Artifacts
- **Test file**: `test_veo_single.py` (521 lines, Playwright + Chromium-1223)
- **Latest run**: `runs/20260713_194007/`
- **Report**: `runs/20260713_194007/report.html`
- **Results**: `runs/20260713_194007/results.json`
- **Screenshots**: 8 PNG files

## Test Date
2026-07-14 02:38 ICT

## Author
Director Studio QA — automated test by Mavis
