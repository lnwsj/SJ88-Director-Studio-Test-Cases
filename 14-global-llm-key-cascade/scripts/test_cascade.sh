#!/bin/bash
# TC-14 test script: Global LLM Key Cascade
# Tests admin setting global key + new user using it
# Re-runnable, idempotent

set -e
API="https://directorstudio.sj88ai.com/api"

echo "============================================"
echo "TC-14: Global LLM Key Cascade"
echo "============================================"

# 1. Admin login
echo ""
echo "[1] Admin login..."
ADMIN_TOKEN=$(curl -sS -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@sj88ai.com","password":"admin1234"}' | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")
echo "  ✓ Admin token obtained"

# 2. Check current state
echo ""
echo "[2] Check current /api/settings (admin)..."
curl -sS "$API/settings" -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -m json.tool

# 3. Set admin's real LLM key as global
echo ""
echo "[3] Setting admin's real LLM key as global..."
ADMIN_LLM_KEY=$(sqlite3 /opt/director-studio/data/studio.db "SELECT llm_api_key_enc FROM settings WHERE user_id = '67c0331d31654504'" 2>/dev/null || echo "")

if [ -z "$ADMIN_LLM_KEY" ]; then
    # Get key from admin's settings via Python
    echo "  (Getting admin's key from DB...)"
    ADMIN_LLM_KEY=$(python3 -c "
import sys
sys.path.insert(0, '/opt/director-studio/api')
from crypto import decrypt
import sqlite3
conn = sqlite3.connect('/opt/director-studio/data/studio.db')
row = conn.execute('SELECT llm_api_key_enc FROM settings WHERE user_id = ?', ('67c0331d31654504',)).fetchone()
if row and row[0]:
    print(decrypt(row[0]))
" 2>/dev/null)
fi

# If still empty, use a placeholder
if [ -z "$ADMIN_LLM_KEY" ]; then
    ADMIN_LLM_KEY="sk-cp-PLACEHOLDER-KEY-FOR-TEST"
    echo "  ⚠ Using placeholder key (admin key not found in DB)"
fi

curl -sS -X PUT "$API/settings/llm-api-key/global" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"llm_api_key\": \"$ADMIN_LLM_KEY\"}"
echo ""

# 4. Check global status
echo ""
echo "[4] Check global key status..."
curl -sS "$API/settings/llm-api-key/global" -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -m json.tool

# 5. Create new user
echo ""
echo "[5] Create new test user..."
TS=$(date +%s)
NEW_EMAIL="tc14_test_${TS}@x.com"
SIGNUP_RESP=$(curl -sS -X POST "$API/auth/signup" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$NEW_EMAIL\",\"password\":\"test1234\",\"display_name\":\"TC14 Test\"}")
USER_TOKEN=$(echo "$SIGNUP_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")
echo "  ✓ New user: $NEW_EMAIL"

# 6. Check new user /api/settings
echo ""
echo "[6] Check new user /api/settings (expect llm_key_source=global)..."
curl -sS "$API/settings" -H "Authorization: Bearer $USER_TOKEN" | python3 -m json.tool

# 7. Test LLM call as new user
echo ""
echo "[7] New user generates script (using global key)..."
LLM_RESP=$(curl -sS -X POST "$API/llm/generate-script" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A boy meets a girl in coffee shop","episode_number":1,"num_scenes":2,"style":"romance","previous_episodes":[]}')
SCENE_COUNT=$(echo "$LLM_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('script',{}).get('scenes',[])))" 2>/dev/null)
FIRST_TITLE=$(echo "$LLM_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('script',{}).get('scenes',[{}])[0].get('title','?'))" 2>/dev/null)

if [ "$SCENE_COUNT" -gt 0 ]; then
    echo "  ✅ SUCCESS: Got $SCENE_COUNT scenes"
    echo "  First scene: $FIRST_TITLE"
else
    echo "  ❌ FAILED: $LLM_RESP" | head -c 300
fi

# 8. Test 403 for non-admin
echo ""
echo "[8] Test 403 for non-admin trying to set global..."
RESULT=$(curl -sS -o /dev/null -w "%{http_code}" -X PUT "$API/settings/llm-api-key/global" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"llm_api_key":"test"}')
if [ "$RESULT" = "403" ]; then
    echo "  ✅ 403 Forbidden (correct RBAC)"
else
    echo "  ⚠ Got $RESULT (expected 403)"
fi

echo ""
echo "============================================"
echo "TC-14 complete"
echo "============================================"
