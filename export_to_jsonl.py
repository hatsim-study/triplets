#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_to_jsonl.py – convert the Apps Script export (JSON from ?action=export&token=…, or the
sheets downloaded as CSV) into sessions.jsonl + trials.jsonl in the analysis format used by qc.py.

  python export_to_jsonl.py --json export.json --out analysis_data/
  python export_to_jsonl.py --csv-dir sheets_csv/ --out analysis_data/     (files sessions.csv, trials.csv, practice.csv, plan_usage.csv)

sessions.jsonl : ONE row per session = last known state (session_start merged with session_end;
                 a session without session_end gets completed=false, n_trials_done = number of trial rows).
                 `study` = "mixed" | "grass" (derived from plan_id for rows written before the grass study).
trials.jsonl   : one row per (session_id, trial_index), duplicates dropped (first row wins), `study_part` = mixed|grass,
                 JSON-typed columns (loop_phase_ms, screen, flags) parsed back to objects,
                 server_received_utc = sheet timestamp `ts`.
practice_trials.jsonl and plan_usage.jsonl are written as well.
"""
import argparse
import csv
import json
import os
import sys

JSON_COLS = {"loop_phase_ms", "screen", "flags", "demographics"}
BOOL_COLS = {"is_repeat", "is_attention", "completed"}
INT_COLS = {"trial_index", "rt_ms", "panel", "playback_errors", "n_trials_target", "n_trials_done", "session_number_for_observer"}


def coerce(row):
    out = {}
    for k, v in row.items():
        if v is None:
            out[k] = None
            continue
        if isinstance(v, str):
            s = v.strip()
            if s == "":
                out[k] = None
                continue
            if k in JSON_COLS:
                try:
                    out[k] = json.loads(s)
                except ValueError:
                    out[k] = s
                continue
            if k in BOOL_COLS:
                out[k] = s.lower() in ("true", "1", "yes")
                continue
            if k in INT_COLS:
                try:
                    out[k] = int(float(s))
                except ValueError:
                    out[k] = s
                continue
            if k == "repeat_of_trial_index":
                try:
                    out[k] = int(float(s))
                except ValueError:
                    out[k] = None
                continue
            out[k] = s
        else:
            out[k] = v
    if "repeat_of_trial_index" in out and out["repeat_of_trial_index"] in ("", None):
        out["repeat_of_trial_index"] = None
    return out


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    return {k: [coerce(r) for r in d.get(k, [])] for k in ("sessions", "trials", "practice", "plan_usage")}


def load_csv_dir(d):
    out = {}
    for name in ("sessions", "trials", "practice", "plan_usage"):
        p = os.path.join(d, name + ".csv")
        rows = []
        if os.path.exists(p):
            with open(p, newline="", encoding="utf-8-sig") as fh:
                rows = [coerce(r) for r in csv.DictReader(fh)]
        out[name] = rows
    return out


TRIAL_FIELDS = ["session_id", "observer_id", "trial_index", "triplet_id", "study", "anchor_clip", "left_clip", "right_clip",
                "B_side", "response", "chosen_clip", "rt_ms", "loop_phase_ms", "is_repeat", "repeat_of_trial_index",
                "is_attention", "panel", "playback_errors", "timestamp_utc", "ui_lang", "screen", "flags", "plan_id", "round",
                "study_part", "server_received_utc"]
SESSION_FIELDS = ["session_id", "observer_id", "session_number_for_observer", "consent_version", "consent_ts", "demographics",
                  "start_ts", "end_ts", "completed", "n_trials_target", "n_trials_done", "user_agent", "completion_code",
                  "ui_lang", "mode", "plan_id", "round", "study", "valid", "end_reason"]


def study_of_plan(pid):
    """Study of a plan id: G* -> grass, everything else -> mixed (rows written before the grass study have no study column)."""
    return "grass" if str(pid or "").startswith("G") else "mixed"


def convert(data, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    # trials: dedupe
    seen = set()
    trials = []
    for r in sorted(data["trials"], key=lambda x: (x.get("ts") or "")):
        key = (r.get("session_id"), r.get("trial_index"))
        if key in seen or r.get("session_id") is None:
            continue
        seen.add(key)
        rec = {k: r.get(k) for k in TRIAL_FIELDS}
        rec["server_received_utc"] = r.get("ts")
        rec["loop_phase_ms"] = rec["loop_phase_ms"] or {"anchor": 0, "left": 0, "right": 0}
        rec["screen"] = rec["screen"] or {"w": 0, "h": 0, "dpr": 1.0}
        rec["flags"] = rec["flags"] or []
        rec["is_repeat"] = bool(rec["is_repeat"])
        rec["is_attention"] = bool(rec["is_attention"])
        rec["panel"] = int(rec["panel"] or 1)
        rec["study_part"] = rec.get("study_part") if rec.get("study_part") in ("mixed", "grass") else study_of_plan(rec.get("plan_id"))
        trials.append(rec)
    n_by_sess = {}
    for r in trials:
        n_by_sess[r["session_id"]] = n_by_sess.get(r["session_id"], 0) + 1
    # sessions: merge start + end
    sess = {}
    for r in sorted(data["sessions"], key=lambda x: (x.get("ts") or "")):
        sid = r.get("session_id")
        if not sid:
            continue
        cur = sess.setdefault(sid, {})
        for k in SESSION_FIELDS:
            v = r.get(k)
            if v is not None or k not in cur:
                cur[k] = v
        cur["_type"] = r.get("type")
    sessions = []
    for sid, cur in sess.items():
        cur["completed"] = bool(cur.get("completed")) and cur.get("_type") == "session_end"
        cur["n_trials_done"] = n_by_sess.get(sid, 0)
        cur["study"] = cur.get("study") if cur.get("study") in ("mixed", "grass") else study_of_plan(cur.get("plan_id"))
        cur["valid"] = True
        if not cur["completed"]:
            cur["end_reason"] = cur.get("end_reason") or "no_session_end"
        cur.pop("_type", None)
        sessions.append(cur)
    # sessions that only appear in trials (session_start lost)
    for sid in n_by_sess:
        if sid not in sess:
            r0 = next(r for r in trials if r["session_id"] == sid)
            sessions.append({"session_id": sid, "observer_id": r0["observer_id"], "session_number_for_observer": None,
                             "consent_version": None, "consent_ts": None, "demographics": {}, "start_ts": None, "end_ts": None,
                             "completed": False, "n_trials_target": None, "n_trials_done": n_by_sess[sid], "user_agent": None,
                             "completion_code": None, "ui_lang": r0.get("ui_lang"), "mode": None, "plan_id": r0.get("plan_id"),
                             "round": r0.get("round"), "study": study_of_plan(r0.get("plan_id")), "valid": True, "end_reason": "no_session_rows"})
    with open(os.path.join(out_dir, "trials.jsonl"), "w", encoding="utf-8") as fh:
        for r in trials:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(out_dir, "sessions.jsonl"), "w", encoding="utf-8") as fh:
        for r in sessions:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(out_dir, "practice_trials.jsonl"), "w", encoding="utf-8") as fh:
        for r in data["practice"]:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(out_dir, "plan_usage.jsonl"), "w", encoding="utf-8") as fh:
        for r in data["plan_usage"]:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(sessions), len(trials)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--json", help="JSON export from ?action=export&token=…")
    g.add_argument("--csv-dir", help="directory with sessions.csv, trials.csv, practice.csv, plan_usage.csv")
    ap.add_argument("--out", default="analysis_data")
    a = ap.parse_args()
    data = load_json(a.json) if a.json else load_csv_dir(a.csv_dir)
    ns, nt = convert(data, a.out)
    print("sessions.jsonl: %d rows, trials.jsonl: %d rows -> %s" % (ns, nt, a.out))


if __name__ == "__main__":
    main()
