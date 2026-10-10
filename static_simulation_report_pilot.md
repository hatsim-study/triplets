# Static deployment – plan assignment simulation report

Backend: `http://127.0.0.1:8787/exec`, mode: pilot, sessions requested: 8 (+0 top-up), dropout: 0.00, seed: 2, elapsed: 2.8 s

Session outcomes: {'ok': 8}


## Checks

| # | rule | result | detail |
|---|---|---|---|
| V1 | second session from the same round as the first | **PASS** | observers_with_2_sessions=0 round_mismatch=0 |
| V2 | max 1 completed sessions per observer | **PASS** | max=1 observers=8 |
| V3 | no observer saw a triplet twice (repeats excluded) | **PASS** | violations=0 |
| V4 | panel-2 observers disjoint from panel-1 observers per triplet | **PASS** | triplets_with_panel2=0 overlap=0 |
| V5 | every plan of the PILOT rounds has >= 1 completed session | **PASS** | plans=3 completed=3 uncovered_by_round={} |
| V6 | trial rows idempotent and complete for completed sessions | **PASS** | trial_rows=160 duplicate_keys=0 completed_sessions_missing_trials=0 |
| V7 | plans of abandoned/expired sessions were re-issued and completed | **PASS** | abandoned_or_stale=0 later_completed=0 |

## Totals

| quantity | value |
|---|---|
| sessions_rows | 8 |
| completed_sessions | 8 |
| observers | 8 |
| trial_rows | 160 |

## Plans per round

| round | plans | completed |
|---|---|---|
| P1 | 3 | 0 |
| P2 | 3 | 0 |
| P3 | 3 | 0 |
| P4 | 3 | 0 |
| P5 | 3 | 0 |
| P6 | 3 | 0 |
| P7 | 3 | 0 |
| PILOT | 3 | 3 |
| R1 | 27 | 0 |
| R2 | 27 | 0 |
| R3 | 27 | 0 |
| R4 | 27 | 0 |
| R5 | 27 | 0 |
| R6 | 27 | 0 |
| R7 | 27 | 0 |

## Backend status

```json
{
 "generated_utc": "2026-10-10T11:24:23.805Z",
 "plans_total": 213,
 "plans_completed": 3,
 "plans_reserved": 0,
 "rounds": {
  "R1": {
   "plans": 27,
   "completed": 0,
   "active": 0,
   "panel": 1,
   "mode": "main"
  },
  "R2": {
   "plans": 27,
   "completed": 0,
   "active": 0,
   "panel": 1,
   "mode": "main"
  },
  "R3": {
   "plans": 27,
   "completed": 0,
   "active": 0,
   "panel": 1,
   "mode": "main"
  },
  "R4": {
   "plans": 27,
   "completed": 0,
   "active": 0,
   "panel": 1,
   "mode": "main"
  },
  "R5": {
   "plans": 27,
   "completed": 0,
   "active": 0,
   "panel": 1,
   "mode": "main"
  },
  "R6": {
   "plans": 27,
   "completed": 0,
   "active": 0,
   "panel": 1,
   "mode": "main"
  },
  "R7": {
   "plans": 27,
   "completed": 0,
   "active": 0,
   "panel": 1,
   "mode": "main"
  },
  "P1": {
   "plans": 3,
   "completed": 0,
   "active": 0,
   "panel": 2,
   "mode": "main"
  },
  "P2": {
   "plans": 3,
   "completed": 0,
   "active": 0,
   "panel": 2,
   "mode": "main"
  },
  "P3": {
   "plans": 3,
   "completed": 0,
   "active": 0,
   "panel": 2,
   "mode": "main"
  },
  "P4": {
   "plans": 3,
   "completed": 0,
   "active": 0,
   "panel": 2,
   "mode": "main"
  },
  "P5": {
   "plans": 3,
   "completed": 0,
   "active": 0,
   "panel": 2,
   "mode": "main"
  },
  "P6": {
   "plans": 3,
   "completed": 0,
   "active": 0,
   "panel": 2,
   "mode": "main"
  },
  "P7": {
   "plans": 3,
   "completed": 0,
   "active": 0,
   "panel": 2,
   "mode": "main"
  },
  "PILOT": {
   "plans": 3,
   "completed": 3,
   "active": 0,
   "panel": 1,
   "mode": "pilot"
  }
 },
 "n_trial_rows": 160,
 "n_plan_usage_rows": 16,
 "observers": 8,
 "reservation_min": 90.0
}
```
