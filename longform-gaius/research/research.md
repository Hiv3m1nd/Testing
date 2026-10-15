# Gaius Caesar: The Heir Who Never Came Home — cold open: research log

Script v3, cold open, narrated verbatim. Tags follow the series rules: **DATED** (securely
dated event), **CONTEXT** (background fact), **ESTIMATE** (reasoned figure), **TRADITION**
(ancient report we cannot verify independently), **SETUP** (framing, no factual claim).

The sources are those gathered and checked for the long-form in the "2AD video production" thread
(summarised in `plan/C_assets_sources_research.md`), plus the image sidecars in `plan/real_images/`.

## Narration claims

| # | Line (as spoken) | Tag | Basis / caveat |
|---|---|---|---|
| 1 | "Near the southern coast of Turkey, among the ruins of an ancient town…" | CONTEXT | Limyra in Lycia (modern Yuvalılar near Turunçova/Finike), a few miles inland. Velleius 2.102.3 ("a city of Lycia which they call Limyra"); Dio 55.10a.9. Coordinates 36.34 N, 30.17 E. |
| 2 | "…stands a tomb built for a Roman prince." | CONTEXT | Strictly a **cenotaph** (honorific monument) for Gaius Caesar at Limyra, raised after his death in 4 AD; its rubble core survives, its reliefs are in the Antalya Archaeological Museum (J. Ganzert, *Das Kenotaph für Gaius Caesar in Limyra*, 1984; vici.org #17237; livius.org). His remains were taken to Rome (Dio 55.12.1; Pisa decree *ossa relata*). "Tomb" is the owner's chosen word; the on-screen label says "the cenotaph of Gaius Caesar". Who paid for it is not claimed. |
| 3 | "The young man it was built for was supposed to inherit the Roman world." | CONTEXT | Adopted by Augustus with his brother Lucius in 17 BC (Dio 54.18.1) and marked out as heir. |
| 4 | "His grandfather, Augustus, the master of that world, had planned his entire life for him: his name, his titles, his future." | CONTEXT | Adoption made him Gaius (Julius) Caesar, son of Augustus; *princeps iuventutis* and consul-designate from 5 BC, consul for 1 AD (Res Gestae 14). |
| 5 | "Rome even put his name on its coins." | DATED | RIC I² 198–199 (c. 8 BC, C CAES[AR]); RIC I² 205–212, the C L CAESARES type of the two brothers, Lugdunum mint, from 2 BC. |
| 6 | "And then, at twenty-two, with all of it finally within reach, he asked to walk away." | DATED / ESTIMATE | 3 AD, after his wound at Artagira: he asked to retire from public life (Dio 55.10a.8; Velleius 2.102.2–3). "Twenty-two" by year count (born 20 BC; birth month unknown). |
| 7 | "He never made it home." | DATED | Died at Limyra on 21 February 4 AD (Pisa decree CIL XI 1421: *a.d. VIIII Kal. Martias*), on his way back to Rome. His remains were brought to Rome afterwards; "home" here means alive. |
| 8 | "This is the story of Gaius Caesar: the boy who was given everything, except a choice." | SETUP | Framing line. |

## What is on screen, and what it is

| Shot | What you see | Status | Source / licence |
|---|---|---|---|
| Aerial, 0–6.6 s | The coast around Finike, Limyra and the Toçak Dağı at night, rendered in 3D from real elevation and satellite data; a warm point marks Limyra. | Real data, night grade, **today** (label says so). The glow is an illustration. | Copernicus Sentinel-2 L2A, 6 July 2025 ("Contains modified Copernicus Sentinel data [2025]"); Copernicus WorldDEM-30 GLO-30 (© DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the EU and ESA). Both allow commercial use with attribution. |
| Ruins, 5.8–11.5 s and 28.6–38.3 s | A torch carried through ruins: rubble core of the monument, frieze slabs, colonnade, walls, water. | **Illustration**, labelled. A plausible ruin field, not a survey of the site. The carved figures are generic procession figures, not the actual Limyra reliefs. | Generated in code (`src/sdf.py`, `src/scene_limyra.py`). |
| Head of a youth, 11–16.5 s | Met 2011.376, "Stone head of a Julio-Claudian youth, possibly of Gaius Caesar", gypsum alabaster, c. 5 BC or later, relit in 2.5D. | Real object; the identification is the Met's tentative one, so the label says "possibly". | The Metropolitan Museum of Art, Gift of George P. Tetzel, 2011. CC0. |
| Augustus, 16–22 s | Met 07.286.115, "Marble portrait of the emperor Augustus", c. 14–37 AD (made after his death), relit in 2.5D. | Real object. | The Metropolitan Museum of Art, Rogers Fund, 1907. CC0. |
| Titles, 21.8–25 s | "C · CAESAR", "PRINC · IVVENT", "COS · DESIG" cut in stone, with their plain meanings. | **Illustration**; wording as on his coins (the RIC I 205–212 legend) and inscriptions. | Generated in code. |
| Coin, 24.8–29 s | The C L CAESARES denarius, as in the Shorts, as a lit 3D object. | **Illustration** after RIC I 207 (labelled). | Generated in code from the 1 AD coin design. |
| Title, 38–48 s | "GAIUS CAESAR / THE HEIR WHO NEVER CAME HOME", carved and gilded; "20 BC – 4 AD". | Title card. | Generated in code. |

The 2.5D shape of the two Met heads is estimated with Depth Anything V2 Small (Apache-2.0). The
photographs supply all colour and detail; only the lighting is new.

## Voice and music

- Narration: Kokoro-82M (Apache-2.0), voice `bm_lewis`, speed 0.95, British G2P (misaki). Name
  overrides as in the long-form thread: Gaius /ɡˈIəs/, Limyra /lˈɪməɹə/.
- Score and sound design: synthesised in code (`src/score.py`). Gaius's lyre theme in D minor is
  the one established for the film.
