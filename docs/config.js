/* HAT-SIM triplet study – static deployment configuration (GitHub Pages + Google Apps Script). */
window.HAT_CONFIG = {
  // URL of the deployed Apps Script web app (ends with /exec). For local tests: "http://127.0.0.1:8787/exec"
  APPS_SCRIPT_URL: "https://script.google.com/macros/s/AKfycbzdB_Vy3V9Lt9x7eKU4f2H0DBcnpol5GAViFK2JIXnCH55PSgCa1F_W5CpM7ynAZ-yKzQ/exec",
  // "pilot" -> only PILOT_* plans are requested; "main" -> R*/P* plans
  MODE: "pilot",
  // clip lookup: clips_index.json maps clip_id -> absolute URL; ids missing there use CLIPS_BASE + id + ".mp4"
  CLIPS_INDEX_URL: "./clips_index.json",
  CLIPS_BASE: "https://hatsim-study.github.io/clips-a/",
  PLANS_URL: "./plans.json",
  // grass study (second study): plans + clip index; remove/leave empty to offer only the mixed-scenes study
  PLANS_GRASS_URL: "./plans_grass.json",
  CLIPS_INDEX_GRASS_URL: "./clips_index_grass.json",
  CONSENT_VERSION: "v1.1",
  MIN_PLAY_MS: 2000,          // answer allowed only after all three clips played this long
  BREAK_AFTER: { mixed: 30, grass: 20 },   // break after N trials, per study (a plain number applies to both)
  MIN_SCREEN_WIDTH: 900,
  CLIP_DURATION_S: 10,
  DEFAULT_LANG: "cs",
  MAX_SESSIONS: 2
};
