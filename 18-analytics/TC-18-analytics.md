# TC-18 — Analytics Dashboard

**Test Date**: 2026-07-15
**Result**: ✅ **31/31 PASS** (100%)
**Component**: Director Studio v2.5+ — Analytics (`/api/analytics/*`)
**Live URL**: https://directorstudio.sj88ai.com/

---

## What it tests

Director Studio's personal analytics dashboard: project counts, episode counts, job stats, Veo success rate, 7-day activity chart, credits estimation, and per-user data isolation.

| Area | Coverage |
|------|----------|
| Backend endpoint | `GET /api/analytics/me` (auth required) |
| Project counts | total + episodes (from data.episodes) |
| Job stats | total + by_type + by_status |
| Veo stats | total + success + success_rate + by_status |
| Credits | estimated (Veo=1, LLM=0.1) |
| 7-day chart | daily job counts for last 7 days |
| Top project | most recently updated |
| Per-user isolation | User A's data never leaks to User B |
| UI | Analytics tab renders, 8 quota items, 7 chart bars, populated vs empty |

## Test scenarios — detailed

### T1. Setup
- Create 3 users: NEW (empty), POP (4 projects + 2 episodes + 1 job), ISO (1 project)

### T2. API structure (populated user)
- `GET /api/analytics/me` → 200 with full body
- **Verifies**: projects, jobs, veo_tasks, credits, last_7_days (7 items)

### T3. API auth required
- No token → **401 Unauthorized**

### T4. Per-user isolation (API)
- POP has 4+ projects, ISO has 1 project
- ISO never sees POP's data

### T5. 7-day chart structure
- Returns exactly 7 days
- Labels are weekday names (Wed, Thu, Fri, Sat, Sun, Mon, Tue)
- All counts are non-negative integers
- Pop user's 7-day total includes the job we created (≥1)

### T6. UI - empty state
- New user (0 projects) opens Analytics tab
- 8 quota items rendered (2 rows × 4 items: Projects/Episodes/LLM Jobs/Veo Videos + Credits/Success Rate/Job Statuses/Last 7 days)
- No "Top project" line (no projects exist)
- Screenshot: `01-empty-state.png`

### T7. UI - populated state
- POP user opens Analytics tab
- **Verifies**:
  - 7 chart bars (one per day)
  - "Top project" line visible
  - Quota values include real numbers: `['4', '2', '1', '0', '0.1', '0%', '⏳1', '1 jobs']`
  - Screenshots: `02-populated.png` + `03-chart-detail.png`

### T8. UI - per-user isolation (visible)
- ISO user (1 project) opens Analytics tab
- Quota values: `['1', '0', '0', '0', '0', '0%', '—', '0 jobs']`
- Does NOT see "4" (pop user's data)
- Screenshot: `04-isolation.png`

### T9. Veo success rate formula
- `success_rate = round(success / total * 100, 1)` if total > 0 else 0
- Verified: 0/0 → 0%

### T10. Credits estimation
- Veo task = 1 credit, LLM job = 0.1 credit
- 1 LLM job → `llm_credits = 0.1`
- `total = veo_credits + llm_credits`

## Key files (existing — already implemented)

| File | Purpose |
|------|---------|
| `backend/routes/analytics.py` | `GET /api/analytics/me` with full stats |
| `backend/tests/test_analytics.py` | 6 pytest tests (auth, structure, counts, isolation, credits) |
| `frontend/js/analytics.js` | Chart rendering + 8 quota items + top project |
| `frontend/index.html` | `<a data-tab="analytics" id="nav-analytics">` + `<div id="analytics-content">` |

## What TC-18 added (vs existing pytest)

| Aspect | pytest | TC-18 PW |
|--------|--------|----------|
| API structure | ✅ 6 tests | ✅ T2-T5 (structure + isolation + 7-day) |
| Auth | ✅ 401 | ✅ T3 |
| UI render | ❌ | ✅ T6-T8 |
| Empty state | ❌ | ✅ T6 |
| Populated state | ❌ | ✅ T7 |
| Visual chart | ❌ | ✅ T7 (7 bars + screenshots) |
| Per-user UI | ❌ | ✅ T8 |
| Credits formula | ✅ basic | ✅ T10 (with math verification) |
| Veo rate formula | ❌ | ✅ T9 |

## How to run

```bash
cd /workspace/director-studio-test-cases/18-analytics/scripts
python3 test_tc18_analytics.py
```

**Output**: 31/31 PASSED, 4 screenshots in `screenshots/`

## Screenshots

| # | File | What it shows |
|---|------|---------------|
| 1 | `01-empty-state.png` | New user with 0 projects, 0 jobs |
| 2 | `02-populated.png` | 4 projects, 2 episodes, 1 job, top project shown |
| 3 | `03-chart-detail.png` | 7-day chart bars (scrolled into view) |
| 4 | `04-isolation.png` | Iso user sees only own data (1 project) |

## Key findings (RCA)

1. **Backend + frontend ALREADY implemented** (v2.5 commit `e3ba9a9` "B5 — Analytics dashboard with chart")
2. **API returns rich data**: projects.episodes, jobs.by_type, veo_tasks.success_rate, credits.estimated_used, last_7_days
3. **8 quota items** in 2 rows (not 7 as I initially guessed — bug in my assertion, fixed)
4. **Chart bars use CSS height** = `(count / max) * 80px` — no SVG/canvas, just flexbox + divs
5. **Veo success rate gracefully handles 0** (no division by zero)
6. **Per-user isolation** is enforced at SQL level (WHERE user_id = ?) — no manual filtering

## Coverage contribution

| Metric | Before | After |
|--------|--------|-------|
| Total TCs | 15 (TC-17) | **16 (TC-18 added)** |
| Pass rate | 97% (161/166) | **98% (192/197)** |
| Analytics endpoints | 100% (1/1) | **100% (1/1)** + UI verified |

## Status

✅ **DEPLOYED & TESTED** — All 31 scenarios pass against live site.
📊 Analytics dashboard works as designed end-to-end.
