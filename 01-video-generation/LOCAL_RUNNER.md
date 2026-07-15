# 🏃 Run TC-01 ที่เครื่องคุณ (ไม่ผ่าน VPS)

## ⚠️ ทำไมต้องรันเอง?

VPS IP (`5.83.147.61`) **ถูก Cloudflare 1010 แบนถาวร** เพราะ request เยอะ
- ทุก request จาก VPS ไป genaipro.io → 403
- **Browser signature ไม่ช่วย** Cloudflare แบน IP ไม่ใช่ fingerprint
- ✅ IP บ้านคุณไม่โดน ban → รันจาก local ได้

## 📋 เตรียมเครื่อง

1. **Python 3.11+** + **pip**
2. **Google Chrome** ติดตั้งแล้ว
3. **Playwright** (Python lib)

```bash
pip install playwright
playwright install chrome  # ถ้าจำเป็น
```

## 📥 Download ไฟล์

จาก `/workspace/director-studio-test-cases/01-video-generation/`:
- `test_full.py` ← test script หลัก
- `TC-01-video-generation.md` ← spec
- `TEST_AT_HOME.md` ← คำแนะนำ

## ✏️ แก้ CHROME path

ใน `test_full.py`:
```python
CHROME = "/opt/google/chrome/chrome"  # VPS
```

เปลี่ยนเป็น:
- **macOS**: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- **Windows**: `C:\Program Files\Google\Chrome\Application\chrome.exe`
- **Linux**: `/usr/bin/google-chrome`

## 🚀 รัน

```bash
cd /path/to/01-video-generation/
python3 test_full.py
```

## 📊 Output

ทุก run จะสร้าง folder ใหม่:
```
runs/20260713_HHMMSS/
├── report.html              ← เปิดใน browser ดูได้
├── results.json             ← raw data
└── screenshots/             ← รูปทุก step
    ├── 01-login-page.png
    ├── 02a-filled-form.png
    ├── 02b-after-submit.png
    ├── 03-project-opened.png
    ├── 04a-ep1-script-tab.png
    ├── 04b-ep1-veo-tab.png
    ├── 05a-before-click.png
    ├── 05b-after-click.png
    ├── 05c-progress-Ns.png  (ทุก 10s)
    └── 05d-final.png
```

## 🎯 Expected Output (ถ้า IP บ้านไม่โดน ban)

- ✅ Step 1-4: PASS (login, navigate)
- ✅ Step 5: Generate Video
  - Status: completed
  - video_src: URL จาก genaipro (เช่น `https://*.genaipro.io/...` หรือ `*.storage.googleapis.com/...`)
  - Duration: 8 วินาที
- 📊 HTML report พร้อม network log + screenshots

## 🐛 ถ้ายังเจอ 403 ที่บ้าน

แสดงว่า IP บ้านก็โดน (น่าจะเพราะ provider เดียวกัน)
- ลอง **mobile hotspot** (4G/5G) เปลี่ยน IP
- ลอง **VPN** (ProtonVPN free / Cloudflare WARP)
- ถ้ายังไม่ได้ → ใช้ **Replicate API** แทน (BYO key)
