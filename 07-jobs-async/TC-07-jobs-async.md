# TC-07: Jobs Async (UI + API + WebSocket)

## Status: ✅ **28/28 PASS (100%)**

## What This Test Covers
Validates the **async job system** end-to-end:
- REST API: submit, list, get, cancel
- WebSocket: real-time progress events (race-free: connect BEFORE submit)
- Cross-tenant: no-token returns 401
- Edge cases: 404 on missing, 400 on invalid type, 400 on cancel-completed
- UI: Jobs tab renders correctly

## Test Flow (13 Steps)

| # | Step | What | Type |
|---|------|------|------|
| 1 | UI Login | Auth as admin via form | UI |
| 2 | Auth required | GET/POST /api/jobs without token → 401 | API |
| 3 | List jobs | GET /api/jobs returns array | API |
| 4 | Submit job | POST /api/jobs (script_gen) returns job_id | API |
| 5 | Poll status | Job transitions past `queued` | API |
| 6 | WebSocket flow | Connect WS → submit job → receive update events | **WS** |
| 7 | Final status | Job reaches `completed` + has result | API |
| 8 | Cancel mid-flight | Submit + DELETE while running → status=cancelled | API |
| 9 | 404 on missing | GET /api/jobs/nonexistent → 404 | API |
| 10 | Cannot cancel completed | DELETE on terminal job → 400 | API |
| 11 | UI Jobs tab | Click Jobs nav → see counters | UI |
| 12 | Invalid job type | POST {type: "fake_type"} → 400 | API |
| 13 | Final state | Test jobs in final list | API |

## Results

### ✅ 28/28 PASS (100%)

| Step | What | Status |
|------|------|--------|
| 1 | UI Login | ✅ PASS |
| 2 | GET no-token → 401 | ✅ PASS |
| 2 | POST no-token → 401 | ✅ PASS |
| 3 | GET returns ok | ✅ PASS |
| 3 | Has 'jobs' array | ✅ PASS |
| 4 | POST returns ok | ✅ PASS |
| 4 | job_id returned | ✅ PASS |
| 4 | Initial status = queued | ✅ PASS |
| 5 | Job transitioned past queued | ✅ PASS |
| 6 | Submit job for WS test | ✅ PASS |
| 6 | WS received update event(s) | ✅ PASS |
| 6 | Update event has job_id | ✅ PASS |
| 6 | Update event has status | ✅ PASS |
| 6 | Update event has progress | ✅ PASS |
| 6 | Last WS update = completed | ✅ PASS |
| 7 | Final status = completed | ✅ PASS |
| 7 | Progress = 100 | ✅ PASS |
| 7 | Result has script | ✅ PASS |
| 8 | Submit job for cancel | ✅ PASS |
| 8 | DELETE returns ok | ✅ PASS |
| 8 | Status = cancelled | ✅ PASS |
| 8 | Final status is terminal | ✅ PASS |
| 9 | 404 on missing | ✅ PASS |
| 10 | Cancel terminal → 400 | ✅ PASS |
| 11 | Jobs tab loaded | ✅ PASS |
| 11 | Jobs tab shows counters | ✅ PASS |
| 12 | Invalid type → 400 | ✅ PASS |
| 13 | Both test jobs in final list | ✅ PASS |

## WebSocket Test Details

### Race-free approach
```python
async with websockets.connect(f"wss://...?token={TOKEN}") as ws:
    # Wait for snapshot
    snapshot = await ws.recv()
    # NOW submit (so WS is already watching)
    submit = api_post("/api/jobs", body, token)
    # Listen for updates
    for msg in ws:
        if msg['job_id'] == submit['job_id']:
            events.append(msg)
            if msg['status'] in ('completed', 'failed', 'cancelled'):
                break
```

### WS event structure
```json
{
  "type": "update",
  "job_id": "61a340286e174406",
  "status": "running",
  "progress": 25,
  "message": "Calling LLM (~30s) with 3 ref(s)...",
  "result": null,
  "error": null,
  "updated_at": 1783978654.123
}
```

### Why race-free matters
The WS server **only emits updates on state change**. If you submit a job and *then* connect, the job may already be `running` or even `completed` by the time you connect, and you'd miss the update event. Solution: connect WS first, then submit.

## Job Types Tested

| Type | Handler | Use Case |
|------|---------|----------|
| `script_gen` | LLM JSON gen | Stage 1 (idea → script) |
| `veo_gen` | LLM YAML gen | Stage 2 (script → Veo prompts) |
| `video_gen` | Veo API | Stage 3 (Veo → video) |
| `image_gen` | genaipro | Refs / storyboard |

For test speed, we use `script_gen` (~10s per job).

## Security Verification

- ✅ **No-token GET** → 401
- ✅ **No-token POST** → 401
- ✅ **Invalid job type** → 400 (not 500)
- ✅ **404 on missing job** → 404 (not 500)
- ✅ **Cannot cancel completed** → 400 (idempotency guard)

## Files

- `test_jobs_async.py` — Playwright + websockets async test
- `runs/{timestamp}/report.html` — Full HTML report with WS events
- `runs/{timestamp}/screenshots/` — UI screenshots (01-11)

## Screenshots Captured

| File | What |
|------|------|
| `01_after_login.png` | After UI login |
| `11_jobs_tab.png` | Jobs tab with Active/Done/Failed counters |
