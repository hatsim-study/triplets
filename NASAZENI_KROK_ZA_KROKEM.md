# Nasazení studie — co kliknout (10 kroků, ~30 minut)

Tři repozitáře na GitHubu v nové organizaci **hatsim-study** (Settings → Organizations → New organization, plán Free) (složky jsou připravené v `C:\Users\grafi\Documents\Věda\hat_cvpr_article_v1\`):

| složka | repozitář | obsah | velikost |
|---|---|---|---|
| `triplets\` | hatsim-study/triplets | aplikace (složka `docs/` = web) | 5 MB |
| `clips-a\` | hatsim-study/clips-a | 243 klipů | 378 MB |
| `clips-b\` | hatsim-study/clips-b | 243 klipů | 346 MB |

1. Na GitHubu založte tři prázdné veřejné repozitáře s těmito názvy.
2. V každé složce: `git init` → `git add -A` → `git commit -m init` → `git branch -M main` → `git remote add origin https://github.com/hatsim-study/<název>.git` → `git push -u origin main`. (U klipů push trvá několik minut.)
3. U `clips-a` a `clips-b`: Settings → Pages → Source „Deploy from a branch", branch `main`, folder `/ (root)`. Po pár minutách ověřte, že se otevře např. `https://hatsim-study.github.io/clips-a/54aa110.mp4`.
4. U `triplets`: Settings → Pages → branch `main`, folder `/docs`.
5. Google tabulka: na drive.google.com založte novou tabulku „HAT-SIM study", Rozšíření → Apps Script, smažte obsah a vložte `static_app/apps_script/Code.gs`. Postup krok za krokem je v `DEPLOY_APPS_SCRIPT.md` (včetně nastavení ADMIN_TOKEN a registrace plánů).
6. Nasadit → Nová nasazení → Webová aplikace → Spustit jako: já, Přístup: kdokoli → Nasadit → zkopírovat URL (končí `/exec`).
7. V `triplets/docs/config.js` vyplňte `APPS_SCRIPT_URL` tou URL; `MODE` nechte `"pilot"`; commit + push.
8. Otevřete `https://hatsim-study.github.io/triplets/` a projděte jedno sezení sami (pilotní plán, 20 úloh). Zkontrolujte v tabulce, že se objevily řádky.
9. Pilot: pošlete odkaz ≤10 lidem. Po pilotu změňte `MODE` na `"main"` a commitněte.
10. Export dat kdykoli: `…/exec?action=export&token=VÁŠ_TOKEN` → uložit JSON → `python static_app/export_to_jsonl.py` → `analysis/qc.py` atd. (README_analysis.md).

Limity GitHub Pages: 100 GB přenosu/měsíc (odhad sběru ≈ 25 GB), 1 GB na web (klipy 0,38 + 0,35 GB). Apps Script: ~90 min běhu/den — při více než ~100 sezeních denně se export/plánování zpomalí.
