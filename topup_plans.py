#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
topup_plans.py – generate additional session plans ("top-up" rounds T1, T2, …) for triplets that
still have fewer than 5 decided votes after QC.

Input
  --majority majority.csv     columns: triplet_id, panel, n_decided   (from majority.py)
  --triplets triplets.csv     frozen triplet table (anchor, B, C, study, panel2, …)
  --plans    plans.json       existing plans (for the plan structure, attention pool and seed continuity)
Output
  --out      plans_topup.json same structure as plans.json ({meta, practice, plans}); the plans carry
                              round "T1".."Tk" and plan_id "T1_00" …; merge into plans.json with --merge
                              (writes a new file plans_merged.json) and register the new plan ids
                              (plan_index_topup.csv / register_plans).

Rules kept from the original generator: within one round each triplet appears at most once
(plans of a round are triplet-disjoint), so the "same round for the second session" rule still
guarantees that an observer never sees a triplet twice. A triplet needing k more votes is placed in
k consecutive rounds. Each plan: 51 fresh trials (fewer in the last plan of a round), 10 % mirrored
repeats (6, mirrored side, >= 8 trials after the original) and 5 % attention checks (3, A_* triplets),
positions as in the original plans. B_side of fresh trials is random (seeded).
Panel-2 top-ups are placed into separate rounds (TP1.., panel=2) so that a top-up observer never votes on
panel 1 and panel 2 of the same triplet; observer disjointness from the original panel-1 voters
is guaranteed by the same-round rule (T rounds are only given to new observers).
"""
import argparse
import csv
import hashlib
import json
import math
import random
from collections import defaultdict

FRESH, N_REPEAT, N_ATT, MIN_GAP, MIN_DECIDED = 51, 6, 3, 8, 5


def build_plan(plan_id, rnd, panel, fresh_triplets, attention_pool, rng):
    """fresh_triplets: list of triplet rows (dicts). Returns a plan dict in the plans.json structure."""
    n_fresh = len(fresh_triplets)
    n_rep = max(0, round(n_fresh * N_REPEAT / FRESH)) if n_fresh >= 20 else 0
    n_att = max(1, round(n_fresh * N_ATT / FRESH)) if n_fresh >= 10 else 1
    N = n_fresh + n_rep + n_att
    slots = ["fresh"] * N
    att_pos = rng.sample(range(2, N), min(n_att, N - 2))
    for p in att_pos:
        slots[p] = "attention"
    lo = max(MIN_GAP + 2, N // 3)
    rep_cands = [i for i in range(lo, N) if slots[i] == "fresh"]
    for p in rng.sample(rep_cands, min(n_rep, len(rep_cands))):
        slots[p] = "repeat"
    fresh = list(fresh_triplets)
    rng.shuffle(fresh)
    atts = rng.sample(attention_pool, min(n_att, len(attention_pool)))
    trials = []
    repeated = set()
    for i, slot in enumerate(slots):
        if slot == "attention" and atts:
            a = atts.pop()
            trials.append({"triplet_id": a["triplet_id"], "study": "attention", "anchor": a["anchor"], "B": a["B"], "C": a["C"],
                           "B_side": rng.choice(["left", "right"]), "is_repeat": False, "is_attention": True, "panel": panel,
                           "repeat_of": None, "trial_index": i})
            continue
        if slot == "repeat":
            cands = [t for t in trials if not t["is_repeat"] and not t["is_attention"] and t["trial_index"] <= i - MIN_GAP
                     and t["trial_index"] not in repeated]
            if cands:
                src = rng.choice(cands)
                repeated.add(src["trial_index"])
                trials.append(dict(src, B_side=("right" if src["B_side"] == "left" else "left"), is_repeat=True,
                                   repeat_of=src["trial_index"], trial_index=i))
                continue
        if fresh:
            t = fresh.pop()
            trials.append({"triplet_id": t["triplet_id"], "study": t["study"], "anchor": t["anchor"], "B": t["B"], "C": t["C"],
                           "B_side": rng.choice(["left", "right"]), "is_repeat": False, "is_attention": False, "panel": panel,
                           "repeat_of": None, "trial_index": i})
        else:
            break
    for i, t in enumerate(trials):
        t["trial_index"] = i
    for t in trials:          # repeat_of must point at the re-indexed original (indices unchanged unless the tail was cut)
        if t["is_repeat"] and t["repeat_of"] is not None and t["repeat_of"] >= len(trials):
            t["is_repeat"], t["repeat_of"] = False, None
    return {"plan_id": plan_id, "round": rnd, "panel": panel, "n_trials": len(trials), "trials": trials}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--majority", required=True)
    ap.add_argument("--triplets", required=True)
    ap.add_argument("--plans", required=True)
    ap.add_argument("--out", default="plans_topup.json")
    ap.add_argument("--merge", action="store_true", help="also write plans_merged.json (= plans.json + top-up plans)")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--round-prefix", default="T")
    a = ap.parse_args()

    with open(a.triplets, newline="", encoding="utf-8") as fh:
        triplets = {r["triplet_id"]: r for r in csv.DictReader(fh)}
    with open(a.plans, encoding="utf-8") as fh:
        plans = json.load(fh)
    existing_rounds = {p["round"] for p in plans["plans"]}
    need = defaultdict(int)       # (triplet_id, panel) -> missing votes
    with open(a.majority, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            tid, panel, n = r["triplet_id"], int(r.get("panel") or 1), int(float(r["n_decided"]))
            if tid not in triplets:
                continue
            if panel == 2 and str(triplets[tid].get("panel2", "")).lower() != "true":
                continue
            if n < MIN_DECIDED:
                need[(tid, panel)] = MIN_DECIDED - n
    if not need:
        print("nothing to top up")
        json.dump({"meta": {"n_plans": 0}, "practice": plans.get("practice", []), "plans": []}, open(a.out, "w"), indent=0)
        return
    seed = a.seed if a.seed is not None else int(hashlib.sha256(json.dumps(sorted(need.items())).encode()).hexdigest(), 16) % (2 ** 31)
    rng = random.Random(seed)
    attention_pool = [t for t in triplets.values() if t["study"] == "attention"]
    k_max = max(need.values())
    out_plans = []
    counter = 0
    for k in range(1, k_max + 1):
        for panel in (1, 2):
            # panel-1 and panel-2 top-ups live in SEPARATE rounds (T1.. vs TP1..): an observer stays within one
            # round, so nobody votes on both panels of the same triplet
            rnd = "%s%s%d" % (a.round_prefix, "" if panel == 1 else "P", k)
            while rnd in existing_rounds:
                counter += 1
                rnd = "%s%s%d_%d" % (a.round_prefix, "" if panel == 1 else "P", k, counter)
            tids = [triplets[tid] for (tid, p), n in sorted(need.items()) if p == panel and n >= k]
            if not tids:
                continue
            rng.shuffle(tids)
            n_plans = math.ceil(len(tids) / FRESH)
            for j in range(n_plans):
                chunk = tids[j * FRESH:(j + 1) * FRESH]
                pid = "%s_%02d" % (rnd, j)
                out_plans.append(build_plan(pid, rnd, panel, chunk, attention_pool, rng))
    meta = {"seed": seed, "n_plans": len(out_plans), "source_majority": a.majority,
            "n_triplet_panels_topped_up": len(need), "votes_missing_total": sum(need.values()),
            "rounds": sorted({p["round"] for p in out_plans}), "rule": "T rounds: same structure as plans.json; "
            "triplet-disjoint within a round; a triplet needing k votes appears in rounds T1..Tk; new observers only (same-round rule)"}
    result = {"meta": meta, "practice": plans.get("practice", []), "plans": out_plans}
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, separators=(",", ":"))
    with open(a.out.replace(".json", "_index.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["plan_id", "round", "panel", "n_trials", "mode"])
        for p in out_plans:
            w.writerow([p["plan_id"], p["round"], p["panel"], p["n_trials"], "main"])
    if a.merge:
        merged = {"meta": dict(plans["meta"], topup=meta), "practice": plans.get("practice", []), "plans": plans["plans"] + out_plans}
        with open("plans_merged.json", "w", encoding="utf-8") as fh:
            json.dump(merged, fh, ensure_ascii=False, separators=(",", ":"))
    print("top-up: %d (triplet,panel) need %d votes -> %d plans in rounds %s -> %s" %
          (len(need), sum(need.values()), len(out_plans), meta["rounds"], a.out))


if __name__ == "__main__":
    main()
