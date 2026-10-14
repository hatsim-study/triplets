# Nasazení Google Apps Script backendu (klikací postup)

Backend je jeden soubor `apps_script/Code.gs`. Tabulku otevírá podle vlastnosti skriptu `SPREADSHEET_ID`, takže může běžet i v samostatném projektu Apps Script. Drží jen počitadla použití plánů a záznamy (trialy, sezení, cvičení). Žádné IP adresy, e-maily ani Google účty pozorovatelů se neukládají.

## 1. Nová tabulka a skript

1. Na Google Drive: **Nový → Tabulky Google**, pojmenujte např. `HATSIM_triplets_data`.
2. V tabulce: **Rozšíření → Apps Script**, nebo vytvořte samostatný projekt na `https://script.google.com/` pod účtem vlastníka tabulky.
3. Smažte obsah editoru a vložte celý obsah souboru `apps_script/Code.gs`. Uložte (ikona diskety / Ctrl+S).
4. V **Nastavení projektu (ozubené kolo) → Vlastnosti skriptu** uložte dvě vlastnosti: `SPREADSHEET_ID` = ID tabulky mezi `/d/` a `/edit` v její adrese; `ADMIN_TOKEN` = dlouhý náhodný řetězec (např. 32 náhodných bajtů v hexadecimálním zápisu). Token nevkládejte do veřejného repozitáře ani do `docs/config.js`.
   *(Bez tokenu je export a registrace plánů vypnutá – `CHANGE_ME`.)*
5. (Volitelné) V editoru vyberte funkci `setupSheets` a klikněte **Spustit** → potvrďte oprávnění. Google uděluje širší oprávnění k Tabulkám; tento kód otevírá pouze ID nastavené v `SPREADSHEET_ID`. Vytvoří listy `plans`, `plan_usage`, `sessions`, `trials`, `practice` s hlavičkami. Listy se jinak vytvoří samy při prvním použití.

## 2. Nasazení jako webová aplikace

1. Vpravo nahoře **Nasadit → Nové nasazení**.
2. Typ (ozubené kolo vlevo) → **Webová aplikace**.
3. Popis libovolný; **Spustit jako: Já** (vlastník tabulky); **Kdo má přístup: Kdokoli** (anonymní pozorovatelé bez přihlášení).
4. **Nasadit** → potvrďte oprávnění → zkopírujte **URL webové aplikace** (končí `/exec`).
5. Vložte URL do `docs/config.js` → `APPS_SCRIPT_URL`.

Ověření: otevřete v prohlížeči `…/exec?action=health` → `{"ok":true,…}`.

> Po každé změně kódu je nutné **Nasadit → Spravovat nasazení → (tužka) → Verze: Nová verze → Nasadit**, jinak běží stará verze. URL zůstává stejná.

## 3. Registrace plánů sezení

Backend musí znát seznam plánů (id, kolo, panel, počet trialů, režim):

* buď `python register_plans.py --url <URL/exec> --token <ADMIN_TOKEN> --index plan_index.json`
* nebo ručně: otevřete list `plans` a importujte `plan_index.csv` (**Soubor → Importovat → Nahrát → Připojit k aktuálnímu listu**, oddělovač čárka). Hlavička musí být `plan_id, round, panel, n_trials, mode`.

Kontrola: `…/exec?action=status` → `plans_total: 213`.

Stejně se později zaregistrují doplňkové plány (`plans_topup_index.csv`, viz README_static.md → Top-up).

## 3b. Aktualizace na dvě studie (tráva) — 13. 10. 2026

Pokud už skript běží (pilot smíšené studie), přidání travní studie je **nová verze téže webové aplikace** — URL `…/exec` zůstává, `config.js` se nemění:

1. V editoru Apps Script nahraďte obsah `Code.gs` novým souborem `apps_script/Code.gs` (přidává parametr `study`, oddělená počitadla, sloupce `study`/`study_part`). Uložit.
2. **Nasadit → Spravovat nasazení → (tužka) → Verze: Nová verze → Nasadit.** Staré řádky v listech zůstávají; chybějící sloupce (`study`, `study_part`) skript doplní na konec hlaviček při prvním zápisu (nebo spusťte `setupSheets`).
3. Zaregistrujte travní plány: `python register_plans.py --url <URL/exec> --token <ADMIN_TOKEN> --index docs/plans_grass.json` (nebo import `plan_index_grass.csv` do listu `plans`; hlavička `plan_id, round, panel, n_trials, mode, study`). Už registrované smíšené plány se přeskočí (idempotentní).
4. Kontrola: `…/exec?action=status` → `plans_total: 367`, `studies.grass.plans: 154`; `…/exec?action=next_plan&observer_id=obs_test000000&mode=main&study=grass` vrátí plán `GR*`/`GP*` (testovací rezervace vyprší za 90 min, nebo ji ukončete POSTem `session_end` s `completed:false`).
5. Nahrajte na GitHub Pages `docs/plans_grass.json`, `docs/clips_index_grass.json` a upravené `docs/*.js`, `index.html`, `style.css`, `texts/instructions_*.md`.

## 4. Chování API (pro kontrolu)

| volání | odpověď |
|---|---|
| `GET …/exec?action=next_plan&observer_id=obs_xxx&mode=main&study=mixed|grass&session_number=1` | `{plan_id, round, study, session_id, resumed, session_number}` – nejméně použitý nedokončený plán dané studie; 2. sezení ze stejného kola (per studie); max 2 sezení na studii; rezervace 90 min; `{error:"max_sessions"}` / `{error:"no_plan_available"}` |
| `GET …/exec?action=status` | pokrytí: plány celkem / dokončené / rezervované, po studiích (`studies.mixed`, `studies.grass`) a po kolech, počet řádků trialů, počet pozorovatelů |
| `GET …/exec?action=export&token=…` | JSON všech listů (`{plans, plan_usage, sessions, trials, practice, exported_utc}`) |
| `POST …/exec` (Content-Type `text/plain`, tělo JSON) | `type: trial` (idempotentní na `session_id`+`trial_index`), `session_start`, `session_end` (uzavře rezervaci plánu jako `completed`/`abandoned`), `practice_trial`, `register_plans` (s tokenem) |

Proč `text/plain`: Apps Script neumí odpovědět na CORS preflight (OPTIONS); „jednoduchý“ požadavek bez preflightu je POST s `text/plain`, který Apps Script přijme a odpověď `ContentService` je čitelná z libovolného originu. Apps Script odpovídá přesměrováním (302) na `script.googleusercontent.com`; `fetch(..., {redirect:"follow"})` to zvládne.

## 5. Limity a provoz

* Kvóty Apps Script (bezplatný účet): ~20 000 volání URL Fetch/den se netýká (my jsme volaní), ale **celkový běh skriptu 90 min/den** a **30 souběžných běhů**. Každý POST trialu běží ~0,3–1 s (zámek + zápis + kontrola duplicit); 60 trialů × 100 sezení/den ≈ 6 000 volání ≈ 1–1,5 h běhu – při větším náporu rozložte sběr do více dní nebo nasaďte backend `web/` (Python).
* `recordTrial_` kontroluje duplicity čtením sloupců listu `trials`; při > ~30 000 řádcích se zpomalí (≈ 1 s) – pro hlavní studii (~13 000 řádků) v pořádku.
* Tabulku zálohujte: **Soubor → Vytvořit kopii** nebo `…?action=export&token=…` → `export.json` → `python export_to_jsonl.py --json export.json --out analysis_data/`.
* Zámek `LockService` serializuje zápisy; souběžní pozorovatelé čekají max 30 s.
