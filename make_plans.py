"""Static-deployment session plans (no live scheduler). Usage: make_plans.py <triplets.csv> <sdyn_siblings.csv> <out_dir>
Rounds 1..7: every eligible main + S-dyn triplet once per round (panel 1); rounds P1..P7: every panel2 triplet once per round (panel 2).
Plan = 60 trials: 51 fresh (from one round), 6 mirrored repeats of earlier trials in the same plan, 3 attention checks. Seed 20261011.
"""
import sys, os, json, hashlib
import numpy as np, pandas as pd
SEED = 20261011; FRESH = 51; N_REP = 6; N_ATT = 3; ROUNDS = 7
TRIP, SIB, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True); rng = np.random.default_rng(SEED)
T = pd.read_csv(TRIP); S = pd.read_csv(SIB)
# S-dyn reduction (decision 10. 10. 2026): keep anchors whose w1 is a true same-scene sibling
keep_anchor = set(S[S.w1_level == "scene"].anchor)
T["eligible"] = (T.study == "main") | ((T.study == "sdyn") & T.anchor.str.split("__").str[0].isin(keep_anchor))
elig = T[T.eligible].reset_index(drop=True); att = T[T.study == "attention"].reset_index(drop=True); pilot = T[T.study == "pilot"].reset_index(drop=True)
p2 = elig[elig.panel2].reset_index(drop=True)
print("eligible", len(elig), elig.study.value_counts().to_dict(), "panel2", len(p2))
def make_round(df, panel, rid):
    ids = df.triplet_id.tolist(); rng.shuffle(ids); plans = []
    chunks = [ids[i:i + FRESH] for i in range(0, len(ids), FRESH)]
    # merge a short tail into previous chunks (keeps plans ~equal; a plan may have < FRESH fresh trials only in the last chunk)
    if len(chunks) > 1 and len(chunks[-1]) < FRESH // 2:
        tail = chunks.pop()
        for k, t in enumerate(tail): chunks[k % len(chunks)].append(t)
    for k, ch in enumerate(chunks):
        plans.append(dict(plan_id=f"{rid}_{k:02d}", round=rid, panel=panel, fresh=ch))
    return plans
plans = []
for r in range(1, ROUNDS + 1): plans += make_round(elig, 1, f"R{r}")
for r in range(1, ROUNDS + 1): plans += make_round(p2, 2, f"P{r}")
# build trial lists
trip = T.set_index("triplet_id")
out = []
for p in plans:
    fresh = p["fresh"]; n = len(fresh)
    trials = []
    for tid in fresh:
        r = trip.loc[tid]; side = "left" if rng.random() < 0.5 else "right"
        trials.append(dict(triplet_id=tid, study=r.study, anchor=r.anchor, B=r.B, C=r.C, B_side=side, is_repeat=False, is_attention=False, panel=p["panel"], repeat_of=None))
    a_ids = att.triplet_id.tolist(); rng.shuffle(a_ids)
    for tid in a_ids[:N_ATT]:
        r = trip.loc[tid]; side = "left" if rng.random() < 0.5 else "right"
        trials.append(dict(triplet_id=tid, study="attention", anchor=r.anchor, B=r.B, C=r.C, B_side=side, is_repeat=False, is_attention=True, panel=p["panel"], repeat_of=None))
    rng.shuffle(trials)
    # mirrored repeats: pick 6 fresh trials from the first 2/3, place in the last third, >=10 positions later
    cand = [i for i, t in enumerate(trials) if not t["is_attention"] and i < len(trials) * 2 // 3]
    rep_src = sorted(rng.choice(cand, N_REP, replace=False).tolist())
    for i in rep_src:
        t = dict(trials[i]); t["is_repeat"] = True; t["repeat_of"] = i; t["B_side"] = "right" if t["B_side"] == "left" else "left"
        pos = int(rng.integers(max(i + 10, len(trials) * 2 // 3), len(trials) + 1)); trials.insert(pos, t)
    # fix repeat_of indices after insertions: recompute by matching
    idx_of = {}
    for i, t in enumerate(trials):
        if not t["is_repeat"]: idx_of.setdefault(t["triplet_id"], i)
    for i, t in enumerate(trials):
        if t["is_repeat"]: t["repeat_of"] = idx_of[t["triplet_id"]]; assert t["repeat_of"] < i
        t["trial_index"] = i
    out.append(dict(plan_id=p["plan_id"], round=p["round"], panel=p["panel"], n_trials=len(trials), trials=trials))
practice = [dict(triplet_id=r.triplet_id, anchor=r.anchor, B=r.B, C=r.C, B_side="left") for r in pilot.head(3).itertuples()]
pilot_plans = []
pil = pilot.triplet_id.tolist()
for k in range(3):
    rng.shuffle(pil); trials = []
    for i, tid in enumerate(pil[:20]):
        r = trip.loc[tid]; trials.append(dict(triplet_id=tid, study="pilot", anchor=r.anchor, B=r.B, C=r.C, B_side="left" if rng.random() < 0.5 else "right", is_repeat=False, is_attention=False, panel=1, repeat_of=None, trial_index=i))
    pilot_plans.append(dict(plan_id=f"PILOT_{k}", round="PILOT", panel=1, n_trials=len(trials), trials=trials))
meta = dict(seed=SEED, n_plans=len(out), rounds=ROUNDS, fresh_per_plan=FRESH, repeats=N_REP, attention=N_ATT, n_eligible_triplets=int(len(elig)), n_panel2=int(len(p2)),
            sdyn_anchors_kept=sorted(keep_anchor), n_sdyn_triplets=int((elig.study == "sdyn").sum()), plan_sizes=sorted({p["n_trials"] for p in out}),
            rule_second_session="same round as first session (plans within a round are triplet-disjoint); never a P-round plan for an observer whose R-round plan contained that triplet -> enforced by same-round rule")
json.dump(dict(meta=meta, practice=practice, plans=out + pilot_plans), open(os.path.join(OUT, "plans.json"), "w"), indent=0)
elig[["triplet_id"]].to_csv(os.path.join(OUT, "eligible_triplets.csv"), index=False)
h = hashlib.sha256(open(os.path.join(OUT, "plans.json"), "rb").read()).hexdigest(); meta["plans_sha256"] = h
json.dump(meta, open(os.path.join(OUT, "plans_meta.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in meta.items() if k != "sdyn_anchors_kept"}, indent=0))
