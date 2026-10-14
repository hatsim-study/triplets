# Změny k commitu (Claude, 10. 10. 2026) — checkout repos/triplets, výchozí commit ab0678d

Soubory:
- docs/app.js — tokeny {{N_TRIALS}}, {{DURATION}}, {{BREAK_SENTENCE}} se doplňují podle přiděleného plánu (nebo podle MODE před přidělením); po přidělení plánu se instrukce, souhlas a debrief znovu vykreslí.
- docs/i18n.js — instrukce a text po cvičení používají tokeny (dříve napevno „60 kroků, 12–15 minut, přestávka po 30").
- docs/texts/consent_cs.md, consent_en.md — věta o délce sezení přes tokeny; debrief_cs/en.md — jen komentář.
- check_pilot_session.py — kontrola úplnosti sezení proti plans.json (ověřeno na 4 simulovaných pilotních sezeních přes mock_apps_script: ALL OK).
- PILOT_PRUCHOD_A_KONTROLA.md — postup lidského pilotu a kontroly.
- AUTORSKA_POLE.md — seznam 12 polí k doplnění Tomášem.
Beze změny: config.js (MODE pilot, CONSENT_VERSION v1.0-placeholder), Code.gs, plans.json.
Syntaxe JS ověřena parserem (esprima); vizuální test v prohlížeči ze sandboxu neproběhl.
Navržený commit: "Session-size tokens in participant texts (pilot = 20 trials); pilot completeness check"

## Doplnění (10. 10. 2026, odpoledne)
- docs/texts/* (kromě ethics_application_*): autorská pole vyplněna — správce ČVUT v Praze (sídlo), řešitel Radek Richtr, odměna žádná, právní základ souhlas (čl. 6/1/a GDPR), uchování anonymních dat 10 let, odvolání dat kódem do 9. 11. 2026, umístění dat GitHub Pages + Google tabulka, korekce zraku ponechána, věty o etické komisi vypuštěny, URL studie doplněna. E-mail řešitele doplněn (richtrad@fit.cvut.cz); žádné prázdné pole v textech pro účastníky nezbývá.
- docs/config.js: CONSENT_VERSION "v1.0"; consent_cs/en.md verze v1.0.
- Navržený commit: "Participant texts: author fields filled, consent v1.0; session-size tokens; pilot completeness check"

## Doplnění (13. 10. 2026)
- Závěrečná obrazovka nově výslovně říká, že sezení je dokončené a okno lze zavřít (i18n end_done, app.js, index.html, style.css); instructions_cs/en.md: krok 5 o konci sezení, délka a přestávka přes tokeny.

## Travní studie, 13. 10. 2026

Druhá studie „tráva“ + úvodní volba studie; navazuje na tokeny {{N_TRIALS}}/{{DURATION}}/{{BREAK_SENTENCE}} a end_done (nic z toho nepřepsáno). Nic necommitováno.

Nové soubory:
- docs/plans_grass.json (154 plánů GR1–GR7 ×18 panel 1, GP1–GP7 ×4 panel 2; sha256 dle plans_grass_meta.json), docs/clips_index_grass.json (73 klipů G_* → https://hatsim-study.github.io/clips-grass/<id>.mp4), plans_grass_meta.json, triplets_grass.csv, plan_index_grass.json/.csv (sloupec study=grass), static_simulation_report_grass.md.

Upravené soubory:
- docs/index.html — obrazovka „Výběr studie“ (screen-study: tráva / smíšené scény / obojí) mezi demografií a instrukcemi; na závěrečné obrazovce blok „Druhá část“ (pokračovat hned / dokončit jindy).
- docs/app.js — načítá plans.json i plans_grass.json a slučuje clips_index.json + clips_index_grass.json; stav S.study (mixed|grass), S.choice (mixed|grass|both), localStorage hat_parts_v1 (postup volby „obojí“: pending část se při návratu nabídne jako jediná); next_plan posílá study; session_start/session_end nesou study, trialy study_part (+ dosavadní study trojice beze změny); cvičné trojice per studie (practice z plans_grass.json); BREAK_AFTER per studie (objekt {mixed, grass}, číslo = obě); sessionVars: DURATION 40 úloh → „6–8 minut“, nový token {{STUDY_SENTENCE}}; body.className = study-<study> pro layout; druhá část se spouští bez opakování souhlasu/demografie (nová rezervace plánu, nové session_id); klávesa ↓ přidána jako alias „nelze rozhodnout“ (instructions_*.md ji uvádějí, dosud fungoval jen mezerník).
- docs/i18n.js — klíče study_*, instr_study_grass/mixed, second_part_*; v instr_html token {{STUDY_SENTENCE}} (CZ i EN).
- docs/style.css — .vid-box pevná výška, body.study-grass šířka 384/336/480 px (4:3), object-fit: contain (dřív fill) → klip jiného poměru se nedeformuje; styly .study-grid/.study-opt/.second-part.
- docs/config.js — PLANS_GRASS_URL, CLIPS_INDEX_GRASS_URL, BREAK_AFTER: { mixed: 30, grass: 20 }; APPS_SCRIPT_URL, MODE (pilot), CONSENT_VERSION beze změny.
- docs/texts/instructions_cs.md, instructions_en.md — nový oddíl 1a „Dvě studie, stejná úloha“ (věta o travní části: jemné rozdíly v pohybu a struktuře).
- apps_script/Code.gs — next_plan(observer_id, mode, study): oddělená počitadla (prefix G = tráva), pravidlo stejného kola a limit MAX_SESSIONS=2 per studie (2 smíšená + 2 travní); v pilotu se tráva přiděluje z GR/GP plánů, travní sezení s mode:"pilot" se nepočítá jako dokončení plánu; expirovaná/opuštěná rezervace nově také „připne“ kolo pozorovatele a blokuje opakované přidělení téhož plánu (dřív mohl pozorovatel po vypršení dostat plán z jiného kola a vidět část trojic podruhé); sloupce study (plans, plan_usage, sessions) a study_part (trials) se do existujících listů doplní na konec hlavičky (migrace v sheet_, appendRow_ zapisuje podle hlavičky listu); status vrací studies.mixed/grass; řádky bez study = mixed. SPREADSHEET_ID/ADMIN_TOKEN beze změny.
- mock_apps_script.py — stejná logika jako Code.gs; --register lze opakovat a přijímá i plans*.json.
- simulate_static_observers.py — --plans-grass, --p-mixed, --p-both (pozorovatel „obojí“ s p=0,5 pokračuje druhou částí), --require-coverage, --observer-prefix; kontroly V1/V2 per studie, V5/V7 jen pro požadované studie. Výsledek (260+30 sezení, seed 3: 180 travních pokusů, 110 smíšených, 36 pozorovatelů s oběma studiemi, 14 dropoutů): V1–V7 PASS, 154/154 GR/GP plánů dokončeno.
- export_to_jsonl.py — sessions.jsonl pole study, trials.jsonl pole study_part (u starších řádků odvozeno z plan_id); check_pilot_session.py — --plans přijímá více souborů (plans.json plans_grass.json), vypisuje study; register_plans.py — umí registrovat plans_grass.json / plan_index_grass.csv, doplňuje sloupec study.
- README_static.md — oddíl „Dvě studie (tráva + smíšené scény)“ + příkazy simulace; DEPLOY_APPS_SCRIPT.md — krok 3b „Aktualizace na dvě studie“ (nová verze téže webové aplikace, URL zůstává, registrace plans_grass.json), tabulka API.

Odchylky / rozhodnutí: (1) v trialech je study_part (mixed|grass) vedle dosavadního study trojice, aby se nerozbila analýza main/sdyn; (2) v pilotu tráva = 2 sezení na pozorovatele jako v hlavním sběru (pilotní smíšená studie zůstává 1); (3) pokrytí smíšených plánů se v simulaci nevyžadovalo (110 sezení < 210 plánů), tráva 100 %; (4) vizuální test v prohlížeči ze sandboxu neproběhl — JS/Code.gs ověřeny parserem (esprima), frontend servírován mockem; (5) klíč ↓ přidán navíc k mezerníku.
Navržený commit: "Grass study: study selection screen, plans_grass.json, per-study plan counters in Apps Script, simulation"

## Travní studie — doplnění Claude (14. 10. 2026)
- Zdroje: hat_cvpr_article_v1\grass_source (59 souborů) → 29 záběrů tráva/keře → 73 klipů 7,2 s (704×528, nativní fps); klipy v repozitáři clips-grass (složka hat_cvpr_article_v1\clips-grass, 211 MB, .nojekyll, clips_manifest.sha256) — Codex: založit hatsim-study/clips-grass, push, Pages z root.
- Trojice a plány: seed 20261013, 600 trojic + 30 attention, 154 plánů (sha256 dac7e73e…); replikovatelné skripty v results\grass_study_20261013.
- Metriky (po zmrazení trojic): v12 na FFV1 klipech, target 10 Hz, rytmus ≤ 4 Hz (10fps zdroje nedovolí 15 Hz); ψ(D12, D9) na travních trojicích 0,025; D9 volí kandidáta stejné rodiny (tráva/keř) jen v 54,5 % smíšených trojic.
- Test: mock + simulate_static_observers (--p-both 1.0, pilot) → export_to_jsonl → check_pilot_session --plans plans.json plans_grass.json: travní i smíšená sezení OK, dropouty správně označeny.
- Preregistrace: dodatek 4 (S-grass, explorativní) v PREREGISTRACE_v1.2_changelog.md.
Navržený commit (po commitu travní studie od webového vlákna): "Grass study: clips repo, prereg addendum 4, metric predictions"

## Nasazení Codex — 14. 10. 2026

- Zachována původní URL Apps Scriptu, vlastnosti skriptu a pilotní režim. Nová implementace: verze 3; 213 smíšených + 154 travních plánů. Původní řádky před aktualizací zálohovány neveřejně a následně porovnány.
- `hatsim-study/clips-grass`: 73 MP4, 210 761 618 bajtů; lokálně ověřeny všechny SHA-256 podle dodaného manifestu. Pages z `main` a kořene repozitáře.
- Obnoveny verze URL JS/CSS pro cache (`20261014-grass`). Nabídka trávy uvádí skutečný rozsah 24–40 úloh; popis smíšené studie nezávisí na právě otevřené části při přepnutí jazyka.
- Souhlas v1.1: odstraněn rozpor o nepředávání dat třetím stranám versus Google/GitHub hosting; bez nezaručeného tvrzení o zpracování výhradně v EU. Kontakt pověřence opraven na dpo@cvut.cz podle https://www.cvut.cz/ochrana-osobnich-udaju-gdpr. Kontakt řešitele zůstává richtrad@fit.cvut.cz.
- Technické testy jsou syntetické; lidský travní pilot a posouzení jeho odpovědí se tím nenahrazují.

- Úplný test prohlížečem zachytil starý počet úloh na obrazovce po cvičení; `practiceDone()` nyní znovu vykreslí délku a přestávku podle přiděleného plánu. Text přestávky nepředpokládá, že jde přesně o polovinu.
- Doplněno při skutečném průchodu: debrief nezobrazuje autorské HTML komentáře, prázdnou variantu odměny ani nevyplněný token kódu. Ukáže se až po potvrzení posledních zápisů. Rozlišen kód pozorovatele pro návrat a kód dokončení pro odvolání dat. Exportér převádí číselně typované identifikátory klipů z Google Tabulek na text; původní surová data nezměněna.
