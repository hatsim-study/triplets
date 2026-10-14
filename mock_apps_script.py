#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mock_apps_script.py – stdlib HTTP server that emulates the Google Apps Script backend
(apps_script/Code.gs) over JSONL files, and serves the static frontend (docs/) so the
whole study can be tested locally without Google.

  python mock_apps_script.py --port 8787 --data test_data [--docs docs] [--reservation-min 90]
  frontend: http://127.0.0.1:8787/            (set APPS_SCRIPT_URL in docs/config.js to http://127.0.0.1:8787/exec)
  API:      http://127.0.0.1:8787/exec?action=next_plan&observer_id=..&mode=main
            POST http://127.0.0.1:8787/exec   (text/plain JSON, same body as for Apps Script)

Sheets are files <data>/<sheet>.jsonl, one row per line (same columns as the Google Sheet).
"""
import argparse
import json
import mimetypes
import os
import random
import re
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

SHEETS = ("plans", "plan_usage", "sessions", "trials", "practice")


def study_of_plan(pid):
    return "grass" if str(pid or "").startswith("G") else "mixed"


def norm_study(s, pid):
    return s if s in ("grass", "mixed") else study_of_plan(pid)


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


class Store:
    def __init__(self, data_dir, reservation_min, admin_token):
        self.dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.lock = threading.RLock()
        self.reservation_min = reservation_min
        self.admin_token = admin_token
        self.rows = {s: self._read(s) for s in SHEETS}
        self.trial_keys = {(r["session_id"], int(r["trial_index"])) for r in self.rows["trials"]}

    def _read(self, sheet):
        p = os.path.join(self.dir, sheet + ".jsonl")
        if not os.path.exists(p):
            return []
        with open(p, encoding="utf-8") as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def append(self, sheet, row):
        row = dict(row)
        row["ts"] = utcnow()
        self.rows[sheet].append(row)
        with open(os.path.join(self.dir, sheet + ".jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    # ---- mirrors planState_ / nextPlan_ / status_ of Code.gs
    def plan_state(self):
        plans = {r["plan_id"]: {"round": str(r["round"]), "panel": int(r["panel"]), "mode": str(r.get("mode", "main")),
                                "study": norm_study(r.get("study"), r["plan_id"]),
                                "n_trials": int(r["n_trials"]), "completed": 0, "active": 0} for r in self.rows["plans"]}
        by_session = {}
        for u in self.rows["plan_usage"]:
            by_session[u["session_id"]] = u
        by_obs = {}
        cutoff = time.time() - self.reservation_min * 60
        for sid, u in by_session.items():
            st = u["status"]
            ts = datetime.strptime(u["ts"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).timestamp()
            if st == "reserved" and ts < cutoff:
                st = "expired"
            p = plans.get(u["plan_id"])
            study = norm_study(u.get("study"), u["plan_id"])
            mode = str(u.get("mode") or "main")
            counts_for_plan = not (study == "grass" and mode == "pilot")   # pilot grass sessions are excluded by the analysis
            if p and counts_for_plan:
                if st == "completed":
                    p["completed"] += 1
                elif st == "reserved":
                    p["active"] += 1
            by_obs.setdefault(u["observer_id"], []).append({"plan_id": u["plan_id"], "round": str(u["round"]),
                                                            "status": st, "session_id": sid, "study": study, "mode": mode})
        return plans, by_obs

    def next_plan(self, observer_id, mode, study=None, session_number=None):
        if not observer_id:
            return {"error": "missing_observer_id"}
        mode = "pilot" if mode == "pilot" else "main"
        study = "grass" if study == "grass" else "mixed"
        plans, by_obs = self.plan_state()
        hist = [u for u in by_obs.get(observer_id, []) if u["study"] == study]     # per study, incl. expired/abandoned
        prev = [u for u in hist if u["status"] in ("completed", "reserved")]
        max_sessions = 1 if (study == "mixed" and mode == "pilot") else 2
        for u in prev:
            if u["status"] == "reserved":
                return {"plan_id": u["plan_id"], "round": u["round"], "study": study, "session_id": u["session_id"],
                        "resumed": True, "session_number": len(prev)}
        if len(prev) >= max_sessions:
            return {"error": "max_sessions", "max_sessions": max_sessions, "sessions": len(prev), "study": study}
        rnd = hist[0]["round"] if hist else None       # abandoned sessions pin the round too
        used = {u["plan_id"] for u in hist}
        plan_mode = "main" if study == "grass" else mode
        reuse = (study == "mixed" and mode == "pilot")
        cands = [(pid, p["round"], p["completed"] + p["active"]) for pid, p in plans.items()
                 if p["study"] == study and p["mode"] == plan_mode and (rnd is None or p["round"] == rnd) and pid not in used
                 and (reuse or p["completed"] < 1)]
        if not cands:
            return {"error": "no_plan_available", "round": rnd, "study": study}
        m = min(c[2] for c in cands)
        pid, r, _ = random.choice([c for c in cands if c[2] == m])
        sid = "s_" + uuid.uuid4().hex
        self.append("plan_usage", {"plan_id": pid, "round": r, "session_id": sid, "observer_id": observer_id,
                                   "mode": mode, "status": "reserved", "study": study})
        return {"plan_id": pid, "round": r, "study": study, "session_id": sid, "resumed": False, "session_number": len(prev) + 1}

    def status(self):
        plans, by_obs = self.plan_state()
        by_round = {}
        by_study = {"mixed": {"plans": 0, "completed": 0, "active": 0}, "grass": {"plans": 0, "completed": 0, "active": 0}}
        total = done = active = 0
        for pid, p in plans.items():
            r = by_round.setdefault(p["round"], {"plans": 0, "completed": 0, "active": 0, "panel": p["panel"], "mode": p["mode"], "study": p["study"]})
            r["plans"] += 1
            r["completed"] += min(1, p["completed"])
            r["active"] += p["active"]
            s = by_study.setdefault(p["study"], {"plans": 0, "completed": 0, "active": 0})
            s["plans"] += 1
            s["completed"] += min(1, p["completed"])
            s["active"] += p["active"]
            total += 1
            done += min(1, p["completed"])
            active += p["active"]
        return {"generated_utc": utcnow(), "plans_total": total, "plans_completed": done, "plans_reserved": active,
                "studies": by_study, "rounds": by_round, "n_trial_rows": len(self.rows["trials"]), "n_plan_usage_rows": len(self.rows["plan_usage"]),
                "observers": len(by_obs), "reservation_min": self.reservation_min}

    def post(self, body):
        t = body.get("type")
        if t == "trial":
            if not body.get("session_id") or body.get("trial_index") is None:
                return {"error": "bad_record"}
            key = (body["session_id"], int(body["trial_index"]))
            if key in self.trial_keys:
                return {"ok": True, "duplicate": True}
            self.trial_keys.add(key)
            body = dict(body, study_part=norm_study(body.get("study_part"), body.get("plan_id")))
            self.append("trials", body)
            return {"ok": True}
        if t == "practice_trial":
            self.append("practice", body)
            return {"ok": True}
        if t == "session_start":
            self.append("sessions", dict(body, completed=False, study=norm_study(body.get("study"), body.get("plan_id"))))
            return {"ok": True}
        if t == "session_end":
            self.append("sessions", dict(body, study=norm_study(body.get("study"), body.get("plan_id"))))
            status = "completed" if body.get("completed") else "abandoned"
            self.append("plan_usage", {"plan_id": body.get("plan_id"), "round": body.get("round"), "session_id": body.get("session_id"),
                                       "observer_id": body.get("observer_id"), "mode": body.get("mode"), "status": status,
                                       "study": norm_study(body.get("study"), body.get("plan_id"))})
            return {"ok": True, "status": status}
        if t == "register_plans":
            if self.admin_token == "CHANGE_ME" or body.get("token") != self.admin_token:
                return {"error": "forbidden"}
            existing = {r["plan_id"] for r in self.rows["plans"]}
            n = 0
            for pl in body.get("plans", []):
                if pl["plan_id"] not in existing:
                    self.append("plans", dict({"mode": "main"}, **dict(pl, study=norm_study(pl.get("study"), pl["plan_id"]))))
                    existing.add(pl["plan_id"])
                    n += 1
            return {"ok": True, "added": n, "total": len(existing)}
        return {"error": "unknown_type"}


class Handler(BaseHTTPRequestHandler):
    store = None
    docs = None
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _json(self, obj, status=200):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path == "/exec":
            action = q.get("action", "health")
            with self.store.lock:
                if action == "health":
                    return self._json({"ok": True, "ts": utcnow()})
                if action == "next_plan":
                    return self._json(self.store.next_plan(q.get("observer_id"), q.get("mode"), q.get("study"), q.get("session_number")))
                if action == "status":
                    return self._json(self.store.status())
                if action == "export":
                    if self.store.admin_token == "CHANGE_ME" or q.get("token") != self.store.admin_token:
                        return self._json({"error": "forbidden"})
                    out = {s: self.store.rows[s] for s in SHEETS}
                    out["exported_utc"] = utcnow()
                    return self._json(out)
                return self._json({"error": "unknown_action"})
        # static frontend
        if not self.docs:
            return self._json({"error": "not_found"}, 404)
        rel = u.path.lstrip("/") or "index.html"
        p = os.path.normpath(os.path.join(self.docs, rel))
        if not p.startswith(os.path.normpath(self.docs)) or not os.path.isfile(p):
            return self._json({"error": "not_found"}, 404)
        size = os.path.getsize(p)
        ctype = mimetypes.guess_type(p)[0] or "application/octet-stream"
        start, end, status = 0, size - 1, 200
        rng = self.headers.get("Range")
        m = re.match(r"bytes=(\d*)-(\d*)", rng or "")
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else size - 1
            else:
                start = max(0, size - int(m.group(2)))
            end = min(end, size - 1)
            status = 206
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        if status == 206:
            self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
        self.end_headers()
        with open(p, "rb") as fh:
            fh.seek(start)
            self.wfile.write(fh.read(end - start + 1))

    def do_POST(self):
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        if u.path != "/exec":
            return self._json({"error": "not_found"}, 404)
        try:
            body = json.loads(raw.decode("utf-8"))
        except ValueError:
            return self._json({"error": "bad_json"})
        with self.store.lock:
            return self._json(self.store.post(body))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data"))
    ap.add_argument("--docs", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs"))
    ap.add_argument("--reservation-min", type=float, default=90.0)
    ap.add_argument("--admin-token", default="testtoken")
    ap.add_argument("--register", default=None, action="append",
                    help="plan index to register at start-up (plan_index.json, plan_index_grass.json or plans*.json); repeatable")
    a = ap.parse_args()
    Handler.store = Store(a.data, a.reservation_min, a.admin_token)
    Handler.docs = a.docs if os.path.isdir(a.docs) else None
    for reg in (a.register or []):
        with open(reg, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and "plans" in data:      # a plans*.json file -> index entries
            data = [{"plan_id": p["plan_id"], "round": p["round"], "panel": p["panel"], "n_trials": p["n_trials"],
                     "mode": "pilot" if p["round"] == "PILOT" else "main", "study": p.get("study") or study_of_plan(p["plan_id"])}
                    for p in data["plans"]]
        res = Handler.store.post({"type": "register_plans", "token": a.admin_token, "plans": data})
        sys.stderr.write("register_plans %s: %s\n" % (reg, res))
    httpd = ThreadingHTTPServer((a.host, a.port), Handler)
    httpd.daemon_threads = True
    sys.stderr.write("mock Apps Script at http://%s:%d/exec  (frontend: http://%s:%d/)\n" % (a.host, a.port, a.host, a.port))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
