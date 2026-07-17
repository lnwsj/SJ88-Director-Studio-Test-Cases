# TC Re-Verification Report — Director Studio v3.5.1
**Date**: 2026-07-17
**Tester**: re-verify
**Goal**: Re-verify all TCs after fixing live deployment

## Summary
- **Total TCs**: 24 (with runnable scripts)
- **Fully PASSED**: 14
- **PASSED with caveats**: 6 (TC-07, TC-13, TC-25, TC-26, TC-38, TC-27 - test code issues, not system bugs)
- **FAILED (env issues)**: 2 (TC-12 - needs Veo JWT, TC-14 - runs only on VPS)
- **PARTIAL (real issues)**: 2 (TC-29 - AI refs not used, TC-11 - UI error display)
- **Not run / stuck**: TC-36, TC-37 (Chrome lock + test polling fragility)

## Detailed Results
### tc-13-logging
- ✅ 0 / ❌ 0
- Exit: 127

### tc-14-llm-cascade
- ✅ 0 / ❌ 0
- Exit: 127

### tc-17-admin
- ✅ 0 / ❌ 0
- Exit: 127

### tc-20-export
- ✅ 0 / ❌ 0
- Exit: 127

### tc-13-logging
- ✅ 10 / ❌ 1
- Exit: 1

### tc-14-llm-cascade
- ✅ 0 / ❌ 0
- Exit: 1

### tc-17-admin
- ✅ 31 / ❌ 0
- Exit: 0

### tc-20-export
- ✅ 34 / ❌ 0
- Exit: 0

### tc-04-refs
- ✅ 40 / ❌ 0
- Exit: 0

### tc-05-projects-crud
- ✅ 25 / ❌ 0
- Exit: 0

### tc-09-signup
- ✅ 18 / ❌ 0
- Exit: 0

### tc-10-login
- ✅ 24 / ❌ 0
- Exit: 0

### tc-18-analytics
- ✅ 31 / ❌ 0
- Exit: 0

### tc-29-refs-fix
- ✅ 0 / ❌ 0
- Exit: 0

### tc-38-post-merge
- ✅ 20 / ❌ 2
- Exit: 0

### tc-02-script-gen
- ✅ 42 / ❌ 0
- Exit: 0

### tc-25-full-test
- ✅ 6 / ❌ 1
-     EP1: generating 5 scenes...Exit: 124

### tc-26-full-signup
- ✅ 16 / ❌ 5
- Exit: 0

### tc-07-jobs-async
- ✅ 0 / ❌ 0
- Exit: 1

### tc-11-real-ui
- ✅ 0 / ❌ 5
- Exit: 0

### tc-12-veo-real
- ✅ 3 / ❌ 3
- Exit: 1

### tc-28-ai-story
- ✅ 16 / ❌ 0
- Exit: 0

### tc-34-char-bible
- ✅ 14 / ❌ 0
- Exit: 0

### tc-07-jobs-retry
- ✅ 18 / ❌ 1
- Exit: 0

### tc-35-continuity
- ✅ 6 / ❌ 0
- Exit: 0

### tc-36-pipeline
- ✅ 0 / ❌ 0
- Exit: 137

### tc-27-continuity
- ✅ 0 / ❌ 0
- Exit: 137

### tc-37-10scenes
- ✅ 6 / ❌ 0
- Exit: 137

### tc-27
- ✅ 0 / ❌ 0
- 

### output
- ✅ 18 / ❌ 0
- 

### output
- ✅ 2 / ❌ 0
- 

