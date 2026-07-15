"""
config.py — TC-25 Full Test Configuration
แก้ค่าตรงนี้ → รันใหม่ได้เลย ไม่ต้องแก้ test script
"""
import os
from pathlib import Path

# ============================================================
# 🎬 TEST CONFIG (แก้ตรงนี้ที่เดียว)
# ============================================================

# Stories (เรื่อง) — จำนวน stories ที่จะ generate
NUM_STORIES = int(os.getenv("TC25_STORIES", "3"))  # default 3 (10 takes too long)

# Episodes per story — จำนวน EP ต่อเรื่อง
EPISODES_PER_STORY = int(os.getenv("TC25_EPISODES", "3"))  # default 3 (5 takes too long)

# Scenes per episode — จำนวน scenes ต่อ EP
SCENES_PER_EP = int(os.getenv("TC25_SCENES", "5"))  # default 5 (10 takes too long)

# How many videos to actually generate (0 = none, only scripts)
# Default: first story, first EP, all scenes
VIDEO_STORY_IDX = int(os.getenv("TC25_VIDEO_STORY", "0"))  # 0-indexed
VIDEO_EP_IDX = int(os.getenv("TC25_VIDEO_EP", "0"))  # 0-indexed
VIDEO_SCENE_COUNT = int(os.getenv("TC25_VIDEO_SCENES", str(SCENES_PER_EP)))  # all scenes in that EP

# ============================================================
# 📂 PATHS
# ============================================================
LIVE = os.getenv("TC25_LIVE", "https://directorstudio.sj88ai.com")
ADMIN_EMAIL = os.getenv("TC25_ADMIN_EMAIL", "admin@sj88ai.com")
ADMIN_PW = os.getenv("TC25_ADMIN_PW", "admin1234")

SCRIPT_DIR = Path(__file__).parent
TEST_DIR = SCRIPT_DIR.parent
REF_FILE = TEST_DIR / "refs" / "ref1.jpg"
SCREENSHOTS_DIR = TEST_DIR / "screenshots"
VIDEOS_DIR = TEST_DIR / "videos"
DOWNLOADS_DIR = TEST_DIR / "downloads"

SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# ⏱️ TIMEOUTS
# ============================================================
LLM_TIMEOUT_S = 180  # per script gen
VEO_TIMEOUT_S = 300  # per video gen (poll every 5s)
VEO_POLL_INTERVAL_S = 5

# ============================================================
# 🎨 STORY IDEAS (one per story)
# ============================================================
STORY_IDEAS = [
    # 10 ideas, all Thai horror with the character
    "สาวจีนในชุดเชียงเชียนแดงกลับมาที่บ้านเก่าในต่างจังหวัด เธอเห็นเงาของตัวเองในกระจก แต่เงายิ้มก่อนเธอ",
    "สาวจีนสืบทอดร้านอาหารจีนโบราณ เมื่อเปิดร้านตอนกลางคืน ลูกค้าที่มาทานดูเหมือนคนเดิมทุกคืน แต่ไม่มีใครจ่ายเงิน",
    "สาวจีนได้รับจดหมายจากคุณยายที่เสียชีวิตไปแล้ว 10 ปี จดหมายบอกให้เธอกลับไปที่หมู่บ้านเก่า ที่นั่นมีความลับที่ถูกซ่อนไว้",
    "สาวจีนทำงานเป็นพนักงานต้อนรับในโรงแรมเก่าแก่ ผู้เข้าพักห้อง 303 มักหายตัวไปในตอนกลางคืน และกลับมาในตอนเช้าโดยไม่รู้ตัว",
    "สาวจีนซื้อตุ๊กตาผ้าโบราณจากตลาดนัด ตุ๊กตาดูเหมือนเด็กผู้หญิง ทุกคืนตุ๊กตาจะย้ายที่ในห้อง",
    "สาวจีนได้งานเป็นครูสอนภาษาจีนที่โรงเรียนป่า ที่นั่นนักเรียนทุกคนรู้จักชื่อเธอ ทั้งที่เธอเพิ่งมาถึง",
    "สาวจีนขับรถกลับบ้านตอนดึก เห็นผู้หญิงชุดแดงยืนขอทาง ทุกครั้งที่เธอจอดรถ ผู้หญิงคนนั้นอยู่ใกล้ขึ้นเรื่อยๆ",
    "สาวจีนเช่าห้องในอพาร์ตเมนต์เก่า เพื่อนบ้านบอกว่าห้องนี้ไม่มีใครอยู่ได้นาน เพราะทุกคืนจะมีเสียงร้องเพลงจีนดังมาจากกำแพง",
    "สาวจีนถ่ายภาพในงานศพของครอบครัวเศรษฐี เมื่อล้างฟิล์ม เธอเห็นคนตายยืนอยู่ข้างศพ หันมายิ้มให้กล้อง",
    "สาวจีนทำงานในร้านตัดเสื้อของคุณป้า คุณป้าเย็บชุดเชียงเชียนแดงให้ลูกค้าทุกคน แต่ลูกค้าไม่เคยกลับมารับ",
]

# Use the configured number of stories
STORY_IDEAS = STORY_IDEAS[:NUM_STORIES]

# ============================================================
# 📊 DERIVED
# ============================================================
TOTAL_SCRIPTS = NUM_STORIES * EPISODES_PER_STORY * SCENES_PER_EP
TOTAL_VIDEOS = VIDEO_SCENE_COUNT if VIDEO_SCENE_COUNT > 0 else 0

print(f"""
TC-25 Full Test Configuration:
  Stories:           {NUM_STORIES}
  EPs per story:     {EPISODES_PER_STORY}
  Scenes per EP:     {SCENES_PER_EP}
  ─────────────────────────────
  Total scripts:     {TOTAL_SCRIPTS} ({NUM_STORIES} × {EPISODES_PER_STORY} × {SCENES_PER_EP})
  Video gen:         {TOTAL_VIDEOS} scenes
                     (story #{VIDEO_STORY_IDX+1}, EP #{VIDEO_EP_IDX+1})
  Live URL:          {LIVE}
  Ref image:         {REF_FILE.name if REF_FILE.exists() else 'NOT FOUND'}
""")
