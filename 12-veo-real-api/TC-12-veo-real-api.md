# TC-12: Real Veo API Integration

## Purpose
Verifies the **backend can actually call genaipro API with the stored Veo JWT** and get a 200 OK response with valid user data.

## Why this test exists
Previously the service returned 401 `invalid_token` even when the same token worked when called directly from a shell. This test:
1. **Locks in the real API integration** so we don't regress
2. Verifies `settings` endpoint returns `fingerprint` (sha256:...) so the UI + worker can correlate the key version
3. Verifies the UI Settings page shows the fingerprint

## Design principles
- **ONE** genaipro call per test run (to avoid rate-limit/revocation)
- No direct probe of genaipro from outside the service (everything via our `/api/*`)
- Real Chromium screenshots, not curl
- IP-aware: test runs against `directorstudio.sj88ai.com` (live)

## Phases

### 1. Backend health
- `GET /api/health` → 200 OK

### 2. Login as admin
- `POST /api/auth/login` → 200, role = admin

### 3. Verify Veo JWT is configured
- `GET /api/settings` → `has_veo_jwt: true`, `veo_jwt_decrypt_ok: true`
- `veo_jwt_fingerprint` starts with `sha256:` (15 chars total = 7+8 hex)

### 4. Test JWT via real genaipro API
- `GET /api/settings/veo-jwt/test` → `ok: true`, `username: sj888`
- `balance` is a number ≥ 0
- `total_remaining` is a number ≥ 0 (from /v2/veo/credits)

### 5. UI verification
- Open `/auth.html` → login as admin
- Open `/settings.html` → verify Test button works
- Verify `sha256:...` visible somewhere in UI

## Expected result
**15/15 PASS** when token is valid and IP not banned by Cloudflare.

## Failure modes
- ❌ `error: HTTP 401` → JWT invalid/expired/revoked (generate new at genaipro.io)
- ❌ `error: HTTP 403` + `cf-ray` → Cloudflare IP ban
- ❌ `error: no_key` → JWT not configured in Settings
- ❌ `error: decrypt_failed` → FERNET key rotated, re-save JWT

## Files
- `test_veo_real.py` — main test (10KB, 250 LOC)
- `runs/<timestamp>/report.html` — per-run report
- `runs/<timestamp>/*.png` — UI screenshots

## Run
```bash
cd /workspace/director-studio-test-cases/12-veo-real-api
/usr/bin/python3 test_veo_real.py
```

## Notes
- Uses `/root/.cache/ms-playwright/chromium-1223/chrome-linux/chrome`
- 1 real genaipro call per run (don't run repeatedly to avoid token revocation)
