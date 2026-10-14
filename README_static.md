# HAT-SIM trojicová studie – statické nasazení (GitHub Pages + Google Apps Script)

Varianta bez vlastního serveru: frontend je statický (GitHub Pages, `https://grafitctu.github.io/hatsim-triplets/`), plány sezení jsou předgenerované (`docs/plans.json`), odpovědi se ukládají do Google tabulky přes Apps Script. Původní varianta s Python serverem a živým schedulerem zůstává ve složce `web/` (viz `README_deploy.md`).

## Obsah

```
static_app/
  docs/                      ← kořen GitHub Pages (Settings → Pages → Branch: main, Folder: /docs)
    index.html, app.js, style.css, i18n.js   frontend (čisté HTML/JS, relativní cesty, CZ/EN)
    config.js                APPS_SCRIPT_URL, MODE (pilot|main), CLIPS_BASE, CLIPS_INDEX_URL, …
    plans.json               213 předgenerovaných plánů (3 MB; R1–R7 ×27 panel 1, P1–P7 ×3 panel 2, PILOT ×3) + 3 cvičné trojice
    clips_index.json         {clip_id: absolutní URL klipu}  (zatím lokální testovací mapování → nahradit)
    clips_test/              3 syntetické šumové klipy pro test (mp4v – prohlížeč je nepřehraje, viz níže)
    texts/                   consent_{cs,en}.md, debrief_{cs,en}.md (PLACEHOLDERY)
  apps_script/Code.gs        backend pro Google Apps Script
  DEPLOY_APPS_SCRIPT.md      klikací postup nasazení skriptu
  plan_index.json / .csv     index plánů k registraci v backendu
  register_plans.py          registrace plánů přes API (nebo ruční import CSV)
  make_clips_index.py        vytvoření clips_index.json pro dva klipové repozitáře (A/B)
  export_to_jsonl.py         export Apps Scriptu (JSON/CSV) → sessions.jsonl + trials.jsonl pro qc.py
  topup_plans.py             doplňkové plány (kola T1…, TP1…) pro trojice s < 5 rozhodnutými hlasy
  mock_apps_script.py        lokální emulace Apps Scriptu (stdlib) + servírování docs/ pro test bez Google
  simulate_static_observers.py  simulace pozorovatelů proti mocku/Apps Scriptu + kontroly V1–V7
  static_simulation_report.md   výstup simulace (main), static_simulation_report_pilot.md (pilot)
  plans_meta.json            metadata generátoru plánů (seed, sha256 plans.json)
```

## Jak to funguje

* **Plány místo scheduleru.** Každý plán = hotové sezení (60–62 trialů: 51 čerstvých, 6 zrcadlených opakování, 3 attention). Plány uvnitř jednoho kola jsou trojicově disjunktní; každá (trojice, panel) je v 7 plánech (7 kol) → po dokončení všech 210 plánů má každá trojice 7 hlasů panelu 1 a 158 trojic 7 hlasů panelu 2. Strana B/C a pořadí jsou v plánu **pevné**; klient randomizuje jen počáteční fázi smyčky.
* **Přidělování** (`Code.gs → nextPlan_`): nejméně použitý (dokončené + aktivní rezervace) ještě nedokončený plán daného režimu; rezervace 90 min; **druhé sezení pozorovatele je ze stejného kola** jako první (nikdy nevidí trojici dvakrát, panel 2 je vždy od jiných pozorovatelů, protože P-kola jsou jiná kola než R-kola); max 2 sezení (pilot: 1, protože plány PILOT se v trojicích překrývají; plány PILOT se opakovaně přidělují dalším pozorovatelům).
* **Pozorovatel** = `observer_id` (`obs_` + 12 znaků) v `localStorage` + zobrazený na závěrečné obrazovce; pro 2. sezení z jiného prohlížeče jej lze zadat ručně na obrazovce demografie.
* **Ukládání**: každý trial ihned `POST` (text/plain JSON) do Apps Scriptu; při výpadku fronta v `localStorage` s exponenciálním opakováním; duplicity (`session_id`, `trial_index`) backend ignoruje. Přerušené sezení se po obnovení stránky obnoví od prvního nezodpovězeného trialu (plán je statický – bez volání serveru).
* **Kód dokončení** = `HAT-XXXX-XXXX` ze SHA-256(`session_id|plan_id`) (klient), uložený v `session_end`; ověřitelný v listu `sessions`.

## Nasazení frontendu na GitHub Pages

1. Nový repozitář `hatsim-triplets` (public – GitHub Pages zdarma vyžaduje public repo).
2. Zkopírujte obsah `static_app/` do repozitáře (frontend je v podsložce `docs/`).
3. **Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: `main`, Folder: `/docs` → Save.** Za 1–2 min běží `https://grafitctu.github.io/hatsim-triplets/`.
4. `docs/config.js`: nastavte `APPS_SCRIPT_URL` (viz DEPLOY_APPS_SCRIPT.md), `MODE` (`pilot`/`main`), `CLIPS_BASE`, `CONSENT_VERSION`.
5. Texty `docs/texts/*.md` nahraďte finálními (souhlas, debriefing).
6. Prohlížeče cachují `plans.json` (`cache: force-cache`) – při výměně plánů (top-up) změňte název souboru nebo přidejte `?v=2` do `PLANS_URL`.

Všechny cesty ve frontendu jsou relativní (`./app.js`, `./plans.json`, `./texts/…`), takže web funguje v podsložce `/hatsim-triplets/` i lokálně (`python mock_apps_script.py` → `http://127.0.0.1:8787/`).

## Klipy

* 486 klipů používaných plány (seznam: `python make_clips_index.py` → `clips_split.csv`), 352×288 H.264 yuv420p, 10 s, bez zvuku (~0,3–1 MB/klip). Hostované ve dvou repozitářích GitHub Pages (`hatsim-clips-a`, `hatsim-clips-b`, každý < 1 GB), cesta `clips/<id>.mp4`.
* `clips_index.json` mapuje `clip_id → absolutní URL`; id, které v indexu chybí, se načte z `CLIPS_BASE + id + ".mp4"`. Vytvoření: `python make_clips_index.py --base-a https://grafitctu.github.io/hatsim-clips-a/clips/ --base-b https://grafitctu.github.io/hatsim-clips-b/clips/ [--split-list clips_in_b.txt]`.
* GitHub Pages posílá `Accept-Ranges: bytes` a `Access-Control-Allow-Origin: *` – nastavení `currentTime` (náhodná fáze) i cross-origin přehrávání `<video>` fungují.
* Testovací klipy v `docs/clips_test/` jsou kódované `mp4v` (OpenCV bez H.264) – slouží jen simulaci; pro vizuální test v prohlížeči nahraďte H.264 klipy (např. `ffmpeg -i in.mp4 -c:v libx264 -pix_fmt yuv420p -an out.mp4`).

**Limity GitHub Pages**: 1 GB na web, 100 GB přenosu/měsíc (měkký limit), 10 buildů/h. Odhad přenosu: 1 sezení ≈ 63 trialů × 3 klipy × ~0,6 MB ≈ 110 MB (bez cache; klipy se opakují, cache prohlížeče část ušetří) → ~250 sezení ≈ 25–30 GB, s rezervou v limitu. Dva klipové repozitáře dělí zátěž i objem.

## Dvě studie (tráva + smíšené scény)

Od 13. 10. 2026 nabízí aplikace po souhlasu a demografii obrazovku **Výběr studie**: *Studie tráva* (40 úloh, ~6–8 min; `docs/plans_grass.json`, 154 plánů GR1–GR7 ×18 panel 1 + GP1–GP7 ×4 panel 2, 40 trialů = 34 čerstvých + 4 zrcadlená opakování + 2 attention, několik plánů 24/28; klipy `G_*` 704×528 4:3, 7,2 s, `docs/clips_index_grass.json` → `https://hatsim-study.github.io/clips-grass/<id>.mp4`), *Studie smíšené scény* (dosavadní `plans.json`) a *Obojí*.

* **Obojí**: pořadí částí je náhodné; po dokončení první části se nabídne pokračovat druhou hned, nebo skončit a druhou dokončit jindy — při návratu (stejný prohlížeč, nebo zadaný kód pozorovatele) se na úvodní obrazovce nabídne jen zbývající část (`localStorage` klíč `hat_parts_v1`; z jiného prohlížeče stav nepřenáší, limity hlídá backend).
* **Backend** (`Code.gs`): `next_plan` má parametr `study=mixed|grass`; počitadla plánů, pravidlo „2. sezení ze stejného kola“ i limit **max 2 sezení na studii** (2 smíšená + 2 travní) jsou vedeny per studie. Plány tráv se poznají podle prefixu `G`; řádky zapsané před zavedením tráv nemají sloupec `study` a berou se jako `mixed`. Nové sloupce (`study` v `plans`, `plan_usage`, `sessions`; `study_part` v `trials`) se do existujících listů doplní automaticky na konec hlavičky.
* **Pilot**: travní studie nemá PILOT plány — v režimu `pilot` se tráva nabízí normálně z plánů GR/GP, sezení nese `mode:"pilot"` a analýza je vyřadí; takové sezení se nepočítá jako dokončení plánu (plán se v hlavním sběru přidělí znovu). Smíšená studie v pilotu = PILOT plány, 1 sezení na pozorovatele (beze změny).
* **Záznamy**: `sessions` i `plan_usage` nesou `study` (`mixed|grass`), `trials` nesou `study_part` (`mixed|grass`) vedle dosavadního `study` trojice (`main|sdyn|attention|pilot|grass|attention_grass`) a `plan_id`. `export_to_jsonl.py` doplní `study`/`study_part` z `plan_id` u starších řádků; `check_pilot_session.py --plans docs/plans.json docs/plans_grass.json` hledá plán v obou souborech.
* **Délka a texty**: tokeny `{{N_TRIALS}}`, `{{DURATION}}` (40 úloh → „6–8 minut“), `{{BREAK_SENTENCE}}` a nový `{{STUDY_SENTENCE}}` (věta o travní / smíšené části v instrukcích); přestávka per studie `config.js → BREAK_AFTER: { mixed: 30, grass: 20 }`.
* **Layout**: `.vid-box` má pevnou výšku, šířku podle studie (`body.study-grass` → 384 px = 4:3, jinak 352 px) a `object-fit: contain`, takže se klip jiného poměru nikdy nedeformuje.
* **Registrace plánů**: `python register_plans.py --url …/exec --token … --index docs/plans_grass.json` (nebo `plan_index_grass.csv` ručně do listu `plans`; hlavička `plan_id, round, panel, n_trials, mode, study`).
* **Simulace** (`simulate_static_observers.py --plans-grass docs/plans_grass.json --p-both 0.3 …`, výstup `static_simulation_report_grass.md`): 290 sezení (180 travních pokusů, 110 smíšených; 36 pozorovatelů s oběma studiemi, polovina „obojí“ končí po první části) — V1–V7 PASS: kola per studie, max 2+2 sezení, žádná trojice 2×, panel 2 od jiných pozorovatelů, všech 154 GR/GP plánů dokončeno.

## Pilot vs. main

`docs/config.js → MODE`:
* `"pilot"` → žádají se jen plány `PILOT_*` (3 plány × 20 trialů, trojice `P_*`, 1 sezení na pozorovatele; plány se znovu přidělují dalším pozorovatelům). Pilotní data nikdy nespojovat s hlavní analýzou – doporučeno použít **jinou tabulku/nasazení skriptu** pro pilot a pro hlavní studii.
* `"main"` → plány `R*` (panel 1) a `P*` (panel 2).

Změna režimu = úprava `config.js` + commit (Pages se přegeneruje do ~1 min).

## Export a analýza

```bash
curl -o export.json "https://script.google.com/macros/s/…/exec?action=export&token=ADMIN_TOKEN"
python export_to_jsonl.py --json export.json --out analysis_data/
#   nebo stáhněte listy jako CSV (Soubor → Stáhnout → CSV, každý list zvlášť) a:
python export_to_jsonl.py --csv-dir sheets_csv/ --out analysis_data/
```

Výstup: `sessions.jsonl` (jeden řádek na sezení = poslední stav; sezení bez `session_end` má `completed=false`, `end_reason=no_session_end`), `trials.jsonl` (bez duplicit, JSON pole parsovaná, `server_received_utc` = čas zápisu v tabulce) + `practice_trials.jsonl`, `plan_usage.jsonl` – formát shodný s variantou `web/` (vstup pro `qc.py → majority.py → tests.py`). Navíc sloupce `plan_id`, `round`.

## Top-up (doplnění hlasů po QC)

Po QC některé trojice nemají ≥ 5 rozhodnutých hlasů (vyřazení pozorovatelé, „nelze rozhodnout“). Z `majority.csv` (`triplet_id, panel, n_decided`):

```bash
python topup_plans.py --majority majority.csv --triplets ../web/stimuli/triplets.csv --plans docs/plans.json --out plans_topup.json --merge
#  -> plans_topup.json (+ plans_topup_index.csv, plans_merged.json)
python register_plans.py --url …/exec --token ADMIN_TOKEN --index plans_topup_index.csv
cp plans_merged.json docs/plans.json   # + změnit PLANS_URL na ./plans.json?v=2 (cache) a commitnout
```

Kola `T1..Tk` (panel 1) a `TP1..TPk` (panel 2): trojice chybějících k hlasů je v k kolech; uvnitř kola disjunktní; stejná struktura (51/6/3). Top-up plány dostanou jen **noví** pozorovatelé (pravidlo stejného kola), takže žádný nevidí trojici podruhé a panel 2 zůstává oddělený. V simulaci (`test_data/majority.csv`, 30 % pozorovatelů vyřazeno): 606 (trojice, panel) → 22 plánů v 8 kolech.

## Test bez Google

```bash
cd static_app
python mock_apps_script.py --port 8787 --data test_data --register plan_index.json --admin-token testtoken --reservation-min 0.05
python simulate_static_observers.py --url http://127.0.0.1:8787/exec --n-sessions 230 --dropout 0.05 --topup-sessions 40 --wait-expiry-s 4 --report static_simulation_report.md
python simulate_static_observers.py --url http://127.0.0.1:8787/exec --mode pilot --n-sessions 8 --report static_simulation_report_pilot.md
```

Frontend proti mocku: `config.js → APPS_SCRIPT_URL: "http://127.0.0.1:8787/exec"`, otevřít `http://127.0.0.1:8787/`.

Výsledek v sandboxu (270 sezení, 5 % dropoutů): V1–V7 PASS – 2. sezení vždy ze stejného kola, max 2 sezení, žádná trojice 2× u pozorovatele, panel 2 od jiných pozorovatelů (158 trojic), všech 210 plánů R/P dokončeno, 13 111 trialů bez duplicit, 12 opuštěných rezervací znovu přiděleno a dokončeno.

## GDPR

* Apps Script běží „jako já“ s přístupem „kdokoli“ → pozorovatel se nepřihlašuje, Google o něm nic neukládá do tabulky; skript nezapisuje IP ani e-mail (Apps Script je ani nemá k dispozici).
* `observer_id` je náhodný; `user_agent` jen jako `sha256:` otisk; demografie: věková kategorie, korekce zraku, jazyk.
* GitHub Pages: GitHub loguje IP adresy návštěvníků pro vlastní provoz (viz GitHub Privacy Statement) – uvést v informovaném souhlasu („stránka je hostována na GitHub Pages“). Pro ČVUT alternativu bez třetí strany použijte `web/`.
* Tabulku sdílejte jen s řešiteli; po skončení sběru export, záloha a omezení přístupu.

## Odchylky od varianty se serverem

* Žádná živá QC a žádný adaptivní scheduler: pokrytí je dané plány (7 hlasů na trojici/panel), doplnění po QC řeší `topup_plans.py`.
* Kód dokončení vzniká na klientu (bez tajného klíče), ověřitelný proti listu `sessions`.
* Režim pilot: 1 sezení na pozorovatele; PILOT plány se opakují.
