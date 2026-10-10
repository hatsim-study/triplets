# Nasazení Google Apps Script backendu (klikací postup)

Backend je jeden soubor `apps_script/Code.gs` vázaný na Google tabulku. Drží jen počitadla použití plánů a záznamy (trialy, sezení, cvičení). Žádné IP adresy, e-maily ani Google účty pozorovatelů se neukládají.

## 1. Nová tabulka a skript

1. Na Google Drive: **Nový → Tabulky Google**, pojmenujte např. `HATSIM_triplets_data`.
2. V tabulce: **Rozšíření → Apps Script** (otevře se editor s prázdným `Code.gs`).
3. Smažte obsah editoru a vložte celý obsah souboru `apps_script/Code.gs`. Uložte (ikona diskety / Ctrl+S).
4. Nastavte administrátorský token: v levém menu **Nastavení projektu (ozubené kolo) → Vlastnosti skriptu → Přidat vlastnost**: název `ADMIN_TOKEN`, hodnota = dlouhý náhodný řetězec (např. 32 znaků). Uložit.
   *(Bez tokenu je export a registrace plánů vypnutá – `CHANGE_ME`.)*
5. (Volitelné) V editoru vyberte funkci `setupSheets` a klikněte **Spustit** → potvrďte oprávnění (skript smí upravovat tuto tabulku). Vytvoří listy `plans`, `plan_usage`, `sessions`, `trials`, `practice` s hlavičkami. Listy se jinak vytvoří samy při prvním použití.

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

## 4. Chování API (pro kontrolu)

| volání | odpověď |
|---|---|
| `GET …/exec?action=next_plan&observer_id=obs_xxx&mode=main&session_number=1` | `{plan_id, round, session_id, resumed, session_number}` – nejméně použitý nedokončený plán; 2. sezení ze stejného kola; rezervace 90 min; `{error:"max_sessions"}` / `{error:"no_plan_available"}` |
| `GET …/exec?action=status` | pokrytí: plány celkem / dokončené / rezervované, po kolech, počet řádků trialů, počet pozorovatelů |
| `GET …/exec?action=export&token=…` | JSON všech listů (`{plans, plan_usage, sessions, trials, practice, exported_utc}`) |
| `POST …/exec` (Content-Type `text/plain`, tělo JSON) | `type: trial` (idempotentní na `session_id`+`trial_index`), `session_start`, `session_end` (uzavře rezervaci plánu jako `completed`/`abandoned`), `practice_trial`, `register_plans` (s tokenem) |

Proč `text/plain`: Apps Script neumí odpovědět na CORS preflight (OPTIONS); „jednoduchý“ požadavek bez preflightu je POST s `text/plain`, který Apps Script přijme a odpověď `ContentService` je čitelná z libovolného originu. Apps Script odpovídá přesměrováním (302) na `script.googleusercontent.com`; `fetch(..., {redirect:"follow"})` to zvládne.

## 5. Limity a provoz

* Kvóty Apps Script (bezplatný účet): ~20 000 volání URL Fetch/den se netýká (my jsme volaní), ale **celkový běh skriptu 90 min/den** a **30 souběžných běhů**. Každý POST trialu běží ~0,3–1 s (zámek + zápis + kontrola duplicit); 60 trialů × 100 sezení/den ≈ 6 000 volání ≈ 1–1,5 h běhu – při větším náporu rozložte sběr do více dní nebo nasaďte backend `web/` (Python).
* `recordTrial_` kontroluje duplicity čtením sloupců listu `trials`; při > ~30 000 řádcích se zpomalí (≈ 1 s) – pro hlavní studii (~13 000 řádků) v pořádku.
* Tabulku zálohujte: **Soubor → Vytvořit kopii** nebo `…?action=export&token=…` → `export.json` → `python export_to_jsonl.py --json export.json --out analysis_data/`.
* Zámek `LockService` serializuje zápisy; souběžní pozorovatelé čekají max 30 s.
