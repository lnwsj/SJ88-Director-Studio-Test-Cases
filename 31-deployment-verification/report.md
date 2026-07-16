# TC-31: Post-Deployment Verification

**Date**: 2026-07-16 06:47:04
**Deployed version**: 3.4.0 (commit ed50716)
**Total test time**: 66.6s

## Results: 14/15 PASS

- ✅ **Health check**: version=3.4.0
- ✅ **API login**: Got JWT
- ✅ **Find project**: 8 scenes, 8 timeline
- ✅ **v3.4 regenerate-scene API**: elapsed=18.5s, scene keys=28, feedback_applied=True
- ✅ **v3.4 regenerate-scene + Veo**: elapsed=31.8s, veo prompt=1382 chars
- ✅ **UI Login**: URL=https://directorstudio.sj88ai.com/
- ✅ **Project cards visible**: 1 cards
- ✅ **EP cards visible**: 1 eps
- ✅ **Scenes in modal**: 8 scenes (expected ≥8)
- ✅ **🔄 buttons**: 8 buttons for 8 scenes
- ✅ **Regen modal**: Modal appears on click
- ✅ **Modal cancel**: Modal closes on cancel
- ✅ **Veo tab**: 8 veo items
- ⚠️ **Videos in Veo tab**: 0 <video> elements visible
- ✅ **JS errors**: Clean console
