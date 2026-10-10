# Static deployment – plan assignment simulation report

Backend: `http://127.0.0.1:8787/exec`, mode: main, sessions requested: 230 (+40 top-up), dropout: 0.05, seed: 1, elapsed: 198.5 s

Session outcomes: {'ok': 210, 'dropped': 12, 'no_plan_available': 12, 'max_sessions': 36}


## Checks

| # | rule | result | detail |
|---|---|---|---|
| V1 | second session from the same round as the first | **PASS** | observers_with_2_sessions=75 round_mismatch=0 |
| V2 | max 2 completed sessions per observer | **PASS** | max=2 observers=135 |
| V3 | no observer saw a triplet twice (repeats excluded) | **PASS** | violations=0 |
| V4 | panel-2 observers disjoint from panel-1 observers per triplet | **PASS** | triplets_with_panel2=158 overlap=0 |
| V5 | every plan of the R/P rounds has >= 1 completed session | **PASS** | plans=210 completed=210 uncovered_by_round={} |
| V6 | trial rows idempotent and complete for completed sessions | **PASS** | trial_rows=13111 duplicate_keys=0 completed_sessions_missing_trials=0 |
| V7 | plans of abandoned/expired sessions were re-issued and completed | **PASS** | abandoned_or_stale=12 later_completed=12 |

## Totals

| quantity | value |
|---|---|
| sessions_rows | 222 |
| completed_sessions | 210 |
| observers | 135 |
| trial_rows | 13111 |

## Plans per round

| round | plans | completed |
|---|---|---|
| P1 | 3 | 3 |
| P2 | 3 | 3 |
| P3 | 3 | 3 |
| P4 | 3 | 3 |
| P5 | 3 | 3 |
| P6 | 3 | 3 |
| P7 | 3 | 3 |
| PILOT | 3 | 0 |
| R1 | 27 | 27 |
| R2 | 27 | 27 |
| R3 | 27 | 27 |
| R4 | 27 | 27 |
| R5 | 27 | 27 |
| R6 | 27 | 27 |
| R7 | 27 | 27 |

## Backend status

```json
{
 "generated_utc": "2026-10-10T11:21:42.847Z",
 "plans_total": 213,
 "plans_completed": 210,
 "plans_reserved": 0,
 "rounds": {
  "R1": {
   "plans": 27,
   "completed": 27,
   "active": 0,
   "panel": 1,
   "mode": "main"
  },
  "R2": {
   "plans": 27,
   "completed": 27,
   "active": 0,
   "panel": 1,
   "mode": "main"
  },
  "R3": {
   "plans": 27,
   "completed": 27,
   "active": 0,
   "panel": 1,
   "mode": "main"
  },
  "R4": {
   "plans": 27,
   "completed": 27,
   "active": 0,
   "panel": 1,
   "mode": "main"
  },
  "R5": {
   "plans": 27,
   "completed": 27,
   "active": 0,
   "panel": 1,
   "mode": "main"
  },
  "R6": {
   "plans": 27,
   "completed": 27,
   "active": 0,
   "panel": 1,
   "mode": "main"
  },
  "R7": {
   "plans": 27,
   "completed": 27,
   "active": 0,
   "panel": 1,
   "mode": "main"
  },
  "P1": {
   "plans": 3,
   "completed": 3,
   "active": 0,
   "panel": 2,
   "mode": "main"
  },
  "P2": {
   "plans": 3,
   "completed": 3,
   "active": 0,
   "panel": 2,
   "mode": "main"
  },
  "P3": {
   "plans": 3,
   "completed": 3,
   "active": 0,
   "panel": 2,
   "mode": "main"
  },
  "P4": {
   "plans": 3,
   "completed": 3,
   "active": 0,
   "panel": 2,
   "mode": "main"
  },
  "P5": {
   "plans": 3,
   "completed": 3,
   "active": 0,
   "panel": 2,
   "mode": "main"
  },
  "P6": {
   "plans": 3,
   "completed": 3,
   "active": 0,
   "panel": 2,
   "mode": "main"
  },
  "P7": {
   "plans": 3,
   "completed": 3,
   "active": 0,
   "panel": 2,
   "mode": "main"
  },
  "PILOT": {
   "plans": 3,
   "completed": 0,
   "active": 0,
   "panel": 1,
   "mode": "pilot"
  }
 },
 "n_trial_rows": 13111,
 "n_plan_usage_rows": 432,
 "observers": 135,
 "reservation_min": 0.05
}
```
