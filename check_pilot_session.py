#!/usr/bin/env python3
"""check_pilot_session.py – completeness check of human pilot sessions against plans.json.
Usage: python check_pilot_session.py --data analysis_data/ --plans docs/plans.json [docs/plans_grass.json ...] [--session SESSION_ID]
(--plans accepts several files: a session's plan is looked up in plans.json OR plans_grass.json; the study of a session is printed.)
(analysis_data/ = output of export_to_jsonl.py). Checks per session: plan exists; trial_index 0..n-1 contiguous, no gaps/duplicates;
each trial's triplet_id/anchor/left/right/B_side match the plan (mirrored repeats: B_side flipped); responses valid; RT range;
loop phases 0–10 000 ms; session_end present + completion_code; practice = 3 trials; playback errors; timestamps increasing.
"""
import argparse, json, os, sys, collections
def jl(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []
ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--plans", required=True, nargs="+"); ap.add_argument("--session", default=None); a = ap.parse_args()
plans = {}
for pf in a.plans:
    for p in json.load(open(pf, encoding="utf-8"))["plans"]: plans[p["plan_id"]] = p
S = jl(os.path.join(a.data, "sessions.jsonl")); T = jl(os.path.join(a.data, "trials.jsonl")); P = jl(os.path.join(a.data, "practice_trials.jsonl"))
by = collections.defaultdict(list)
for t in T: by[t["session_id"]].append(t)
pr = collections.defaultdict(list)
for t in P: pr[t["session_id"]].append(t)
ok_all = True
for s in S:
    sid = s["session_id"]
    if a.session and sid != a.session: continue
    issues = []; trials = sorted(by[sid], key=lambda t: t["trial_index"]); plan = plans.get(s.get("plan_id"))
    if plan is None: issues.append(f"unknown plan_id {s.get('plan_id')}"); print(f"[{sid}] FAIL: {issues}"); ok_all = False; continue
    n = len(plan["trials"]); idx = [t["trial_index"] for t in trials]
    if idx != list(range(n)): issues.append(f"trial indices {len(idx)}/{n}: missing {sorted(set(range(n)) - set(idx))[:10]} dup {[i for i, c in collections.Counter(idx).items() if c > 1][:10]}")
    for t in trials:
        if t["trial_index"] >= n: continue
        pt = plan["trials"][t["trial_index"]]
        exp_left, exp_right = (pt["B"], pt["C"]) if pt["B_side"] == "left" else (pt["C"], pt["B"])
        if t["triplet_id"] != pt["triplet_id"]: issues.append(f"#{t['trial_index']} triplet {t['triplet_id']} != plan {pt['triplet_id']}")
        if (t.get("anchor_clip"), t.get("left_clip"), t.get("right_clip")) != (pt["anchor"], exp_left, exp_right): issues.append(f"#{t['trial_index']} clips differ from plan")
        if t.get("B_side") != pt["B_side"]: issues.append(f"#{t['trial_index']} B_side {t.get('B_side')} != plan {pt['B_side']}")
        if bool(t.get("is_repeat")) != bool(pt["is_repeat"]) or bool(t.get("is_attention")) != bool(pt["is_attention"]): issues.append(f"#{t['trial_index']} repeat/attention flags differ")
        if t.get("response") not in ("left", "right", "undecided"): issues.append(f"#{t['trial_index']} bad response {t.get('response')}")
        exp_chosen = {"left": t.get("left_clip"), "right": t.get("right_clip"), "undecided": None}.get(t.get("response"))
        if t.get("chosen_clip") != exp_chosen: issues.append(f"#{t['trial_index']} chosen_clip inconsistent")
        rt = t.get("rt_ms")
        if not isinstance(rt, int) or rt < 500 or rt > 300000: issues.append(f"#{t['trial_index']} rt_ms {rt}")
        lp = t.get("loop_phase_ms") or {}
        if any(k not in lp or not (0 <= lp[k] <= 10000) for k in ("anchor", "left", "right")): issues.append(f"#{t['trial_index']} loop_phase {lp}")
        if t.get("playback_errors", 0): issues.append(f"#{t['trial_index']} playback_errors={t['playback_errors']}")
    ts = [t.get("timestamp_utc") for t in trials]
    if ts != sorted(ts): issues.append("timestamps not increasing")
    if not s.get("completed"): issues.append(f"session not completed (end_reason={s.get('end_reason')})")
    if not s.get("completion_code"): issues.append("missing completion_code")
    if len(pr[sid]) != 3: issues.append(f"practice trials {len(pr[sid])} != 3")
    und = sum(t.get("response") == "undecided" for t in trials); att_fail = sum(1 for t in trials if t.get("is_attention") and t.get("chosen_clip") != t.get("anchor_clip"))
    print(f"[{sid}] plan {s.get('plan_id')} study {s.get('study') or plan.get('study') or 'mixed'} observer {s.get('observer_id')} trials {len(trials)}/{n} undecided {und} attention_fail {att_fail} "
          f"median_rt {sorted(t['rt_ms'] for t in trials)[len(trials)//2] if trials else 'n/a'} ms -> {'OK' if not issues else 'ISSUES'}")
    for i in issues[:25]: print("   -", i)
    ok_all &= not issues
print("ALL OK" if ok_all else "SOME ISSUES"); sys.exit(0 if ok_all else 1)
