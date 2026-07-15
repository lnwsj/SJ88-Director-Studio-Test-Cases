"""
summarize_logs.py — Read all per-TC logs and produce summary
"""
import re
from pathlib import Path

LOG_DIR = Path("/workspace/regression-2026-07-15")
# Pattern 1: "=== RESULT: N/M PASS (XX%) ==="
# Pattern 2: "TC-XX RESULT: N/M PASSED"
# Pattern 3: "Videos: 0 downloaded" etc.

PATTERN_RESULT = re.compile(
    r"(?:=== RESULT: |TC-\d+ RESULT: |===\s*|\U0001F4CA RESULT:\s*|📊 RESULT:\s*)(\d+)/(\d+)(?:\s+PASS\s*\((\d+)%\))?"
)

# Also some have just `=== RESULT: 22/24 PASS (92%) ===`

print("=" * 70)
print("REGRESSION RESULTS (parsed from logs)")
print("=" * 70)

total_passed = 0
total_tests = 0
crashed = []
results = []

for log_path in sorted(LOG_DIR.glob("*.log")):
    if log_path.name in ("regression_runner.py.log", "summarize_logs.py.log"):
        continue
    tc = log_path.stem
    content = log_path.read_text()
    # Look for result patterns
    matches = PATTERN_RESULT.findall(content)
    if matches:
        # Last match is the most recent result
        passed, total, pct = matches[-1]
        passed, total = int(passed), int(total)
        status = "PASS" if passed == total else "PARTIAL"
        results.append((tc, passed, total, status))
        total_passed += passed
        total_tests += total
    else:
        crashed.append(tc)
        results.append((tc, 0, 0, "CRASH"))

for tc, passed, total, status in results:
    if status == "PASS":
        icon = "✅"
    elif status == "PARTIAL":
        icon = "⚠️ "
    else:
        icon = "💥"
    if total > 0:
        print(f"  {icon} {tc:45s} {passed:>3}/{total:<3}  [{status}]")
    else:
        print(f"  {icon} {tc:45s}  --/--  [{status}]")

print(f"\nTotal: {total_passed}/{total_tests} passed across {len(results)} tests")
if crashed:
    print(f"\nCrashed (no RESULT line): {len(crashed)}")
    for c in crashed:
        print(f"  💥 {c}")
