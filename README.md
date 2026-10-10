# HAT-SIM triplet study

Static study application prepared by Claude, hosted in the separate `hatsim-study` organization.

- Website: https://hatsim-study.github.io/triplets/
- Frontend: `docs/`, published from `main` via GitHub Pages.
- Video repositories: [clips-a](https://github.com/hatsim-study/clips-a), [clips-b](https://github.com/hatsim-study/clips-b), 243 clips each.
- Google backend: `apps_script/Code.gs`; instructions in `DEPLOY_APPS_SCRIPT.md`.

## Deployment status

The Google Apps Script backend is deployed and configured in `docs/config.js` (2026-10-10). All 213 plans are registered. A synthetic API smoke test verified pilot-plan assignment, response recording, duplicate suppression, session closure, and token-protected export; the synthetic rows were archived locally and removed from the collection sheet. `MODE: "pilot"` and the placeholder consent version remain. Participant information and consent documents contain fields awaiting completion. A complete human pilot session is still pending; do not recruit participants using this deployment yet.

The original application and study plans are preserved. No participant responses are included. `README_static.md` is the inherited technical guide; some names and paths there describe the earlier package layout. The current repository and website addresses above are authoritative.

Local authoring source: `hat_cvpr_article_v1/triplets`. This deployment uses an isolated Git checkout and does not include the article or other workspace projects.
