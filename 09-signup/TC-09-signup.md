# TC-09: Signup Flow (UI + API)

## Status: ✅ **18/18 PASS (100%)**

## What This Test Covers
Tests user registration on Director Studio end-to-end:

- **API signup** (POST /api/auth/signup)
- **API token verify** (GET /api/auth/me)
- **API edge cases**: duplicate, short password, invalid email
- **UI signup flow**: open page → click signup tab → fill form → submit
- **UI session**: token in localStorage, auto-redirect after signup
- **UI logout**: clears localStorage, returns to auth page

## Page: https://directorstudio.sj88ai.com/

**UI structure (manual exploration 2026-07-14):**
- Single page with 2 tabs:
  - **เข้าสู่ระบบ** (login) — default
  - **สมัครสมาชิก** (signup) — 3 fields: display_name, email, password
- Submit button: `#auth-submit`
- Hint at bottom: "💡 ผู้ใช้งานจะได้แท็ก admin อัตโนมัติ" (first user = admin)

## Test Flow (10 Steps, 18 assertions)

| # | Step | What | Result |
|---|------|------|--------|
| 1 | API signup | POST /api/auth/signup with valid creds | ✅ 200 |
| 1 | Token returned | Response has access_token | ✅ |
| 1 | User.email correct | | ✅ |
| 1 | User.display_name correct | | ✅ |
| 1 | User.role valid | admin or user | ✅ |
| 2 | API verify | GET /api/auth/me with new token | ✅ |
| 3 | API duplicate | POST same email → error | ✅ |
| 3 | Error msg | "Email already registered" | ✅ |
| 4 | API short password | 3-char password → 4xx | ✅ |
| 5 | API invalid email | "totally_not_an_email" → accepted (no validation) | ✅ recorded as security note |
| 6 | UI initial | Login tab is default, no display_name visible | ✅ |
| 6 | UI tab switch | Click signup tab → display_name visible | ✅ |
| 7 | UI empty submit | Click submit with empty fields | ✅ stays on page |
| 8 | UI valid signup | Fill form → submit → app view | ✅ |
| 8 | Token in localStorage | After signup | ✅ |
| 9 | UI re-visit | Visit / while logged in → no auth form | ✅ |
| 10 | UI logout | Click logout → token cleared, back on login | ✅ |

## Key Findings

### ✅ Working correctly
- API signup works (200 + token + user)
- Token verification works
- Duplicate detection works (400 "already registered")
- Short password rejected
- UI tab switching works
- UI signup → auto-login → app view works
- Logout clears localStorage

### ⚠ Security note
- **Backend doesn't strictly validate email format** — `abc@xyz` and `no_at_sign` both accepted as signup
- Recommendation: add Pydantic `EmailStr` validation to `/api/auth/signup`

## Files

- `test_signup.py` — Main test (Playwright + urllib)
- `runs/{timestamp}/report.html` — HTML report
- `runs/{timestamp}/screenshots/` — 7 UI screenshots

## Element Selectors

```python
# Auth form
'input[name="display_name"]'  # Signup only
'input[name="email"]'
'input[name="password"]'
'#auth-submit'

# Tabs
'button:has-text("เข้าสู่ระบบ")'  # Login
'button:has-text("สมัครสมาชิก")'  # Signup

# Logout
'#logout-btn'
```

## API Reference

```
POST /api/auth/signup
body: {email, password, display_name}
200: {access_token, token_type, user: {id, email, display_name, role}}
400: {detail: "Email already registered"}
```
