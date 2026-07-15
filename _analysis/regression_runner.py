"""
regression_runner.py — Run all TC PW tests sequentially + summarize
"""
import os
import subprocess
import time
import re
from pathlib import Path

TC_DIR = Path("/workspace/director-studio-test-cases")
SCREENSHOTS_DIR = Path("/workspace/regression-2026-07-15")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# All PW test scripts (in scripts/ subdir OR direct in TC dir)
PW_TESTS = sorted(set(
    list(TC_DIR.glob("[0-9][0-9]-*/scripts/test_*.py")) +
    list(TC_DIR.glob("[0-9][0-9]-*/test_*.py"))
))

# Exclude demo scripts (not real tests)
PW_TESTS = [t for t in PW_TESTS if "demo" not in t.name]

print(f"Found {len(PW_TESTS)} PW test scripts to run")
print("=" * 70)

results = {}
for i, test_path in enumerate(PW_TESTS, 1):
    # tc_name = TC directory (e.g. "01-video-generation")
    tc_name = test_path.parent.parent.name
    # Use full path for log name to avoid collisions
    log_name = f"{tc_name}_{test_path.stem}"
    print(f"\n[{i}/{len(PW_TESTS)}] Running {tc_name}/{test_path.name}")
    print("-" * 70)
    t0 = time.time()
    try:
        # Run with 180s timeout
        proc = subprocess.run(
            ["python3", str(test_path)],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(test_path.parent),
        )
        dt = time.time() - t0
        # Parse "TC-XX RESULT: passed/total PASSED" from output
        match = re.search(r"TC-\d+ RESULT: (\d+)/(\d+) PASSED", proc.stdout)
        if match:
            passed = int(match.group(1))
            total = int(match.group(2))
            results[log_name] = (passed, total, "PASS" if passed == total else "FAIL", dt)
            print(f"  → {passed}/{total} PASSED ({dt:.1f}s)")
        else:
            # No RESULT line = crashed
            results[log_name] = (0, 0, "CRASH", dt)
            print(f"  → CRASHED ({dt:.1f}s)")
            print(f"  Last 5 lines of output:")
            for line in proc.stdout.strip().split("\n")[-5:]:
                print(f"    {line}")
        # Save output (append with run timestamp)
        log_file = SCREENSHOTS_DIR / f"{log_name}.log"
        with open(log_file, "a") as f:
            f.write(f"\n\n=== Run at {time.strftime('%Y-%m-%d %H:%M:%S')} ({dt:.1f}s) ===\n")
            f.write(f"=== STDOUT ===\n{proc.stdout}\n\n=== STDERR ===\n{proc.stderr}\n")
    except subprocess.TimeoutExpired:
        dt = time.time() - t0
        results[log_name] = (0, 0, "TIMEOUT", dt)
        print(f"  → TIMEOUT after {dt:.1f}s")

# Final summary
print("\n" + "=" * 70)
print("REGRESSION SUITE SUMMARY")
print("=" * 70)
total_passed = 0
total_tests = 0
fails = []
for tc, (passed, total, status, dt) in results.items():
    if status == "PASS":
        icon = "✅"
    elif status == "FAIL":
        icon = "⚠️"
    elif status == "CRASH":
        icon = "💥"
    else:  # TIMEOUT
        icon = "⏱️"
    print(f"  {icon} {tc:55s} {passed:>3}/{total:<3} ({dt:.1f}s) [{status}]")
    total_passed += passed
    total_tests += total
    if status != "PASS":
        fails.append((tc, status, passed, total))

print(f"\nTotal: {total_passed}/{total_tests} passed")
print(f"Failures: {len(fails)}")
if fails:
    for tc, status, p, t in fails:
        print(f"  ❌ {tc}: {p}/{t} ({status})")
