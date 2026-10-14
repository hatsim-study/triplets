#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simulate_static_observers.py – play N sessions of synthetic observers against the (mock or real)
Apps Script backend using the pre-generated plans, then verify the plan-assignment rules from
the backend's export:

  V1  second session of an observer is from the SAME round as the first (per study)
  V2  no observer has more than 2 sessions per study (mixed: 1 in pilot mode)
  V3  no observer saw a triplet twice (repeats excluded)
  V4  panel-2 votes on a triplet come from observers who never saw it in panel 1
  V5  every plan of the R rounds (and P rounds) has >= 1 completed session when enough sessions ran
  V6  trial rows are idempotent (no duplicate session_id+trial_index) and complete for completed sessions
  V7  abandoned sessions release their plan (plan re-issued after the reservation expired)

Usage:
  python simulate_static_observers.py --url http://127.0.0.1:8787/exec --plans docs/plans.json \
      --n-sessions 240 --dropout 0.05 --data test_data --report static_simulation_report.md
"""
import argparse
import hashlib
import json
import math
import os
import random
import sys
import time
import urllib.request
from collections import Counter, defaultdict

_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def api_get(url, **params):
    from urllib.parse import urlencode
    req = urllib.request.Request(url + "?" + urlencode(params))
    with _OPENER.open(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def api_post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "text/plain;charset=utf-8")
    with _OPENER.open(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def latent(tid):
    return "B" if int(hashlib.sha256(tid.encode()).hexdigest(), 16) % 2 == 0 else "C"


def view(tr):
    left, right = (tr["B"], tr["C"]) if tr["B_side"] == "left" else (tr["C"], tr["B"])
    return left, right


def play_session(url, oid, plans_by_id, practice, rng, args, drop, study="mixed"):
    d = api_get(url, action="next_plan", observer_id=oid, mode=args.mode, study=study, session_number=1)
    if "plan_id" not in d:
        return d.get("error", "unknown")
    plan = plans_by_id[d["plan_id"]]
    sid, rnd = d["session_id"], d["round"]
    base = {"session_id": sid, "observer_id": oid, "plan_id": plan["plan_id"], "round": rnd, "mode": args.mode, "study": study}
    start = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    api_post(url, dict(base, type="session_start", session_number_for_observer=d.get("session_number"), consent_version="sim",
                       consent_ts=start, demographics={"age_band": "25-34", "vision_corrected": "normal", "lang": "cs"},
                       start_ts=start, end_ts=None, completed=False, n_trials_target=len(plan["trials"]), n_trials_done=0,
                       user_agent="sha256:sim", completion_code=None, ui_lang="cs"))
    for i, p in enumerate(practice):
        left, right = view(p)
        api_post(url, dict(base, type="practice_trial", trial_index=-3 + i, triplet_id=p["triplet_id"],
                           response=rng.choice(["left", "right"]), rt_ms=3000, playback_errors=0,
                           timestamp_utc=start, flags=["practice", "simulated"]))
    answers = {}
    n_done = 0
    for tr in plan["trials"]:
        if drop is not None and tr["trial_index"] >= drop:
            break
        left, right = view(tr)
        if tr["is_attention"]:
            resp = "left" if left == tr["anchor"] else "right"
            if rng.random() < 0.03:
                resp = "right" if resp == "left" else "left"
        elif tr["is_repeat"] and tr["repeat_of"] in answers:
            prev = answers[tr["repeat_of"]]
            if rng.random() < args.consistency:
                resp = "undecided" if prev == "undecided" else ("left" if left == prev else "right")
            else:
                resp = rng.choice(["left", "right"]) if prev == "undecided" else ("right" if left == prev else "left")
        elif rng.random() < args.p_undecided:
            resp = "undecided"
        else:
            pick_b = (latent(tr["triplet_id"]) == "B") == (rng.random() < 0.8)
            resp = tr["B_side"] if pick_b else ("right" if tr["B_side"] == "left" else "left")
        chosen = None if resp == "undecided" else (left if resp == "left" else right)
        answers[tr["trial_index"]] = chosen if chosen else "undecided"
        rec = dict(base, type="trial", trial_index=tr["trial_index"], triplet_id=tr["triplet_id"], study=tr["study"],
                   anchor_clip=tr["anchor"], left_clip=left, right_clip=right, B_side=tr["B_side"], response=resp, chosen_clip=chosen,
                   rt_ms=int(min(40000, max(1200, math.exp(rng.gauss(math.log(3500), 0.45))))),
                   loop_phase_ms={"anchor": rng.randrange(10000), "left": rng.randrange(10000), "right": rng.randrange(10000)},
                   is_repeat=tr["is_repeat"], repeat_of_trial_index=tr.get("repeat_of"), is_attention=tr["is_attention"],
                   panel=tr["panel"], playback_errors=0, timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   ui_lang="cs", screen={"w": 1920, "h": 1080, "dpr": 1.0}, flags=["simulated"], study_part=study)
        api_post(url, rec)
        if rng.random() < 0.02:
            api_post(url, rec)          # duplicate POST (offline-queue retry) -> must be ignored
        n_done += 1
    if drop is None:
        api_post(url, dict(base, type="session_end", session_number_for_observer=d.get("session_number"), start_ts=start,
                           end_ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), completed=True,
                           n_trials_target=len(plan["trials"]), n_trials_done=n_done, completion_code="HAT-SIM-" + sid[-4:],
                           ui_lang="cs", end_reason="completed", demographics={}, consent_version="sim", user_agent="sha256:sim"))
    return "ok" if drop is None else "dropped"


def run(args, plans):
    """plans: {"mixed": plans.json dict, "grass": plans_grass.json dict or None}."""
    rng = random.Random(args.seed)
    plans_by_id = {}
    for st, pj in plans.items():
        for p in (pj or {}).get("plans", []):
            plans_by_id[p["plan_id"]] = p
    observers = []           # [oid, {"mixed": n, "grass": n}]
    outcomes = Counter()
    dropped_obs = set()
    studies = [s for s in ("mixed", "grass") if plans.get(s)]
    weights = {"mixed": args.p_mixed, "grass": 1.0 - args.p_mixed} if len(studies) == 2 else {studies[0]: 1.0}
    n = 0
    while n < args.n_sessions:
        # study of this session: a new observer draws mixed/grass; "both" observers play two parts in random order
        cands = [o for o in observers if o[0] not in dropped_obs and 0 < sum(o[1].values()) and max(o[1].values()) == 1]
        if cands and rng.random() < args.two_session_fraction and args.mode != "pilot":
            o = rng.choice(cands)
            study = rng.choice([s for s in studies if o[1].get(s, 0) == 1]) if rng.random() < 0.5 else rng.choice(studies)
            parts = [study]
        else:
            o = ["obs_%s%07d" % (args.observer_prefix, len(observers) + 1), {"mixed": 0, "grass": 0}]
            observers.append(o)
            if len(studies) == 2 and rng.random() < args.p_both:
                parts = studies[:]
                rng.shuffle(parts)                      # "both": random order of the two parts ...
                if rng.random() >= 0.5:
                    parts = parts[:1]                   # ... and with probability 0.5 the observer stops after the first part
            else:
                study = rng.choices(studies, weights=[weights[s] for s in studies])[0]
                parts = [study]
        for study in parts:
            if n >= args.n_sessions:
                break
            drop = rng.randrange(5, 24) if rng.random() < args.dropout else None
            res = play_session(args.url, o[0], plans_by_id, (plans.get(study) or {}).get("practice", []), rng, args, drop, study)
            outcomes[(study, res)] += 1
            n += 1
            if res == "ok":
                o[1][study] += 1
            elif res == "dropped":
                dropped_obs.add(o[0])
                break
            if n % 40 == 0:
                sys.stderr.write("  session %d/%d\n" % (n, args.n_sessions))
    return outcomes


def read_jsonl(p):
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def verify(args, plans):
    exp = api_get(args.url, action="export", token=args.token)
    if "trials" not in exp:
        sys.exit("export failed: %s" % exp)
    usage = exp["plan_usage"]
    trials = exp["trials"]
    all_plans = [p for st in ("mixed", "grass") for p in ((plans.get(st) or {}).get("plans", []))]
    plans_by_id = {p["plan_id"]: p for p in all_plans}
    checks = []

    def study_of(pid):
        return "grass" if str(pid).startswith("G") else "mixed"

    def add(code, name, ok, detail):
        checks.append((code, name, "PASS" if ok else "FAIL", detail))

    # final status per session (last plan_usage row wins)
    last = {}
    for u in usage:
        last[u["session_id"]] = u
    completed = [u for u in last.values() if u["status"] == "completed"]
    by_obs = defaultdict(lambda: defaultdict(list))        # observer -> study -> [usage]
    for u in completed:
        by_obs[u["observer_id"]][u.get("study") or study_of(u["plan_id"])].append(u)
    # V1 (per study)
    bad_round = sum(1 for o, d in by_obs.items() for st, us in d.items() if len({u["round"] for u in us}) > 1)
    n2 = sum(1 for d in by_obs.values() for us in d.values() if len(us) >= 2)
    add("V1", "second session from the same round as the first (per study)", bad_round == 0,
        "observer-study pairs with 2 sessions=%d round_mismatch=%d" % (n2, bad_round))
    # V2 (per study)
    lim = {"mixed": 1 if args.mode == "pilot" else 2, "grass": 2}
    over = sum(1 for d in by_obs.values() for st, us in d.items() if len(us) > lim[st])
    mx = {st: max((len(d.get(st, [])) for d in by_obs.values()), default=0) for st in ("mixed", "grass")}
    both = sum(1 for d in by_obs.values() if d.get("mixed") and d.get("grass"))
    add("V2", "max 2 completed sessions per observer and study (mixed pilot: 1)", over == 0,
        "max=%s observers=%d observers_with_both_studies=%d" % (dict(mx), len(by_obs), both))
    # V3 / V4 from trials
    seen = defaultdict(Counter)
    panel_obs = defaultdict(lambda: defaultdict(set))   # tid -> panel -> observers
    keys = Counter()
    for r in trials:
        keys[(r["session_id"], int(r["trial_index"]))] += 1
        if r.get("is_repeat") or r.get("is_attention"):
            continue
        seen[r["observer_id"]][r["triplet_id"]] += 1
        panel_obs[r["triplet_id"]][int(r["panel"])].add(r["observer_id"])
    twice = sum(1 for o, c in seen.items() for n in c.values() if n > 1)
    add("V3", "no observer saw a triplet twice (repeats excluded)", twice == 0, "violations=%d" % twice)
    overlap = sum(1 for tid, d in panel_obs.items() if 2 in d and (d[1] & d[2]))
    add("V4", "panel-2 observers disjoint from panel-1 observers per triplet", overlap == 0,
        "triplets_with_panel2=%d overlap=%d" % (sum(1 for d in panel_obs.values() if 2 in d), overlap))
    # V5 coverage (only for the studies listed in --require-coverage)
    done_plans = {u["plan_id"] for u in completed if not (u.get("mode") == "pilot" and study_of(u["plan_id"]) == "grass")}
    rounds = defaultdict(lambda: [0, 0])
    for p in all_plans:
        rounds[p["round"]][0] += 1
        rounds[p["round"]][1] += int(p["plan_id"] in done_plans)
    want = []
    for st in args.require_coverage:
        if st == "grass":
            want += [r for r in rounds if r.startswith("G")]
        elif args.mode == "pilot":
            want += ["PILOT"]
        else:
            want += [r for r in rounds if (r.startswith("R") or r.startswith("P")) and r != "PILOT"]
    uncovered = {r: rounds[r][0] - rounds[r][1] for r in want if rounds[r][1] < rounds[r][0]}
    add("V5", "every plan of the required studies (%s) has >= 1 completed session" % ",".join(args.require_coverage), not uncovered,
        "plans=%d completed=%d uncovered_by_round=%s" % (sum(rounds[r][0] for r in want), sum(rounds[r][1] for r in want), dict(uncovered) or "{}"))
    # V6 idempotence / completeness
    dups = sum(1 for n in keys.values() if n > 1)
    by_sess = Counter(k[0] for k in keys)
    incomplete = sum(1 for u in completed if by_sess.get(u["session_id"], 0) < plans_by_id[u["plan_id"]]["n_trials"])
    add("V6", "trial rows idempotent and complete for completed sessions", dups == 0 and incomplete == 0,
        "trial_rows=%d duplicate_keys=%d completed_sessions_missing_trials=%d" % (len(trials), dups, incomplete))
    # V7 abandoned sessions re-issued
    abandoned_plans = {u["plan_id"] for u in last.values() if u["status"] in ("abandoned", "reserved")
                       and study_of(u["plan_id"]) in args.require_coverage}
    reissued = sum(1 for pid in abandoned_plans if pid in done_plans)
    add("V7", "plans of abandoned/expired sessions were re-issued and completed (required studies)", not abandoned_plans or reissued == len(abandoned_plans),
        "abandoned_or_stale=%d later_completed=%d" % (len(abandoned_plans), reissued))
    stats = {"sessions_rows": len(last), "completed_sessions": len(completed), "observers": len(by_obs),
             "completed_by_study": dict(Counter((u.get("study") or study_of(u["plan_id"])) for u in completed)),
             "observers_with_both_studies": both,
             "trial_rows": len(trials), "rounds": {r: {"plans": v[0], "completed": v[1]} for r, v in sorted(rounds.items())}}
    return checks, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8787/exec")
    ap.add_argument("--plans", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "plans.json"))
    ap.add_argument("--plans-grass", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "plans_grass.json"),
                    help="plans of the grass study ('' to simulate the mixed study only)")
    ap.add_argument("--p-mixed", type=float, default=0.3, help="P(new single-study observer chooses the mixed study)")
    ap.add_argument("--p-both", type=float, default=0.3, help="P(new observer chooses 'both'); half of them stop after the first part")
    ap.add_argument("--require-coverage", default="grass", help="comma list of studies whose plans must all be completed (V5)")
    ap.add_argument("--mode", default="main", choices=["main", "pilot"])
    ap.add_argument("--n-sessions", type=int, default=240)
    ap.add_argument("--two-session-fraction", type=float, default=0.4)
    ap.add_argument("--dropout", type=float, default=0.05)
    ap.add_argument("--consistency", type=float, default=0.8)
    ap.add_argument("--p-undecided", type=float, default=0.08)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--token", default="testtoken")
    ap.add_argument("--wait-expiry-s", type=float, default=0.0, help="sleep before the final top-up pass (mock reservation expiry)")
    ap.add_argument("--topup-sessions", type=int, default=0, help="extra sessions after the wait (re-issue of abandoned plans)")
    ap.add_argument("--report", default="static_simulation_report.md")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--observer-prefix", default="sim", help="observer id prefix (use a new one when continuing a run)")
    args = ap.parse_args()
    with open(args.plans, encoding="utf-8") as fh:
        plans = {"mixed": json.load(fh), "grass": None}
    if args.plans_grass and os.path.exists(args.plans_grass):
        with open(args.plans_grass, encoding="utf-8") as fh:
            plans["grass"] = json.load(fh)
    args.require_coverage = [s for s in args.require_coverage.split(",") if s]
    outcomes, elapsed = Counter(), 0.0
    if not args.verify_only:
        t0 = time.time()
        outcomes = run(args, plans)
        if args.topup_sessions:
            time.sleep(args.wait_expiry_s)
            a2 = argparse.Namespace(**vars(args))
            a2.n_sessions, a2.dropout, a2.seed, a2.observer_prefix = args.topup_sessions, 0.0, args.seed + 1000, args.observer_prefix + "t"
            outcomes += run(a2, plans)
        elapsed = time.time() - t0
    checks, stats = verify(args, plans)
    status = api_get(args.url, action="status")
    L = ["# Static deployment – plan assignment simulation report\n",
         "Backend: `%s`, mode: %s, sessions requested: %d (+%d top-up), dropout: %.2f, seed: %d, elapsed: %.1f s\n"
         % (args.url, args.mode, args.n_sessions, args.topup_sessions, args.dropout, args.seed, elapsed),
         "Session outcomes (study, result): %s\n" % {("%s/%s" % k if isinstance(k, tuple) else k): v for k, v in outcomes.items()},
         "\n## Checks\n", "| # | rule | result | detail |", "|---|---|---|---|"]
    for c in checks:
        L.append("| %s | %s | **%s** | %s |" % c)
    L += ["\n## Totals\n", "| quantity | value |", "|---|---|"]
    for k in ("sessions_rows", "completed_sessions", "completed_by_study", "observers", "observers_with_both_studies", "trial_rows"):
        L.append("| %s | %s |" % (k, stats[k]))
    L += ["\n## Plans per round\n", "| round | plans | completed |", "|---|---|---|"]
    for r, v in stats["rounds"].items():
        L.append("| %s | %d | %d |" % (r, v["plans"], v["completed"]))
    L += ["\n## Backend status\n", "```json", json.dumps(status, indent=1, ensure_ascii=False), "```"]
    with open(args.report, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    for c in checks:
        print("%-3s %-72s %s   %s" % (c[0], c[1][:72], c[2], c[3]))
    print("report:", args.report)
    sys.exit(0 if all(c[2] == "PASS" for c in checks) else 1)


if __name__ == "__main__":
    main()
