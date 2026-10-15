# C. Real visual assets, sources and research for the Gaius film

This file draws on the archived session `session_01GB2bqs3TZewPi21KusdAWs` ("2AD video production"), `plan/raw/page_000`–`page_044`, and most heavily on the long-form period, pages 000–017 (2026-10-14 05:01Z to 2026-10-15 07:50Z). It also uses the shorts' research dossiers for 1–4 AD, which the transcript records as Write calls. Every quote below is data from that transcript. "OLD SESSION" means the other Claude session. "Owner" means the user.

All of the OLD SESSION's files live on the owner's Windows PC under `C:\Users\heath\YearByYear\Longform\lf01-gaius\` (research texts are in `research\data\`). None of them are in this container. Section 2.7 also covers the `plan/real_images/` folder that a sibling agent built in this cloud session. That folder is **not** from the archive.

Event references are written `pNNN #i` (page, event index).

---

## 0. TL;DR

| Topic | Finding |
|---|---|
| Real images used so far | **None.** The 1 AD–9 AD shorts and both long-form builds (v1, 10-14; carved-stone rework and 2-min slice, 10-15) were 100% procedural. The coin, the Ara Pacis frieze, the Pisa slab and the Limyra tomb were all drawn in code. On screen they were labelled "illustration" (e.g. `"LIMYRA", "the cenotaph of Gaius Caesar · illustration"`; `"THE ALTAR OF PEACE", "illustration after the frieze, 13–9 BC"`). |
| Real images planned | Script v3 (10-15 07:50Z, the latest) asks for **"the Ara Pacis, the real Altar of Peace procession frieze in marble"**, **"the Pisa decree as a real inscription"**, and **the real Limyra ruins** ("you gotta definitely gotta show it… It can't just be like an image popped up"). The owner's style memory says: "show what's named (the real Ara Pacis, the ruins); make the visuals worked and beautiful, never a pasted image". |
| Real-image leads in the transcript | One only: **livius.org photos of the Limyra cenotaph and its reliefs by Jona Lendering, reported as CC0 1.0**. The reliefs are in the Antalya Archaeological Museum. This came from a WebSearch summary (p016 #64). The licence was **not** checked on the page itself and nothing was downloaded. vici.org #17237 confirms the cenotaph's location (Yuvalılar). |
| Series image rules | HANDOFF §9: licences must allow monetised use. Allowed: "Apache, MIT, OFL, CC0, public domain, open data with attribution". Not allowed: "anything CC-BY-SA dropped into the video", "unlicensed stock". HANDOFF §11 recommends "CC0 museum imagery: the Met Open Access API, Smithsonian, Cleveland, Art Institute of Chicago … portrait busts of Augustus, Gaius and Tiberius … Animate them with the existing parallax and relief tools, and credit them in the research document." Also: "Mark illustrations as illustrations." |
| Research quality | Strong for v1. The primary texts were downloaded (LacusCurtius Loeb translations, Perseus Gellius, the heurist edition of the Pisa decree) and grepped on 10-14 05:05–05:18Z. `research/research.md` maps each line to its source. A fact-check pass fixed 8+ errors, including "an invented dinner detail". |
| Research gap | Scripts **v2 and v3 (10-15) added new claims with no verification tool calls** (Maecenas's warning, Agrippa's death, Vipsania's tears, the hunger strike, *Pater Patriae*, the ashes in the Mausoleum, an extra Gellius line). `research.md` was never updated for v2 or v3. Some v3 lines also **undo earlier fact-check fixes** (§3.6). |
| Cold-open claims (v3) | All are supportable, with caveats. **"A tomb built for a Roman prince"**: it is a cenotaph (an honorific monument; his remains went to Rome). The owner chose the word "tomb" and dropped "empty". **"Rome even put his name on its coins"**: RIC I² 198–199 (c. 8 BC) and 205–212 (C L CAESARES, from 2 BC). **"At twenty-two … he asked to walk away"**: Dio 55.10a.8 and Velleius 2.102.3; 22 by year count in AD 3, birth month unknown. **"He never made it home"**: rhetorical, since his remains were brought to Rome (Dio 55.12.1; the Pisa decree's *ossa relata*). v3 pays this off later. |
| Owner on accuracy | "we want to be accurate and tell the story, but also do so in a way that grips people" (10-11). "It needs to be dramatic… and that doesn't mean inaccurate" and "we still want to be accurate" (10-15). "if you can't tell the stuff from the historical records, you don't have to bring it up." |

---

## 1. Method

- I flattened all 45 pages (3,212 events) to text and grepped them for: Limyra, cenotaph, tomb, Ara Pacis, Pisa, CIL, denarius, RIC, Lugdunum, coin, museum, photo, CC0, public domain, Wikimedia, Met, livius, real, and the names of the ancient authors.
- I then read every matching event in full.
- Long tool inputs were decoded from the raw JSON: the research dossiers, `lf_art.py`, `lf_scenes.py`, `script_data.py`, `research.md` and `LONGFORM.md`.

---

## 2. Real visual assets

### 2.1 Bottom line: what was used

Nothing real was used. In the OLD SESSION's own words:
- 1 AD technical report (cloud, p043 #59): "**No image generation** … no local diffusion model could be fetched or run usefully on CPU | No AI stills at all | Everything is procedural: map, globe, coins, stone, ink, architecture, the pheasant". It also says: "Illustration ceiling. … A local image model … or permitted museum photography (CC0) would lift this considerably."
- 2 AD technical report (p037 #36): "**Still no people.** As in 1 AD, people appear only as names, coin figures and silhouettes. No museum imagery was added this time; the time went into research and the census map instead."
- Long-form `lf_art.py` docstring (p015 #60): "Art for long-form #1 (Gaius Caesar). **All illustrations**; see research/research.md."
- 1 AD research licence table: "| Coins, inscription, maps, environments | generated in code | Original |". The 2–4 AD dossiers repeat this, for example "Coins, rhinoceros, maps, environments | generated in code | Original".
- One stray line is misleading. In a shorts brainstorm (p022 #79) the OLD SESSION said "We already render real Roman coins, and Augustus and Tiberius have actual coin portraits". In fact the coins are code recreations "after the real coin types".

### 2.2 Series rules that govern real imagery

These rules come from HANDOFF.md as read in p043 #32. The repo's `CLAUDE.md` is the same in substance.
- §9 "Accuracy and licences":
  - "Mark illustrations as illustrations. In 1 AD that covered the inscription, the coins, the environments, the pheasant and the night lights."
  - "**Licences must allow commercial/monetised use.** Allowed: Apache, MIT, OFL, CC0, public domain, open data with attribution."
  - "Not allowed: … anything CC-BY-SA dropped into the video; unlicensed stock".
- §11 "Known weaknesses to improve":
  - "**CC0 museum imagery:** the Met Open Access API, Smithsonian, Cleveland, Art Institute of Chicago. Use real artifacts: portrait busts of Augustus, Gaius and Tiberius; Han tomb figurines and bricks. Animate them with the existing parallax and relief tools, and credit them in the research document."
- The 1 AD cloud container could not reach Wikipedia, museum APIs or NASA (technical report §2). The OLD SESSION on the owner's PC **could** fetch LacusCurtius, Perseus/perseids, heurist.huma-num.fr and vici.org. curl to zh.wikisource sometimes returned a "Wikimedia Error" page (p034 #41, p025 #1).

### 2.3 Item by item

#### A. Limyra: the cenotaph of Gaius ("the tomb")
- **What the sources say.** Velleius 2.102.3: he "died in a city of Lycia which they call Limyra". Dio 55.10a.9: he "took a trading vessel to Lycia, where, at Limyra, he passed away".
- **Real-world evidence found (p016 #61–#64, 10-14 05:07Z):**
  - vici.org #17237 (WebFetch): the page is "a Vici.org entry for the burial site at Limyra, Yuvalılar, Türkiye". It quotes: "*Cenotaph of Gaius Caesar, the adoptive son and heir presumptive of Augustus, who died in Limyra in 4 AD.*" The German note adds that the cenotaph was put up in his honour after his death. The page links to a livius.org article.
  - WebSearch "livius.org Limyra cenotaph Gaius Caesar" summary:
    - "Livius.org's biography stub for Gaius Caesar gives his dates as 20 BCE to 4 CE. It places his death at Limyra in Lycia, around 4, **21 or 22 February**, and notes **he was buried in Rome's Mausoleum of Augustus, with a cenotaph erected at Limyra** … the Limyra memorial was built even though his body lay in Rome."
    - "Livius.org has a photo entry titled 'Limyra, Cenotaph of Gaius Caesar,' dated 4 CE, with a separate entry for the relief. **Jona Lendering took the relief photographs, and the sculpture is held in the Antalya Archaeological Museum. Both are licensed CC0.** The damaged relief entry lists Jona Lendering as creator, the Antalya Archaeological Museum as location, and a CC0 1.0 Universal license."
    - "Livius.org's Limyra town article describes it as a Lycian town … with a mountain acropolis and a port at Phoenix (modern Finike)."
  - URLs returned:
    - `https://www.livius.org/pictures/turkey/turuncova-limyra/limyra-cenotaph-of-gaius-caesar/`
    - `…/limyra-cenotaph-of-gaius-caesar-damaged-relief/`
    - `…/limyra-cenotaph-of-gaius-caesar-relief`
    - the index `https://www.livius.org/pictures/turkey/turuncova-limyra/`
    - `https://livius.org/articles/place/limyra`
    - `https://www.livius.org/articles/person/gaius-caesar/`
- **Scholarship cited** in `research.md` row i9: "The cenotaph at Limyra survives as ruins. | J. Ganzert, *Das Kenotaph für Gaius Caesar in Limyra* (1984)".
- **Accuracy fix (p015 #1, 10-14 05:11Z).** The draft said "Far away, the people of Limyra built a monument for him beside their town." It became "Far away, a monument to him was raised at Limyra. Its ruins are still there." The OLD SESSION did not claim to know who built it.
- **How it was shown:**
  - v1, `l_cenotaph`: `lf_art.cenotaph()` is "the monument at Limyra, as a stylised silhouette" (podium, upper storey, frieze band, pediment).
  - The rework, `o_tomb`/`tomb_env()`, is "a real ruin (podium, standing broken columns, frieze, steps), a big torch, deep night" (p004 #57). It is procedural, not modelled on photos.
  - Lower thirds: v1 "LIMYRA · the cenotaph of Gaius Caesar · illustration". Slice hook: "LIMYRA, IN LYCIA / southern Turkey · the empty tomb of a Roman prince". **The word "empty" must go** (owner, 10-15 07:48Z).
- **The owner's direction (p000 #52, 07:24Z):** "A monument was raised to him and its ruins are still there. So, like, yeah, if you bring that up, like, you gotta definitely gotta show it. Show of the ruins. Um, and when you're showing the ruins and the visuals, like, you gotta make it look nice. It can't just be like an image popped up. You gotta do some work to it to make it, like, really pop. I want you to put that in the notes."
- **"Tomb" vs "empty tomb" (p000 #55, 07:48Z):** "also the tomb thing is confusing. you wrote that its an empty tomb and at the end the big reveal is that it isn't a tomb? but you said it was a tomb. I would just take that out. when you mention it in the beginning and the end you can call it a tomb, but you don't need to mention the empty part. that wasn't a good reveal, so let's not bring attention to it."
- **v3 wording:**
  - Open: "Near the southern coast of Turkey, among the ruins of an ancient town, stands a tomb built for a Roman prince."
  - Close: "And near the southern coast of Turkey, among the ruins of Limyra, the tomb they built for him still stands."
  - Show note: "Night. A torch moves slowly through the ruins at Limyra, over carved stone, broken columns and dust drifting in the light. It has to look beautiful: real light and depth, never a picture that just pops up."
- **Caveat for the new build.**
  - Strictly, the monument is a **cenotaph** (Livius, vici.org, Ganzert). v3 also says his ashes went to "the great tomb Augustus had built for his family", so the film uses "tomb" for two buildings. Keep narration as v3, by the owner's choice. In `research.md`, tag the Limyra line "cenotaph (honorific monument); the remains went to the Mausoleum of Augustus".
  - On-screen labels may say "the cenotaph of Gaius Caesar" without the word "empty".
  - The procedural tomb (standing columns) was **not** checked against photos of the real remains. If real photos are used, the illustration should match them or be labelled an impression.
- **Not found anywhere in the transcript:** any photo of the cenotaph actually fetched, any Wikimedia Commons file, any check of livius' CC0 claim on the page.

#### B. Coins with Gaius's name
- **Type shown everywhere:** the Gaius & Lucius denarius, drawn procedurally by `relief.coin_gaius_lucius()`. The code docstring reads "Standing togate prince, round shield at his outer side, spear behind it (Gaius/Lucius denarius type, RIC I 207)".
- **1 AD research (p043 #58), verbatim:** "*On screen:* a reconstruction of the **Gaius & Lucius denarius** (RIC I 207, Lugdunum mint). Its reverse shows the two princes standing with shields and spears, a simpulum and lituus above, the exergue *C L CAESARES*, and the legend *AVGVSTI F COS DESIG PRINC IVVENT*. The issue is usually dated **2 BC – AD 4**, so it was being struck in AD 1. The coin in the film is drawn procedurally after this type. **It is not a photograph.**"
- **2 AD research, item 27:** "The type (RIC I 207) was struck from about 2 BC into the following decade, so it was still being minted after Lucius's death."
- **Long-form `research.md`:**
  - h1: "Coins showing Gaius before he was 20. | Denarius of Gaius on horseback, c. 8 BC (RIC I² 198–199). C L CAESARES coins from 2 BC (RIC I² 205–212)."
  - b8: "Coins of the two brothers with shields and spears, struck in very large numbers. | RIC I² 205–212 (Lugdunum)".
- **Accuracy fix:** "Millions of them passed through Roman hands" was changed to "Huge numbers of them…" (p015 #1). It is listed in the fact-check log. v3 says "enormous numbers of them passed through Roman hands", which is fine. Avoid any specific number.
- **Slice citation** (`o_coin`): "DENARIUS OF GAIUS AND LUCIUS · C · L · CAESARES". Lower third elsewhere: "DENARIUS OF GAIUS AND LUCIUS / struck from 2 BC".
- **v3 hook:** "Rome even put his name on its coins." This is supported: the legend reads C(aius) and L(ucius) CAESARES, and RIC I² 198–199 reads C CAES[AR]. v3 body: "the same coin as in our shorts". The owner likes the continuity ("I like that you bring up the mint coins because the, that was brought up in the um, shorts").
- **No real coin photo was fetched in the archive.** In this cloud session the sibling agent's `real_images` holds only Met CC0 coins of Octavian and Augustus, each tagged "NOT the Gaius & Lucius (RIC I 207) type" (§2.7). A real RIC I 207 photo still needs a CC0 or public-domain source.

#### C. Ara Pacis (the Altar of Peace)
- **v1 line a10:** "On Rome's great Altar of Peace, a small boy walks in the imperial procession, holding on to a grown man's toga. Many think he is Gaius."
- **research.md a10:** "Child holding a toga on the Ara Pacis: 'many think' it is Gaius. | **Disputed.** Some read the children as foreign princes; see C. B. Rose, *AJA* 94 (1990)."
- The heurist commentary on the Pisa decree (p016 #70) gives another identification: "even depicted on the *Ara Pacis* as Romulus (Lucius) and Ascanius (Caius)". The identifications differ, so keep the hedge.
- **How it was shown:** `lf_art.frieze()`, "a marble procession relief, lit by a moving light (**illustration after the Ara Pacis**)". The frieze is a procedural height field ("togate adults of varied height, one small child holding a toga"). Lower third: "THE ALTAR OF PEACE / illustration after the frieze, 13–9 BC".
- **Owner (p000 #52):** "Many think he is Gaius. Yeah, see, that's thrown in there randomly. Um, I I like that, that that fact's in there. And by the way, **when you show it, you should show the altar of peace that you're talking about in the video.**"
- **v3:** "(SHOW: the Ara Pacis, the real Altar of Peace procession frieze in marble, with light travelling across it. Slowly reveal the little boy clutching a man's toga.)" Narration: "a small boy holds on to the toga of a man most historians think is Agrippa. Many believe the boy is Gaius, holding on to his father."
- **No real Ara Pacis image was fetched in the archive.** The sibling agent's list in this session has CC BY 2.0 Flickr candidates, including ISAW's "Children on the Ara Pacis (II)" and "Procession on the Ara Pacis (I)", to fetch from the laptop (§2.7).

#### D. The Pisa decrees (CIL XI 1420 for Lucius, CIL XI 1421 for Gaius)
- **Text source:** `https://heurist.huma-num.fr/heurist/judaism_and_rome/hml/225`, "The Arch of Gaius at Pisa (CIL XI, 1421)". It was fetched with curl to `research/data/pisa_heurist.xml`, and the Latin was extracted to `pisa_decree_latin.txt` (p016 #69–#74).
  - The heurist record describes the object: "White marble tablet with a border along the left side and the bottom … Fragmented in two pieces but restored. The first six lines, and an introductory heading containing the date and meeting-place of the local senate, are lost."
  - **No location or photo of the stone was recorded.** The transcript never says which museum holds it.
- **Commentary quoted from heurist (p016 #70):**
  - "the achievements of Gaius are celebrated here in almost poetic language: 'snatched away from the Roman people by the cruel fates' (*crudelibus fatis ereptum populo Romano*)".
  - "The anniversary of his death, 21 February, is also to be commemorated annually … 'equivalent to the day of Allia' (*diemque eum quo die Caius Caesar obiit qui dies est ante diem VIIII Kalendas Martias pro Alliensi*) … (Cooley, *Age of Augustus*, p. 223)".
  - "a period of mourning, during which the temples, baths and shops of the town must all be closed, and all must abstain from banqueting".
  - "Gaius and Lucius were the patrons of the colony, the *colonia Obsequens Iulia Pisana*".
- **Key Latin as extracted (p016 #74), verbatim:**
  - "…quod [v(erba) f(acta)] sunt cum in colonia nostra **propter contentiones candidatorum magistratuus non essent** …"
  - "cum a(nte) [d(iem) II]II Nonas Apriles allatus esset nuntius C(aium) Caesarem …"
  - "post consulatum quem ultra finis extremas populi [Ro]mani bellum gerens feliciter peregerat … ipsum volneribus pro re pu[bli]ca exceptis ex eo casu **crudelibus fatis ereptum populo Romano** iam designatu[m i]ustissimum ac simillumum parentis sui virtutibus principem coloniaeque no[st]rae unicum praesidium …"
  - "… ex ea die qu[a ei]us deces(s)us nuntiatus esset usqu ad eam diem qua **ossa relata atque co[nd]ita** iustaque eius Manibus perfecta essent cunctos veste mutata templisqu[e d]eorum immortalium balneisque publicis et tabernis omnibus clausis co[nv]ictibus sese apstinere matronas … sublugere"
  - "di[em]que eum quo die C(aius) Caesar obi(i)t qui dies est **a(nte) d(iem) VIIII K(alendas) Martias pro Alliensi** lu[gub]rem memoriae prodi …"
- **Other sources tried:**
  - Cambridge excerpt PDF (Cooley/Warmington, *Inscriptions of the Roman Empire, AD 14–117*): unreadable, because pypdf and pdftoppm were missing (p016 #52–#58).
  - Scholarship listed in search results: Marotta D'Agata, *Decreta pisana* (1980); Sherk, *Municipal Decrees of the Latin West* (1970); Kleiner, "The Arch of Gaius Caesar at Pisa (CIL XI, 1421)", *Latomus* 44.1 (1985) 156–164.
- **Lucius's decree (CIL XI 1420):** it sets the annual rites for his death day, 20 August (*a.d. XIII Kal. Sept.*) (2 AD research item 25; p041 #26). The OLD SESSION noted that the "XIII K" reading was its own calendar calculation, not a quoted source.
- **How it was shown:** `lf_art.slab()`, "a marble slab with a carved Latin inscription under a raking light", is procedural. Slab text: `PISA = ["CRVDELIBVS FATIS EREPTVM", "POPVLO ROMANO", "DIEM QVO C · CAESAR OBIIT", "PRO ALLIENSI"]`. Lower third: "PISA / the town's decree for Gaius · news arrived 2 April, AD 4". Citation: "CIL XI 1421".
- **v3:** "a decree, one that still survives, carved in stone. (SHOW: the Pisa decree as a real inscription, with the light reading along its lines.)" No photograph of the actual stone was sourced. A faithful procedural reconstruction of the real lines may be the honest fallback; label it "reconstruction of the inscription".

#### E. Portraits
- HANDOFF §11 suggested CC0 museum busts of Augustus, Gaius and Tiberius. **None were fetched in the archive.**
- In this cloud session the sibling agent fetched Met CC0 portraits (§2.7). Two carry tentative identifications:
  - **Met 2011.376**, "Stone head of a Julio-Claudian youth, possibly of Gaius Caesar". The note says "narrate as 'possibly'".
  - **Met 14.130.1**, "Bronze statue of an aristocratic boy", with object name "Statue of a boy, Gaius Caesar ?". The note says the identification is speculative.
- Several Augustus portraits there are posthumous (Met 07.286.115 and 08.258.47, "carved ca. AD 14–37"). Caption them "portrait of Augustus", not as images from Gaius's lifetime.

#### F. Mausoleum of Augustus (where the remains went)
- **Sources in the transcript:**
  - Dio 55.12.1 (WebFetch, p034 #26): "The bodies of Lucius and Gaius were brought to Rome by the military tribunes and by the chief men of each city." He adds that the golden shields and spears from the knights "were set up in the senate-house".
  - The Livius stub: buried in the Mausoleum of Augustus.
  - The Pisa decree: "ossa relata atque condita".
  - Lucius's epitaph CIL VI 895 was searched but **not** found (p041 #25, #32).
- **v3:** "His ashes were carried back across the sea to Rome and placed in the great tomb Augustus had built for his family, with his father, Agrippa, and his brother, Lucius."
  - Agrippa's burial in Augustus's tomb (Dio 54.28.5) was **not** checked in the transcript.
  - "Remains"/"bones" matches *ossa* more closely than "ashes". "Ashes" is defensible for a Roman cremation, but keep it attributed.

#### G. Other places (Euphrates, Artagira, Lycian coast)
- **Euphrates meeting island:** the site is unknown. The 2 AD short showed "The island's exact site is unknown, and the screen says so." Any real Euphrates photo is illustrative only.
- **Artagira:** "**not securely located**; the screen says 'site uncertain'" (3 AD). The long-form v1 lower third was "ARTAGIRA, ARMENIA / AD 3 · the site is not securely identified".
- **Limyra:** coordinates used: `"Limyra": (36.34, 30.17)` (`geo.py`). Narration: "a few miles from the sea". The fact-check changed "on the coast" to "near the coast".

### 2.4 The owner's directions on real visuals and "pop"

From the archive:
- 10-14 18:13Z (critique of v1): "it's too similar to our shorts … take a second pass through all of the visuals not only to check them for mistakes, but also to um, make them more detailed and better."
- 10-15 01:08Z: "ensure the quality of the visuals is higher than the shorts as well as the othe4r things ive said".
- 10-15 07:24Z, Ara Pacis: "when you show it, you should show the altar of peace that you're talking about in the video."
- 10-15 07:24Z, Limyra: "if you bring that up, like, you gotta definitely gotta show it. Show of the ruins … It can't just be like an image popped up. You gotta do some work to it to make it, like, really pop. I want you to put that in the notes."
- OLD SESSION memory `longform-script-style.md` (p000 #57), under "Show notes in parentheses": "show what's named (the real Ara Pacis, the ruins); make the visuals worked and beautiful, never a pasted image; make big moments intense."

Current cloud request (this session, not in the archive): "I want you to pull from real visuals. In the story. … At the times that are appropriate. And the times that you can. But … Make it pop … make it look more 3D, or … make it come to life … Instead of just being an image."

### 2.5 How the OLD SESSION fetched things (methods that worked on the owner's PC)

- **LacusCurtius pages:**
  ```
  B="https://penelope.uchicago.edu/Thayer/E/Roman/Texts"
  curl -sL -A "Mozilla/5.0 (research)" -o $n.html "$B/$u"
  ```
  Results by file name, path and size:
  - `vell2c` `Velleius_Paterculus/2C*.html` (119 KB)
  - `vell2d` `Velleius_Paterculus/2D*.html` (125 KB)
  - `aug` `Suetonius/12Caesars/Augustus*.html` (326 KB)
  - `tib` `Suetonius/12Caesars/Tiberius*.html` (214 KB)
  - `dio54` `Cassius_Dio/54*.html` (110 KB)
  - `dio55` `Cassius_Dio/55*.html` (144 KB)
  - `rg` `Augustus/Res_Gestae/3*.html` (51 KB)
  - `tac1` `Tacitus/Annals/1A*.html` (55 KB)
  - **failed (49 bytes, "Sorry: I cannot find the page"):** `gellius15` (`Gellius/15*.html`) and `florus2` (`Florus/Epitome/2K*.html`)
- **Gellius 15.7:** `https://fgh.perseids.org/read/latinLit/phi1254/phi001/perseus-eng1/15.7` (Rolfe's translation), saved as `gellius15_7.html`.
- **Pisa decree:** `curl` of the heurist URL above.
- **Search helper:** a grep script, `srcdl\grep_src.py` ("Print passages around a keyword in a downloaded LacusCurtius/Perseus page").
- **Searching:** WebSearch and WebFetch for discovery (livius, vici, Cambridge PDF). In the shorts, curl to zh.wikisource needed a User-Agent and sometimes returned "Wikimedia Error".
- **Final `research/data` contents:** vell2c, vell2d, aug, tib, dio54, dio55, rg, tac1, gellius15_7.html, pisa_heurist.xml, pisa_decree_latin.txt, cambridge_excerpt.pdf (unreadable).

### 2.6 Licences for text quotations

- "Loeb translations of Velleius (1924), Dio and Florus (1929) via LacusCurtius: public domain in the US, used as short quotations" (3 AD dossier §5).
- "Velleius quotations | F. W. Shipley, Loeb (1924), via LacusCurtius | Public domain in the US; short quotations" (2 AD).
- The Tacitus wording in the shorts was "our own translation of *Annals* 1.3". The long-form used the LacusCurtius Jackson translation.

### 2.7 Context: `plan/real_images/` (built in THIS cloud session on 10-15, not in the archive)

There are 96 files, each with a JSON sidecar giving title, institution, accession number, licence, `how_verified` and `accuracy_note`. Groups:

- **1_limyra.** A Sentinel-2 TCI crop at 7680×4320 and 10 m/px, centred on Limyra, from 6 July 2025. Attribution "Contains modified Copernicus Sentinel data [2025]". The note says "label 'today'". `terrain/` adds a Copernicus DEM tile (N36 E030) with a hillshade preview and the EULA PDF.
- **2_coins.** Met CC0 coins of Octavian and Augustus, each tagged "NOT the Gaius & Lucius type". One CC BY 2.0 Flickr coin display, "Do not caption as Gaius & Lucius".
- **3_portraits.**
  - Met CC0: Augustus (several, mostly posthumous), Livia, "possibly Gaius Caesar" head 2011.376, and the bronze boy 14.130.1 ("Gaius Caesar ?").
  - Flickr CC BY 2.0: Augustus busts, including Prima Porta and Via Labicana.
- **4_ara_pacis.** Two CC BY 2.0 Flickr overall views (ISAW; MCAD Library).
- **5_lycia.** A Met CC0 19th-century print of the Telmessos rock tombs, plus CC BY 2.0 Flickr photos of the Lycian coast, Patara, Olympos, Fethiye and Xanthos. All are tagged "**Not Limyra**".
- **x_.**
  - Met CC0 Parthian drachm of Phraates IV ("Do not caption as Phraataces").
  - Met CC0 Goeree print of the Mausoleum of Augustus (conjectural).
  - Cooper Hewitt (Smithsonian) CC0 Piranesi, "Ruins of the Mausoleum of Augustus" (1756). Its note says "CIL VI 895 urn inscription; confirm in research.md before narrating".
  - ISAW CC BY 2.0, the Euphrates at Dura-Europos (illustrative only).
- **`provenance/flickr_ccby_originals_to_fetch_from_laptop.json`.** Flickr CC BY 2.0 originals to fetch from the laptop, because Flickr is blocked here:
  - "Procession on the Ara Pacis (I)" and "Children on the Ara Pacis (II)" (ISAW);
  - "North wall …" and "South wall of Ara Pacis";
  - "Sacrificial procession…" and "Panel of Tellus";
  - "Rome - Roman Forum 'Dedicated to Lucius Caesar from his Grandfather Augustus'";
  - "forum: portico of gaius + lucius, inscription";
  - "Mausoleum of Augustus"; Lycian tombs; "Coins of Augustus"; and others.
- **Notes from `build_real_images.py`:** "images.metmuseum.org itself is blocked from this container", so the Met/Google GCS mirror was used. "ids.si.edu is blocked here". "Flickr itself is blocked from this container, so the licence was NOT re-checked live; re-check the Flickr page before publishing."
- **Not in this folder:** any photo of the **actual Limyra cenotaph**, the **Pisa decree stone**, a **Gaius & Lucius denarius** (RIC I 207), or a **close-up of the Ara Pacis child**. The livius.org CC0 cenotaph photos by Jona Lendering (§2.3 A) are the obvious lead for the first gap.
- **Licence note.** CC BY 2.0 allows commercial use with attribution, but the HANDOFF allow-list does not name it. It names "CC0, public domain, open data with attribution", and CLAUDE.md requires "Every licence must allow monetised use". Credit CC BY images in the description and in `research.md`, and never use CC BY-SA.

---

## 3. Research and fact-check status

### 3.1 Timeline of the research work

| When (UTC) | What | Where |
|---|---|---|
| 10-10 to 10-11 | Shorts dossiers for 1–4 AD, covering Gaius as consul (1 AD), the Euphrates, Lollius and Lucius (2 AD), Artagira (3 AD), and his death at Limyra on 21 Feb (4 AD). | p043 #58 (1 AD), p038 #3 (2 AD), p033 #67 (3 AD), p030 #46 (4 AD) |
| 10-14 05:05–05:09Z | Long-form primary-source pass: downloads, greps, Gellius, Velleius in full, the Pisa decree, Livius and vici on the cenotaph, and a cross-check against the 3 AD dossier. | p016 #6–#80 |
| 10-14 05:10Z | Script v1 written (~1,950 words). | p016 #84 |
| 10-14 05:11Z | **Fact-check pass: 8 errors fixed.** | p015 #0–#4 |
| 10-14 05:17–05:18Z | Three more sourced passages added, each verified: the standards returned (Dio 54.8), Julia's exile terms (Suet. *Aug.* 65.3), Lucius reading Gaius's letters (Dio 55.10a.9). | p015 #10–#15 |
| 10-14 08:53Z | `research/research.md` written. Fixed later on 10-14: the consulship "thirteenth"→"twelfth", and "sixty-fourth birthday"→"his birthday". | p010 #69, #72; p007 #29 |
| 10-15 01:13Z | New hook for the rework: "a tomb with no one inside it… at twenty-two, he asked to walk away…". **No new research.** | p005 #59 |
| 10-15 07:28Z | Script v2: much new material. **No verification tool calls in that turn** (07:24 owner message → 07:28 reply). | p000 #52–#54 |
| 10-15 07:50Z | Script v3: the latest. Same gap. | p000 #61 |

### 3.2 The fact-check pass on v1 (p015 #0–#1), verbatim

OLD SESSION's summary: "I reviewed the ~1,950-word draft against the sources and corrected eight factual errors—covering Augustus's age, Limyra's location, Gaius's coming of age, Lollius's betrayal, Livia's son, the Armenian revolt date, **an invented dinner detail**, and the closing line's phrasing."

The replacements in `lf_fix1.py`:
- "in a small town in Lycia, **on** the coast of what is now Turkey, after begging not to be **sent** home" → "**near** the coast … not to be **brought** home"
- "Tiberius was the best soldier in Rome" → "one of the finest generals in Rome"
- "The next year, Gaius turned fourteen and put on…" → "The next year, at fourteen, Gaius put on…"
- "Millions of them passed through Roman hands." → "Huge numbers of them…"
- "**Somewhere between the courses, the king told Gaius a secret.** His trusted guardian, Lollius, **had been taking bribes from the kings of the East.**" → "Around the meeting, the king passed Gaius a secret. His trusted guardian, Lollius, was betraying him." This was the invented dinner detail; the bribes come from Pliny, not from the meeting.
- "**Then a letter came from the west.**" → "**Then news came from the west.**"
- "**In 3 AD, it rose in revolt**, and Gaius marched in." → "It rose in revolt, and Gaius marched in." Dio dates the revolt to the consuls of AD 2.
- "On the ninth of September, the commander struck." → "On the ninth of September, 3 AD, the commander struck."
- "But the wound did not heal." → "But the wound left him ill."
- "Augustus was sixty-six." → "sixty-five"
- "and now there was no one left in his way." → "and her son was now the obvious heir."
- "Far away, **the people of Limyra built** a monument for him beside their town." → "Far away, a monument to him was raised at Limyra."
- "with the heir he had never wanted." → "with the heir he had once passed over."

Later fixes (`research.md` fact-check log):
- **b6.** "'thirteenth' consulship corrected to **twelfth** (Suet. *Aug.* 26.2). On-screen 'CONSVL XIII' corrected to 'XII', and the caption under it changed from 'his thirteenth consulship' to 'his twelfth'." (The thirteenth, in 2 BC, was for Lucius.)
- **d9.** "'his sixty-fourth birthday' changed to 'his birthday'. … This removes the inclusive-count contradiction." The note: "Augustus calls the day his 'sixty-fourth birthday' (*quartum et sexagesimum natalem*). Romans counted the day of birth itself, so he was turning 63."

### 3.3 `research/research.md` (written 10-14 08:53Z for v1), key content verbatim

> **Ages and dates.** Gaius's birth month is unknown (Dio places the birth in 20 BC). The film gives ages by year count, as standard references do:
> - 8 when Agrippa died (12 BC);
> - 14 at his coming of age (5 BC; RG 14.1 says "in his fifteenth year");
> - 18 in 2 BC;
> - 20 as consul (AD 1);
> - 21 at the Euphrates (AD 2);
> - "about twenty-three" at death (AD 4).
>
> Augustus was born on 23 September 63 BC (Suet. *Aug.* 5), so he was 65 in February AD 4.

Abbreviations: "Pisa decree = *Decreta Pisana* for Gaius, CIL XI 1421 (ILS 140)."

Rows most relevant to the cold open and Limyra:

| Line | Claim | Source |
|---|---|---|
| h1 | Coins showing Gaius before he was 20. | Denarius of Gaius on horseback, c. 8 BC (RIC I² 198–199). C L CAESARES coins from 2 BC (RIC I² 205–212). |
| h2 | Dinner on an island in the Euphrates with the Parthian king, AD 2. | Vell. 2.101.1–3 |
| h3 | Died in Lycia after asking not to return to Rome. | Vell. 2.102.3; Dio 55.10a.8–9 |
| a3 | Annual sacrifice voted for his birthday. | Dio 54.8.5 |
| a4–a6 | Lucius born 17 BC. Augustus adopted both boys at home by a symbolic sale "with bronze and scales". | Suet. *Aug.* 64.1; Dio 54.18.1 |
| a10 | Child holding a toga on the Ara Pacis: "many think" it is Gaius. | Disputed. Some read the children as foreign princes; see C. B. Rose, *AJA* 94 (1990). |
| b7 | Consul designate, to take office after five years. The knights gave silver shields and spears and named him *princeps iuventutis*. | RG 14.1 |
| d4–d7 | Meeting with Tiberius. The sources differ: Samos (Suetonius) or Chios (Dio). Received with honour (Velleius), coldly because of Lollius (Suetonius), or after grovelling (Dio). | Vell. 2.101.1; Suet. *Tib.* 12.2; Dio 55.10.19 |
| d8 | A guest offered to sail to Rhodes and bring back "the head of the exile". | Suet. *Tib.* 13.1 |
| d9–d11 | Letter of 23 September: "my dearest little donkey", "preparing to succeed to my position". | Gell. 15.7.3 |
| e6–e7 | The king revealed Lollius's treachery. Lollius died within days. | Vell. 2.102.1 (Pliny, *NH* 9.118, says poison) |
| f1–f4 | Armenian revolt. Addon promised secrets, lured Gaius to the wall and wounded him, 9 September AD 3. | Dio 55.10a.6; Vell. 2.102.2; Florus 2.32; date from the Fasti Cuprenses |
| g2 | Never robust; the illness affected his mind. | Dio 55.10a.8 |
| g5–g6 | Asked to retire to private life in Syria. Augustus, grieved, told the Senate and urged him to come at least to Italy. | Dio 55.10a.8–9; Vell. 2.102.3 ("some remote corner of the world rather than return to Rome") |
| g7 | Laid down his offices. Sailed on a merchant ship after long resistance, against his will. | Dio 55.10a.9; Vell. 2.102.3 |
| i2–i3 | Died at Limyra in Lycia, 21 February AD 4 (a.d. IX K. Mart.). | Pisa decree; Vell. 2.102.3; Dio 55.10a.9 |
| i4 | News reached Pisa on 2 April (a.d. IV Non. Apr.), about 40 days later. Gaius was the colony's patron. | Pisa decree |
| i5 | No magistrates that year "because of the contentions of the candidates". | Pisa decree |
| i6 | Temples, baths and shops closed; mourning until the remains were brought home. | Pisa decree |
| i7 | "*crudelibus fatis ereptum populo Romano*" | Pisa decree |
| i8 | Death day to be kept like the *dies Alliensis* (390 BC). | Pisa decree; Livy 5.38–39 |
| i9 | The cenotaph at Limyra survives as ruins. | J. Ganzert, *Das Kenotaph für Gaius Caesar in Limyra* (1984) |
| j1 | Augustus was 65. He lost both sons within 18 months (Aug AD 2 to Feb AD 4). | (blank; Suet. *Aug.* 65.1 has "within the span of eighteen months") |
| j2 | "my sons, whom fortune snatched from me in their youth" | RG 14.1 |
| j3–j4 | Suspicion of Livia: repeated by Tacitus and Dio. | Tac. *Ann.* 1.3.3; Dio 55.10a.10 |
| j5–j6 | Tiberius adopted 26 June AD 4: "This I do for reasons of state". | Vell. 2.103.3, 2.104.1; Suet. *Tib.* 15.2 |

Note: `research.md` does **not** use the DATED / CONTEXT / ESTIMATE / TRADITION / SETUP tags that this repo's CLAUDE.md requires. The shorts dossiers do. A new `research.md` should add them.

The upload description's source list (`YOUTUBE_UPLOAD.md`, p010 #77):
- Velleius 2.99–104;
- Suetonius, *Aug.* 26, 64–65; *Tib.* 10–15;
- Dio 54–55;
- RG 14;
- Gellius 15.7;
- Tacitus, *Ann.* 1.3;
- Josephus, *AJ* 18.40–42;
- "The Pisa decrees for Gaius Caesar (CIL XI 1421)".

### 3.4 Cold open (v3): claim-by-claim status

| v3 sentence | Status | Source / caveat |
|---|---|---|
| "Near the southern coast of Turkey, among the ruins of an ancient town, stands a tomb built for a Roman prince." | **Supported, with a wording caveat.** | The Limyra monument is a **cenotaph** (vici.org; Livius; Ganzert 1984). His remains went to Rome (Dio 55.12.1; Pisa decree *ossa relata*). The owner told the session to call it "a tomb" and drop "empty". Limyra is about 5 km inland: the fact-check settled on "near the coast". The builder is not attested, so avoid "the people of Limyra built". |
| "The young man it was built for was supposed to inherit the Roman world. His grandfather, Augustus … had planned his entire life for him: his name, his titles, his future." | Supported (CONTEXT). | Adoption (Suet. *Aug.* 64.1; Dio 54.18.1); consul designate and *princeps iuventutis* (RG 14.1); Gellius letter "preparing to succeed to my position". |
| "Rome even put his name on its coins." | Supported. | RIC I² 205–212 (C L CAESARES, Lugdunum, from 2 BC); RIC I² 198–199 (c. 8 BC). The film's coin is a **procedural recreation**, not a photo. |
| "And then, at twenty-two, with all of it finally within reach, he asked to walk away." | Supported (paraphrase). | Dio 55.10a.8: "At last he begged leave to retire to private life, and it was his desire to remain somewhere in Syria." Vell. 2.102.3: "he wished to spend his life in a remote and distant corner of the world rather than return to Rome." **Age 22** is by year count in AD 3 (after the 9 Sept wound); the birth month is unknown. The research convention gives 21 in AD 2 and "about twenty-three" at death in AD 4, so 22 is consistent. "Finally within reach" is rhetoric. |
| "He never made it home." | Rhetorical. True of his living journey. | Vell. 2.102.3: "in the act of returning to Italy … he died" at Limyra. His remains did reach Rome (Dio 55.12.1). v3 pays this off later ("And then, at last, Gaius did go home. His ashes…"). |
| "This is the story of Gaius Caesar: the boy who was given everything, except a choice." | Interpretive tagline. | Not a factual claim. |

The hook that was **built** in the 2-min slice is the older one (p005 #59):
- h1 "In the ruins of an old town in southern Turkey, there is a tomb with no one inside it." (The owner later cut "no one inside".)
- h3 "His name was on coins all across the empire. At twenty-one, he dined with the King of Parthia, on an island in the middle of the Euphrates."
- h4 "He was heir to everything. And at twenty-two, he asked to walk away from all of it."
- h5 "A few months later, he was dead. He never made it home."

The slice's lower third "the empty tomb of a Roman prince" must change.

### 3.5 v2/v3 additions: verification status

The OLD SESSION listed these as "New material, all from the ancient sources" (p000 #54). **No tool calls checked them on 10-15.** Status from the archive:

| v2/v3 claim | Cited by OLD SESSION | Checked in transcript? |
|---|---|---|
| A trusted adviser warned Augustus to make Agrippa family "or have him killed" | Dio 54.6 | **No.** dio54.html was downloaded but never grepped for this. Dio attributes it to Maecenas (54.6.5). |
| Agrippa fell ill returning from campaign; Augustus arrived too late; gave the eulogy; buried him in his own tomb | Dio 54.28–29 | **No** |
| Postumus born after Agrippa's death | Dio 54.29 | **No** |
| Julia "a widow again at twenty-seven"; Agrippa "more than twice Julia's age" | (none) | **No.** Plausible from Julia b. 39 BC and Agrippa b. c. 63 BC. |
| Tiberius forced to divorce Vipsania; the tears; steps taken so he never saw her again | Suet. *Tib.* 7 | **No** |
| Four-day hunger strike; mother's pleas; Augustus complained to the Senate of being abandoned | Suet. *Tib.* 10 | Partly. A 10-10 WebFetch summary (p042 #41) gives "His mother and stepfather pleaded with him to stay. He refused food for four days." |
| "Father of His Country" the same year as Julia's exile (2 BC) | RG 35 | **No** |
| Pandateria "a tiny volcanic island" | (none) | Not checked. Pandateria/Ventotene is in the 1 AD research. |
| The scroll at Artagira ("a list of treasures") | Florus 2.32 | Yes, for 3 AD. The quote: Dones "attacked the general while he was engaged in examining a document which he had himself handed to him as containing a list of the treasures, and suddenly struck him with his drawn sword". Florus wrote in the 2nd century AD. |
| "His ashes were carried back … to Rome and placed in the great tomb Augustus had built … with … Agrippa, and … Lucius" | (Mausoleum) | Partly. Dio 55.12.1 says the bodies were brought to Rome. The Livius stub says he was buried in the Mausoleum. The Agrippa part was not checked. |
| Extra Gellius line: "But on days like today especially, my eyes look for my Gaius." | Gell. 15.7 | The text was fetched (p016 #37), but **v3 misquotes it.** Rolfe reads "But especially on such days as to-day my eyes are eager for my Gaius". Use the exact wording. |
| "on his sixty-third birthday" | Gell. 15.7 + research note | Consistent with the `research.md` note: born 23 Sep 63 BC, he turned 63 on 23 Sep AD 1. The letter itself says "sixty-fourth" by inclusive count, so **never show "sixty-fourth" on screen next to "sixty-third" in the narration.** |
| "Ten years later, Tiberius was emperor." | — | Correct: AD 14. |

### 3.6 v3 lines that undo earlier fact-check fixes

1. **"In 3 AD, Armenia rose against the king Rome had given it."**
   - The 10-14 fact-check deliberately removed "In 3 AD, it rose in revolt".
   - Dio 55.10a.5 dates the revolt to "the following year, when Publius Vinicius and Publius Varus were consuls" (AD 2). The 3 AD dossier: "**Dating:** Dio's fragments attach the revolt to … (AD 2). The fighting at Artagira belongs to AD 3."
   - Fix: "In 3 AD, Gaius marched into Armenia to crush a revolt", or keep the revolt undated.
2. **"Then a letter came from the west."** (Lucius's death)
   - Changed to "news came" on 10-14 because no source mentions a letter.
3. **The Gellius quotation in quote marks has been paraphrased** (§3.5). Quotes must be verbatim.
4. **Smaller embellishments to check or soften:**
   - "Augustus … read his son's letter aloud to the Senate". Dio says he "communicated his wish to the senate".
   - "begging him to come home". Dio: "urged him to come at least to Italy".
   - "A Roman officer who was there called it one of the most memorable sights **of his life**". Velleius: "truly a notable and a memorable sight".
   - "the man Gaius trusted most".
   - "one of Julia's freedwomen, **caught up in the scandal**". Suetonius: "one of her confidantes, a freedwoman called Phoebe".
5. **Euphrates date.**
   - v3: "In 2 AD, Gaius reached the Euphrates." The 2 AD dossier flags the date as **debated**: "most modern accounts put the meeting in AD 2 … livius.org gives AD 1". The short showed "2 AD by most reckonings · some say 1 AD".
   - CLAUDE.md requires contested claims to be attributed in the narration, so consider "In 2 AD, by most reckonings,…" or an on-screen note.

### 3.7 Key primary-source passages (verbatim, as fetched)

**Velleius Paterculus 2.101–102** (Shipley, Loeb 1924; LacusCurtius; p016 #43):

> 101 1 Shortly after this Gaius Caesar, who had previously made a tour of other provinces, but only as a visitor, was dispatched to Syria. On his way he first paid his respects to Tiberius Nero, whom he treated with all honour as his superior. … On an island in the Euphrates, with an equal retinue on each side, Gaius had a meeting with the king of the Parthians, a young man of distinguished presence. This spectacle of the Roman army arrayed on one side, the Parthian on the other, 2 while these two eminent leaders not only of the empires they represented but also of mankind thus met in conference — truly a notable and a memorable sight — 3 it was my fortunate lot to see early in my career as a soldier, when I held the rank of tribune. … As for the meeting, first the Parthian dined with Gaius upon the Roman bank, and later Gaius supped with the king on the soil of the enemy.
>
> 102 1 It was at this time that there were revealed to Caesar, through the Parthian king, the traitorous designs, revealing a crafty and deceitful mind, of Marcus Lollius, whom Augustus had desired to be the adviser of his still youthful son; … In regard to his death, which occurred within a few days, I do not know whether it was accidental or voluntary. … 2 Then Gaius entered Armenia and at first conducted his campaign with success; but later, in a parley near Artagera, to which he rashly entrusted his person, he was seriously wounded by a man named Adduus, so that, in consequence, his body became less active, and his mind of less service to the state. 3 Nor was there lacking the companionship of persons who encouraged his defects by flattery — for flattery always goes hand in hand with high position — as a result of which he wished to spend his life in a remote and distant corner of the world rather than return to Rome. Then, in the act of returning to Italy, after long resistance and still against his will, he died in a city of Lycia which they call Limyra, his brother Lucius having died about a year before at Massilia on his way to Spain.

**Cassius Dio 55.10a.6–10** (Cary, Loeb; LacusCurtius; p016 #29):

> 6 … a certain Addon, who was holding Artagira, induced Gaius to come up close to the wall, pretending that he would reveal to him some of the Parthian king's secrets, and then wounded him, whereupon he was besieged. He held out for a long time; 7 but when he was at last captured, not only Augustus but Gaius also assumed the title of imperator … 8 Gaius became ill from his wound, and since he was not robust to begin with and the condition of his health had impaired his mind, this illness blunted his faculties still more. At last he begged leave to retire to private life, and it was his desire to remain somewhere in Syria. Augustus, accordingly, grieved at heart, communicated his wish to the senate, and urged him to come at least to Italy and then do as he pleased. 9 So Gaius resigned at once all the duties of his office and took a trading vessel to Lycia, where, at Limyra, he passed away. But even before Gaius' death the spark of life in Lucius had been quenched at Massilia. … it was his custom personally to read the letters of Gaius in the senate, whenever he was present. 10 His death was due to a sudden illness. In connexion with both deaths, therefore, suspicion attached to Livia, and particularly because it was just at this time that Tiberius returned to Rome from Rhodes.

**Dio 55.12.1** (p034 #26): "The bodies of Lucius and Gaius were brought to Rome by the military tribunes and by the chief men of each city." / "And the golden targets and spears which they had received from the knights on entering the class of youths of military age" / "were set up in the senate-house."

**Suetonius, *Augustus* 64.1, 64.3, 65.1** (Rolfe; p016 #13, #32):

> Gaius and Lucius he adopted at home, privately buying them from their father by a symbolic sale, and initiated them into administrative life when they were still young, sending them to the provinces and the armies as consuls elect. … He taught his grandsons reading, swimming, and the other elements of education, for the most part himself, taking special pains to train them to imitate his own handwriting; and he never dined in their company unless they sat beside him on the lowest couch, or made a journey unless they preceded his carriage or rode close by it on either side. 65 1 But at the height of his happiness … Fortune proved fickle. … He lost Gaius and Lucius within the span of eighteen months, for the former died in Lycia and the latter at Massilia.

**Suetonius, *Augustus* 26.2** (the consulships): "he asked of his own accord for a twelfth after a long interval, no less than seventeen years, and two years later for a thirteenth, wishing to hold the highest magistracy at the time when he introduced each of his sons Gaius and Lucius to public life upon their coming of age."

**Suetonius, *Tiberius* 12.2, 13.1** (p016 #16):
- 12.2: "for when he had crossed to Samos to visit his stepson Gaius, who had been made governor of the Orient, he found him somewhat estranged through the slanders of Marcus Lollius, a member of Gaius' staff and his guardian."
- 13.1: "when mention was once made of him at a private dinner party, a man got up and assured Gaius that if he would say the word, he would at once sail to Rhodes and bring back the head of 'the exile'." The last part comes from the 10-10 summary and research.md d8.

**Res Gestae 14** (Shipley): "My sons Gaius and Lucius Caesar, whom fortune snatched away from me in their youth, the senate and the Roman people to do me honour made consuls designate, each in his fifteenth year, providing that each should enter upon that office after a period of five years. … the entire body of Roman knights gave each of them the title of princeps iuventutis and presented them with silver shields and spears."

**Aulus Gellius 15.7.3** (Rolfe; perseids; p016 #37):

> The ninth day before the Kalends of October [Sept. 23]. Greeting, my dear Gaius, my dearest little donkey, whom, so help me! I constantly miss whenever you are away from me. But especially on such days as to-day my eyes are eager for my Gaius, and wherever you have been to-day, I hope you have celebrated my sixty-fourth birthday in health and happiness. For, as you see, I have passed the climacteric common to all old men, the sixty-third year. And I pray the gods that whatever time is left to me I may pass with you safe and well, with our country in a flourishing condition, while you are playing the man and preparing to succeed to my position.

**Tacitus, *Annals* 1.3** (Jackson; p016 #19): "untimely fate, or the treachery of their stepmother Livia, cut off both Lucius and Caius Caesar, Lucius on his road to the Spanish armies, Caius — wounded and sick — on his return from Armenia."

**Dio 54.18.1** (adoption motive; p016 #29): "Augustus immediately adopted him together with his brother Gaius, not waiting for them to become men, but appointing them then and there successors to his office, in order that fewer plots might be formed against him."

**Dio 54.8.5** (birth): "And Julia gave birth to a boy, who received the name Gaius; and a permanent annual sacrifice on his birthday was granted."

**Florus 2.32** (from the 3 AD dossier): Dones "pretending to betray his master, attacked the general while he was engaged in examining a document which he had himself handed to him as containing a list of the treasures, and suddenly struck him with his drawn sword".

### 3.8 Continuity with the shorts (dates and conventions to keep)

From the 1–4 AD dossiers:
- **Gaius:**
  - born 20 BC; consul AD 1, "aged about 20" (1 AD);
  - "aged about 21" at the Euphrates (2 AD);
  - wounded 9 Sep AD 3 ("the date comes from a Roman calendar, the Fasti Cuprenses"; the year is a modern inference: "the most recent 9 September before his death in February AD 4");
  - died 21 Feb AD 4 "about twenty-three" ("the date from the decree of the town of Pisa", on screen in 4 AD).
- **Commander's name:** "Addon (Dio), Adduus (Velleius II.102.2) and Dones (Florus II.32)". Artagira/Artagera's site is uncertain.
- **Lucius:** died at Massilia on 20 Aug AD 2 (CIL XI 1420), aged 18. 1 AD's promise was "one of the two heirs will not live to see the year's end".
- **Tiberius:** returned AD 2 "in the eighth year after his retirement" (Suet. *Tib.* 14.1), with Gaius's consent (13.2). Adopted June AD 4. Velleius gives 27 June and other evidence 26 June, so the 4 AD screen said only "June". The long-form `research.md` says 26 June.
- **Livia suspicion:** "Later writers repeat a rumour … They offer no proof" (TRADITION, attributed).
- **4 AD research:** "Within eighteen months, Augustus had lost both of his adopted sons" (Suet. *Aug.* 65.1).
- **Pronunciations:**
  - Limyra: `[Limyra](/lˈɪməɹə/)`. "Limyra should be 'LIM-ih-ruh', not 'li-MY-ra'" (p031 #76).
  - Artagira: `/ˌɑɹtəɡˈIɹə/`; Lollius: `/lˈɑliəs/`; Allia: `/ˈæliə/`; Gaius: `/ɡˈIəs/`; Lucius: `/lˈusiəs/`; Velleius: `/vəlˈAəs/`.
  - These are Kokoro/misaki overrides. Check whether they carry over to the chosen voice, **bm_lewis**.

---

## 4. What the owner said about accuracy (verbatim)

- **2026-10-11 18:46Z (shorts, p022 #77):** "we want to be accurate and tell the story, but also do so in a way that grips people and people are driven by narratives."
- **2026-10-14 05:01Z (long-form brief, p017 #49):** "I'd like these to be like narrative driven and that doesn't mean true. But like delivered as a story." This is dictated and ambiguous. Read it with the later, explicit statements below, which ask for accuracy.
- **2026-10-15 07:24Z (script critique, p000 #52):**
  - "if you don't, if you can't tell the stuff from the historical records, you don't have to bring it up."
  - "It needs to be dramatic. It needs to be, and, and that doesn't mean inaccurate. Just, just more dramatic."
  - On Lollius: "I would just not even put Valais admits he could not say it was an accident or suicide. Just don't say what it was. Just state the facts, but state saying those two facts next to each other is the implication. … even though it's tr- it is true. We don't necessarily need a whole lot of nuance. … **we still want to be accurate**, but like, you know, you can, you know, leave that sentence out".
  - On wording: "even though they say things a certain way back in history … we don't necessarily need to just stick s- strictly to the terminology … put it in a different wording that, like, makes it sound more natural to the … modern English speaker."
  - Questions he wanted answered from the record "if we can": how Agrippa died; how the family felt about each other; why Syria; what "against his will" meant; how Gaius died. He added: "Maybe you can find answers to them. Maybe not."
- **2026-10-15 07:48Z (p000 #55):** the empty-tomb reveal "was confusing … just take that out … you can call it a tomb".
- **OLD SESSION memory** (p000 #57): "**Implication over hedging where it's still accurate.** Example: 'the king revealed Lollius's betrayal… a few days later, Lollius was dead', without 'Velleius can't say if it was accident or suicide'." Also: "**Reveals must be real and clearly set up.**"
- **Series rules that bind the film** (HANDOFF / CLAUDE.md): "Never invent events or quotes"; "Tag every claim … in the episode's research/research.md"; "Attribute contested claims in the narration itself"; "Mark illustrations as illustrations".

---

## 5. Implications for the new build (the 30-second cold open first)

1. **Limyra.**
   - The best real candidates are the livius.org CC0 photos of the cenotaph by Jona Lendering (licence unchecked) and the Copernicus Sentinel-2 crop already in `real_images` (label it "today").
   - Check the livius licence on the page itself before use. Credit "Jona Lendering / Livius.org (CC0)".
   - Label real photos as modern views ("Limyra today") and any procedural rebuild as "illustration".
   - Drop "empty" from all labels.
2. **Coin.**
   - Real RIC I 207 photos are still missing. Keep the procedural coin, labelled "after the denarius of Gaius and Lucius (RIC I 207)", or find a CC0 or public-domain specimen.
   - Do not caption any Augustus or Octavian coin as Gaius & Lucius.
3. **Cold-open narration (v3)** can stand as written. Put these lines in a tagged `research.md`:
   - Limyra cenotaph: CONTEXT. Ganzert 1984; vici.org; Livius.
   - Coins: CONTEXT. RIC I² 198–199 and 205–212.
   - "at twenty-two … asked to walk away": TRADITION/DATED. Dio 55.10a.8; Vell. 2.102.3; year-count age.
   - "never made it home": rhetorical. Vell. 2.102.3, with Dio 55.12.1 noted.
4. **Before the rest of the film,** fix the §3.6 regressions:
   - the "In 3 AD, Armenia rose" dating;
   - "a letter came";
   - the misquoted Gellius line;
   - Euphrates date attribution.
   Also verify the §3.5 items against the downloaded Dio 54 and Suetonius *Tiberius* texts, or re-fetch them from LacusCurtius.
5. **Ara Pacis and Pisa.**
   - Ara Pacis: use the ISAW/Flickr CC BY 2.0 frieze photos with attribution after a live licence check, and keep "many believe" on the Gaius identification.
   - Pisa stone: no photo was sourced. A reconstruction of the real Latin lines (§2.3 D) is the honest fallback; label it "reconstruction of the inscription".
