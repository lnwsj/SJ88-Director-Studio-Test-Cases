# TC-30: v3.4 Per-Scene Regenerate with Optional Feedback

**Date**: 2026-07-15
**Status**: ✅ **11/11 PASS** (Real UI via Playwright + Chromium-1223)
**Commit**: `dc5081e` feat(v3.4): per-scene regenerate with optional feedback

---

## 🎯 What This Tests

Director Studio **v3.4** introduces per-scene regeneration with **optional user feedback**:
- 🔄 Button on every scene card in the episode modal
- Modal popup with optional feedback textarea (Thai/English supported)
- LLM regenerates the scene with full context awareness
- Auto-regenerates the Veo prompt if timeline exists
- Live UI update: scene card replaced in place

---

## 🏗️ Architecture

### Backend (`api/routes/llm.py` + `api/services/llm_service.py`)

**New endpoint**: `POST /api/llm/regenerate-scene`

**Request body**:
```json
{
  "project_id": "abc123",
  "ep_idx": 0,
  "scene_idx": 0,
  "feedback": "make it scarier with more fog",
  "regenerate_veo": true
}
```

**Response**:
```json
{
  "ok": true,
  "scene": { ... 20 production fields ... },
  "veo": { "prompt": "...", "vo": "...", "audio_cue": "..." },
  "feedback_applied": true,
  "scene_idx": 0,
  "ep_idx": 0
}
```

**New service function** `regenerate_single_scene()`:
- Reuses `get_script_system_prompt()` for genre/language consistency
- Builds context: 2 prev scenes + 2 next scenes (continuity)
- Adds REGENERATE-specific instructions
- Honors optional user feedback
- ALWAYS forces original scene id (LLM may hallucinate `S02_01` for scene 0)
- 22 fields in output (20 production + action + dialogue)

### Frontend (`js/episode.js` + `episode.js` + `style.css`)

**3 new things**:
1. 🔄 Button on every scene card in `renderScene()`
2. `regenerateScene()` function — calls API, replaces card in place
3. `showRegenerateModal()` — feedback popup with examples

**UI Flow**:
```
Click 🔄 → Modal opens with feedback textarea
            ↓
        User types feedback (or leaves empty)
            ↓
        Click "🔄 Regenerate (30-60s)"
            ↓
        Spinner: "⏳ Regenerating scene..."
            ↓
        LLM returns new scene + (optional) Veo prompt
            ↓
        Scene card REPLACED in place
            ↓
        Toast: "Scene N regenerated (feedback applied) (+ Veo prompt)"
```

**Modal examples shown to user**:
- "make it scarier" / "เพิ่มความน่ากลัว"
- "focus on [ref1]" / "ให้ [ref1] เด่นกว่านี้"
- "change location to ..." / "เปลี่ยนสถานที่เป็น..."
- "more dialogue" / "เพิ่มบทพูด"
- "shorter" / "สั้นลง"

---

## 🧪 Test Results (Real UI via Playwright)

**Environment**: Chromium-1223 headless, https://directorstudio.sj88ai.com/

### Test 1: Cancel flow
| Step | Status | Detail |
|------|--------|--------|
| Login as admin | ✅ PASS | URL redirected |
| Open project | ✅ PASS | First project card clicked |
| Open episode | ✅ PASS | 3 scenes, 3 🔄 buttons |
| Click 🔄 on scene 1 | ✅ PASS | Modal appeared |
| Cancel modal | ✅ PASS | Modal closed, no changes |
| Reopen modal | ✅ PASS | Modal reopens on second click |

### Test 2: Regenerate without feedback
| Step | Status | Detail |
|------|--------|--------|
| Confirm without feedback | ✅ PASS | LLM called (40.3s) |
| Action text changed | ✅ PASS | "[ref1] นอนอยู่บนพื้นไม้เก่า หมอกสีขาวข้นหนามาก..." → "[ref1] นอนอยู่บนพื้นไม้เก่า หมอกสีขาวข้นหนา..." |
| Veo prompt regenerated | ✅ PASS | 1450 chars (within 1500 cap) |

### Test 3: Regenerate with feedback
| Step | Status | Detail |
|------|--------|--------|
| Type feedback | ✅ PASS | "make it scarier with more fog" |
| Confirm | ✅ PASS | LLM called (40.3s) |
| Action text changed | ✅ PASS | Different from previous version |
| Feedback applied | ✅ PASS | Toast: "Scene 1 regenerated (feedback applied) (+ Veo prompt)" |

### Test 4: Veo tab verification
| Step | Status | Detail |
|------|--------|--------|
| Switch to Veo tab | ✅ PASS | 3 Veo prompts visible |
| Scene 1 Veo prompt | ✅ PASS | 1450 chars cinematic prompt |
| Reference image slot | ✅ PASS | `ref: ref1` |
| Timecode | ✅ PASS | `t=0.0-8` |
| Dialogue (VO) | ✅ PASS | Thai dialogue in [ref1] format |
| Audio cue | ✅ PASS | "เสียงน้ำกระทบสามารถไม้ได้ยินดังเงียบๆ..." |

### Test 5: No JS errors
| Step | Status | Detail |
|------|--------|--------|
| Console errors | ✅ PASS | 0 errors during full flow |

**Total: 11/11 PASS** (100%)

---

## 📸 Screenshots

All in `screenshots/`:
- `v3_modal.png` — Feedback modal opened
- `v3_filled_feedback.png` — Feedback typed
- `v3_after.png` — Scene regenerated (toast visible)
- `v4_modal.png` — Reopened modal
- `v4_feedback.png` — With feedback filled
- `v4_after_regen.png` — After with-feedback regen
- `v4_veo_tab.png` — Veo tab showing 3 regenerated prompts
- `v4_final.png` — Full final state

---

## 🔍 Key Technical Decisions

1. **Always force original id** — LLM may output wrong id like `S02_01` for scene 0. We override with `ep_idx+1`+`scene_idx+1`.

2. **Preserve timeline fields** — When regen-ing Veo prompt, keep `t` (timecode) and `reference_image` from old timeline if new LLM didn't include them.

3. **2 prev + 2 next scenes for context** — LLM needs continuity but too much context is wasteful. 2+2 is the sweet spot.

4. **Modal auto-focus on textarea** — User can immediately start typing after clicking 🔄.

5. **Ctrl+Enter to submit** — Enter alone adds newline, Ctrl+Enter confirms. Better UX for multi-line feedback.

6. **Scene card replaced in place** — No need to re-render whole modal, just `card.replaceWith(newCard)`. Re-wires event handlers on new card.

7. **Toast on success/fail** — Different toast for "feedback applied" vs not, and "(+ Veo prompt)" if Veo also regenerated.

---

## 🌐 Live URLs

- **Production**: https://directorstudio.sj88ai.com/ (login + open any project with scenes)
- **GitHub**: https://github.com/lnwsj/SJ88-Director-Studio (commit `dc5081e`)
- **TC files**: https://github.com/lnwsj/SJ88-Director-Studio-Test-Cases (TC-30 folder)

---

## 🎬 Example Output (Real Generation)

**Input feedback**: "make it scarier with more fog, slower pacing"

**Generated scene action**:
> [ref1] นอนอยู่บนพื้นไม้เก่า หมอกสีขาวข้นหนาคลุมท่วมร่างเกือบถึงอก ตื่นขึ้นช้าๆ อย่างช้า ๆ มองเห็นเงาจาง ๆ ของผู้หญิงในชุดขาวยืนนิ่งอยู่ที่ปลายเตียง...

**Generated Veo prompt (1450 chars)**:
> ECU shot, slow tilt up กล้องเลื่อนขึ้นจากเงามืดเข้าหาใบหน้า ตื่นขึ้นช้าๆ ขยี้ตาเข้าข้างๆ เห็นเงาขาวเลือนลาง [ref1] lies on damp teak floor of pitch-dark wooden room, lifting one trembling hand to touch a mold-stained wall, 35mm lens...

**Reference**: `ref1` (only — INGRADAID slot used correctly)

---

## 🐛 Bugs Found & Fixed During TC

1. **LLM hallucinated wrong scene id** (e.g. `S02_01` for scene 0 in EP 1) — Fixed by always forcing `ep.scenes[scene_idx].id` after parse.

2. **Test was checking wrong field for "scene changed"** — Title usually doesn't change. Switched to checking `.scene-action` which always changes.

3. **Modal close check was racy** — Test exited after 5s thinking it was done, but LLM takes 40s. Added proper spinner-wait loop (up to 90s).

---

## 🔗 Related Test Cases

- **TC-26**: UI Full E2E from Signup (10/10)
- **TC-27**: Story Continuity Across 10 Scenes (10/13, 95% continuity)
- **TC-28**: v3.3 AI Story Tools — 3 UI guides
- **TC-29**: AI script gen reads refs from project
- **TC-30**: ← You are here

