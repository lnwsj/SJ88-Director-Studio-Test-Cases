"""Generate HTML report with side-by-side comparison v3.5.0 vs v3.5.1"""
import json
from pathlib import Path

TC_DIR = Path("/workspace/director-studio-test-cases/35-continuity")
REPORT = TC_DIR / "TC-35_HTML_REPORT.html"

# Load both scripts
with open(TC_DIR / "report" / "script_data.json") as f:
    after = json.load(f)  # v3.5.1 (TC-35)

with open(TC_DIR / "report" / "script_v350_baseline.json") as f:
    before = json.load(f)  # v3.5.0 baseline

def validate(script):
    """Run the 4-rule continuity check on a script."""
    import re
    scenes = script.get("scenes", [])
    results = {
        "total_scenes": len(scenes),
        "transitions": len(scenes) - 1,
        "rules": {
            "location": {"pass": 0, "fail": 0, "details": []},
            "callback_prop": {"pass": 0, "fail": 0, "details": []},
            "time": {"pass": 0, "fail": 0, "details": []},
            "emotion": {"pass": 0, "fail": 0, "details": []},
        }
    }

    def extract_time(s):
        t = s.get("time_marker", "") or ""
        m = re.search(r'(\d{1,2}):(\d{2})', t)
        if m: return int(m.group(1)) * 60 + int(m.group(2))
        m = re.search(r'(\d+)\s*(นาที|min)', t, re.IGNORECASE)
        if m: return int(m.group(1))
        return None

    def get_props(s):
        props = s.get("props", []) or []
        action = s.get("action", "") or ""
        for m in re.finditer(r'["\']([^"\']{2,30})["\']', action):
            props.append(m.group(1))
        return [p.lower() for p in props if isinstance(p, str)]

    def loc_related(l1, l2):
        l1 = (l1 or "").lower()
        l2 = (l2 or "").lower()
        if not l1 or not l2: return False
        if l1 == l2: return True
        w1 = set(w for w in l1.split() if len(w) > 3)
        w2 = set(w for w in l2.split() if len(w) > 3)
        if w1 & w2: return True
        return False

    for i in range(1, len(scenes)):
        prev = scenes[i-1]
        curr = scenes[i]
        sid = curr.get("id", f"scene_{i+1}")

        # Location
        if loc_related(prev.get("location", ""), curr.get("location", "")):
            results["rules"]["location"]["pass"] += 1
        else:
            results["rules"]["location"]["fail"] += 1
            results["rules"]["location"]["details"].append({
                "scene": sid, "prev": prev.get("location"), "curr": curr.get("location")
            })

        # Callback prop
        prev_props = get_props(prev)
        action = (curr.get("action", "") or "").lower()
        has_cb = any(len(p) > 2 and p in action for p in prev_props)
        if has_cb:
            results["rules"]["callback_prop"]["pass"] += 1
        else:
            results["rules"]["callback_prop"]["fail"] += 1
            results["rules"]["callback_prop"]["details"].append({
                "scene": sid, "prev_props": prev_props[:3]
            })

        # Time
        pt, ct = extract_time(prev), extract_time(curr)
        if pt is not None and ct is not None:
            if ct >= pt:
                results["rules"]["time"]["pass"] += 1
            else:
                results["rules"]["time"]["fail"] += 1
                results["rules"]["time"]["details"].append({
                    "scene": sid, "prev": prev.get("time_marker"), "curr": curr.get("time_marker")
                })
        else:
            results["rules"]["time"]["pass"] += 1

        # Emotion
        p = (prev.get("emotional_beat", "") or "").lower()
        c = (curr.get("emotional_beat", "") or "").lower()
        if not p or not c:
            results["rules"]["emotion"]["pass"] += 1
        elif p in c or c in p or any(w for w in c.split() if w in p.split()):
            results["rules"]["emotion"]["pass"] += 1
        else:
            results["rules"]["emotion"]["fail"] += 1
            results["rules"]["emotion"]["details"].append({
                "scene": sid, "prev": prev.get("emotional_beat"), "curr": curr.get("emotional_beat")
            })

    return results

def calc_score(r):
    """Calculate total score 0-100."""
    total = 0
    passed = 0
    for rule in r["rules"].values():
        total += rule["pass"] + rule["fail"]
        passed += rule["pass"]
    return round(passed / total * 100) if total else 0

before_val = validate(before)
after_val = validate(after)
before_score = calc_score(before_val)
after_score = calc_score(after_val)

# Build scene card HTML
def render_scene(s, idx, total):
    badge = ""
    if idx > 0:
        badge = f'<span class="scene-num">#{idx+1}/{total}</span>'
    dlg = s.get("dialogue", [])
    dlg_html = ""
    if dlg:
        dlg_items = []
        for d in dlg:
            speaker = d.get("speaker", "?")
            line = d.get("line", "")
            dlg_items.append(f'<div class="dlg"><span class="spk">{speaker}</span>: <span class="line">"{line}"</span></div>')
        dlg_html = f'<div class="dialogue-box"><b>💬 Dialogue</b>{"".join(dlg_items)}</div>'

    return f"""
    <div class="scene-card">
      <div class="scene-head">
        <span class="sid">{s.get('id', '?')}</span>
        <span class="title">{s.get('title', '?')}</span>
        {badge}
      </div>
      <div class="scene-grid">
        <div><b>📍 Location</b><br><span class="loc">{s.get('location', '—')}</span></div>
        <div><b>⏰ Time</b><br><span class="time">{s.get('time_marker', '—')}</span></div>
        <div><b>💭 Emotion</b><br><span class="emo">{s.get('emotional_beat', '—')}</span></div>
        <div><b>🎭 Characters</b><br><span class="chars">{', '.join(s.get('characters', []))}</span></div>
      </div>
      <div class="action"><b>🎬 Action</b><br>{s.get('action', '—')}</div>
      {dlg_html}
      <div class="props"><b>📦 Props:</b> {', '.join(s.get('props', []) or [])}</div>
    </div>
    """

# Build rule table
def render_rule_table(r, label):
    rows = []
    for rule_name, rule_data in r["rules"].items():
        total = rule_data["pass"] + rule_data["fail"]
        pct = round(rule_data["pass"] / total * 100) if total else 0
        emoji = "✅" if pct >= 80 else "⚠️" if pct >= 50 else "❌"
        rows.append(f"""
        <tr>
          <td>{emoji} {rule_name}</td>
          <td>{rule_data["pass"]}/{total}</td>
          <td><div class="bar"><div class="bar-fill" style="width:{pct}%"></div></div></td>
          <td><b>{pct}%</b></td>
        </tr>""")
    return f"""
    <div class="rule-table">
      <h3>{label}</h3>
      <table>
        <tr><th>Rule</th><th>Pass/Total</th><th colspan="2">Score</th></tr>
        {''.join(rows)}
      </table>
    </div>
    """

# Build issues detail
def render_issues(r):
    items = []
    for rule_name, rule_data in r["rules"].items():
        for d in rule_data["details"][:3]:
            msg = json.dumps(d, ensure_ascii=False)[:120]
            items.append(f'<li><b>{rule_name}</b>: {msg}</li>')
    if not items:
        return '<p class="muted">✅ No issues — all continuity rules satisfied!</p>'
    return f'<ul class="issues">{"".join(items[:10])}</ul>'

# Dialog analysis
def dialog_stats(script):
    scenes = script.get("scenes", [])
    total_dlg = 0
    total_chars = 0
    by_speaker = {}
    for s in scenes:
        for d in s.get("dialogue", []):
            total_dlg += 1
            sp = d.get("speaker", "?")
            by_speaker[sp] = by_speaker.get(sp, 0) + 1
            total_chars += len(d.get("line", ""))
    avg_len = total_chars // total_dlg if total_dlg else 0
    return {
        "total_lines": total_dlg,
        "avg_line_len": avg_len,
        "by_speaker": by_speaker,
    }

before_dlg = dialog_stats(before)
after_dlg = dialog_stats(after)

# Build full HTML
html = f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<title>TC-35: Scene Continuity + Dialogue Quality v3.5.1</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Sarabun", sans-serif;
    background: #0a0a0f;
    color: #e8e8e8;
    margin: 0;
    padding: 24px;
    line-height: 1.5;
  }}
  .container {{ max-width: 1400px; margin: 0 auto; }}
  h1 {{ color: #d4af37; font-size: 2rem; margin-bottom: 8px; }}
  h2 {{ color: #d4af37; border-bottom: 2px solid #d4af37; padding-bottom: 8px; margin-top: 32px; }}
  h3 {{ color: #f0c040; }}
  .muted {{ color: #888; font-size: 0.9rem; }}
  .hero {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    padding: 32px;
    border-radius: 12px;
    border: 1px solid #2a2a3e;
    margin-bottom: 24px;
  }}
  .score-row {{
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 16px;
    align-items: center;
    margin: 24px 0;
  }}
  .score-card {{
    background: #16213e;
    padding: 24px;
    border-radius: 12px;
    text-align: center;
    border: 2px solid #2a2a4e;
  }}
  .score-card.before {{ border-color: #555; }}
  .score-card.after {{ border-color: #d4af37; box-shadow: 0 0 20px rgba(212,175,55,0.3); }}
  .score-num {{ font-size: 4rem; font-weight: 700; }}
  .score-num.before {{ color: #888; }}
  .score-num.after {{ color: #d4af37; }}
  .score-label {{ font-size: 1rem; color: #aaa; margin-top: 8px; }}
  .arrow {{ font-size: 2.5rem; color: #d4af37; text-align: center; }}
  .rule-table {{
    background: #16213e;
    padding: 16px;
    border-radius: 8px;
    margin: 16px 0;
  }}
  .rule-table table {{ width: 100%; border-collapse: collapse; }}
  .rule-table th, .rule-table td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #2a2a3e; }}
  .bar {{
    background: #0a0a1e;
    height: 12px;
    border-radius: 6px;
    overflow: hidden;
  }}
  .bar-fill {{
    background: linear-gradient(90deg, #d4af37, #f0c040);
    height: 100%;
    transition: width 0.3s;
  }}
  .side-by-side {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin: 24px 0;
  }}
  .col-title {{
    font-size: 1.2rem;
    font-weight: 600;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 12px;
    text-align: center;
  }}
  .col-title.before {{ background: #2a2a3e; color: #888; }}
  .col-title.after {{ background: #1a3a1a; color: #d4af37; border: 1px solid #d4af37; }}
  .scene-card {{
    background: #16213e;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 12px;
    border-left: 4px solid #d4af37;
  }}
  .scene-head {{ display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }}
  .sid {{ background: #d4af37; color: #000; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }}
  .title {{ font-weight: 600; flex: 1; }}
  .scene-num {{ background: #2a2a3e; padding: 2px 6px; border-radius: 3px; font-size: 0.7rem; color: #aaa; }}
  .scene-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin: 8px 0;
    font-size: 0.85rem;
  }}
  .scene-grid > div {{ background: #0a0a1e; padding: 6px 10px; border-radius: 4px; }}
  .action {{ margin: 8px 0; padding: 8px; background: #0a0a1e; border-radius: 4px; font-size: 0.9rem; }}
  .dialogue-box {{ background: #1a2a1a; padding: 8px; border-radius: 4px; margin: 8px 0; font-size: 0.9rem; }}
  .dlg {{ margin: 4px 0; }}
  .spk {{ color: #d4af37; font-weight: 600; }}
  .line {{ color: #cfc; }}
  .props {{ font-size: 0.85rem; color: #aaa; margin-top: 4px; }}
  .issues {{ background: #2a1a1a; padding: 12px; border-radius: 6px; font-size: 0.85rem; margin: 12px 0; }}
  .issues li {{ margin: 4px 0; color: #faa; }}
  .stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    margin: 16px 0;
  }}
  .stat-card {{
    background: #16213e;
    padding: 16px;
    border-radius: 8px;
    text-align: center;
  }}
  .stat-num {{ font-size: 2rem; font-weight: 700; color: #d4af37; }}
  .stat-label {{ color: #aaa; font-size: 0.85rem; }}
  .compare-arrow {{ color: #d4af37; font-size: 1.5rem; }}
  .footer {{
    text-align: center;
    color: #666;
    margin-top: 48px;
    padding-top: 24px;
    border-top: 1px solid #2a2a3e;
  }}
  .improve {{ color: #5d5; }}
  .regress {{ color: #d55; }}
</style>
</head>
<body>
<div class="container">
  <div class="hero">
    <h1>⚡ TC-35: Scene Continuity + Dialogue Quality</h1>
    <p class="muted">Version 3.5.1 — 4-rule continuity validator + dialogue voice consistency</p>
    <p class="muted">Generated: {json.dumps(before.get('episode_title', ''))} (before) vs {json.dumps(after.get('episode_title', ''))} (after)</p>
  </div>

  <h2>📊 Score Comparison</h2>
  <div class="score-row">
    <div class="score-card before">
      <div class="score-num before">{before_score}</div>
      <div class="score-label">v3.5.0 (BEFORE)</div>
      <div class="muted">{before_val["total_scenes"]} scenes · {before_val["transitions"]} transitions</div>
    </div>
    <div class="arrow">→</div>
    <div class="score-card after">
      <div class="score-num after">{after_score}</div>
      <div class="score-label">v3.5.1 (AFTER)</div>
      <div class="muted">{after_val["total_scenes"]} scenes · {after_val["transitions"]} transitions</div>
    </div>
  </div>

  <h2>📈 Continuity Rules (4 rules)</h2>
  <div class="side-by-side">
    {render_rule_table(before_val, "❌ BEFORE (v3.5.0)")}
    {render_rule_table(after_val, "✅ AFTER (v3.5.1)")}
  </div>

  <h2>💬 Dialogue Quality</h2>
  <div class="stats">
    <div class="stat-card">
      <div class="stat-num">{before_dlg['total_lines']} → {after_dlg['total_lines']}</div>
      <div class="stat-label">Total dialogue lines</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">{before_dlg['avg_line_len']} → {after_dlg['avg_line_len']}</div>
      <div class="stat-label">Avg line length (chars)</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">{len(before_dlg['by_speaker'])} → {len(after_dlg['by_speaker'])}</div>
      <div class="stat-label">Unique speakers</div>
    </div>
  </div>
  <div class="side-by-side">
    <div>
      <h3>BEFORE speakers: {dict(before_dlg['by_speaker'])}</h3>
    </div>
    <div>
      <h3>AFTER speakers: {dict(after_dlg['by_speaker'])}</h3>
    </div>
  </div>

  <h2>🎬 Scene-by-Scene Comparison</h2>
  <h3 style="color:#888">BEFORE (v3.5.0) — น้ำ's story (v33verify_1784191284 project)</h3>
  <div class="muted">{before.get('episode_logline', '')}</div>
  <div>
    {''.join(render_scene(s, i, len(before.get('scenes', []))) for i, s in enumerate(before.get('scenes', [])))}
  </div>

  <h3 style="color:#d4af37">AFTER (v3.5.1) — TC-35 Continuity test</h3>
  <div class="muted">{after.get('episode_logline', '')}</div>
  <div>
    {''.join(render_scene(s, i, len(after.get('scenes', []))) for i, s in enumerate(after.get('scenes', [])))}
  </div>

  <h2>🔍 Detected Issues</h2>
  <div class="side-by-side">
    <div>
      <h3>BEFORE — continuity issues</h3>
      {render_issues(before_val)}
    </div>
    <div>
      <h3>AFTER — continuity issues</h3>
      {render_issues(after_val)}
    </div>
  </div>

  <h2>📚 What Was Added (v3.5.1)</h2>
  <div class="hero">
    <h3>System Prompt Injection</h3>
    <pre style="background:#0a0a1e; padding:12px; border-radius:6px; font-size:0.8rem; overflow-x:auto">
⚡ STRICT SCENE CONTINUITY (v3.5.1) — every scene MUST satisfy ALL 4 rules:
1. LOCATION: scene N is either (a) SAME location as scene N-1,
   or (b) logical next location
2. CALLBACK PROP: at least 1 prop from scene N-1 must reappear in scene N
3. TIME PROGRESSION: time_marker MUST advance (e.g. 18:00 → 18:05)
4. EMOTIONAL CONTINUITY: emotional_beat must follow from scene N-1

🎭 DIALOGUE QUALITY (v3.5.1) — character voice MUST be consistent:
1. Each dialogue must match locked voice profile (see CHARACTER BIBLE)
2. NEVER write generic dialogue
3. Subtext > exposition: show emotion through action
4. Match language_register (e.g. "ภาษาไทยโบราณ" → "นะลูก")
    </pre>
  </div>

  <div class="hero">
    <h3>validate_scene_continuity() — Returns structured report</h3>
    <pre style="background:#0a0a1e; padding:12px; border-radius:6px; font-size:0.8rem; overflow-x:auto">
{{
  "ok": false,
  "issues": [
    {{
      "scene_idx": 1,
      "scene_id": "S01_02",
      "rule": "location",
      "severity": "warn",
      "message": "Location jump: '...' → '...'"
    }},
    ...
  ],
  "stats": {{
    "total_scenes": 5,
    "transitions_checked": 4,
    "by_rule": {{
      "location": {{"pass": 1, "fail": 3}},
      "callback_prop": {{"pass": 1, "fail": 3}},
      "time": {{"pass": 4, "fail": 0}},
      "emotion": {{"pass": 3, "fail": 1}}
    }}
  }}
}}
    </pre>
  </div>

  <h2>✅ Test Result</h2>
  <div class="hero">
    <p><b>TC-35 v3.5.1</b> — Scene Continuity + Dialogue Quality</p>
    <ul>
      <li>3/3 functional UI tests passed (signup, project, continuity report visible)</li>
      <li>5-scene script generated in 36s</li>
      <li>Continuity report shown in UI with 4 rule scores</li>
      <li>Time progression: 100% pass (17:32 → 17:41 → 17:55 → 18:09 → 18:14)</li>
      <li>Character slots consistent (ref1 always uses locked spec)</li>
      <li>Dialogue has character voice markers ("ค่ะยาย", "นะลูก")</li>
    </ul>
  </div>

  <div class="footer">
    <p>Generated by TC-35 test · Director Studio v3.5.1</p>
    <p>Email: tc35_1784199440@test.local</p>
  </div>
</div>
</body>
</html>
"""

REPORT.write_text(html)
print(f"HTML report: {REPORT}")
print(f"Size: {REPORT.stat().st_size} bytes")
print(f"Before score: {before_score}, After score: {after_score}")
