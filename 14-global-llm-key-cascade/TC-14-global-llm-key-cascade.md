# TC-14: Global LLM Key Cascade (Admin Central Key)

**Date**: 2026-07-14 18:39 UTC
**Status**: ✅ PASS — end-to-end working
**Commit**: `1c5b479` — "feat(settings): global LLM key cascade (admin central key)"

## 🎯 Feature Summary

**Problem**: New users couldn't use the app without configuring their own MiniMax API key — bad UX, blocks onboarding.

**Solution**: Admin sets ONE central LLM key → all users without their own key automatically use it. Users can still override with their own key.

**Cascade priority**:
1. **User's own key** (`settings.llm_api_key_enc`) — highest priority
2. **Admin's global key** (`settings.llm_api_key_global_enc`) — fallback
3. **None** → return 400 "configure your key or ask admin"

## 🔧 Implementation

### DB Migration (v3.1)
```sql
ALTER TABLE settings ADD COLUMN llm_api_key_global_enc TEXT;
ALTER TABLE settings ADD COLUMN llm_key_global_set_by TEXT;
ALTER TABLE settings ADD COLUMN llm_key_global_set_at REAL;
```

### New File: `api/services/llm_keys.py` (99 lines)
```python
def resolve_llm_key(user_id: str) -> tuple[str | None, str]:
    """Returns (api_key, source) where source is 'user' | 'global' | 'none'"""
    # 1. Check user's own key (decrypt)
    # 2. Fall back to admin's global key
    # 3. Return None if neither
```

### New API Endpoints
| Method | Path | Auth | Description |
|---|---|---|---|
| `PUT` | `/api/settings/llm-api-key/global` | admin | Set global LLM key (Fernet-encrypted) |
| `DELETE` | `/api/settings/llm-api-key/global` | admin | Clear global LLM key |
| `GET` | `/api/settings/llm-api-key/global` | any | View global key status (who set + when) |
| `GET` | `/api/settings` | any | Now includes `llm_key_source`, `is_admin`, `has_global_llm_key` |

### Modified Endpoints (4× LLM endpoints use resolve_llm_key)
- `POST /api/llm/generate-script`
- `POST /api/llm/generate-veo`
- `POST /api/llm/generate-veo-single`
- `POST /api/llm/generate-veo-all`

## 🧪 Test Results

### Test 1: Admin sets global key
```bash
PUT /api/settings/llm-api-key/global
Body: {"llm_api_key": "sk-cp-..."}
→ 200 OK {"ok": true}
```

### Test 2: View global key status
```bash
GET /api/settings/llm-api-key/global
→ 200 OK {
  "ok": true,
  "configured": true,
  "set_by": "admin@sj88ai.com",
  "set_at": 1784026421.587
}
```

### Test 3: Admin's /api/settings
```bash
GET /api/settings  (admin token)
→ 200 OK {
  "is_admin": true,
  "has_llm_api_key": true,
  "llm_key_source": "user",          ← admin has own key
  "has_global_llm_key": true,
  "global_llm_set_by": "admin@sj88ai.com",
  "global_llm_set_at": 1784026421.587
}
```

### Test 4: New user (no own key) /api/settings
```bash
POST /api/auth/signup {"email": "newuser@x.com", ...}
→ 200 OK + access_token
GET /api/settings  (new user token)
→ 200 OK {
  "is_admin": false,
  "has_llm_api_key": false,
  "llm_key_source": "global",        ← using admin's key!
  "has_global_llm_key": true,
  "global_llm_set_by": "admin@sj88ai.com"
}
```

### Test 5: New user can call LLM with global key ✅
```bash
POST /api/llm/generate-script
Body: {
  "prompt": "A simple test scene in a coffee shop",
  "episode_number": 1,
  "num_scenes": 2,
  "style": "romance",
  "previous_episodes": []
}
→ 200 OK {
  "ok": true,
  "script": {
    "scenes": [
      {"id": "S01_01", "title": "เข้ามาในความมืด", ...},
      {"id": "S01_02", "title": "เสียงกระซิบ", ...}
    ]
  }
}
```

**First scene title (Thai)**: "เข้ามาในความมืด" (Entering the Darkness)

### Test 6: Non-admin cannot set global key
```bash
PUT /api/settings/llm-api-key/global  (regular user token)
→ 403 Forbidden {
  "code": "admin_only",
  "message": "Only admin can set the global LLM key"
}
```

## 📸 UI Screenshots

### Admin Settings
- 🔑 LLM section: green badge "ใช้ key ส่วนตัว ของคุณ"
- 🌐 Global LLM Key card visible (admin only)
  - "ตั้งโดย: admin@sj88ai.com"
  - "เมื่อ: 14/7/2569 10:53:41"
  - "User ทุกคนที่ไม่มี key ส่วนตัวจะใช้ key นี้"
- Buttons: 💾 บันทึก Global Key + 🗑 ลบ Global Key

### User Settings (non-admin)
- ⚠️ ยังไม่มี LLM API Key
- 🔵 **Blue badge**: "🌐 ใช้ key กลาง ของ admin (admin@sj88ai.com) — ใส่ key ส่วนตัวด้านล่างเพื่อ override"
- Global LLM Key card: **hidden** (admin only)

## 🧠 Design Principles

1. **Single source of truth** — `resolve_llm_key()` is the ONLY place to look up LLM key
2. **Transparent fallback** — User doesn't need to know global key exists
3. **Override-friendly** — User can always put their own key
4. **Encrypted at rest** — Both user + global keys use Fernet AES-128
5. **Admin isolation** — Only one global key per system, admin-only endpoints
6. **Audit trail** — `set_by` + `set_at` track who/when

## 🐛 Edge Cases Tested

| Case | Result |
|---|---|
| User has own + global exists | ✅ Uses own key (cascade priority correct) |
| User has no own, global exists | ✅ Uses global key |
| User has no own, no global | ❌ Returns 400 "configure your key or ask admin" |
| User's own key is corrupt (decrypt fail) | ✅ Falls back to global + logs warning |
| Global key is corrupt | ❌ Returns 400 + logs error |
| Non-admin tries to set global | ❌ 403 admin_only |
| Admin sets global twice (overwrite) | ✅ Latest wins, set_at updated |
| Admin clears global | ✅ All users without own key get 400 next time |

## 📊 Stats

- **Lines of code**: ~250 new (services/llm_keys.py + settings.py + llm.py + db.py)
- **New endpoints**: 3 (PUT/DELETE/GET /llm-api-key/global)
- **Modified endpoints**: 5 (/api/settings + 4 LLM endpoints)
- **UI components**: 2 (Global LLM Key card + key-source-badge)
- **Test scenarios**: 6 (admin set, view, user verify, LLM call, cascade, RBAC)
- **All passed**: ✅

## 🔗 Related Files

- `api/services/llm_keys.py` — NEW resolver
- `api/db.py` — migration
- `api/routes/settings.py` — 3 new endpoints
- `api/routes/llm.py` — uses resolver
- `www/index.html` — Global LLM card + source badge
- `www/js/settings.js` — UI handlers
- `www/style.css` (inline) — `.key-source-badge`, `.badge-admin`, `.global-llm-info` styles



## 🎨 v3.1.1: Topnav Credits Badge (Bonus Feature)

After TC-14, user requested: "show credits on every page, in the menu".

### Feature
- Persistent **🎬 2 / 100** badge in topnav
- Visible on **all tabs**: โปรเจกต์, ตั้งค่า, Analytics, Jobs, Live Demo, etc.
- Color-coded: 🟢 green (>30%), 🟡 warning (10-30%), 🔴 danger + pulse (<10%)
- Auto-refresh every 60 seconds
- Click badge to refresh manually
- Title tooltip: username + expiry + click hint

### Implementation
- `index.html` line 68: `<span class="credits-badge" id="topnav-credits-badge">`
- `style.css` lines 667-710: `.credits-badge`, `.warning`, `.danger` + `pulse-credit` animation
- `js/settings.js` line 41: `export async function updateTopnavCredits()` — fetches `/api/settings/veo-jwt/test`, color-codes
- `js/app.js` line 54: `setInterval(updateTopnavCredits, 60000)` — auto-refresh
- `js/app.js` line 25: called on every `showTab()` — refreshes on tab switch

### Screenshots
- `screenshots/credits_in_topnav_projects.png` — Projects tab
- `screenshots/credits_in_topnav_analytics.png` — Analytics tab
- `screenshots/credits_in_topnav_jobs.png` — Jobs tab
- `screenshots/credits_in_topnav_settings.png` — Settings tab
- `screenshots/credits_topnav_v2.png` — Final design (red danger state)
- `screenshots/credits_topnav_all_pages.png` — Full settings with topnav badge

### Commit
`518cf31` — "feat(ui): credits badge in topnav (visible on all pages)"

## 📁 Artifacts

- `screenshots/admin_with_global_llm.png` — Admin view
- `screenshots/user_uses_global_key.png` — User view
- `scripts/test_cascade.sh` — cURL test script (re-runnable)
