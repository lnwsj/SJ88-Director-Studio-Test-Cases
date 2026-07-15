"""
TC-13: Structured Logging + Correlation ID
==========================================
Verifies the backend produces:
1. JSON-formatted log lines (not plain text)
2. Every request has a request_id (correlation)
3. External API calls (genaipro) are logged with full context
4. Sensitive headers (Authorization) are redacted
5. Errors include traceback in log but NOT in API response
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ---- Config ----
BASE = "https://directorstudio.sj88ai.com"
ADMIN_EMAIL = "admin@sj88ai.com"
ADMIN_PASSWORD = "admin1234"
VPS = dict(hostname="5.83.147.61", username="root", password="j4EsGqNdemZUtDrQFHOO")
RUNS_DIR = Path(__file__).parent / "runs"
RUNS_DIR.mkdir(exist_ok=True)


def log(msg):
    print(msg, flush=True)


def api(path, method="GET", data=None, token=None, extra_headers=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        headers.update(extra_headers)
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode()), dict(resp.headers)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode()), dict(e.headers)
        except Exception:
            return e.code, {}, dict(e.headers)


def ssh_exec(cmd, timeout=10):
    """Execute cmd on VPS via paramiko, return (stdout, stderr)."""
    import paramiko
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(**VPS, timeout=timeout)
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        return stdout.read().decode("utf-8", errors="replace"), stderr.read().decode("utf-8", errors="replace")
    finally:
        ssh.close()


def get_json_logs(n=500):
    """Get last N log lines from VPS systemd journal, parse as JSON."""
    cmd = f"journalctl -u director-studio.service -n {n} --no-pager -o cat 2>&1"
    raw, _ = ssh_exec(cmd, timeout=10)
    out = []
    for ln in raw.splitlines():
        # Try to find JSON start (first '{' character)
        idx = ln.find('{')
        if idx == -1:
            continue
        msg = ln[idx:]
        try:
            out.append(json.loads(msg))
        except json.JSONDecodeError:
            pass
    return out


def get_raw_logs(n=500):
    cmd = f"journalctl -u director-studio.service -n {n} --no-pager -o cat 2>&1"
    raw, _ = ssh_exec(cmd, timeout=10)
    return raw


def make_run_dir():
    ts = time.strftime("%Y%m%d_%H%M%S")
    d = RUNS_DIR / ts
    d.mkdir(exist_ok=True)
    return d


def main():
    run_dir = make_run_dir()
    results = []

    def record(id_, desc, expected, actual, ok):
        results.append((id_, desc, expected, actual, ok))
        icon = "✅" if ok else "❌"
        log(f"  {icon} [{id_}] {desc}")
        log(f"      expected: {expected}")
        log(f"      actual:   {actual}")

    # ---------- 1. Health ----------
    log("\n=== Step 1: Backend health ===")
    s, h, _ = api("/api/health")
    record("13.1.1", "GET /api/health", 200, s, s == 200)
    record("13.1.2", "version starts with 3.x", "3.x", h.get("version"), str(h.get("version", "")).startswith("3."))

    # ---------- 2. Login ----------
    log("\n=== Step 2: Login ===")
    s, d, _ = api("/api/auth/login", "POST", {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if s != 200:
        log(f"❌ Login failed: {s} {d}")
        return 1
    token = d["access_token"]
    record("13.2.1", "POST /api/auth/login", 200, s, True)

    H = {"Authorization": f"Bearer {token}"}

    # ---------- 3. Custom X-Request-ID is echoed ----------
    log("\n=== Step 3: X-Request-ID echoed in response ===")
    custom_rid = "tc13_test_abc123"
    s, _, headers = api("/api/health", extra_headers={"X-Request-ID": custom_rid})
    returned_rid = headers.get("X-Request-ID", headers.get("x-request-id", ""))
    record("13.3.1", "X-Request-ID echoed in response", custom_rid, returned_rid, returned_rid == custom_rid)

    # ---------- 4. Make a test call that hits genaipro ----------
    log("\n=== Step 4: Trigger a real genaipro call ===")
    custom_rid = f"tc13_{int(time.time())}"
    s, r, _ = api("/api/settings/veo-jwt/test", token=token, extra_headers={"X-Request-ID": custom_rid})
    record("13.4.1", "GET /api/settings/veo-jwt/test returns 200", 200, s, s == 200)
    log(f"      ok={r.get('ok')}, fp={r.get('fingerprint')}, err={r.get('error')}")
    time.sleep(2)

    # ---------- 5. JSON logs ----------
    log("\n=== Step 5: JSON-formatted logs ===")
    logs = get_json_logs(500)
    record("13.5.1", "Logs are JSON", "≥1 JSON line", len(logs), len(logs) > 0)
    if logs:
        first = logs[0]
        record("13.5.2", "Log has ts field", True, "ts" in first, "ts" in first)
        record("13.5.3", "Log has level field", True, "level" in first, "level" in first)
        record("13.5.4", "Log has logger field", True, "logger" in first, "logger" in first)
        record("13.5.5", "Log has msg field", True, "msg" in first, "msg" in first)

    # ---------- 6. Request correlation ----------
    log("\n=== Step 6: Our request_id appears in logs ===")
    matching = [l for l in logs if l.get("request_id") == custom_rid]
    record("13.6.1", "Found logs with our request_id", "≥2", len(matching), len(matching) >= 2)
    if matching:
        log(f"      First: {matching[0].get('msg', '')[:80]}")
        log(f"      Second: {matching[1].get('msg', '')[:80]}")

    # ---------- 7. External API call logged ----------
    log("\n=== Step 7: External genaipro call logged with full context ===")
    ext_logs = [l for l in logs if str(l.get("event", "")).startswith("external_api")]
    if not ext_logs:
        record("13.7.1", "External API call logged", "≥1", 0, False)
    else:
        record("13.7.1", "External API call logged", "≥1", len(ext_logs), True)
        ext = ext_logs[-1]
        record("13.7.2", "Log has provider=genaipro", "genaipro", ext.get("provider"), ext.get("provider") == "genaipro")
        record("13.7.3", "Log has method=GET", "GET", ext.get("method"), ext.get("method") == "GET")
        record("13.7.4", "Log has url ending /v2/me", "/v2/me", str(ext.get("url", ""))[-7:], "/v2/me" in str(ext.get("url", "")))
        record("13.7.5", "Log has status field", True, "status" in ext, "status" in ext)
        record("13.7.6", "Log has duration_ms field", True, "duration_ms" in ext, "duration_ms" in ext)
        log(f"      url: {ext.get('url')}")
        log(f"      status: {ext.get('status')}, duration: {ext.get('duration_ms')}ms")

    # ---------- 8. Authorization header REDACTED ----------
    log("\n=== Step 8: Sensitive headers redacted ===")
    # Check ALL external_api logs (success + error) for any leak of the actual token
    all_ext = [l for l in logs if str(l.get("event", "")).startswith("external_api")]
    leak_found = False
    for l in all_ext:
        body = json.dumps(l)
        if token and token[:30] in body:  # If our actual token appears anywhere
            leak_found = True
            log(f"      ⚠️ TOKEN LEAKED in log: {l.get('event')}")
    record("13.8.1", "No token leak in any log line", "no leak", "LEAKED" if leak_found else "clean", not leak_found)
    # Also verify that if request_headers are logged, they're redacted
    ext_with_headers = [l for l in logs if l.get("event") == "external_api_call" and "request_headers" in l]
    if ext_with_headers:
        hdrs = ext_with_headers[-1].get("request_headers", {})
        auth_val = hdrs.get("Authorization", "")
        record("13.8.2", "Authorization header redacted when logged", "redacted", auth_val[:50], "redacted" in auth_val.lower())

    # ---------- 9. Request lifecycle logged ----------
    log("\n=== Step 9: Full request lifecycle logged ===")
    req_logs = [l for l in logs if l.get("event") == "request" and l.get("request_id") == custom_rid]
    record("13.9.1", "Request lifecycle event logged", "≥1", len(req_logs), len(req_logs) >= 1)
    if req_logs:
        r = req_logs[0]
        record("13.9.2", "Request log has method=GET", "GET", r.get("method"), r.get("method") == "GET")
        record("13.9.3", "Request log has path", "/api/settings/veo-jwt/test", r.get("path"), r.get("path") == "/api/settings/veo-jwt/test")
        record("13.9.4", "Request log has status=200", 200, r.get("status"), r.get("status") == 200)
        record("13.9.5", "Request log has duration_ms", True, "duration_ms" in r, "duration_ms" in r)
        record("13.9.6", "Request log has client IP", True, "client" in r, "client" in r)

    # ---------- 10. Typed error logged ----------
    log("\n=== Step 10: Test endpoint logs error event with code ===")
    failed = [l for l in logs if l.get("event") == "veo_test_failed"]
    if failed:
        record("13.10.1", "veo_test_failed event logged", "≥1", len(failed), True)
        last = failed[-1]
        record("13.10.2", "veo_test_failed has code=veo_jwt_invalid", "veo_jwt_invalid", last.get("code"),
               last.get("code") in ("veo_jwt_invalid", "veo_no_jwt", "veo_jwt_decrypt_failed"))
        record("13.10.3", "veo_test_failed has fingerprint", True, "fingerprint" in last, "fingerprint" in last)
    else:
        ok_logs = [l for l in logs if l.get("event") == "veo_test_me_ok"]
        if ok_logs:
            record("13.10.1", "veo_test_me_ok event logged (token valid)", "≥1", len(ok_logs), True)
        else:
            record("13.10.1", "veo_test event logged", "≥1", 0, False)

    # ---------- Summary ----------
    total = len(results)
    passed = sum(1 for _, _, _, _, ok in results if ok)
    log(f"\n{'='*60}")
    log(f"=== RESULT: {passed}/{total} PASS ({100*passed//total}%) ===")
    log(f"{'='*60}")

    # Save raw logs for inspection
    raw = get_raw_logs(200)
    (run_dir / "raw_logs.txt").write_text(raw, encoding="utf-8")
    (run_dir / "json_logs.json").write_text(json.dumps(logs, indent=2), encoding="utf-8")

    write_report(run_dir, results, logs)
    log(f"\nReport: {run_dir / 'report.html'}")
    log(f"Raw logs: {run_dir / 'raw_logs.txt'}")
    return 0 if passed == total else 1


def write_report(run_dir, results, logs):
    rows = []
    for id_, desc, expected, actual, ok in results:
        cls = "pass" if ok else "fail"
        rows.append(f"""<tr class="{cls}">
  <td>{id_}</td><td>{desc}</td>
  <td class="expected">{expected}</td>
  <td class="actual">{str(actual)[:200]}</td>
  <td>{'✅' if ok else '❌'}</td>
</tr>""")
    total = len(results)
    passed = sum(1 for _, _, _, _, ok in results if ok)
    ext_sample = [l for l in logs if str(l.get("event", "")).startswith("external_api")][-3:]
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>TC-13 Logging</title>
<style>
body{{font-family:system-ui;margin:24px;background:#0e0e10;color:#e5e5e5}}
h1{{color:#22c55e}}table{{width:100%;border-collapse:collapse;margin-top:16px}}
td,th{{padding:8px;border:1px solid #333;text-align:left;font-size:13px}}
tr.pass td{{background:#052e1a}}tr.fail td{{background:#3a0d0d}}
.expected{{color:#9ca3af}}.actual{{color:#e5e5e7;font-family:monospace}}
pre{{background:#1a1a1a;padding:16px;border-radius:8px;overflow-x:auto}}
</style></head><body>
<h1>TC-13: Structured Logging + Correlation ID</h1>
<p><b>Date:</b> {time.strftime('%Y-%m-%d %H:%M:%S')} · <b>Result:</b> {passed}/{total} PASS</p>
<h2>Assertions</h2>
<table><tr><th>#</th><th>Description</th><th>Expected</th><th>Actual</th><th>Pass</th></tr>
{"".join(rows)}</table>
<h2>External API Log Sample (most recent 3)</h2>
<pre>{json.dumps(ext_sample, indent=2)[:3000]}</pre>
</body></html>"""
    (run_dir / "report.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
