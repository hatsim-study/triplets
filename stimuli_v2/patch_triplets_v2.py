"""Audit patch v2 (14. 10. 2026): remove audited videos from the frozen v1 triplet set with minimal change.
Rules: excluded ANCHOR -> all its main/attention/S-dyn triplets dropped; excluded CANDIDATE -> replaced in each triplet by a candidate
of the same fold and the same relation to the anchor (same class / same family-other class / other family), never the anchor's scene,
never the other candidate, least-used first, ties by seeded RNG. panel2 re-filled to 40 per difficulty. Seed 20261014.
Usage: patch_triplets_v2.py <v1_dir(stimuli)> <out_dir> [deployed_clips_index.json]"""
import sys, os, json, collections, numpy as np, pandas as pd
SEED = 20261014
EXCL = {"6485510": "A people clearly visible (plaza, walking)", "6485610": "A people clearly visible (plaza, walking)",
        "6486210": "A people clearly visible (pool)", "6489c10": "C manipulated objects (market stall, mirrors, person)"}
V1, OUT = sys.argv[1:3]; DEPLOYED = set(json.load(open(sys.argv[3]))) if len(sys.argv) > 3 else None; os.makedirs(OUT, exist_ok=True); rng = np.random.default_rng(SEED)
T = pd.read_csv(os.path.join(V1, "triplets.csv")); roles = pd.read_csv(os.path.join(V1, "videos_roles.csv")); S = pd.read_csv(os.path.join(V1, "sdyn_siblings.csv"))
V = roles.set_index("video")
log = []
# 1) drop triplets anchored on excluded videos (main, attention, S-dyn)
base = T.anchor.str.split("__").str[0]
drop = T[base.isin(EXCL)].triplet_id.tolist()
for t in drop: log.append(dict(triplet_id=t, action="dropped", reason="anchor excluded"))
T2 = T[~T.triplet_id.isin(drop)].copy()
# 2) replace excluded candidates
use = collections.Counter(list(T2[T2.study == "main"].B) + list(T2[T2.study == "main"].C))
def relation(a, x):
    A, X = V.loc[a], V.loc[x]
    return "same_class" if X.class_id == A.class_id else ("same_family" if X.family == A.family else "other_family")
def replacement(a, x, other, fold):
    rel = relation(a, x); A = V.loc[a]
    c = roles[(roles.fold == fold) & (roles.role == "candidate") & (~roles.video.isin(EXCL)) & (roles.scene_id != A.scene_id) & (roles.video != other)]
    if DEPLOYED is not None: c = c[c.video.isin(DEPLOYED)]   # only clips already deployed on clips-a/clips-b
    order = {"same_class": ["same_class", "same_family", "other_family"], "same_family": ["same_family", "other_family"], "other_family": ["other_family"]}[rel]
    for lvl in order:   # fallback order identical to select_stimuli.py
        if lvl == "same_class": cc = c[c.class_id == A.class_id]
        elif lvl == "same_family": cc = c[(c.family == A.family) & (c.class_id != A.class_id)]
        else: cc = c[c.family != A.family]
        if len(cc): break
    rel = rel if lvl == rel else f"{rel}->fallback:{lvl}"; cands = cc.video.tolist(); assert cands, (a, x, rel)
    m = min(use[v] for v in cands); low = sorted(v for v in cands if use[v] == m)
    return low[rng.integers(len(low))], rel
for i, r in T2.iterrows():
    if r.study not in ("main", "attention"): continue
    for col, oth in (("B", "C"), ("C", "B")):
        x = r[col]
        if x in EXCL:
            new, rel = replacement(r.anchor, x, r[oth], r.fold); use[new] += 1
            T2.loc[i, col] = new; T2.loc[i, col + "_class"] = V.loc[new].class_id
            log.append(dict(triplet_id=r.triplet_id, action=f"replaced {col}", reason=f"{x} -> {new} ({rel})"))
# 3) S-dyn sibling replacement (6489c10 was w1 of 6489b10; that anchor is not in the reduced set, patched for consistency)
S2 = S.copy()
for i, r in S2.iterrows():
    for w in ("w1", "w2"):
        if r[w] in EXCL:
            A = V.loc[r.anchor]; tp = roles[(roles.partition == "test") & (~roles.video.isin(EXCL)) & (~roles.sdyn_anchor)]
            c = tp[(tp.class_id == A.class_id) & (tp.scene_id != A.scene_id) & (tp.video != r["w2" if w == "w1" else "w1"])]
            lvl = "class"
            if len(c) == 0: c = tp[(tp.family == A.family) & (tp.scene_id != A.scene_id)]; lvl = "family"
            if len(c) == 0: c = tp[tp.scene_id != A.scene_id]; lvl = "any"
            vv = sorted(c.video); new = vv[rng.integers(len(vv))]
            S2.loc[i, w] = new; S2.loc[i, w + "_level"] = lvl
            m = T2.triplet_id.str.startswith(f"S_{r.anchor}_")
            for j in T2[m].index:
                for col in ("B", "C"):
                    if T2.loc[j, col] == r[w]: T2.loc[j, col] = new; log.append(dict(triplet_id=T2.loc[j, "triplet_id"], action=f"replaced {col}", reason=f"{r[w]} -> {new} (sdyn sibling, {lvl})"))
S2 = S2[~S2.anchor.isin(EXCL)]
# 4) panel2 refill: 40 per difficulty among test main triplets
for d in ("easy", "medium", "hard"):
    m = (T2.study == "main") & (T2.fold == "test") & (T2.difficulty == d)
    have = int((m & T2.panel2).sum())
    if have < 40:
        pool = T2[m & ~T2.panel2].index.to_numpy().copy(); rng.shuffle(pool)
        T2.loc[pool[:40 - have], "panel2"] = True
        log.append(dict(triplet_id="", action="panel2 refill", reason=f"{d}: +{40 - have}"))
assert T2[(T2.study == "main") & T2.panel2].shape[0] == 120
# checks
for r in T2.itertuples():
    for x in (r.anchor, r.B, r.C): assert x.split("__")[0] not in EXCL, r.triplet_id
    if r.study in ("main",): assert len({r.anchor, r.B, r.C}) == 3 and V.loc[r.B].scene_id != V.loc[r.anchor].scene_id and V.loc[r.C].scene_id != V.loc[r.anchor].scene_id
roles2 = roles.copy(); roles2.loc[roles2.video.isin(EXCL), "role"] = "excluded_audit"; roles2["audit_reason"] = roles2.video.map(EXCL).fillna("")
T2.to_csv(os.path.join(OUT, "triplets.csv"), index=False); roles2.to_csv(os.path.join(OUT, "videos_roles.csv"), index=False); S2.to_csv(os.path.join(OUT, "sdyn_siblings.csv"), index=False)
pd.DataFrame(log).to_csv(os.path.join(OUT, "patch_log.csv"), index=False)
clips = sorted({x for r in T2.itertuples() for x in (r.anchor, r.B, r.C)})
open(os.path.join(OUT, "clips_needed.txt"), "w").write("\n".join(clips) + "\n")
meta = dict(seed=SEED, excluded=EXCL, n_dropped=len(drop), n_replaced=sum(1 for l in log if l["action"].startswith("replaced")), n_triplets=T2.study.value_counts().to_dict(),
            n_clips=len(clips), candidate_use_max=max(use.values()), candidate_use_mean=float(np.mean(list(use.values()))))
json.dump(meta, open(os.path.join(OUT, "patch_meta.json"), "w"), indent=1); print(json.dumps(meta, indent=0))
