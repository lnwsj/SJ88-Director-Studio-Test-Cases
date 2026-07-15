# TC-01 · Video Generation (USER SIDE TEST)

**สถานะ: ต้อง test ที่เครื่อง user เอง (IP บ้าน)**

---

## ⚠️ ปัญหา

VPS IP (`5.83.147.61`) **ถูก Cloudflare แบน** หลังจาก request เยอะ
- Test ผ่าน UI จริง 4/5 steps (Login, เปิด Project, EP1, Veo tab)
- แต่ Step 5 (Generate Video) → backend VPS ส่ง request ไป genaipro → IP ถูก ban → 403
- **ไม่สามารถ test ได้จาก server-side** แม้จะใช้ Chrome signature จริง (Cloudflare แบน IP ไม่ใช่ signature)

## ✅ วิธี test ที่ถูก

**User ต้อง run test ที่เครื่องตัวเอง** (IP บ้าน ไม่โดน ban)

### ขั้นตอน:

1. **Download test script:** `/workspace/director-studio-test-cases/01-video-generation/test_ui_video_gen.py`
2. **Install Python deps:** `pip install playwright`
3. **Install Chrome:** `playwright install chrome`
4. **แก้ CHROME path** ใน script ตาม OS:
   - macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
   - Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe`
   - Linux: `/usr/bin/google-chrome`
5. **Run:** `python3 test_ui_video_gen.py`
6. **ดู screenshots** ที่ `01-video-generation/screenshots/`

### ผลที่คาดหวัง:

ถ้า IP บ้านไม่โดน ban:
- ✅ Step 5: Generate Video
- ✅ Video player ปรากฏ
- ✅ Video URL เป็น `*.genaipro.io` หรือ `*.storage.googleapis.com`
- ✅ Duration: 8 วินาที

## 🧪 Alternative: เทสแบบ manual ใน browser

ถ้าไม่อยาก run script:

1. เปิด https://directorstudio.sj88ai.com/ ใน Chrome
2. Login: admin@sj88ai.com / admin1234
3. คลิก "โรงเรียนรัก"
4. คลิก "วันแรกที่โรงเรียน"
5. Tab "Veo"
6. คลิก 🎬 "Generate Video" scene 1
7. **ถ้า IP บ้านไม่โดน ban** → จะเห็น video player ภายใน 30-90 วินาที

## 📌 สรุป

- ✅ Test framework ทำงาน (Playwright + Chrome)
- ✅ Login/navigate/episodes ทำงาน
- ❌ Video gen ต้อง IP ที่ไม่โดน ban (user's local)
- 💡 Cloudflare 1010 = IP ban, ไม่ใช่ browser fingerprint
