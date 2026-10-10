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
 * GET  ?action=next_plan&observer_id=..&mode=pilot|main&session_number=1|2  -> {plan_id, round, session_id}
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
var MAX_SESSIONS = 2;              // per observer (main mode)
var PILOT_MAX_SESSIONS = 1;        // PILOT plans overlap in triplets -> one session per pilot observer;
                                   // PILOT plans are reused (least-used first) until the pilot is stopped

var HEADERS = {
  plans: ['plan_id', 'round', 'panel', 'n_trials', 'mode'],
  plan_usage: ['ts', 'plan_id', 'round', 'session_id', 'observer_id', 'mode', 'status'],
  sessions: ['ts', 'type', 'session_id', 'observer_id', 'session_number_for_observer', 'plan_id', 'round', 'mode',
             'consent_version', 'consent_ts', 'demographics', 'start_ts', 'end_ts', 'completed', 'n_trials_target',
             'n_trials_done', 'user_agent', 'completion_code', 'ui_lang', 'end_reason'],
  trials: ['ts', 'session_id', 'observer_id', 'trial_index', 'triplet_id', 'study', 'anchor_clip', 'left_clip',
           'right_clip', 'B_side', 'response', 'chosen_clip', 'rt_ms', 'loop_phase_ms', 'is_repeat',
           'repeat_of_trial_index', 'is_attention', 'panel', 'playback_errors', 'timestamp_utc', 'ui_lang',
           'screen', 'flags', 'plan_id', 'round'],
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
  }
  return sh;
}

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
  var head = HEADERS[name];
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
                         n_trials: Number(p.n_trials), completed: 0, active: 0 };
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
    if (p) {
      if (st === 'completed') { p.completed += 1; }
      else if (st === 'reserved') { p.active += 1; }
    }
    if (st === 'completed' || st === 'reserved') {
      (byObserver[u.observer_id] = byObserver[u.observer_id] || []).push({ plan_id: u.plan_id, round: String(u.round), status: st, session_id: sid });
    }
  });
  return { plans: plans, byObserver: byObserver };
}

function nextPlan_(observerId, mode, sessionNumber) {
  if (!observerId) { return { error: 'missing_observer_id' }; }
  mode = mode === 'pilot' ? 'pilot' : 'main';
  var st = planState_();
  var prev = st.byObserver[observerId] || [];
  var maxSessions = mode === 'pilot' ? PILOT_MAX_SESSIONS : MAX_SESSIONS;
  // an unfinished reservation of this observer -> resume it
  for (var i = 0; i < prev.length; i++) {
    if (prev[i].status === 'reserved') {
      return { plan_id: prev[i].plan_id, round: prev[i].round, session_id: prev[i].session_id, resumed: true,
               session_number: prev.length };
    }
  }
  if (prev.length >= maxSessions) { return { error: 'max_sessions', max_sessions: maxSessions, sessions: prev.length }; }
  var round = prev.length ? prev[0].round : null;      // second session: same round as the first
  var usedPlans = {};
  prev.forEach(function (u) { usedPlans[u.plan_id] = true; });
  var cands = [];
  Object.keys(st.plans).forEach(function (pid) {
    var p = st.plans[pid];
    if (p.mode !== mode) { return; }
    if (round !== null && p.round !== round) { return; }
    if (usedPlans[pid]) { return; }
    if (mode !== 'pilot' && p.completed >= 1) { return; } // each R/P plan needs exactly one completed session; PILOT plans are reused
    cands.push({ plan_id: pid, round: p.round, usage: p.completed + p.active });
  });
  if (!cands.length) { return { error: 'no_plan_available', round: round }; }
  var minUsage = Math.min.apply(null, cands.map(function (c) { return c.usage; }));
  cands = cands.filter(function (c) { return c.usage === minUsage; });
  var pick = cands[Math.floor(Math.random() * cands.length)];
  var sessionId = 's_' + Utilities.getUuid().replace(/-/g, '');
  appendRow_('plan_usage', { plan_id: pick.plan_id, round: pick.round, session_id: sessionId, observer_id: observerId,
                             mode: mode, status: 'reserved' });
  return { plan_id: pick.plan_id, round: pick.round, session_id: sessionId, resumed: false, session_number: prev.length + 1 };
}

function status_() {
  var st = planState_();
  var byRound = {};
  var total = 0, done = 0, active = 0;
  Object.keys(st.plans).forEach(function (pid) {
    var p = st.plans[pid];
    var r = byRound[p.round] = byRound[p.round] || { plans: 0, completed: 0, active: 0, panel: p.panel, mode: p.mode };
    r.plans += 1; r.completed += Math.min(1, p.completed); r.active += p.active;
    total += 1; done += Math.min(1, p.completed); active += p.active;
  });
  var nTrials = Math.max(0, sheet_('trials').getLastRow() - 1);
  var nSessions = Math.max(0, sheet_('plan_usage').getLastRow() - 1);
  var observers = Object.keys(st.byObserver).length;
  return { generated_utc: new Date().toISOString(), plans_total: total, plans_completed: done, plans_reserved: active,
           rounds: byRound, n_trial_rows: nTrials, n_plan_usage_rows: nSessions, observers: observers,
           reservation_min: RESERVATION_MIN };
}

// ---------------------------------------------------------------- HTTP entry points
function doGet(e) {
  var p = (e && e.parameter) || {};
  var action = p.action || 'health';
  try {
    if (action === 'health') { return json_({ ok: true, ts: new Date().toISOString() }); }
    if (action === 'next_plan') {
      return json_(withLock_(function () { return nextPlan_(p.observer_id, p.mode, p.session_number); }));
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
      if (type === 'trial') { return recordTrial_(body); }
      if (type === 'practice_trial') { appendRow_('practice', body); return { ok: true }; }
      if (type === 'session_start') {
        appendRow_('sessions', Object.assign({}, body, { completed: false }));
        return { ok: true };
      }
      if (type === 'session_end') {
        appendRow_('sessions', body);
        var status = body.completed ? 'completed' : 'abandoned';
        appendRow_('plan_usage', { plan_id: body.plan_id, round: body.round, session_id: body.session_id,
                                   observer_id: body.observer_id, mode: body.mode, status: status });
        return { ok: true, status: status };
      }
      if (type === 'register_plans') {
        if (ADMIN_TOKEN === 'CHANGE_ME' || body.token !== ADMIN_TOKEN) { return { error: 'forbidden' }; }
        var existing = {};
        rows_('plans').forEach(function (r) { existing[r.plan_id] = true; });
        var n = 0;
        (body.plans || []).forEach(function (pl) {
          if (!existing[pl.plan_id]) { appendRow_('plans', pl); existing[pl.plan_id] = true; n += 1; }
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
