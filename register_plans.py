#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
register_plans.py – register the plan index in the Apps Script backend (sheet "plans") so that
?action=next_plan can hand plans out. Idempotent (existing plan ids are skipped). Also used for
top-up plans (plans_topup_index.csv) and for the grass study (plan_index_grass.json or docs/plans_grass.json
directly; the `study` column is filled from the plan id). Alternative without Python: import plan_index.csv /
plan_index_grass.csv into the sheet "plans" manually (File -> Import -> Append to current sheet).

  python register_plans.py --url https://script.google.com/macros/s/…/exec --token ADMIN_TOKEN [--index plan_index.json]
"""
import argparse, csv, json, os, urllib.request

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--token", required=True)
    ap.add_argument("--index", default="plan_index.json", help=".json (list of dicts) or .csv with plan_id,round,panel,n_trials,mode")
    ap.add_argument("--chunk", type=int, default=100)
    ap.add_argument("--no-proxy", action="store_true", help="ignore HTTP(S)_PROXY environment variables")
    a = ap.parse_args()
    if a.index.endswith(".csv"):
        with open(a.index, newline="", encoding="utf-8") as fh:
            plans = [dict(r, panel=int(r["panel"]), n_trials=int(r["n_trials"])) for r in csv.DictReader(fh)]
    else:
        with open(a.index, encoding="utf-8") as fh:
            plans = json.load(fh)
        if isinstance(plans, dict) and "plans" in plans:      # a plans*.json file (e.g. plans_grass.json) -> index entries
            plans = [{"plan_id": p["plan_id"], "round": p["round"], "panel": p["panel"], "n_trials": p["n_trials"],
                      "mode": "pilot" if p["round"] == "PILOT" else "main",
                      "study": p.get("study") or ("grass" if p["plan_id"].startswith("G") else "mixed")} for p in plans["plans"]]
    for p in plans:                                             # study column (rows without it = mixed)
        p.setdefault("study", "grass" if str(p["plan_id"]).startswith("G") else "mixed")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({})) if a.no_proxy else urllib.request.build_opener()
    for i in range(0, len(plans), a.chunk):
        body = {"type": "register_plans", "token": a.token, "plans": plans[i:i + a.chunk]}
        req = urllib.request.Request(a.url, data=json.dumps(body).encode("utf-8"), method="POST")
        req.add_header("Content-Type", "text/plain;charset=utf-8")
        with opener.open(req, timeout=120) as r:
            print(i, r.read().decode("utf-8"))

if __name__ == "__main__":
    main()
