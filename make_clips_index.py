#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_clips_index.py – build docs/clips_index.json ({clip_id: absolute URL}) for the clips hosted on
two GitHub Pages repositories (hatsim-clips-a / hatsim-clips-b, ~1 GB limit per site).

  python make_clips_index.py --plans docs/plans.json \
      --base-a https://grafitctu.github.io/hatsim-clips-a/clips/ \
      --base-b https://grafitctu.github.io/hatsim-clips-b/clips/ \
      [--split-list clips_in_b.txt] [--out docs/clips_index.json]

Without --split-list the sorted clip ids are split in halves (first half -> A, second -> B); the
same split is written to clips_split.csv so that the files can be copied into the two repositories
(web/clips/<id>.mp4 -> <repo>/clips/<id>.mp4). For local tests use --local ./clips_test (3 noise clips).
"""
import argparse, csv, json, os

def clip_ids(plans):
    ids = set()
    for t in plans.get("practice", []):
        ids |= {t["anchor"], t["B"], t["C"]}
    for p in plans["plans"]:
        for t in p["trials"]:
            ids |= {t["anchor"], t["B"], t["C"]}
    return sorted(ids)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plans", default=os.path.join("docs", "plans.json"))
    ap.add_argument("--base-a", default="https://grafitctu.github.io/hatsim-clips-a/clips/")
    ap.add_argument("--base-b", default="https://grafitctu.github.io/hatsim-clips-b/clips/")
    ap.add_argument("--split-list", default=None, help="text file with clip ids that live in repository B")
    ap.add_argument("--local", default=None, help="local test mode: map every id onto noise{0,1,2}.mp4 in this folder")
    ap.add_argument("--out", default=os.path.join("docs", "clips_index.json"))
    a = ap.parse_args()
    with open(a.plans, encoding="utf-8") as fh:
        ids = clip_ids(json.load(fh))
    if a.local:
        index = {cid: "%s/noise%d.mp4" % (a.local.rstrip("/"), sum(map(ord, cid)) % 3) for cid in ids}
    else:
        if a.split_list:
            with open(a.split_list, encoding="utf-8") as fh:
                in_b = {l.strip() for l in fh if l.strip()}
        else:
            in_b = set(ids[len(ids) // 2:])
        index = {cid: (a.base_b if cid in in_b else a.base_a) + cid + ".mp4" for cid in ids}
        with open("clips_split.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["clip_id", "repo"])
            for cid in ids:
                w.writerow([cid, "B" if cid in in_b else "A"])
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=0)
    print("%d clip ids -> %s" % (len(index), a.out))

if __name__ == "__main__":
    main()
