# TC-20 — Export (.md / .json / .txt)

**Test Date**: 2026-07-15
**Result**: ✅ **34/34 PASS** (100%)
**Component**: Director Studio — Project Settings → Export
**Live URL**: https://directorstudio.sj88ai.com/

---

## What it tests

Export project to **3 formats** for different use cases:
- **.md** (Markdown) — readable, for review/sharing
- **.json** (JSON) — full structure, for programmatic use
- **.txt** (Plain text) — **1 prompt per line**, ready to copy-paste into Sora/Runway/Veo

## User requirement (literal)
> "Export .md/.json และ txt คำสั่งล่ะ 1 ไฟล์ เพื่อเอาไปเจนที่อื่น"

## Test scenarios — detailed

### T1. Project structure (sanity)
- Project with 2 EPs × 3 scenes + Veo prompts in timeline

### T2. API .json export
- `GET /api/projects/{id}` returns full project
- JSON-serializable, includes episodes

### T3. UI buttons present
- `#project-export-btn` (.json) ✓
- `#project-export-md-btn` (.md) ✓
- `#project-export-txt-btn` (.txt) ✓
- Screenshot: `01-export-buttons.png`

### T4. Real .json download (browser)
- Click → download triggered
- File saved: `Ghost_Cafe_xxx.json`
- 2 episodes, all fields preserved

### T5. Real .md download (browser)
- Click → download triggered
- File contains:
  - `# Ghost Cafe` title
  - `## 📋 2 Episodes` count
  - EP1 + EP2 titles
  - scene mentions

### T6. Real .txt download (browser) — **the new feature**
- Click → download triggered
- File: `Ghost_Cafe_prompts.txt`
- **Format**: `EP1_S01_01: <prompt>` (1 per line)
- **No markdown noise** (no ## or **)
- **No JSON syntax** (no {)
- **Real content** preserved (cinematic horror, Thai horror, etc.)
- Header is comment-style (`# Ghost Cafe`)
- Screenshot: `02-after-downloads.png`

### T7. Empty project
- `.md` shows "No episodes yet"
- `.txt` shows "(no episodes yet)"

### T8. .txt ready for copy-paste
- 6 real prompts (2 EPs × 3 scenes)
- All prompts > 50 chars (substantive for AI tools)

## Sample .txt output

```
# Ghost Cafe
# Project ID: 0d863f9e61dc4d65
# Exported: 2026-07-14T20:11:44.942Z
# Genre: horror
# Language: th
# Aspect: 9:16

# ===== EP1: เข้าร้าน =====
# EP1: เข้าร้าน
# น้ำเข้าร้านกาแฟเที่ยงคืน เห็นเงาเด็กในกระจก
# Exported: 2026-07-14T20:11:44.942Z

EP1_S01_01: ผู้หญิงเดินเข้าร้านกาแฟมืด ประตูไม้เก่า เสียงกระดิ่งดังเบาๆ cinematic horror
EP1_S01_02: close-up เคาน์เตอร์ไม้ บาริสต้าชราผูกผ้ากันเปื้อน หลอดไฟแก้วสั่น Thai horror atmosphere
EP1_S01_03: เงาเด็กผู้หญิงในกระจก ยิ้มก่อนตัวจริง slow motion supernatural
...
```

## Files modified (v3.2)

| File | Change |
|------|--------|
| `frontend/js/export.js` | Added `scriptToText()` + `projectToText()` (66 new lines) |
| `frontend/js/projects.js` | Added 2 new buttons + handlers (33 new lines) |
| `frontend/index.html` | Added .md + .txt buttons + hint text in project settings modal |

## New functions

### `scriptToText(ep, epNum)`
- 1 prompt per line format
- Prefers Veo timeline prompts (Stage 2 output)
- Falls back to scene.action if no Veo prompts
- Comment-style header (`# ...`)

### `projectToText(project)`
- All episodes, all scenes
- Includes meta (genre, language, aspect)
- Episode separator: `# ===== EP<n>: <title> =====`

## How to run

```bash
cd /workspace/director-studio-test-cases/20-export/scripts
python3 test_tc20_export.py
```

**Output**: 34/34 PASSED, 2 screenshots, 6 download files (real .json, .md, .txt, empty.md, empty.txt, real .json from first run)

## Key findings (RCA)

1. **Live site has 2 copies of `projects.js`** — `/js/projects.js` AND `/projects.js` — easy to miss when deploying. Both must be updated.
2. **`export.js` previously had only Markdown** — no .txt function. Added now.
3. **Project Settings modal had 1 button** (.json) — now has 3 (.json, .md, .txt) with hint text explaining the use case.
4. **Downloaded .txt format**: `EP{n}_S{xx}_{yy}: <prompt>` — parses cleanly with regex `^EP\d+_S\d+_\d+: .+`
5. **Comment-style header** (`# ...`) keeps .txt parseable but adds context
6. **Empty state handling**: `.md` says "No episodes yet", `.txt` says "(no episodes yet)"

## Use cases unlocked

| Format | Tool | Workflow |
|--------|------|----------|
| .md | Notion / Obsidian / Slack | Review script, share with team |
| .json | Backup / migration | Restore project, version control |
| **.txt** | **Sora / Runway / Veo (other accounts) / Midjourney video** | **Paste prompts one by one, generate, repeat** |

## Screenshots

| # | File | What it shows |
|---|------|---------------|
| 1 | `01-export-buttons.png` | Project Settings modal with 3 export buttons + .txt hint |
| 2 | `02-after-downloads.png` | After all 3 downloads complete |

## Sample downloads (in `downloads/`)

- `Ghost_Cafe_xxx.json` (3.6KB) — full project structure
- `Ghost_Cafe_xxx.md` (536B) — readable markdown
- `Ghost_Cafe_prompts.txt` (1.6KB) — **1 prompt per line**
- `empty.md` (131B) — empty project
- `empty.txt` (96B) — empty project

## Coverage contribution

| Metric | Before | After |
|--------|--------|-------|
| Total TCs | 16 (TC-18) | **17 (TC-20 added)** |
| Pass rate | 98% (192/197) | **98% (226/231)** |
| Export formats | 1 (.json) | **3 (.json, .md, .txt)** |

## Status

✅ **DEPLOYED & TESTED** — All 34 scenarios pass against live site.
📤 Users can now export prompts in any format for use in Sora/Runway/etc.
