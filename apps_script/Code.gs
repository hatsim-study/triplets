/**
 * HAT-SIM triplet study – Google Apps Script backend (web app with a configured Google Sheet).
 *
 * Sheets (created by setupSheets() or on first use):
 *   plans       plan_id, round, panel, n_trials, mode              – registered plan index (from plan_index.csv)
 *   plan_usage  ts, plan_id, round, session_id, observer_id, mode, status   (reserved | completed | abandoned)
 *   sessions    one row per event (session_start / session_end); last row per session_id = state
 *   trials      one row per trial (idempotent on session_id + trial_index)
 *   practice    practice trials
 *
 * GET  ?action=next_plan&observer_id=..&mode=pilot|main&study=mixed|grass&session_number=1|2
 *                                                                         -> {plan_id, round, study, session_id}
 *      Two studies share the backend: "mixed" (plans.json, plan ids R.., P.., PILOT_..) and "grass"
 *      (plans_grass.json, plan ids G..). Counters, the same-round rule and the session limit are
 *      kept per study. Rows written before the grass study have no `study` column -> treated as "mixed".
 * GET  ?action=status                                                        -> coverage
 * GET  ?action=export&token=ADMIN_TOKEN                                      -> JSON of all sheets
 * GET  ?action=health
 * POST (Content-Type: text/plain, JSON body)  {type: "trial"|"session_start"|"session_end"|"practice_trial"
 *                                              |"register_plans", ...}
 *
 * Privacy: no IP address, no e-mail, no Google account is recorded (deploy as "Execute as: Me",
 * "Who has access: Anyone"). The client sends only a random observer_id and a sha256 of its user agent.
 */

var ADMIN_TOKEN = PropertiesService.getScriptProperties().getProperty('ADMIN_TOKEN') || 'CHANGE_ME';
var RESERVATION_MIN = 90;          // a reserved plan is released after this many minutes without completion
var MAX_SESSIONS = 2;              // per observer AND per study (2 mixed + 2 grass)
var PILOT_MAX_SESSIONS = 1;        // PILOT plans overlap in triplets -> one session per pilot observer;
                                   // PILOT plans are reused (least-used first) until the pilot is stopped

var HEADERS = {
  // NOTE: new columns are only ever APPENDED (sheet_() adds missing header cells to existing sheets)
  plans: ['plan_id', 'round', 'panel', 'n_trials', 'mode', 'study'],
  plan_usage: ['ts', 'plan_id', 'round', 'session_id', 'observer_id', 'mode', 'status', 'study'],
  sessions: ['ts', 'type', 'session_id', 'observer_id', 'session_number_for_observer', 'plan_id', 'round', 'mode',
             'consent_version', 'consent_ts', 'demographics', 'start_ts', 'end_ts', 'completed', 'n_trials_target',
             'n_trials_done', 'user_agent', 'completion_code', 'ui_lang', 'end_reason', 'study'],
  trials: ['ts', 'session_id', 'observer_id', 'trial_index', 'triplet_id', 'study', 'anchor_clip', 'left_clip',
           'right_clip', 'B_side', 'response', 'chosen_clip', 'rt_ms', 'loop_phase_ms', 'is_repeat',
           'repeat_of_trial_index', 'is_attention', 'panel', 'playback_errors', 'timestamp_utc', 'ui_lang',
           'screen', 'flags', 'plan_id', 'round', 'study_part'],
  practice: ['ts', 'session_id', 'observer_id', 'trial_index', 'triplet_id', 'response', 'rt_ms',
             'playback_errors', 'timestamp_utc', 'flags']
};

// ---------------------------------------------------------------- helpers
function ss_() {
  var id = PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID');
  if (!id) { throw new Error('Missing SPREADSHEET_ID script property'); }
  return SpreadsheetApp.openById(id);
}

function sheet_(name) {
  var ss = ss_();
  var sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    sh.appendRow(HEADERS[name]);
    sh.setFrozenRows(1);
  } else if (sh.getLastRow() >= 1) {
    // header migration: append header cells for columns added later (e.g. `study`)
    var want = HEADERS[name];
    var have = sh.getRange(1, 1, 1, Math.max(1, sh.getLastColumn())).getValues()[0].map(String);
    var missing = want.filter(function (h) { return have.indexOf(h) < 0; });
    if (missing.length) { sh.getRange(1, have.length + 1, 1, missing.length).setValues([missing]); }
  }
  return sh;
}

function studyOfPlan_(pid) { return (String(pid || '').charAt(0) === 'G') ? 'grass' : 'mixed'; }
function normStudy_(s, pid) { return s === 'grass' || s === 'mixed' ? s : studyOfPlan_(pid); }

function setupSheets() {            // run once from the editor (optional – sheets are also created lazily)
  Object.keys(HEADERS).forEach(function (n) { sheet_(n); });
}

function rows_(name) {               // -> array of objects
  var sh = sheet_(name);
  var vals = sh.getDataRange().getValues();
  if (vals.length < 2) { return []; }
  var head = vals[0];
  var out = [];
  for (var i = 1; i < vals.length; i++) {
    var o = {};
    for (var j = 0; j < head.length; j++) { o[head[j]] = vals[i][j]; }
    out.push(o);
  }
  return out;
}

function cell_(v) {                  // objects/arrays -> JSON string; keep primitives
  if (v === undefined || v === null) { return ''; }
  if (typeof v === 'object') { return JSON.stringify(v); }
  return v;
}

function appendRow_(name, obj) {
  var sh = sheet_(name);
  // write in the order of the sheet's header row (which may differ from HEADERS on migrated sheets)
  var head = sh.getLastColumn() >= 1 ? sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0].map(String) : HEADERS[name];
  var row = head.map(function (k) { return k === 'ts' ? new Date().toISOString() : cell_(obj[k]); });
  sh.appendRow(row);
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function withLock_(fn) {
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try { return fn(); } finally { lock.releaseLock(); }
}

function nowMs_() { return new Date().getTime(); }

// ---------------------------------------------------------------- plan assignment
function planState_() {
  // -> {plans: {plan_id: {round, panel, mode, n_trials, completed, active}}, byObserver: {observer_id: [usage rows]}}
  var plans = {};
  rows_('plans').forEach(function (p) {
    plans[p.plan_id] = { round: String(p.round), panel: Number(p.panel), mode: String(p.mode || 'main'),
                         study: normStudy_(p.study, p.plan_id), n_trials: Number(p.n_trials), completed: 0, active: 0 };
  });
  var bySession = {};
  var usage = rows_('plan_usage');
  usage.forEach(function (u) { bySession[u.session_id] = u; });   // last row per session wins
  var byObserver = {};
  var cutoff = nowMs_() - RESERVATION_MIN * 60 * 1000;
  Object.keys(bySession).forEach(function (sid) {
    var u = bySession[sid];
    var p = plans[u.plan_id];
    var st = String(u.status);
    var ts = new Date(u.ts).getTime();
    if (st === 'reserved' && ts < cutoff) { st = 'expired'; }
    var study = normStudy_(u.study, u.plan_id);
    var mode = String(u.mode || 'main');
    // grass sessions run in pilot mode are excluded by the analysis -> they do not count as plan completions
    var countsForPlan = !(study === 'grass' && mode === 'pilot');
    if (p && countsForPlan) {
      if (st === 'completed') { p.completed += 1; }
      else if (st === 'reserved') { p.active += 1; }
    }
    // expired/abandoned sessions do not count toward the session limit, but they pin the observer's round
    // (the observer may have seen part of that plan) and block re-issuing the same plan to them
    (byObserver[u.observer_id] = byObserver[u.observer_id] || []).push({ plan_id: u.plan_id, round: String(u.round), status: st,
                                                                        session_id: sid, study: study, mode: mode });
  });
  return { plans: plans, byObserver: byObserver };
}

function nextPlan_(observerId, mode, study, sessionNumber) {
  if (!observerId) { return { error: 'missing_observer_id' }; }
  mode = mode === 'pilot' ? 'pilot' : 'main';
  study = study === 'grass' ? 'grass' : 'mixed';
  var st = planState_();
  // sessions of this observer IN THIS STUDY (any mode): limit and same-round rule are per study
  var hist = (st.byObserver[observerId] || []).filter(function (u) { return u.study === study; });
  var prev = hist.filter(function (u) { return u.status === 'completed' || u.status === 'reserved'; });
  var maxSessions = (study === 'mixed' && mode === 'pilot') ? PILOT_MAX_SESSIONS : MAX_SESSIONS;
  // an unfinished reservation of this observer in this study -> resume it
  for (var i = 0; i < prev.length; i++) {
    if (prev[i].status === 'reserved') {
      return { plan_id: prev[i].plan_id, round: prev[i].round, study: study, session_id: prev[i].session_id, resumed: true,
               session_number: prev.length };
    }
  }
  if (prev.length >= maxSessions) { return { error: 'max_sessions', max_sessions: maxSessions, sessions: prev.length, study: study }; }
  var round = hist.length ? hist[0].round : null;      // same round as the first plan ever given (within the study), incl. abandoned
  var usedPlans = {};
  hist.forEach(function (u) { usedPlans[u.plan_id] = true; });
  // plan pool: mixed -> plans of the requested mode (PILOT_.. in pilot, R../P.. in main);
  //            grass -> always the GR../GP.. plans (there are no pilot grass plans; the session row carries mode "pilot")
  var planMode = study === 'grass' ? 'main' : mode;
  var reuse = (study === 'mixed' && mode === 'pilot');  // PILOT plans are reused; every other plan needs exactly one completion
  var cands = [];
  Object.keys(st.plans).forEach(function (pid) {
    var p = st.plans[pid];
    if (p.study !== study || p.mode !== planMode) { return; }
    if (round !== null && p.round !== round) { return; }
    if (usedPlans[pid]) { return; }
    if (!reuse && p.completed >= 1) { return; }
    cands.push({ plan_id: pid, round: p.round, usage: p.completed + p.active });
  });
  if (!cands.length) { return { error: 'no_plan_available', round: round, study: study }; }
  var minUsage = Math.min.apply(null, cands.map(function (c) { return c.usage; }));
  cands = cands.filter(function (c) { return c.usage === minUsage; });
  var pick = cands[Math.floor(Math.random() * cands.length)];
  var sessionId = 's_' + Utilities.getUuid().replace(/-/g, '');
  appendRow_('plan_usage', { plan_id: pick.plan_id, round: pick.round, session_id: sessionId, observer_id: observerId,
                             mode: mode, status: 'reserved', study: study });
  return { plan_id: pick.plan_id, round: pick.round, study: study, session_id: sessionId, resumed: false, session_number: prev.length + 1 };
}

function status_() {
  var st = planState_();
  var byRound = {};
  var byStudy = { mixed: { plans: 0, completed: 0, active: 0 }, grass: { plans: 0, completed: 0, active: 0 } };
  var total = 0, done = 0, active = 0;
  Object.keys(st.plans).forEach(function (pid) {
    var p = st.plans[pid];
    var r = byRound[p.round] = byRound[p.round] || { plans: 0, completed: 0, active: 0, panel: p.panel, mode: p.mode, study: p.study };
    r.plans += 1; r.completed += Math.min(1, p.completed); r.active += p.active;
    var s = byStudy[p.study] = byStudy[p.study] || { plans: 0, completed: 0, active: 0 };
    s.plans += 1; s.completed += Math.min(1, p.completed); s.active += p.active;
    total += 1; done += Math.min(1, p.completed); active += p.active;
  });
  var nTrials = Math.max(0, sheet_('trials').getLastRow() - 1);
  var nSessions = Math.max(0, sheet_('plan_usage').getLastRow() - 1);
  var observers = Object.keys(st.byObserver).length;
  return { generated_utc: new Date().toISOString(), plans_total: total, plans_completed: done, plans_reserved: active,
           studies: byStudy, rounds: byRound, n_trial_rows: nTrials, n_plan_usage_rows: nSessions, observers: observers,
           reservation_min: RESERVATION_MIN };
}

// ---------------------------------------------------------------- HTTP entry points
function doGet(e) {
  var p = (e && e.parameter) || {};
  var action = p.action || 'health';
  try {
    if (action === 'health') { return json_({ ok: true, ts: new Date().toISOString() }); }
    if (action === 'next_plan') {
      return json_(withLock_(function () { return nextPlan_(p.observer_id, p.mode, p.study, p.session_number); }));
    }
    if (action === 'status') { return json_(status_()); }
    if (action === 'export') {
      if (ADMIN_TOKEN === 'CHANGE_ME' || p.token !== ADMIN_TOKEN) { return json_({ error: 'forbidden' }); }
      var out = {};
      Object.keys(HEADERS).forEach(function (n) { out[n] = rows_(n); });
      out.exported_utc = new Date().toISOString();
      return json_(out);
    }
    return json_({ error: 'unknown_action' });
  } catch (err) {
    return json_({ error: 'server_error', message: String(err) });
  }
}

function doPost(e) {
  var body;
  try { body = JSON.parse(e.postData.contents); } catch (err) { return json_({ error: 'bad_json' }); }
  var type = body.type;
  try {
    return json_(withLock_(function () {
      if (type === 'trial') { body.study_part = normStudy_(body.study_part, body.plan_id); return recordTrial_(body); }
      if (type === 'practice_trial') { appendRow_('practice', body); return { ok: true }; }
      if (type === 'session_start') {
        appendRow_('sessions', Object.assign({}, body, { completed: false, study: normStudy_(body.study, body.plan_id) }));
        return { ok: true };
      }
      if (type === 'session_end') {
        appendRow_('sessions', Object.assign({}, body, { study: normStudy_(body.study, body.plan_id) }));
        var status = body.completed ? 'completed' : 'abandoned';
        appendRow_('plan_usage', { plan_id: body.plan_id, round: body.round, session_id: body.session_id,
                                   observer_id: body.observer_id, mode: body.mode, status: status,
                                   study: normStudy_(body.study, body.plan_id) });
        return { ok: true, status: status };
      }
      if (type === 'register_plans') {
        if (ADMIN_TOKEN === 'CHANGE_ME' || body.token !== ADMIN_TOKEN) { return { error: 'forbidden' }; }
        var existing = {};
        rows_('plans').forEach(function (r) { existing[r.plan_id] = true; });
        var n = 0;
        (body.plans || []).forEach(function (pl) {
          if (!existing[pl.plan_id]) {
            appendRow_('plans', Object.assign({ mode: 'main' }, pl, { study: normStudy_(pl.study, pl.plan_id) }));
            existing[pl.plan_id] = true; n += 1;
          }
        });
        return { ok: true, added: n, total: Object.keys(existing).length };
      }
      return { error: 'unknown_type' };
    }));
  } catch (err) {
    return json_({ error: 'server_error', message: String(err) });
  }
}

function recordTrial_(body) {
  if (!body.session_id || body.trial_index === undefined) { return { error: 'bad_record' }; }
  var sh = sheet_('trials');
  var last = sh.getLastRow();
  if (last > 1) {
    // idempotence: (session_id, trial_index) must be unique – scan the two key columns
    var keys = sh.getRange(2, 2, last - 1, 3).getValues();   // session_id, observer_id, trial_index
    for (var i = 0; i < keys.length; i++) {
      if (String(keys[i][0]) === String(body.session_id) && Number(keys[i][2]) === Number(body.trial_index)) {
        return { ok: true, duplicate: true };
      }
    }
  }
  appendRow_('trials', body);
  return { ok: true };
}
