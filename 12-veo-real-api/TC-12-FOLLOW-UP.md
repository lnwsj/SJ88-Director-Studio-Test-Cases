# TC-12 FOLLOW-UP: Real genaipro Submit + Completed Video

**Date**: 2026-07-14 14:50 UTC
**Status**: ✅ PASS — full end-to-end video gen works

## 🎯 Critical Discovery

The submit was failing with **400 "Aspect ratio must be VIDEO_ASPECT_RATIO_LANDSCAPE or VIDEO_ASPECT_RATIO_PORTRAIT"** — genaipro V2 expects **enum names**, not ratio strings!

| Field | What we sent (WRONG) | What genaipro wants (RIGHT) |
|---|---|---|
| `aspect_ratio` | `"9:16"` | `"VIDEO_ASPECT_RATIO_PORTRAIT"` |
| `aspect_ratio` | `"16:9"` | `"VIDEO_ASPECT_RATIO_LANDSCAPE"` |
| `number_of_videos` | (missing) | `1` (required) |
| `reference_images` | `images` / `files` / `image` | `reference_images` (only field name that works) |

## 🔧 Fixes Applied (commit `de0aa79`)

1. **`services/veo/client.py`** — added `normalize_aspect_ratio()`:
   ```python
   def normalize_aspect_ratio(aspect: str) -> str:
       if aspect in ("VIDEO_ASPECT_RATIO_LANDSCAPE", "VIDEO_ASPECT_RATIO_PORTRAIT"):
           return aspect
       if aspect == "16:9": return "VIDEO_ASPECT_RATIO_LANDSCAPE"
       if aspect in ("9:16", "1:1"): return "VIDEO_ASPECT_RATIO_PORTRAIT"
       raise VeoBadResponse(...)
   ```

2. **`routes/veo.py`** — extract `external_id` from `histories[0].id` (genaipro wraps response in array for ingredients mode)

3. **`services/veo/__init__.py`** — added missing `resolve_ref_bytes` to public API

## ✅ End-to-End Verified

```
POST /api/veo/submit
  → 200 OK
  → task_id: 3167158181a04e99
  → veo_task_id: 5b8bab22-c8a7-4f38-9be1-d70ccaee140b

GET /api/veo/poll/3167158181a04e99 (after ~80s)
  → 200 OK
  → status: completed
  → video_url: https://files.genaipro.io/video_22b99171-7c6a-43b5-9f24-afea408a8db0_1080p.mp4
  → Content-Length: 18,461,319 bytes (18.4 MB)
  → Content-Type: application/octet-stream (real MP4)
```

## 📁 Artifacts

- `videos/completed_mint_s01_01_1080p.mp4` — actual 18.4MB MP4 file
- Source prompt: 1006-char Veo prompt for S01_01 (Mint walks through school gate, K-drama style)
- Project: โรงเรียนรัก (romance) — 3 refs (mint/phom/peach)
- Mode: `ingredients_to_video` with 3 reference images
- Aspect: 9:16 vertical portrait
- Model: `veo_3_1_r2v_lite_low_priority` (auto-assigned by genaipro)

## 🧠 Lessons Learned

1. **genaipro V2 spec is closed** — no public OpenAPI. Must probe fields one at a time.
2. **Enum names, not values** — aspect_ratio, mode are enum strings.
3. **`histories[]` wrapper** — async submissions return a list, not a single object.
4. **Reference image field name** — only `reference_images` works (not `images`, `files`, `image`).
5. **Low priority queue = slow** — `veo_3_1_r2v_lite_low_priority` takes ~80s for completion.
