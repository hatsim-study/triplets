# Podklad pro žádost o posouzení etickou komisí

**Verze dokumentu:** ethics_application_cs v1.0, 10. 10. 2026
**Určeno pro:** [DOPLNÍ AUTOR: Etická komise ČVUT v Praze / etická komise fakulty …]
**Stav:** podklad k podání; žádný konfirmační hlas nebude sebrán před kladným vyjádřením komise.

---

## 1. Název projektu

Vnímání podobnosti dynamických vizuálních materiálů: online trojicová studie pro validaci počítačové míry podobnosti videí (pracovní označení studie: trojicová studie HAT-SIM).

## 2. Řešitel a pracoviště

- Hlavní řešitel: [DOPLNÍ AUTOR: jméno, titul, pracoviště, e-mail, telefon]
- Spoluřešitelé: [DOPLNÍ AUTOR]
- Pracoviště: [DOPLNÍ AUTOR: fakulta a katedra/ústav, ČVUT v Praze]
- Financování: [DOPLNÍ AUTOR: grant / institucionální podpora / bez financování]
- Zamýšlený výstup: článek do recenzovaného sborníku z oboru počítačového vidění (podání na konferenci CVPR 2027) a zveřejnění anonymního datového souboru.

## 3. Cíl studie

Studie ověřuje, zda pevný (nenaučený) počítačový deskriptor podobnosti dynamických textur predikuje většinovou lidskou volbu v trojicové úloze alespoň tak dobře jako nejsilnější naučený srovnávací model. Vedlejším cílem je změřit lidský strop shody (míru, do níž se lidé shodnou mezi sebou), vůči němuž se shoda počítačových měr interpretuje. Studie neověřuje nic o účastnících samotných; lidské úsudky slouží výhradně jako referenční data pro hodnocení algoritmů.

Primární hypotéza a plán analýzy jsou předem registrovány (oddíl 13); žádná hypotéza nebude po zahájení sběru dat měněna.

## 4. Design studie

| Položka | Hodnota |
|---|---|
| Typ | online behaviorální studie, úloha nuceného výběru ze dvou alternativ s možností „nelze rozhodnout“, zcela anonymní |
| Úloha | trojice videí: referenční klip nahoře, dva kandidáti dole; otázka: „Který z dolních klipů je celkovým dynamickým vizuálním charakterem podobnější hornímu?“; odpovědi: levý / pravý / nelze rozhodnout |
| Délka sezení | 60 úloh, přibližně 12–15 minut, přestávka po 30 úlohách |
| Počet sezení na osobu | nejvýše 2 |
| Cílový počet | ≥ 75 pozorovatelů, ≈ 150 + 49 sezení, ≈ 11 800 trialů před vyřazením (hlavní studie ≈ 8 900 + doplňková rodina S-dyn ≈ 2 900) |
| Prostředí | webová aplikace v prohlížeči účastníka; videa přehrávána ve smyčce bez zvuku; vyžadován počítač s oknem ≥ 900 px (mobilní zařízení odmítnuta) |
| Randomizace | strana kandidátů (vlevo/vpravo), pořadí trojic v sezení, počáteční fáze smyčky každého klipu |
| Kontrola kvality v sezení | 10 % trialů (6) jsou zrcadlená opakování dřívější trojice téhož sezení; 5 % trialů (3) jsou kontrolní trojice se zjevnou odpovědí (jeden kandidát je totožný s referencí) |
| Sběr hlasů | každá trojice sbírá hlasy, dokud nemá ≥ 5 rozhodnutých hlasů od různých pozorovatelů (nejvýše 7); vybraná podmnožina trojic dostane druhý nezávislý panel pozorovatelů pro odhad lidského stropu |
| Pilot | ≤ 10 pozorovatelů × 60 trialů na stimulech mimo hlavní studii; pilotní data se do hlavní analýzy nikdy nespojují; stejný souhlas a stejná pravidla |

Účastník nedostává zpětnou vazbu o „správnosti“ odpovědí (správná odpověď neexistuje; kontrolní trojice se nijak neodlišují).

## 5. Stimuly

- Zdroj: **DynTex** — veřejná akademická databáze dynamických textur (Péteri, Fazekas, Huiskes: *DynTex: A comprehensive database of dynamic textures*, Pattern Recognition Letters 2010), poskytovaná pro výzkumné účely. [DOPLNÍ AUTOR: potvrdit podmínky licence; datum stažení snapshotu.]
- Obsah: krátké záběry přírodních scén a materiálů — voda, vlny, vegetace ve větru, oheň, kouř, tkaniny, vlajky, pravidelné povrchy, vzdálený provoz. Žádný klip nezobrazuje osoby zblízka; **v několika klipech se v dálce objevují postavy nebo vozidla**, bez rozpoznatelných rysů obličeje či registračních značek. Klipy neobsahují násilný, sexuální ani jinak citlivý obsah. Všech 400 videí snapshotu bylo vizuálně anotováno (scéna, sémantická třída); anotace je součástí zmrazeného balíčku stimulů.
- Technické parametry prezentace: H.264 mp4, 352 × 288 px, 10 s (250 snímků), přehrávání ve smyčce, bez zvuku. Žádný klip neobsahuje blikání ani záblesky; některé obsahují rychlý přirozený pohyb. V doplňkové rodině S-dyn jsou některé klipy téhož videa prezentovány ve změněné rychlosti přehrávání (1,5× a 2×), vždy bez vypouštění obrazového obsahu nad rámec rovnoměrného podvzorkování; ani tyto varianty neobsahují blikání.
- Zmrazení: manifest stimulů s otisky SHA-256, seznam trojic a seedy randomizace jsou zmrazeny před sběrem dat a budou zveřejněny.

## 6. Nábor účastníků

- Kanály: [DOPLNÍ AUTOR: e-mail studentům předmětů …, studentské kanály fakulty, interní kanály pracoviště, osobní sítě řešitelů, případně veřejný příspěvek na sociální síti].
- Náborové texty (e-mail, krátký příspěvek, připomínka) jsou přiloženy (`recruitment_cs.md`, `recruitment_en.md`). Neuvádějí očekávaný výsledek ani srovnávané algoritmy.
- Odměna: [DOPLNÍ AUTOR: bez odměny / zápočtový kredit … — v tom případě: účast je jednou z více rovnocenných možností získání kreditu, neúčast nemá žádné důsledky; vyučující nevidí, kdo se zúčastnil, pouze kódy dokončení, které si student sám uplatní].
- Vztah závislosti: [DOPLNÍ AUTOR: pokud jsou oslovováni studenti řešitele — popsat, jak je zajištěno, že neúčast ani výsledky nemají vliv na hodnocení].

## 7. Kritéria zařazení a vyloučení

Zařazení: věk ≥ 18 let; běžný zrak nebo zrak korigovaný brýlemi/čočkami; přístup k počítači s aktuálním prohlížečem a stabilním připojením. Jazyk rozhraní čeština nebo angličtina.

Vyloučení (samovyloučení na základě informace v souhlasu): fotosenzitivní epilepsie nebo nepříjemné pocity při sledování rychle se pohybujících obrazů. Aplikace technicky odmítne mobilní zařízení a okna užší než 900 px a nepřijme třetí sezení téhož pseudonymního identifikátoru.

Věk a zrak se ověřují pouze čestným prohlášením (zaškrtnutí v souhlasu, resp. volba v dotazníku); jiné ověření není při anonymním online sběru možné.

## 8. Průběh z pohledu účastníka

1. Otevření odkazu; kontrola zařízení a šířky okna.
2. Informovaný souhlas (přiložen jako `consent_cs.md` / `consent_en.md`) s odkazem na informační list (`info_sheet_*.md`); šest zaškrtávacích prohlášení, bez nich nelze pokračovat; uloží se verze textu a časová značka.
3. Tři údaje: věková kategorie (pásma), korekce zraku (ano/ne), jazyk.
4. Instrukce (`instructions_*.md`) a 1–2 cvičné trojice (nezaznamenávají se).
5. 60 úloh, přestávka po 30.
6. Debriefing (`debrief_*.md`): poděkování, vysvětlení účelu bez prozrazení hypotéz, kód dokončení, poučení o odvolání dat.

Účastník může kdykoli skončit zavřením okna; neúplná sezení se do analýzy nezahrnují.

## 9. Rizika, zátěž a jejich minimalizace

| Riziko / zátěž | Hodnocení | Opatření |
|---|---|---|
| únava očí, mentální únava | nízké; srovnatelné s 15 minutami sledování videa | sezení omezeno na 60 úloh; přestávka po 30; žádný časový limit na úlohu; možnost kdykoli skončit; nejvýše 2 sezení |
| fotosenzitivní reakce | velmi nízké: stimuly bez blikání/záblesků, přirozený pohyb | explicitní upozornění v souhlasu, náboru i informačním listu; doporučení neúčastnit se při fotosenzitivní epilepsii |
| nepříjemný obsah | žádné: přírodní scény a materiály, bez osob zblízka | anotace všech stimulů před sběrem |
| pocit selhání / hodnocení | nízké | účastník je informován, že správné odpovědi neexistují; žádná zpětná vazba o výkonu; kontrolní trojice nejsou označeny |
| ztráta soukromí | velmi nízké | žádné přímé identifikátory, žádná IP adresa, pseudonymní identifikátor; viz oddíl 10 |
| časová zátěž | 12–15 minut na sezení | uvedeno v náboru i souhlasu |

Studie nezahrnuje klamání účastníků: účel (porovnání počítačových měr s lidským úsudkem) je sdělen předem; neuvádí se pouze konkrétní srovnávané algoritmy a očekávaný výsledek, což je v debriefingu výslovně zdůvodněno. Přítomnost opakovaných a kontrolních trojic je účastníkům v instrukcích oznámena neutrálně.

## 10. Data a ochrana osobních údajů

**Zaznamenávané údaje** (úplný výčet; formát je specifikován ve společném datovém schématu studie):
- na úrovni trialu: identifikátor sezení, pseudonymní identifikátor pozorovatele, pořadí trialu, identifikátor trojice a zobrazených klipů, strana prezentace, odpověď, reakční čas, fáze smyček, příznaky opakování/kontroly, počet chyb přehrávání, časová značka UTC, jazyk rozhraní, rozlišení obrazovky a poměr pixelů;
- na úrovni sezení: identifikátor sezení a pozorovatele, pořadí sezení pozorovatele (1/2), verze a čas souhlasu, věková kategorie, korekce zraku, jazyk, čas začátku a konce, počet dokončených trialů, řetězec user agent, kód dokončení.

**Nezaznamenává se:** jméno, e-mail, IP adresa (server ji neloguje; [DOPLNÍ AUTOR: potvrdit konfiguraci webserveru/reverzní proxy a hostingu]), přesný věk, pohlaví, poloha, cookies třetích stran, žádný sledovací kód.

**Pseudonymizace:** `observer_id` je náhodný řetězec vygenerovaný prohlížečem při prvním spuštění a uložený v lokálním úložišti prohlížeče; slouží jen k zabránění opakovanému zobrazení téže trojice a k omezení na dvě sezení. Není odvozen z žádného osobního údaje. Kód dokončení je náhodný a je jediným prostředkem, jímž účastník může své záznamy označit k výmazu.

**Charakter dat z hlediska GDPR:** Soubor neobsahuje přímé identifikátory; řetězec user agent a rozlišení obrazovky jsou technické údaje s omezeným identifikačním potenciálem. Z opatrnosti se se surovými daty zachází jako s pseudonymními osobními údaji. Právní základ: [DOPLNÍ AUTOR: čl. 6 odst. 1 písm. a) — souhlas / čl. 6 odst. 1 písm. e) — vědecký výzkum ve veřejném zájmu; konzultovat s pověřencem]. Správce: [DOPLNÍ AUTOR: ČVUT v Praze, fakulta]; pověřenec: [DOPLNÍ AUTOR]. Zvláštní kategorie údajů se nezpracovávají (korekce zraku ano/ne není považována za údaj o zdravotním stavu nad rámec běžné popisné charakteristiky; [DOPLNÍ AUTOR: potvrdit s pověřencem; alternativně položku zcela vypustit]).

**Uložení a zabezpečení:** server [DOPLNÍ AUTOR: umístění, v EU; správce serveru]; přenos šifrován (HTTPS); přístup k surovým datům mají pouze řešitelé; zálohy na úložišti pracoviště. Doba uchování surových pseudonymních dat: [DOPLNÍ AUTOR: např. 10 let od publikace] podle [DOPLNÍ AUTOR: vnitřní předpis ČVUT o správě výzkumných dat].

**Odvolání souhlasu / výmaz:** do [DOPLNÍ AUTOR: datum uzavření sběru] na základě kódu dokončení; po tomto datu se ze surových dat odstraní user agent a kód dokončení, data se sloučí a stanou anonymními; výmaz již není technicky možný, o čemž je účastník informován v souhlasu i debriefingu.

**Zveřejnění:** Anonymní soubor (hlasy po trojicích a sezeních, reakční časy, věková kategorie, korekce zraku, jazyk, rozlišení; bez user agent, bez kódů dokončení, bez časových značek s přesností vyšší než den [DOPLNÍ AUTOR: potvrdit granularitu]) bude zveřejněn spolu s publikací v otevřeném repozitáři [DOPLNÍ AUTOR: Zenodo / OSF / institucionální repozitář]. Zveřejní se také manifest stimulů s otisky SHA-256, nikoli samotná videa (licence DynTex) [DOPLNÍ AUTOR: potvrdit].

## 11. Vyřazovací pravidla (zmrazena v preregistraci před sběrem)

Pravidla slouží výhradně k zajištění kvality dat a nezávisí na žádném osobním atributu. Vyřazení se provádí po skončení sběru, před výpočtem jakékoli metriky (dvoustupňové odemčení: nejprve kontrola kvality bez metrik, poté metriky). Všechny počty vyřazení se hlásí.

Vyřazení pozorovatele (všechny jeho hlasy):
1. více než jedno selhání kontrolních trojic se zjevnou odpovědí;
2. konzistence na opakovaných trojicích < 0,6 při ≥ 5 opakováních;
3. medián reakčního času < 1,5 s nebo > 60 s;
4. podíl odpovědí „nelze rozhodnout“ > 40 %;
5. neúplné sezení (< 80 % trialů).

Vyřazení trialu: reakční čas < 1 s; technická chyba přehrávání zaznamenaná aplikací.

Vyřazení trojice z primárního hodnocení: podíl „nelze rozhodnout“ > 50 % sebraných hlasů (hlásí se jako *undecidable*).

Účastník vyřazený podle těchto pravidel o tom není informován (nemá to pro něj žádné důsledky; data zůstávají anonymní) a nárok na případnou odměnu tím není dotčen.

## 12. Informovaný souhlas

Souhlas je udělován elektronicky před prvním trialem; text je přiložen (`consent_cs.md`, `consent_en.md`), delší informační list rovněž (`info_sheet_cs.md`, `info_sheet_en.md`). Souhlas obsahuje: účel, průběh, dobrovolnost a možnost kdykoli skončit, rizika včetně poznámky k fotosenzitivitě, odměnu, výčet zaznamenávaných údajů, právní základ, dobu uchování, zveřejnění anonymních dat, práva subjektu údajů, kontakt na řešitele, pověřence a etickou komisi, šest zaškrtávacích prohlášení (včetně věku ≥ 18) a potvrzovací tlačítko. Verze textu a čas potvrzení se ukládají ke každému sezení.

## 13. Preregistrace

Studie je předem registrována v dokumentu *Preregistrace trojicové studie HAT-SIM v9*, verze 1.1 (9. 10. 2026) s changelogem 1.1 → 1.2 (10. 10. 2026); oba dokumenty jsou přiloženy k žádosti a budou zveřejněny s otiskem SHA-256 [DOPLNÍ AUTOR: po vyjádření komise také registrace na OSF, odkaz]. Preregistrace stanoví: jedinou konfirmační hypotézu, primární endpoint a test, dimenzování (≥ 600 testovacích trojic, ≥ 5 hlasů na trojici, ≥ 75 pozorovatelů), konstrukci stimulů, definici většiny a lidského stropu, vyřazovací pravidla z oddílu 11, sekundární analýzy a pravidla, podle nichž se dokument po zahájení sběru již nemění.

## 14. Harmonogram

| Fáze | Termín |
|---|---|
| podání žádosti etické komisi | [DOPLNÍ AUTOR] |
| pilot (≤ 10 osob, stimuly mimo hlavní studii) | [DOPLNÍ AUTOR: po vyjádření komise] |
| hlavní sběr dat | [DOPLNÍ AUTOR: od – do] |
| uzávěrka pro odvolání dat | [DOPLNÍ AUTOR: = konec sběru] |
| analýza a sepsání | [DOPLNÍ AUTOR] |
| zveřejnění anonymních dat | [DOPLNÍ AUTOR: s publikací] |

## 15. Přílohy

1. `consent_cs.md`, `consent_en.md` — informovaný souhlas
2. `info_sheet_cs.md`, `info_sheet_en.md` — informační list a FAQ
3. `instructions_cs.md`, `instructions_en.md` — instrukce k úloze
4. `recruitment_cs.md`, `recruitment_en.md` — náborové texty
5. `debrief_cs.md`, `debrief_en.md` — debriefing
6. Preregistrace v1.1 a changelog v1.2
7. [DOPLNÍ AUTOR: snímky obrazovky aplikace; ukázkové snímky stimulů; stanovisko pověřence pro ochranu osobních údajů, je-li vyžadováno]

## 16. Prohlášení řešitele

Prohlašuji, že studie bude provedena v souladu s výše uvedeným popisem, s platnými právními předpisy o ochraně osobních údajů a s vnitřními předpisy ČVUT v Praze; že žádná data od účastníků nebudou sbírána před kladným vyjádřením etické komise (s výjimkou interního technického testování aplikace řešiteli); a že jakákoli podstatná změna designu bude komisi předložena k posouzení.

[DOPLNÍ AUTOR: jméno, datum, podpis]
