/* HAT-SIM triplet study – static deployment configuration (GitHub Pages + Google Apps Script). */
window.HAT_CONFIG = {
  // URL of the deployed Apps Script web app (ends with /exec). For local tests: "http://127.0.0.1:8787/exec"
  APPS_SCRIPT_URL: "http://127.0.0.1:8787/exec",
  // "pilot" -> only PILOT_* plans are requested; "main" -> R*/P* plans
  MODE: "pilot",
  // clip lookup: clips_index.json maps clip_id -> absolute URL; ids missing there use CLIPS_BASE + id + ".mp4"
  CLIPS_INDEX_URL: "./clips_index.json",
  CLIPS_BASE: "https://hatsim-study.github.io/clips-a/",
  PLANS_URL: "./plans.json",
  CONSENT_VERSION: "v1.0-placeholder",
  MIN_PLAY_MS: 2000,          // answer allowed only after all three clips played this long
  BREAK_AFTER: 30,            // break after N trials
  MIN_SCREEN_WIDTH: 900,
  CLIP_DURATION_S: 10,
  DEFAULT_LANG: "cs",
  MAX_SESSIONS: 2
};
