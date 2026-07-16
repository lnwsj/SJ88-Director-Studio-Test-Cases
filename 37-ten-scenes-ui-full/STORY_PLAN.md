# TC-37: 1 เรื่อง 1 EP **10 ฉาก** — Full UI Pipeline Test

**Date**: 2026-07-16
**Goal**: Verify system can generate EXACTLY 10 scenes through real UI + create user manual
**Server**: https://directorstudio.sj88ai.com (v3.5.1)
**Test dir**: `/workspace/director-studio-test-cases/37-ten-scenes-ui-full/`

## Story: "น้ำหนาว" (The Cold Water) — Thai horror 10 scenes

**Why this story works for 10 scenes**:
- 4 distinct characters (ลูกค้า ชาย, เจ้าของร้าน, แม่ค้าชรา, เงา)
- 5 distinct locations (ร้านก๋วยเตี๋ยว, ห้องครัว, บ่อน้ำ, ถนน, ศาลพระภูมิ)
- Clear 3-Act structure: Setup (1-3) → Mystery (4-7) → Climax+Resolution (8-10)
- Each scene has strong visual + props (เข็ม, หม้อ, ถ้วย, น้ำ, ผ้าเช็ดมือ, ตะเกียง, ผี, กระดาษ, ตู้เย็น, จดหมาย)

## 10 Scenes Design

| # | Title | Location | Time | Visual anchor | Props |
|---|-------|----------|------|---------------|-------|
| 1 | ลูกค้าคนสุดท้าย | ร้านก๋วยเตี๋ยวเก่า | 22:00 | ร้านมืด พิงโต๊ะ | เข็ม 1 ด้าม |
| 2 | สั่งเมนูลึกลับ | หน้าเคาน์เตอร์ | 22:05 | เจ้าของร้านมองผ่าน | กระดาษสั่ง |
| 3 | หม้อน้ำเดือด | ห้องครัว | 22:10 | ไอน้ำพุ่ง | หม้อ + น้ำ |
| 4 | ถ้วยแตก | หน้าเคาน์เตอร์ | 22:15 | ถ้วยแตกกลางพื้น | ถ้วยแตก |
| 5 | แม่ค้าชราปรากฏ | ประตูหลังร้าน | 22:20 | เงาเดินเข้ามา | ผ้าเช็ดมือ |
| 6 | บ่อน้ำต้องสาป | หลังร้าน | 22:30 | น้ำดำ ไม่นิ่ง | บ่อน้ำ |
| 7 | ตะเกียงดับ | ถนนเปลี่ยว | 22:40 | ตะเกียงวูบ | ตะเกียง |
| 8 | เงาไล่ทัน | ถนน | 22:45 | เงายืนข้างหลัง | เงาในเงา |
| 9 | ศาลพระภูมิ | มุมถนน | 23:00 | ศาลเก่า + ผี | ผี + ศาล |
| 10 | จดหมายในตู้เย็น | ครัว รุ่งเช้า | 06:00 | ตู้เย็นเก่า | จดหมาย |

## 3-Act Structure
- **Act 1 Setup (1-3)**: ลูกค้าเข้าร้านดึก → สั่งอาหาร → เจ้าของร้านทำ
- **Act 2 Mystery (4-7)**: ถ้วยแตก → แม่ค้าชราปรากฏ → บ่อน้ำ → ตะเกียงดับ
- **Act 3 Climax+Resolution (8-10)**: เงาไล่ → ศาลพระภูมิ → จดหมายในตู้เย็น (twist reveal)

## Characters (default 4 — น้ำ/เจ/ยาย/ผี)
- ref1 น้ำ (25F) — ลูกค้าผู้หญิง เสื้อยืดดำ กางเกงยีนส์
- ref2 เจ (32M) — เจ้าของร้าน เสื้อกุ้ยเล่ ผ้ากันเปื้อน
- ref3 ยาย (75F) — แม่ค้าชรา ชุดไทย ผมขาว ไม้เท้า
- ref4 ผี — เงาดำ ผมยาว

## Expected Results
- Stage 1: 10 scenes in ~70-90s (with num_scenes=10)
- Stage 2: 10 Veo prompts (1100-1300 chars each)
- Stage 3: 10 real videos (~2-4 min each, total ~25-40 min)
- Total pipeline: ~30-45 min end-to-end
- 10/10 scenes + 10/10 videos confirmed
