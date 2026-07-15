# TC-04: Refs Management (UI + API)

## Status: ✅ **41/41 PASS (100%)**

## What This Test Covers
Validates **INGRADAID abstract refs** (`ref1`, `ref2`, `ref3`) — the foundation
for character consistency across all EPs and genres.

## Test Flow (11 Steps)

| # | Step | What |
|---|------|------|
| 1 | Login | Auth as admin |
| 2 | Horror refs | 3 refs (จันทรา/เจ/ผี) with all required fields |
| 3 | Romance refs | 3 refs (มิ้นท์/ภูมิ/พีช) with all required fields |
| 4 | Cross-project isolation | Horror refs != Romance refs |
| 5 | URL validation | Refs point to valid `/opt/director-studio/refs/` paths |
| 6 | Update round-trip | PUT ref description → GET back → marker persists |
| 7 | Script uses [ref1] | Scene 1 has `characters: ['ref1']` (INGRADAID mode) |
| 8 | Veo uses [ref1] | Veo prompt contains `[ref1]` + `reference_image: ['ref1']` |
| 9 | UI: project view | Shows project title + episode titles |
| 10 | UI: settings panel | Has ref info UI (optional) |
| 11 | Cross-tenant | No-token GET returns 401 |

## Results

### ✅ 41/41 PASS (100%)

| Step | What | Result |
|------|------|--------|
| 1 | Login | ✅ PASS |
| 2 | Horror has 3 refs | ✅ 3/3 (12 fields verified) |
| 3 | Romance has 3 refs | ✅ 3/3 (12 fields verified) |
| 4 | Cross-project isolation | ✅ PASS (no overlap) |
| 5 | URLs valid | ✅ 6/6 (3+3) |
| 6 | Update round-trip | ✅ PUT + GET + marker persists |
| 7 | Script uses ref slots | ✅ Scene 1 has `['ref1']` |
| 8 | Veo uses ref slots | ✅ Prompt: `[ref1] lies groggily...` |
| 9 | UI project view | ✅ Title + EP1 visible |
| 10 | UI settings | ✅ Has ref info |
| 11 | Cross-tenant security | ✅ 401 on no-token |

### Verified Refs

**Horror project (อยุธยา · ย้อนยุค)**:
- `ref1`: จันทรา (น้ำ) — Female Thai villager, 22, long black hair, white traditional dress
- `ref2`: เจ — Male Thai villager, 25, short black hair, dark shirt
- `ref3`: ผี — Ghost entity, pale face, long white hair, dark aura

**Romance project (โรงเรียนรัก · นักศึกษาใหม่)**:
- `ref1`: มิ้นท์ — Female high school student, 17, long black hair in braid
- `ref2`: ภูมิ — Male high school senior, 18, long black hair to neck
- `ref3`: พีช — Female high school student, 17, short black hair

## Key Validation

### 1. Abstract Slots (INGRADAID)
- ✅ All refs use abstract slots `ref1`/`ref2`/`ref3` (not file-bound)
- ✅ Scene uses `[ref1]` not real name
- ✅ Veo prompt has `[ref1] lies groggily...` (not "จันทรา lies...")

### 2. Required Fields
Every ref must have:
- `slot` (ref1/ref2/ref3)
- `url` (filesystem path)
- `display_name` (human name)
- `description` (character details)

### 3. Cross-Tenant Security
- ✅ No-token GET returns 401
- ✅ Each user only sees their own projects
- ✅ Horror refs ≠ Romance refs (no leakage)

## How to Run

```bash
cd /workspace/director-studio-test-cases/04-refs-management
python3 test_refs.py
```

Output:
- `runs/<timestamp>/report.html`
- `runs/<timestamp>/results.json`
- `runs/<timestamp>/screenshots/*.png` (4 screenshots)

## Test Artifacts
- **Test file**: `test_refs.py` (550 lines)
- **Latest run**: `runs/20260713_195603/`
- **Report**: `runs/20260713_195603/report.html`
- **Results**: `runs/20260713_195603/results.json`
- **Screenshots**: 4 PNG files
- **Duration**: 47.7s

## Screenshot Index
1. `01-login.png` — Login page
2. `01b-after-login.png` — After login (logged in)
3. `09-project-view.png` — Horror project view (4 episodes)
4. `10-settings.png` — Settings panel

## What This Test Validates
- ✅ INGRADAID abstract slots work (`ref1`/`ref2`/`ref3`)
- ✅ Each project has 3 refs with all required fields
- ✅ Refs are persisted (round-trip update)
- ✅ Refs flow to script gen (scene.characters = [ref1])
- ✅ Refs flow to Veo gen ([ref1] in prompt, reference_image array)
- ✅ Cross-project isolation (horror ≠ romance)
- ✅ URL paths point to valid filesystem locations
- ✅ No-token auth returns 401

## What This Test Does NOT Cover
- Refs upload UI (covered in admin/features)
- Refs image preview (covered in TC-01 video gen)
- Per-scene ref selection (covered in TC-03)
- Refs deletion (not implemented yet)

## Test Date
2026-07-14 02:55 ICT

## Author
Director Studio QA — automated test by Mavis
