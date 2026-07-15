# TC-10: Login Flow (UI + API)

## Status: ✅ **24/24 PASS (100%)**

## What This Test Covers
Tests user authentication on Director Studio end-to-end:

- **API login** (POST /api/auth/login)
- **API token verify** (GET /api/auth/me)
- **API security**: wrong password, wrong email, empty body, bad token, no token
- **UI login flow**: open page → fill form → submit → app view
- **UI session**: token in localStorage, persists across refresh
- **UI logout**: clears localStorage, returns to login
- **UI tab switching**: login ↔ signup tabs
- **Multi-user login**: admin + new test user

## Page: https://directorstudio.sj88ai.com/

**UI structure:**
- Login tab (default): 2 inputs (email, password) + "เข้าสู่ระบบ" button
- Signup tab: 3 inputs (display_name, email, password) + "สมัคร" button

## Test Flow (15 Steps, 24 assertions)

### API (Steps 0-7)
| # | Step | What | Result |
|---|------|------|--------|
| 0 | Create test user | Signup API for new test user | ✅ |
| 1 | Login admin | POST /api/auth/login admin | ✅ |
| 1 | Token returned | | ✅ |
| 1 | User.email correct | | ✅ |
| 1 | User.role = admin | | ✅ |
| 2 | Verify token | GET /api/auth/me | ✅ |
| 2 | Email matches | | ✅ |
| 3 | Wrong password | 401 | ✅ |
| 4 | Wrong email | 401 | ✅ |
| 5 | Empty body | 4xx | ✅ |
| 6 | Bad token | GET /api/auth/me with garbage token → 401 | ✅ |
| 7 | No token | GET /api/auth/me without auth → 401 | ✅ |

### UI (Steps 8-15)
| # | Step | What | Result |
|---|------|------|--------|
| 8 | Login form visible | email + password inputs visible | ✅ |
| 9 | Empty submit | Click submit empty → stays on login | ✅ |
| 10 | Wrong password | Stay on login + error message | ✅ |
| 11 | Valid login (admin) | App view loaded, token in localStorage | ✅ |
| 11 | User chip | Shows "admin" | ✅ |
| 12 | Session persists | Refresh → still logged in | ✅ |
| 13 | Logout | Token cleared, back on login | ✅ |
| 14 | Login as new user | Works (multi-user) | ✅ |
| 15 | Tab switch | Login → Signup tab works | ✅ |

## Key Findings

### ✅ Working correctly
- API login works for both admin + new user
- Token in localStorage persists across refresh
- Logout properly clears token
- Tab switching works
- Wrong credentials show error
- All security checks pass (no token / bad token → 401)

## Element Selectors

```python
# Auth form
'input[name="email"]'
'input[name="password"]'
'#auth-submit'

# Tabs
'button:has-text("เข้าสู่ระบบ")'  # Login
'button:has-text("สมัครสมาชิก")'  # Signup

# Logout (in app view)
'#logout-btn'

# User info
'#user-chip'
```

## API Reference

```
POST /api/auth/login
body: {email, password}
200: {access_token, token_type, user: {id, email, display_name, role}}
401: {detail: "Invalid email or password"}

GET /api/auth/me
Headers: Authorization: Bearer <token>
200: {id, email, display_name, role}
401: invalid/missing token
```

## Files

- `test_login.py` — Main test (Playwright + urllib)
- `runs/{timestamp}/report.html` — HTML report
- `runs/{timestamp}/screenshots/` — 8 UI screenshots
