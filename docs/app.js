/* HAT-SIM triplet study – static single page application (GitHub Pages + Google Apps Script).
   Session plans are pre-generated (plans.json); the backend only hands out a plan id and stores records. */
(function () {
  "use strict";

  var C = window.HAT_CONFIG;
  var LS_OBS = "hat_observer_id", LS_SESSION = "hat_static_session_v1", LS_QUEUE = "hat_static_queue_v1", LS_LANG = "hat_lang";
  var ROLES = ["anchor", "left", "right"];
  var OBS_RE = /^obs_[A-Za-z0-9]{12}$/;

  var S = {
    lang: "cs", plans: null, clips: {}, observer_id: null, session_id: null, plan: null, plan_id: null, round: null,
    next_index: 0, nTarget: 60, phase: "init", practice: [], pIdx: 0, cur: null, nextPromise: null,
    ready: false, smallScreen: false, smallAck: false, resumed: false, queue: [], sending: false, backoff: 2000,
    netTimer: null, breakShownFor: -1, completion_code: null, session_number: 1, start_ts: null, demographics: null
  };

  // ------------------------------------------------------------------ utils
  function $(id) { return document.getElementById(id); }
  // Session-size tokens: texts (i18n + texts/*.md) use {{N_TRIALS}}, {{DURATION}}, {{BREAK_SENTENCE}}.
  // Values come from the assigned plan when known, otherwise from the mode (pilot plans = 20 trials, main = 60).
  function sessionVars() {
    var n = (S.plan && S.plan.trials) ? S.plan.trials.length : (C.MODE === "pilot" ? 20 : 60);
    var hasBreak = C.BREAK_AFTER > 0 && n > C.BREAK_AFTER;
    var cs = S.lang !== "en";
    var dur = n <= 25 ? (cs ? "4–6 minut" : "4–6 minutes") : (cs ? "12–15 minut" : "12–15 minutes");
    var brk = hasBreak ? (cs ? "Po " + C.BREAK_AFTER + " úlohách je zařazena přestávka." : "A break is scheduled after " + C.BREAK_AFTER + " trials.")
                       : (cs ? "Sezení je krátké, bez přestávky." : "The session is short, without a break.");
    return { N_TRIALS: String(n), DURATION: dur, BREAK_SENTENCE: brk };
  }
  function fillSession(s) {
    var v = sessionVars();
    return s.replace(/\{\{N_TRIALS\}\}/g, v.N_TRIALS).replace(/\{\{DURATION\}\}/g, v.DURATION).replace(/\{\{BREAK_SENTENCE\}\}/g, v.BREAK_SENTENCE);
  }
  function t(key, vars) {
    var s = (window.I18N[S.lang] && window.I18N[S.lang][key]) || window.I18N.cs[key] || key;
    if (vars) { Object.keys(vars).forEach(function (k) { s = s.replace("{" + k + "}", vars[k]); }); }
    return fillSession(s);
  }
  function show(id) {
    var all = document.querySelectorAll(".screen");
    for (var i = 0; i < all.length; i++) { all[i].classList.add("hidden"); }
    $(id).classList.remove("hidden");
  }
  function nowIso() { return new Date().toISOString(); }
  function sleep(ms) { return new Promise(function (res) { setTimeout(res, ms); }); }
  function escapeHtml(s) { return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
  function mdToHtml(md) {
    var lines = md.replace(/\r/g, "").split("\n"), out = [], para = [], inList = null;
    function flushPara() { if (para.length) { out.push("<p>" + inline(para.join(" ")) + "</p>"); para = []; } }
    function closeList() { if (inList) { out.push("</" + inList + ">"); inList = null; } }
    function inline(s) {
      s = escapeHtml(s);
      s = s.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\*(.+?)\*/g, "<i>$1</i>").replace(/_(.+?)_/g, "<i>$1</i>");
      s = s.replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
      return s.replace(/`([^`]+)`/g, "<code>$1</code>");
    }
    for (var i = 0; i < lines.length; i++) {
      var ln = lines[i], m;
      if ((m = ln.match(/^(#{1,4})\s+(.*)$/))) { flushPara(); closeList(); out.push("<h" + m[1].length + ">" + inline(m[2]) + "</h" + m[1].length + ">"); }
      else if ((m = ln.match(/^\s*[-*]\s+(.*)$/))) { flushPara(); if (inList !== "ul") { closeList(); out.push("<ul>"); inList = "ul"; } out.push("<li>" + inline(m[1]) + "</li>"); }
      else if ((m = ln.match(/^\s*\d+[.)]\s+(.*)$/))) { flushPara(); if (inList !== "ol") { closeList(); out.push("<ol>"); inList = "ol"; } out.push("<li>" + inline(m[1]) + "</li>"); }
      else if (/^\s*$/.test(ln)) { flushPara(); closeList(); }
      else if (/^\s*---+\s*$/.test(ln)) { flushPara(); closeList(); out.push("<hr>"); }
      else { closeList(); para.push(ln.trim()); }
    }
    flushPara(); closeList();
    return out.join("\n");
  }
  function sha256hex(str) {
    var data = new TextEncoder().encode(str);
    if (!(window.crypto && crypto.subtle)) { return Promise.resolve(null); }
    return crypto.subtle.digest("SHA-256", data).then(function (buf) {
      return Array.prototype.map.call(new Uint8Array(buf), function (b) { return ("0" + b.toString(16)).slice(-2); }).join("");
    });
  }
  function randomId(prefix, n) {
    var chars = "abcdefghijklmnopqrstuvwxyz0123456789", out = prefix, arr = new Uint8Array(n);
    (window.crypto || {}).getRandomValues ? crypto.getRandomValues(arr) : arr.forEach(function (_, i) { arr[i] = Math.floor(Math.random() * 256); });
    for (var i = 0; i < n; i++) { out += chars[arr[i] % chars.length]; }
    return out;
  }

  // ----------------------------------------------------------- transport
  // GET: Apps Script answers with JSON; POST uses text/plain to avoid a CORS preflight.
  function apiGet(params) {
    var qs = Object.keys(params).map(function (k) { return encodeURIComponent(k) + "=" + encodeURIComponent(params[k]); }).join("&");
    return fetch(C.APPS_SCRIPT_URL + "?" + qs, { method: "GET", cache: "no-store", redirect: "follow" })
      .then(function (r) { return r.text(); })
      .then(function (txt) { try { return JSON.parse(txt); } catch (e) { return { error: "bad_json" }; } });
  }
  function apiPost(body) {
    return fetch(C.APPS_SCRIPT_URL, { method: "POST", redirect: "follow", headers: { "Content-Type": "text/plain;charset=utf-8" }, body: JSON.stringify(body) })
      .then(function (r) { return r.text(); })
      .then(function (txt) { try { return JSON.parse(txt); } catch (e) { return { error: "bad_json" }; } });
  }
  function apiGetRetry(params) {
    var delay = 1500;
    function attempt() {
      return apiGet(params).then(function (d) {
        if (d && d.error === "server_error") { throw new Error(d.message || "server_error"); }
        hideNet(); return d;
      }).catch(function () {
        showNet(S.queue.length, delay);
        return sleep(delay).then(function () { delay = Math.min(delay * 1.6, 30000); return attempt(); });
      });
    }
    return attempt();
  }

  // --------------------------------------------------------- persistence
  function saveLocal() {
    try {
      if (S.observer_id) { localStorage.setItem(LS_OBS, S.observer_id); }
      if (S.session_id && S.phase !== "done") {
        localStorage.setItem(LS_SESSION, JSON.stringify({ session_id: S.session_id, plan_id: S.plan_id, round: S.round, next_index: S.next_index,
          phase: S.phase, session_number: S.session_number, start_ts: S.start_ts, demographics: S.demographics, mode: C.MODE }));
      } else { localStorage.removeItem(LS_SESSION); }
      localStorage.setItem(LS_QUEUE, JSON.stringify(S.queue));
      localStorage.setItem(LS_LANG, S.lang);
    } catch (e) { /* storage unavailable */ }
  }
  function loadLocal() {
    try {
      S.observer_id = localStorage.getItem(LS_OBS) || null;
      S.lang = localStorage.getItem(LS_LANG) || null;
      S.queue = JSON.parse(localStorage.getItem(LS_QUEUE) || "[]");
      var sess = localStorage.getItem(LS_SESSION);
      return sess ? JSON.parse(sess) : null;
    } catch (e) { return null; }
  }

  // ------------------------------------------------------ upload queue
  function enqueue(body) { S.queue.push({ body: body, ts: Date.now() }); saveLocal(); pumpQueue(); }
  function pumpQueue() {
    if (S.sending) { return; }
    if (!S.queue.length) { hideNet(); return; }
    S.sending = true;
    var item = S.queue[0];
    apiPost(item.body).then(function (d) {
      if (!d || d.error === "server_error" || d.error === "bad_json") { throw new Error("retry"); }
      S.queue.shift(); S.backoff = 2000; saveLocal(); S.sending = false; hideNet(); pumpQueue();
    }).catch(function () {
      S.sending = false;
      showNet(S.queue.length, S.backoff);
      clearTimeout(S.netTimer);
      S.netTimer = setTimeout(function () { S.backoff = Math.min(S.backoff * 1.6, 60000); pumpQueue(); }, S.backoff);
    });
  }
  function flushQueue() {
    return new Promise(function (res) {
      (function check() { if (!S.queue.length && !S.sending) { res(); } else { pumpQueue(); setTimeout(check, 500); } })();
    });
  }
  function showNet(n, delay) { $("overlay-net").classList.remove("hidden"); $("net-detail").textContent = t("net_detail", { n: n, s: Math.round(delay / 1000) }); }
  function hideNet() { $("overlay-net").classList.add("hidden"); }

  // -------------------------------------------------------------- i18n
  function applyLang(lang) {
    S.lang = lang;
    document.documentElement.lang = lang;
    var els = document.querySelectorAll("[data-i18n]");
    for (var i = 0; i < els.length; i++) { els[i].textContent = t(els[i].getAttribute("data-i18n")); }
    var btns = document.querySelectorAll(".lang-btn");
    for (var j = 0; j < btns.length; j++) { btns[j].classList.toggle("active", btns[j].getAttribute("data-lang") === lang); }
    $("instr-text").innerHTML = t("instr_html");
    $("observer-code-hint").textContent = t("observer_code_hint");
    loadDoc("consent", "consent-text");
    loadDoc("debrief", "debrief-text");
    saveLocal();
  }
  function loadDoc(name, elId) {
    fetch("./texts/" + name + "_" + S.lang + ".md", { cache: "no-store" }).then(function (r) {
      return r.ok ? r.text() : fetch("./texts/" + name + "_cs.md").then(function (r2) { return r2.ok ? r2.text() : "(" + name + ")"; });
    }).then(function (md) { $(elId).innerHTML = mdToHtml(fillSession(md)); }).catch(function () { $(elId).textContent = "(" + name + ")"; });
  }

  // ----------------------------------------------------- screen checks
  function checkScreen() {
    var small = window.innerWidth < C.MIN_SCREEN_WIDTH;
    if (!small) { S.smallAck = false; S.smallScreen = false; $("overlay-small").classList.add("hidden"); return; }
    S.smallScreen = true;
    if (!S.smallAck) { $("overlay-small").classList.remove("hidden"); }
  }
  function goFullscreen() {
    var el = document.documentElement;
    var fn = el.requestFullscreen || el.webkitRequestFullscreen || el.mozRequestFullScreen;
    if (fn) { try { var p = fn.call(el); if (p && p.catch) { p.catch(function () {}); } } catch (e) { /* ignore */ } }
  }

  // ---------------------------------------------------------- clips / plans
  function clipUrl(id) { return S.clips[id] || (C.CLIPS_BASE + id + ".mp4"); }
  function planTrialToView(tr) {
    // plan trial {anchor, B, C, B_side, ...} -> view with left/right clips (B_side fixed by the plan)
    var left = tr.B_side === "left" ? tr.B : tr.C, right = tr.B_side === "left" ? tr.C : tr.B;
    return { trial_index: tr.trial_index, triplet_id: tr.triplet_id, study: tr.study || "pilot", anchor_clip: tr.anchor,
             left_clip: left, right_clip: right, B_side: tr.B_side, is_repeat: !!tr.is_repeat,
             repeat_of_trial_index: (tr.repeat_of === undefined ? null : tr.repeat_of), is_attention: !!tr.is_attention, panel: tr.panel || 1 };
  }

  // ---------------------------------------------------- video handling
  function prepareTrial(trial) {
    var P = { trial: trial, vids: {}, phase: { anchor: 0, left: 0, right: 0 }, errors: 0, playing: {}, t0: null, enableTimer: null };
    ROLES.forEach(function (role) {
      var v = document.createElement("video");
      v.loop = true; v.muted = true; v.defaultMuted = true; v.playsInline = true;
      v.setAttribute("playsinline", ""); v.setAttribute("muted", ""); v.setAttribute("loop", "");
      v.preload = "auto"; v.disablePictureInPicture = true;
      v.addEventListener("stalled", function () { P.errors++; });
      v.addEventListener("error", function () { P.errors++; });
      v.addEventListener("loadedmetadata", function () {
        var d = (isFinite(v.duration) && v.duration > 0) ? v.duration : C.CLIP_DURATION_S;
        var tt = Math.random() * Math.max(0, d - 0.05);           // random loop phase (the only client-side randomisation)
        P.phase[role] = Math.round(tt * 1000);
        try { v.currentTime = tt; } catch (e) { /* ignore */ }
      }, { once: true });
      v.src = clipUrl(trial[role + "_clip"]);
      $("hidden-pool").appendChild(v);
      try { v.load(); } catch (e) { /* ignore */ }
      P.vids[role] = v;
    });
    return P;
  }
  function destroyTrial(P) {
    if (!P) { return; }
    clearTimeout(P.enableTimer);
    ROLES.forEach(function (role) {
      var v = P.vids[role];
      if (!v) { return; }
      try { v.pause(); v.removeAttribute("src"); v.load(); } catch (e) { /* ignore */ }
      if (v.parentNode) { v.parentNode.removeChild(v); }
    });
  }
  function displayTrial(P) {
    S.cur = P; S.ready = false;
    setButtons(false);
    $("trial-status").textContent = t("status_loading");
    ["box-anchor", "box-left", "box-right"].forEach(function (id) { $(id).innerHTML = ""; $(id).classList.remove("chosen"); });
    $("box-anchor").appendChild(P.vids.anchor); $("box-left").appendChild(P.vids.left); $("box-right").appendChild(P.vids.right);
    ROLES.forEach(function (role) {
      var v = P.vids[role];
      v.addEventListener("playing", function () {
        if (P !== S.cur || P.playing[role]) { return; }
        P.playing[role] = true;
        if (ROLES.every(function (r) { return P.playing[r]; })) {
          P.t0 = performance.now();                                     // RT clock: all three clips are playing
          $("trial-status").textContent = t("status_wait");
          P.enableTimer = setTimeout(function () {
            if (P !== S.cur) { return; }
            S.ready = true; setButtons(true); $("trial-status").textContent = t("status_ready");
          }, C.MIN_PLAY_MS);
        }
      });
      var pr = v.play();
      if (pr && pr.catch) { pr.catch(function () { P.errors++; setTimeout(function () { try { v.play(); } catch (e) {} }, 500); }); }
    });
    show("screen-trial");
  }
  function setButtons(on) { ["btn-left", "btn-right", "btn-undecided"].forEach(function (id) { $(id).disabled = !on; }); }
  function setProgress(i, n, practice) {
    $("progress-wrap").classList.remove("hidden");
    $("progress-text").textContent = t(practice ? "progress_practice" : "progress", { i: i, n: n });
    $("progress-fill").style.width = Math.round(100 * (practice ? 0 : (i - 1)) / n) + "%";
  }

  // --------------------------------------------------------- responses
  function buildRecord(P, resp, rt) {
    var tr = P.trial, flags = [];
    if (S.smallScreen) { flags.push("small_screen"); }
    if (S.resumed) { flags.push("resumed_session"); }
    if (!document.fullscreenElement) { flags.push("no_fullscreen"); }
    return {
      type: "trial", session_id: S.session_id, observer_id: S.observer_id, trial_index: tr.trial_index, triplet_id: tr.triplet_id,
      study: tr.study, anchor_clip: tr.anchor_clip, left_clip: tr.left_clip, right_clip: tr.right_clip, B_side: tr.B_side,
      response: resp, chosen_clip: resp === "left" ? tr.left_clip : resp === "right" ? tr.right_clip : null,
      rt_ms: rt, loop_phase_ms: P.phase, is_repeat: tr.is_repeat, repeat_of_trial_index: tr.repeat_of_trial_index,
      is_attention: tr.is_attention, panel: tr.panel, playback_errors: P.errors, timestamp_utc: nowIso(), ui_lang: S.lang,
      screen: { w: window.innerWidth, h: window.innerHeight, dpr: window.devicePixelRatio || 1 }, flags: flags,
      plan_id: S.plan_id, round: S.round
    };
  }
  function answer(resp) {
    if (!S.ready || !S.cur) { return; }
    var P = S.cur;
    S.ready = false; setButtons(false);
    var rt = Math.round(performance.now() - P.t0);
    $(resp === "left" ? "box-left" : resp === "right" ? "box-right" : "box-anchor").classList.add("chosen");
    var rec = buildRecord(P, resp, rt);
    if (S.phase === "practice") {
      rec.type = "practice_trial"; rec.flags.push("practice");
      enqueue(rec);
      S.pIdx++;
      setTimeout(nextPractice, 250);
    } else {
      enqueue(rec);
      S.next_index = P.trial.trial_index + 1;
      saveLocal();
      setTimeout(afterMainTrial, 250);
    }
  }

  // ----------------------------------------------------------- practice
  function startPractice() {
    S.phase = "practice"; S.pIdx = 0;
    S.practice = (S.plans.practice || []).map(function (p, i) {
      return planTrialToView({ trial_index: -3 + i, triplet_id: p.triplet_id, study: "pilot", anchor: p.anchor, B: p.B, C: p.C, B_side: p.B_side, panel: 1 });
    });
    if (!S.practice.length) { return practiceDone(); }
    S.nextPromise = Promise.resolve(prepareTrial(S.practice[0]));
    nextPractice();
  }
  function practiceDone() { $("progress-wrap").classList.add("hidden"); show("screen-practice-done"); }
  function nextPractice() {
    var old = S.cur;
    if (S.pIdx >= S.practice.length) { destroyTrial(old); S.cur = null; return practiceDone(); }
    S.nextPromise.then(function (P) {
      destroyTrial(old);
      setProgress(S.pIdx + 1, S.practice.length, true);
      displayTrial(P);
      S.nextPromise = (S.pIdx + 1 < S.practice.length) ? Promise.resolve(prepareTrial(S.practice[S.pIdx + 1])) : Promise.resolve(null);
    });
  }

  // --------------------------------------------------------- main trials
  function getTrial(k) {
    if (!S.plan || k >= S.plan.trials.length) { return Promise.resolve({ done: true }); }
    return Promise.resolve(prepareTrial(planTrialToView(S.plan.trials[k])));
  }
  function startMain() {
    S.phase = "main";
    if (!S.start_ts) {
      S.start_ts = nowIso();
      enqueue({ type: "session_start", session_id: S.session_id, observer_id: S.observer_id, session_number_for_observer: S.session_number,
                plan_id: S.plan_id, round: S.round, mode: C.MODE, consent_version: C.CONSENT_VERSION, consent_ts: S.start_ts,
                demographics: S.demographics || {}, start_ts: S.start_ts, end_ts: null, completed: false, n_trials_target: S.nTarget,
                n_trials_done: 0, user_agent: S.ua_hash || null, completion_code: null, ui_lang: S.lang });
    }
    saveLocal();
    S.nextPromise = getTrial(S.next_index);
    showMainTrial();
  }
  function showMainTrial() {
    var old = S.cur;
    S.nextPromise.then(function (P) {
      destroyTrial(old); S.cur = null;
      if (P.done) { return finishSession(); }
      setProgress(P.trial.trial_index + 1, S.nTarget, false);
      displayTrial(P);
      S.nextPromise = getTrial(P.trial.trial_index + 1);           // preload the following trial
    });
  }
  function afterMainTrial() {
    var k = S.next_index;
    if (k >= S.nTarget) { return showMainTrial(); }
    if (C.BREAK_AFTER > 0 && k % C.BREAK_AFTER === 0 && S.breakShownFor !== k) {
      S.breakShownFor = k;
      destroyTrial(S.cur); S.cur = null;
      show("screen-break");
      return;
    }
    showMainTrial();
  }
  function finishSession() {
    S.phase = "done";
    $("progress-wrap").classList.add("hidden");
    show("screen-end");
    $("completion-code").textContent = "…";
    $("observer-code-end").textContent = S.observer_id || "—";
    $("end-note").textContent = t("end_pending");
    sha256hex(S.session_id + "|" + S.plan_id).then(function (h) {
      var code = h ? "HAT-" + h.slice(0, 4).toUpperCase() + "-" + h.slice(4, 8).toUpperCase() : "HAT-" + S.session_id.slice(-8).toUpperCase();
      S.completion_code = code;
      enqueue({ type: "session_end", session_id: S.session_id, observer_id: S.observer_id, session_number_for_observer: S.session_number,
                plan_id: S.plan_id, round: S.round, mode: C.MODE, consent_version: C.CONSENT_VERSION, demographics: S.demographics || {},
                start_ts: S.start_ts, end_ts: nowIso(), completed: true, n_trials_target: S.nTarget, n_trials_done: S.next_index,
                user_agent: S.ua_hash || null, completion_code: code, ui_lang: S.lang, end_reason: "completed" });
      return flushQueue();
    }).then(function () {
      $("completion-code").textContent = S.completion_code;
      $("end-note").textContent = t("end_done");
      if (S.session_number < C.MAX_SESSIONS && C.MODE !== "pilot") { $("btn-second").classList.remove("hidden"); }
      saveLocal();
    });
  }
  function fatal(titleKey, textKey) {
    show("screen-message");
    $("message-title").textContent = t(titleKey);
    $("message-text").textContent = t(textKey);
  }

  // ----------------------------------------------------------- session
  function planById(pid) {
    for (var i = 0; i < S.plans.plans.length; i++) { if (S.plans.plans[i].plan_id === pid) { return S.plans.plans[i]; } }
    return null;
  }
  function requestPlan() {
    return apiGetRetry({ action: "next_plan", observer_id: S.observer_id, mode: C.MODE, session_number: S.session_number }).then(function (d) {
      if (d.error === "max_sessions") { fatal("max_sessions_title", "max_sessions_text"); return null; }
      if (d.error === "no_plan_available") { fatal("no_plan_title", "no_plan_text"); return null; }
      if (!d.plan_id || !d.session_id) { fatal("error_title", "error_text"); return null; }
      var plan = planById(d.plan_id);
      if (!plan) { fatal("error_title", "error_text"); return null; }
      S.plan = plan; S.plan_id = d.plan_id; S.round = d.round || plan.round; S.session_id = d.session_id;
      S.session_number = d.session_number || S.session_number; S.nTarget = plan.trials.length;
      $("instr-text").innerHTML = t("instr_html"); loadDoc("consent", "consent-text"); loadDoc("debrief", "debrief-text");   // refresh session-size tokens
      S.resumed = !!d.resumed; S.next_index = 0; S.start_ts = null;
      saveLocal();
      return d;
    });
  }

  // --------------------------------------------------------------- init
  function bind() {
    var langBtns = document.querySelectorAll(".lang-btn");
    for (var i = 0; i < langBtns.length; i++) { langBtns[i].addEventListener("click", function (ev) { applyLang(ev.currentTarget.getAttribute("data-lang")); }); }
    $("consent-check").addEventListener("change", function () { $("btn-consent").disabled = !$("consent-check").checked; });
    $("btn-consent").addEventListener("click", function () { show("screen-demo"); });
    $("btn-demo").addEventListener("click", function () {
      if (!$("demo-age").value || !$("demo-vision").value || !$("demo-lang").value) { alert(t("demo_missing")); return; }
      var code = ($("observer-code").value || "").trim();
      if (code) {
        if (!OBS_RE.test(code)) { alert(t("observer_code_bad")); return; }
        S.observer_id = code;
      }
      if (!S.observer_id) { S.observer_id = randomId("obs_", 12); }
      S.demographics = { age_band: $("demo-age").value, vision_corrected: $("demo-vision").value, lang: $("demo-lang").value };
      saveLocal();
      $("btn-demo").disabled = true;
      requestPlan().then(function (d) { $("btn-demo").disabled = false; if (d) { show("screen-instr"); } });
    });
    $("btn-fullscreen").addEventListener("click", goFullscreen);
    $("btn-small-fullscreen").addEventListener("click", function () { goFullscreen(); setTimeout(checkScreen, 600); });
    $("btn-small-continue").addEventListener("click", function () { S.smallAck = true; $("overlay-small").classList.add("hidden"); });
    $("btn-practice").addEventListener("click", function () { $("btn-practice").disabled = true; startPractice(); });
    $("btn-start-main").addEventListener("click", startMain);
    $("btn-break").addEventListener("click", showMainTrial);
    $("btn-left").addEventListener("click", function () { answer("left"); });
    $("btn-right").addEventListener("click", function () { answer("right"); });
    $("btn-undecided").addEventListener("click", function () { answer("undecided"); });
    $("btn-second").addEventListener("click", function () { try { localStorage.removeItem(LS_SESSION); } catch (e) {} window.location.reload(); });
    $("btn-message-ok").addEventListener("click", function () { show("screen-consent"); });
    document.addEventListener("keydown", function (ev) {
      if ($("screen-trial").classList.contains("hidden")) { return; }
      if (ev.key === "ArrowLeft") { ev.preventDefault(); answer("left"); }
      else if (ev.key === "ArrowRight") { ev.preventDefault(); answer("right"); }
      else if (ev.key === " " || ev.code === "Space") { ev.preventDefault(); answer("undecided"); }
    });
    window.addEventListener("resize", checkScreen);
    window.addEventListener("online", pumpQueue);
    window.addEventListener("beforeunload", saveLocal);
  }

  function init() {
    var saved = loadLocal();
    bind();
    applyLang(S.lang || C.DEFAULT_LANG || "cs");
    checkScreen();
    pumpQueue();
    sha256hex(navigator.userAgent || "").then(function (h) { S.ua_hash = h ? "sha256:" + h.slice(0, 32) : null; });
    show("screen-loading");
    $("screen-loading").querySelector("p").textContent = t("loading_plans");
    Promise.all([
      fetch(C.PLANS_URL, { cache: "force-cache" }).then(function (r) { if (!r.ok) { throw new Error("plans"); } return r.json(); }),
      fetch(C.CLIPS_INDEX_URL, { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : {}; }).catch(function () { return {}; })
    ]).then(function (res) {
      S.plans = res[0]; S.clips = res[1] || {};
      if (saved && saved.session_id && saved.phase === "main" && saved.mode === C.MODE) {
        // resume an interrupted session from the first unanswered trial (plan is static, no server call needed)
        var plan = planById(saved.plan_id);
        if (plan && saved.next_index < plan.trials.length) {
          S.plan = plan; S.plan_id = saved.plan_id; S.round = saved.round; S.session_id = saved.session_id;
          S.next_index = saved.next_index; S.session_number = saved.session_number || 1; S.start_ts = saved.start_ts;
          S.demographics = saved.demographics; S.nTarget = plan.trials.length; S.resumed = true;
          show("screen-message");
          $("message-title").textContent = t("resumed_title");
          $("message-text").textContent = t("resumed_text");
          setTimeout(startMain, 1500);
          return;
        }
      }
      if (S.observer_id) { $("observer-code").value = S.observer_id; }
      show("screen-consent");
    }).catch(function () { fatal("error_title", "error_text"); });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
