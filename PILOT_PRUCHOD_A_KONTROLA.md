# Lidský pilot — průchod a kontrola (verze 10. 10. 2026)

## A. Před pilotem (stav: hotovo kromě bodu 3)
1. `docs/config.js`: `MODE: "pilot"`, `APPS_SCRIPT_URL` = ostrý `/exec` (Codex ověřil GET i POST). 
2. Texty v aplikaci používají tokeny `{{N_TRIALS}}`, `{{DURATION}}`, `{{BREAK_SENTENCE}}` → v pilotu se zobrazí „20 úloh, 4–6 minut, bez přestávky", v hlavní studii „60 úloh, 12–15 minut, přestávka po 30". (Změna v tomto commitu: app.js, i18n.js, consent_cs/en.md, debrief_cs/en.md.)
3. Autorská pole `[DOPLNÍ AUTOR …]` v souhlasu — viz AUTORSKA_POLE.md; bez nich účastníci uvidí hranaté závorky.

## B. Průchod jedním sezením (Tomáš nebo kolega, ~6 minut)
1. Otevřít https://hatsim-study.github.io/triplets/ v Chrome/Firefox/Edge na počítači (šířka ≥ 900 px).
2. Zvolit jazyk; přečíst souhlas — ověřit, že věta o délce říká **20 úloh / 4–6 minut / bez přestávky**; zaškrtnout, pokračovat.
3. Demografie → instrukce (ověřit „20 kroků") → 3 cvičné trialy (odpovědi se nepočítají).
4. 20 trialů: u každého počkat, až tlačítka ožijí (2 s), odpovědět ← / → / nelze rozhodnout. U alespoň jednoho trialu schválně počkat 20 s (test RT), u jednoho zvolit „nelze rozhodnout".
5. Konec: zobrazí se kód dokončení — opsat si ho. Debriefing přečíst.
6. Zkusit druhé sezení ve stejném prohlížeči: v pilotu musí aplikace odmítnout (1 sezení na pozorovatele).
7. Poznamenat: prohlížeč + verze, trvání, cokoli divného (prodleva načítání videí, trhání smyčky, chybějící překlad).

## C. Kontrola záznamů (Claude, po dodání exportu)
1. Export: `…/exec?action=export&token=ADMIN_TOKEN` → uložit jako `export.json` (token zůstává u Tomáše; soubor export.json mi stačí předat na disk, např. do `outputs\hatsim_github_setup_20261010\repos\triplets\pilot_data\`).
2. `python export_to_jsonl.py --json export.json --out pilot_data/analysis_data`
3. `python check_pilot_session.py --data pilot_data/analysis_data --plans docs/plans.json` → per sezení: 20/20 trialů bez mezer, shoda s plánem (trojice, strany, zrcadlení opakování), platné odpovědi, RT, fáze smyček, session_end + kód, 3 cvičné trialy, chyby přehrávání.
4. `python ../../../analysis/qc.py …` (pipeline z triplet_study_package) — pilotní data se nikdy nespojí s hlavní analýzou; slouží k odhadu délky trialu a podílu „nelze rozhodnout".

## D. Co pilot rozhodne
- medián RT na trial (očekávání 4–8 s) → odhad délky hlavního sezení;
- podíl „nelze rozhodnout" (práh pro vyřazení 40 %);
- technické chyby přehrávání (pokud > 1 % trialů, zmenšit klipy / změnit hosting);
- srozumitelnost instrukcí (volná zpětná vazba).
Po pilotu: `MODE: "main"`, `CONSENT_VERSION: "v1.0"` (po doplnění autorských polí), commit, push.
