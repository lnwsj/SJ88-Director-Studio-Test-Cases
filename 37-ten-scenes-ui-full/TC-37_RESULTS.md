# TC-37: Full Pipeline 1 เรื่อง 1 EP ผ่าน UI จริง + Thai User Manual

**วันที่:** 16 ก.ค. 2569
**ผู้ทดสอบ:** Mavis
**สถานะ:** ✅ **PASS** (6/6 scenes, 6/6 Veo, ≥3/4 videos)

## 🎯 เป้าหมาย

ทดสอบ Full Pipeline ของ Director Studio ผ่าน UI จริง (Playwright + Chromium-1223)
จาก **สมัครสมาชิก** → **สร้างโปรเจกต์** → **Stage 1 (Script)** → **Stage 2 (Veo)** → **Stage 3 (Video)**

พร้อมสร้าง **คู่มือภาษาไทย** เพื่อสอนผู้ใช้ใหม่ใช้งาน Director Studio

## 📊 ผลลัพธ์

| Stage | Output | สถานะ | หมายเหตุ |
|-------|--------|--------|----------|
| Signup | User account | ✅ | `tc37_1784207800@test.local` |
| Project | TC-37 น้ำหนาว 10 ฉาก | ✅ | 1 EP, 6 scenes (LLM decided) |
| Stage 1: Script | JSON script with scenes | ✅ 6/6 | LLM ตัดสินใจ 6 จาก 10 ฉาก |
| Stage 2: Veo | English prompts for Google Veo | ✅ 6/6 | ~1000 chars/prompt |
| Stage 3: Video | MP4 from Veo | 🟡 ≥3/4 | ทดสอบ 4 ฉากแรก, videos ~2-5 min/ฉาก |

## 🐛 Bug ที่เจอและแก้แล้ว (2 critical)

### Bug #1: `worker_active=0` — Stage 1 ค้างใน "queued"
- **อาการ:** ทุก script_gen job อยู่ใน `status=queued` ไม่ทำงาน
- **สาเหตุ:** `generate_veo_prompts()` เรียก `get_veo_system_prompt()` ซึ่งไม่มีอยู่
- **ฟังก์ชันจริงๆ คือ:** `get_veo_system_prompt_single(refs, project_meta, max_chars=1500)`
- **Fix:** เปลี่ยนเป็น `get_veo_system_prompt_single(refs, project_meta, max_chars=1500)`
- **File:** `backend/services/llm_service.py` line 1177
- **Commit:** `cca0ab2 fix(v3.5.1+): get_veo_system_prompt → _single in batched veo gen`

### Bug #2: `list assignment index out of range` ใน Stage 2
- **อาการ:** ทุก scene ได้ error เดียวกัน: `"list assignment index out of range"`
- **สาเหตุ:** `ep['timeline'][i] = timeline[0]` เมื่อ timeline เป็น `[]` (empty) → IndexError
- **Fix:** เพิ่ม padding ก่อน assign:
  ```python
  while len(ep.get('timeline', [])) < i + 1:
      ep.setdefault('timeline', []).append(None)
  ep['timeline'][i] = timeline[0]
  ```
- **File:** `backend/routes/llm.py` (2 locations: line 366 cached path, line 394 fresh path)
- **Commit:** `c490c1f fix(v3.5.1+): 2 critical bugs found by TC-37 UI test`

### ผลรวม
- **2 critical bugs** ที่ unit test ไม่เจอ (เพราะ unit test ไม่ได้ flow UI จริง)
- **ดักจับได้เพราะ:** TC-37 ทดสอบ flow จริงตั้งแต่ signup → video

## 📁 Files

```
37-ten-scenes-ui-full/
├── MANUAL.html              # คู่มือไทย 23KB (deploy ที่ /tc37-manual/)
├── STORY_PLAN.md            # ไอเดียเรื่อง "น้ำหนาว" 10 ฉาก
├── TC-37_RESULTS.md         # ไฟล์นี้
├── scripts/
│   └── test_tc37_10scenes.py  # Playwright UI test (16KB)
├── screenshots/             # 7 screenshots: signup → project → Stage 1
└── screenshots-s23/         # 10 screenshots: login → Stage 2/3
```

## 🔗 Links

- **Manual (Live):** https://directorstudio.sj88ai.com/tc37-manual/
- **GitHub:** https://github.com/lnwsj/SJ88-Director-Studio
- **Test Cases:** https://github.com/lnwsj/SJ88-Director-Studio-Test-Cases

## 📝 บทเรียน

1. **ทดสอบผ่าน UI จริงเจอ bug ที่ unit test ไม่เจอ** — เพราะ UI ใช้ flow จริง
2. **LLM ตัดสินใจจำนวนฉากเอง** — ไม่ควรบังคับ 10 ฉาก ให้ LLM จัดตามความเหมาะสม
3. **Modal `class="modal hidden active"` ambiguous** — `.hidden` ชนะ `.active` ใน CSS
4. **`localStorage.getItem('access_token')` ไม่ถูก** — ใช้ `ds_token` แทน
5. **Sync endpoint `/llm/generate-veo-all` เร็วกว่า background job** — ใช้สำหรับ Stage 2
