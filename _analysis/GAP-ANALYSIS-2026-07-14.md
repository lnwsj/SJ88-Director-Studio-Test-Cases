# 🔍 TC Gap Analysis · 2026-07-14

> Comprehensive audit of all 13 test cases vs 49 API endpoints + 6 features
> Total coverage: **76%** (37/49 endpoints + 3/9 features)

## 📊 Summary

| Metric | Value |
|---|---|
| Total TCs | 13 (TC-01 to TC-14, with gaps) |
| Total API endpoints | 49 |
| Endpoints tested | 37 (76%) |
| Endpoints UNTESTED | 12 (24%) |
| Features with NO TC | 6 |
| Stale empty folders | 6 |

## 🟢 What's Covered (37/49)

### TC-01 / TC-12: Video Generation
- ✅ POST /api/veo/submit
- ✅ GET /api/veo/poll/{task_id}
- ✅ POST /api/veo/submit-with-refs (legacy)
- ✅ MP4 download + validation (ftyp magic bytes)

### TC-02: Script Generation
- ✅ POST /api/llm/generate-script (20 director fields)

### TC-03: Veo Single-Scene
- ✅ POST /api/llm/generate-veo
- ✅ POST /api/llm/generate-veo-single (1500 char cap)

### TC-04: Refs Management
- ✅ GET /api/projects/{pid}/refs
- ✅ PUT /api/projects/{pid}/refs
- ✅ POST /api/projects/{pid}/refs
- ✅ DELETE /api/projects/{pid}/refs/{name}

### TC-05: Projects CRUD
- ✅ POST /api/projects
- ✅ GET /api/projects
- ✅ GET /api/projects/{pid}
- ✅ PUT /api/projects/{pid}
- ✅ DELETE /api/projects/{pid}

### TC-07: Jobs Async + WebSocket
- ✅ POST /api/jobs
- ✅ GET /api/jobs
- ✅ GET /api/jobs/{job_id}
- ✅ DELETE /api/jobs/{job_id}
- ✅ WS /api/ws

### TC-09 / TC-10: Auth
- ✅ POST /api/auth/signup
- ✅ POST /api/auth/login
- ✅ GET /api/auth/me

### TC-11: Real UI Walkthrough
- ✅ All main pages (UI screenshots)
- ⚠️ Mentions /admin but doesn't test endpoints

### TC-13: Logging (no TC-13.md but has test_logging.py)
- ✅ JSON structured logs
- ✅ request_id correlation
- ✅ Authorization header redaction
- ✅ Traceback in log not in response

### TC-14: Global LLM Key Cascade
- ✅ PUT/DELETE/GET /api/settings/llm-api-key/global
- ✅ Cascade logic (user → global)
- ✅ Admin RBAC

### Settings
- ✅ GET /api/settings
- ✅ PUT/DELETE /api/settings/veo-jwt
- ✅ GET /api/settings/veo-jwt/test
- ✅ PUT/DELETE /api/settings/llm-api-key

## ❌ What's MISSING (12 endpoints + 6 features)

### A. Untested API Endpoints (12)

| # | Endpoint | Risk | Notes |
|---|---|---|---|
| 1 | DELETE /api/projects/{pid}/episodes/{ep_idx} | LOW | Single episode delete |
| 2 | POST /api/llm/generate-veo-all | HIGH | Generate All button — UI exists, no test |
| 3 | GET /api/llm/cache/stats | MED | LLM cache replay feature |
| 4 | POST /api/llm/cache/clear | MED | LLM cache management |
| 5 | GET /api/admin/users | MED | Admin user list |
| 6 | GET /api/admin/users/{user_id} | MED | Admin user detail |
| 7 | GET /api/admin/stats | MED | Admin system stats |
| 8 | DELETE /api/admin/users/{user_id} | HIGH | Admin delete user (destructive) |
| 9 | POST /api/images/generate | HIGH | Stage 0 image generation |
| 10 | GET /api/images/poll/{task_id} | HIGH | Stage 0 image poll |
| 11 | GET /share/{pid} | MED | Public share page (no auth) |
| 12 | GET /api/health | LOW | Trivial |

### B. Features with NO TC (6)

| Feature | UI? | Backend? | TC? |
|---|---|---|---|
| **Stage 0: Image Generation** (GTMage-2) | ✅ | ✅ | ❌ |
| **Public Share page** | ✅ | ✅ | ❌ |
| **Admin Panel** (user management) | ✅ | ✅ | ❌ |
| **Analytics Dashboard** (per-user stats) | ✅ | ✅ | ❌ |
| **LLM Cache Replay** (17x speedup) | ✅ badge | ✅ | ❌ |
| **Export .md / .json** | ✅ buttons | ✅ | ❌ |

### C. Stale Folders (6)

| Folder | Status | Should |
|---|---|---|
| 02-script-fields/ | empty (no .md) | DELETE |
| 02-script-generation/ | empty (no .md) | DELETE |
| 03-veo-prompt-generation/ | empty (no .md) | DELETE |
| 06-auth-tenant/ | empty | MERGE into TC-09/TC-10 |
| 08-share-analytics/ | empty | BECOME TC-16 (share) |
| 13-logging/ | has test_logging.py, NO TC-13.md | ADD TC-13.md |

## 🎯 Recommended New TCs (Priority)

### 🔴 HIGH Priority (User-facing, complex)

**TC-15: Stage 0 Image Generation** (~2 hours)
- POST /api/images/generate with all 5 aspect ratios (1:1, 16:9, 9:16, 3:2, 2:3)
- 4 image variations (n=1, 2, 3, 4)
- Sync vs async mode
- Image URL persistence in project
- Refs integration (use [ref1] in prompt)
- Test filters (blood, weapons rejected)

**TC-16: Public Share Page** (~1.5 hours)
- GET /share/{pid} — no auth required
- Project data displayed (read-only)
- Episode list + script preview
- Veo prompts visible
- Try accessing invalid project → 404
- Try non-shared project → 404 or hidden

### 🟡 MEDIUM Priority (Admin/Ops)

**TC-17: Admin Panel** (~2 hours)
- GET /api/admin/users — list all users
- GET /api/admin/users/{user_id} — detail (verify secrets hidden)
- GET /api/admin/stats — system stats
- DELETE /api/admin/users/{user_id} — destructive (test cannot delete self)
- RBAC: non-admin → 403
- UI: admin tab visible only to admin

**TC-18: Analytics Dashboard** (~1.5 hours)
- GET /api/analytics/me — 7-day activity
- Per-user stats (projects, episodes, jobs, credits used)
- Job status distribution
- Veo success rate
- UI: analytics tab

**TC-19: LLM Cache Replay** (~1.5 hours)
- First call → no cache
- Second call with same scene → cache hit (17x speedup)
- GET /api/llm/cache/stats → returns counts
- POST /api/llm/cache/clear → resets
- UI: "cached" badge visible

### 🟢 LOW Priority (Cleanup)

**TC-20: Export .md / .json** (~1 hour)
- Per-episode markdown export
- JSON export with full structure
- Refs included in output
- Special characters (Thai) preserved

**TC-21: Episode Delete** (~30 min)
- DELETE /api/projects/{pid}/episodes/{ep_idx}
- Verify project still exists, just one EP removed
- Bad index → 400/404

**TC-22: Generate All Veo Flow** (~1.5 hours)
- POST /api/llm/generate-veo-all
- Sequential scene generation
- Cache integration
- Progress events
- UI: "Generate All" button flow

**TC-23: Admin Delete User** (~30 min)
- DELETE /api/admin/users/{id}
- Cannot delete self → 400
- Deleted user cannot login
- Deleted user's projects still exist (or cascade?)

**TC-24: Health Check** (~15 min)
- GET /api/health
- Returns JSON with version + worker status
- No auth required

## 🔄 Tidyup Tasks

- [ ] Remove 5 stale empty folders (keep 13-logging for test_logging.py)
- [ ] Write TC-13.md (logging) — content already in test_logging.py
- [ ] Update INDEX.md to include TC-11 to TC-14
- [ ] Rename 08-share-analytics/ to TC-16 base
- [ ] Add TC count to README

## 📈 Impact

- **Current**: 13 TCs, 96% pass rate, 37 endpoints tested
- **After 10 new TCs**: 23 TCs, still 96%+ target, 49/49 endpoints
- **Total test work**: ~12 hours
- **Coverage increase**: 76% → 100%

## 🎓 Recommendations for User

1. **Quick wins** (1-2 hours): TC-21 (Episode Delete) + TC-24 (Health) + Tidyup
2. **High value** (4 hours): TC-15 (Stage 0) + TC-16 (Share)
3. **Full coverage** (12 hours): all 10 new TCs
4. **Document what we have** (1 hour): update INDEX.md, add TC-13.md
