# Static deployment – plan assignment simulation report

Backend: `http://127.0.0.1:8787/exec`, mode: main, sessions requested: 260 (+30 top-up), dropout: 0.04, seed: 3, elapsed: 149.6 s

Session outcomes (study, result): {'grass/ok': 154, 'mixed/ok': 103, 'mixed/dropped': 7, 'grass/dropped': 7, 'grass/no_plan_available': 19}


## Checks

| # | rule | result | detail |
|---|---|---|---|
| V1 | second session from the same round as the first (per study) | **PASS** | observer-study pairs with 2 sessions=81 round_mismatch=0 |
| V2 | max 2 completed sessions per observer and study (mixed pilot: 1) | **PASS** | max={'mixed': 2, 'grass': 2} observers=140 observers_with_both_studies=36 |
| V3 | no observer saw a triplet twice (repeats excluded) | **PASS** | violations=0 |
| V4 | panel-2 observers disjoint from panel-1 observers per triplet | **PASS** | triplets_with_panel2=278 overlap=0 |
| V5 | every plan of the required studies (grass) has >= 1 completed session | **PASS** | plans=154 completed=154 uncovered_by_round={} |
| V6 | trial rows idempotent and complete for completed sessions | **PASS** | trial_rows=12434 duplicate_keys=0 completed_sessions_missing_trials=0 |
| V7 | plans of abandoned/expired sessions were re-issued and completed (required studies) | **PASS** | abandoned_or_stale=7 later_completed=7 |

## Totals

| quantity | value |
|---|---|
| sessions_rows | 271 |
| completed_sessions | 257 |
| completed_by_study | {'grass': 154, 'mixed': 103} |
| observers | 140 |
| observers_with_both_studies | 36 |
| trial_rows | 12434 |

## Plans per round

| round | plans | completed |
|---|---|---|
| GP1 | 4 | 4 |
| GP2 | 4 | 4 |
| GP3 | 4 | 4 |
| GP4 | 4 | 4 |
| GP5 | 4 | 4 |
| GP6 | 4 | 4 |
| GP7 | 4 | 4 |
| GR1 | 18 | 18 |
| GR2 | 18 | 18 |
| GR3 | 18 | 18 |
| GR4 | 18 | 18 |
| GR5 | 18 | 18 |
| GR6 | 18 | 18 |
| GR7 | 18 | 18 |
| P1 | 3 | 3 |
| P2 | 3 | 3 |
| P3 | 3 | 3 |
| P4 | 3 | 3 |
| P5 | 3 | 2 |
| P6 | 3 | 0 |
| P7 | 3 | 1 |
| PILOT | 3 | 0 |
| R1 | 27 | 18 |
| R2 | 27 | 15 |
| R3 | 27 | 12 |
| R4 | 27 | 12 |
| R5 | 27 | 9 |
| R6 | 27 | 11 |
| R7 | 27 | 11 |

## Backend status

```json
{
 "generated_utc": "2026-10-13T20:41:32.501Z",
 "plans_total": 367,
 "plans_completed": 257,
 "plans_reserved": 0,
 "studies": {
  "mixed": {
   "plans": 213,
   "completed": 103,
   "active": 0
  },
  "grass": {
   "plans": 154,
   "completed": 154,
   "active": 0
  }
 },
 "rounds": {
  "R1": {
   "plans": 27,
   "completed": 18,
   "active": 0,
   "panel": 1,
   "mode": "main",
   "study": "mixed"
  },
  "R2": {
   "plans": 27,
   "completed": 15,
   "active": 0,
   "panel": 1,
   "mode": "main",
   "study": "mixed"
  },
  "R3": {
   "plans": 27,
   "completed": 12,
   "active": 0,
   "panel": 1,
   "mode": "main",
   "study": "mixed"
  },
  "R4": {
   "plans": 27,
   "completed": 12,
   "active": 0,
   "panel": 1,
   "mode": "main",
   "study": "mixed"
  },
  "R5": {
   "plans": 27,
   "completed": 9,
   "active": 0,
   "panel": 1,
   "mode": "main",
   "study": "mixed"
  },
  "R6": {
   "plans": 27,
   "completed": 11,
   "active": 0,
   "panel": 1,
   "mode": "main",
   "study": "mixed"
  },
  "R7": {
   "plans": 27,
   "completed": 11,
   "active": 0,
   "panel": 1,
   "mode": "main",
   "study": "mixed"
  },
  "P1": {
   "plans": 3,
   "completed": 3,
   "active": 0,
   "panel": 2,
   "mode": "main",
   "study": "mixed"
  },
  "P2": {
   "plans": 3,
   "completed": 3,
   "active": 0,
   "panel": 2,
   "mode": "main",
   "study": "mixed"
  },
  "P3": {
   "plans": 3,
   "completed": 3,
   "active": 0,
   "panel": 2,
   "mode": "main",
   "study": "mixed"
  },
  "P4": {
   "plans": 3,
   "completed": 3,
   "active": 0,
   "panel": 2,
   "mode": "main",
   "study": "mixed"
  },
  "P5": {
   "plans": 3,
   "completed": 2,
   "active": 0,
   "panel": 2,
   "mode": "main",
   "study": "mixed"
  },
  "P6": {
   "plans": 3,
   "completed": 0,
   "active": 0,
   "panel": 2,
   "mode": "main",
   "study": "mixed"
  },
  "P7": {
   "plans": 3,
   "completed": 1,
   "active": 0,
   "panel": 2,
   "mode": "main",
   "study": "mixed"
  },
  "PILOT": {
   "plans": 3,
   "completed": 0,
   "active": 0,
   "panel": 1,
   "mode": "pilot",
   "study": "mixed"
  },
  "GR1": {
   "plans": 18,
   "completed": 18,
   "active": 0,
   "panel": 1,
   "mode": "main",
   "study": "grass"
  },
  "GR2": {
   "plans": 18,
   "completed": 18,
   "active": 0,
   "panel": 1,
   "mode": "main",
   "study": "grass"
  },
  "GR3": {
   "plans": 18,
   "completed": 18,
   "active": 0,
   "panel": 1,
   "mode": "main",
   "study": "grass"
  },
  "GR4": {
   "plans": 18,
   "completed": 18,
   "active": 0,
   "panel": 1,
   "mode": "main",
   "study": "grass"
  },
  "GR5": {
   "plans": 18,
   "completed": 18,
   "active": 0,
   "panel": 1,
   "mode": "main",
   "study": "grass"
  },
  "GR6": {
   "plans": 18,
   "completed": 18,
   "active": 0,
   "panel": 1,
   "mode": "main",
   "study": "grass"
  },
  "GR7": {
   "plans": 18,
   "completed": 18,
   "active": 0,
   "panel": 1,
   "mode": "main",
   "study": "grass"
  },
  "GP1": {
   "plans": 4,
   "completed": 4,
   "active": 0,
   "panel": 2,
   "mode": "main",
   "study": "grass"
  },
  "GP2": {
   "plans": 4,
   "completed": 4,
   "active": 0,
   "panel": 2,
   "mode": "main",
   "study": "grass"
  },
  "GP3": {
   "plans": 4,
   "completed": 4,
   "active": 0,
   "panel": 2,
   "mode": "main",
   "study": "grass"
  },
  "GP4": {
   "plans": 4,
   "completed": 4,
   "active": 0,
   "panel": 2,
   "mode": "main",
   "study": "grass"
  },
  "GP5": {
   "plans": 4,
   "completed": 4,
   "active": 0,
   "panel": 2,
   "mode": "main",
   "study": "grass"
  },
  "GP6": {
   "plans": 4,
   "completed": 4,
   "active": 0,
   "panel": 2,
   "mode": "main",
   "study": "grass"
  },
  "GP7": {
   "plans": 4,
   "completed": 4,
   "active": 0,
   "panel": 2,
   "mode": "main",
   "study": "grass"
  }
 },
 "n_trial_rows": 12434,
 "n_plan_usage_rows": 528,
 "observers": 147,
 "reservation_min": 0.05
}
```
