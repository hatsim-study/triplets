# HAT-SIM triplet study

Static study application prepared by Claude, hosted in the separate `hatsim-study` organization.

- Website: https://hatsim-study.github.io/triplets/
- Frontend: `docs/`, published from `main` via GitHub Pages.
- Video repositories: [clips-a](https://github.com/hatsim-study/clips-a), [clips-b](https://github.com/hatsim-study/clips-b), 243 clips each, and [clips-grass](https://github.com/hatsim-study/clips-grass), 73 grass/shrub clips.
- Google backend: `apps_script/Code.gs`; instructions in `DEPLOY_APPS_SCRIPT.md`.

## Deployment status

The Google Apps Script backend supports both mixed scenes and grass, using the original `/exec` URL. The plan sets contain 213 mixed plans and 154 grass plans (367 total). `MODE: "pilot"` remains enabled; grass pilot sessions do not count toward main-study coverage. Consent version is `v1.1` (2026-10-14), including the corrected CTU data-protection contact and an accurate description of the hosting services.

The mixed pilot has one recorded completed session with 20 responses. This deployment does not establish completion of a human grass pilot or of the study. Local mock simulations and technical checks are synthetic and must not be analysed as participant responses. Full human grass pilot review is still required before main collection.

The original application and study plans are preserved. No participant responses are included. `README_static.md` is the inherited technical guide; some names and paths there describe the earlier package layout. The current repository and website addresses above are authoritative.

Local authoring source: `hat_cvpr_article_v1/triplets`. This deployment uses an isolated Git checkout and does not include the article or other workspace projects.
