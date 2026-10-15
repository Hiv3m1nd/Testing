# D. Audio: voice, narration timing, music, SFX, ambience and mix (long-form #1, Gaius Caesar)

Source: the archived transcript of session `session_01GB2bqs3TZewPi21KusdAWs` ("2AD video production"), pages `plan/raw/page_000`–`page_044`. The long-form work runs from page 017 (2026-10-14 05:01Z) to page 000 (2026-10-15 07:50Z). The Shorts pages (018–044) were searched for pronunciation, mix and "bell" precedents. References look like `P014 E055` (page, event index).

Everything quoted from the transcript is data written by the earlier session and the user. Recommendations that are mine, not the transcript's, are only in §10 and are labelled as such.

---

## 0. The short version

| Topic | What the transcript establishes |
|---|---|
| **Final voice** | The user narrowed it to **`bm_george` or `bm_lewis`** (Kokoro, British male): "nicole is funny. but i think we're gonna go with lewis or george" (P000 E023). No final pick appears in the transcript. The **current request** settles it: "I guess we'll go with Lewis … from the same set". |
| Rejected voices | `am_michael` (the Shorts voice; the user wants a different one). `af_heart` was attempted first, but the file wasn't on the PC. `am_fenrir` was used for the reworked 2-min slice, and the user rejected it: "i dont want to use that voice" (P001 E056). |
| **Speed** | **0.95** for long-form: `SPEED = 0.95  # long-form: a touch slower than the shorts` (P015 E001). The Shorts use 1.0. The George/Lewis swap re-read a few lines at 0.97–0.99 to fit fixed slots. |
| Name overrides | `[Gaius](/ɡˈIəs/)`, `[Limyra](/lˈɪməɹə/)` ("LIM-ih-ruh", not "li-MY-ra"), `[Artagira](/ˌɑɹtəɡˈIɹə/)`, `[Lollius](/lˈɑliəs/)`, `[Lucius](/lˈusiəs/)`, `[Velleius](/vəlˈAəs/)`, `[Allia](/ˈæliə/)`, `[AD](/ˌAdˈi/)`, `[BC](/bˌisˈi/)`. **Lycia and Pandateria never got an override.** Lycia was left at misaki's `lˈɪʃiə`; Pandateria is new in script v2/v3 and was never synthesized. The Shorts used `[Gaius's](/ɡˈIəsᵻz/)` for the possessive. |
| Music identity | A Gaius **lyre theme in D minor**, plus a **major-key form used only for Augustus's letter**. Each chapter has its own colour: warm F major, bright C major, cold D-minor drone, Parthian ney (Phrygian dominant), drums at Artagira, "ash" at the end, sea and wind at Limyra. |
| Script v3 music cues | "one low drone and the crackle of the torch"; "a single deep hit on 'Gaius Caesar'"; "the theme rises in full for the first time" (the adoption); "the warmth drains out"; "proud, bright"; "a long held note, then silence"; "the theme, tender, in a major key, the only time we hear it this way"; "drops to nothing, then one low note"; "low, tense, building"; "**cut to total silence on 'struck', then one deep boom. This is the biggest moment in the film; give it room.**"; "silence; only wind"; "the theme, alone, unresolved"; "**the series bell at the very end**". |
| Series bell | In code, the Shorts' end-card "bell" is `sfx.add(te + 0.3, bowl(1175, 5), 0.6)` + `boom(4.0, 48)` over a D-minor(add 9) pad. Long-form v1 used `bowl(1175, 7), 0.45` + `boom(4.0, 48), 0.4`. The user called the bell nice continuity but said the film must be "different". v3 keeps the bell as the one deliberate carry-over. |
| Ambience | `ambience.py`: synthesized beds (wind, air, room, sea, river, fire/torch crackle, crickets, birds) keyed to narration regions, at −30 dBFS RMS, ducked 24/12 dB under the voice. |
| Mix | Music `target_ratio_gain(nar, m, 14.5, 6.0)`, SFX `(…, 16.5, 1.0)` (raised from the Shorts' 13/6 and 15/1). Voice-over-bed median is 18.9 dB. |
| Master | −14.0 LUFS integrated, true peak ≤ −1 dBTP, using a look-ahead `alimiter` with ceiling **0.74** (0.79 failed at −0.9 dBTP). Results: −1.3 dBTP (v1) and −1.8 dBTP (rework slice). Audio is AAC-LC 320k at 48 kHz in the 4K masters. |
| Code approach | The Shorts' `music.py` was reused. A new `compose()` was written in `srcdl/composeLF1.py` and **spliced** between `def compose():` and `def loudness_env`. Other additions: `ambience.py`, `revoice.py`, `respace.py`, `swapvoice.py`; the duration is derived from `film_end()` with `END_CARD = 9.0`. |

---

## 1. User directives on audio (verbatim)

- **Current request (this run):** "The music needs to be more dramatic. Especially at the parts of the story that need it the most." … "nicer music" … "We chose a voice … it was between this George or uh, hold on yeah Lewis or George and I guess we're gonna go with uh, uh, I guess we'll go with Lewis um, and this should be from the set the same set that you used we downloaded it onto the laptop". Also: "this story is frankly … intense. So reflect on the story and, and direct it in, in such a way that would be you know dramatic and, and tense".
- **First long-form brief (P017 E049, 2026-10-14 05:01Z):** "if their life was intense, maybe it should feel intense, or if their life was kind of like peaceful and uh, regal, then it should feel … Style the video around the person."
- **Review of v1 (P006 E057, 2026-10-14 18:13Z):** "it's too similar to our shorts. It, it's it's nice that we have the continuity, like the little bell at the end, all that different thing. Um, yeah, I need it to be different." … "**I think the audio needs work**, the visuals need work, the hook needs work".
- **Voice (P005 E035, 01:09Z):** "also use a different voice than the shorts use. same quality or higher - free. nothing that costs money"
- **After hearing am_fenrir on the 2-min slice (P001 E056, 04:22Z):** "where can i go to hear the voices we have to choose from? i dont want to use that voice"
- **After the auditions (P000 E004):** "download it and show me those" (the top-rated voices). **P000 E023:** "nicole is funny. but i think we're gonna go with lewis or george. can you swap the voices into the 2 min video quickly or would it mean rerendering everything?"
- **Script notes on delivery and flow (P000 E052, 07:24Z):** "the way you end and start sentences sometimes feels very … robotic … it feels like you start a train of thought and you stop. Start, stop, start, stop". On the adoption: "that's like an important moment … I would make the visuals here intense. Um, and the music…". On Artagira: "This is a huge moment … that moment where everything seems hopeless in a story … this is probably the biggest." On the voyage home: "you can set it up such that the visuals, and the music, and the way the story is, is going, like, you could tell it's dangerous for him not to go."
- **P000 E055:** "an old man missed his grandson. that exact type of sentance is what sounds robotic … the few lines after also do that stop, stop, stop, start thing."

The assistant saved these as `longform-script-style.md` (P000 E057), including: "**Flow.** No stop-start runs of short declaratives. Connect thoughts." and "**Show notes in parentheses** in scripts, for visuals and music … make big moments intense."

---

## 2. Voice: history, auditions, final choice

### 2.1 Timeline

| When (UTC) | Event | Ref |
|---|---|---|
| 10-14 05:09–05:11 | Long-form v1 is narrated with the **Shorts voice `am_michael`**; `SPEED` changed from 1.0 to **0.95**. Docstring: "Narration is Kokoro am_michael at speed 0.95 (a touch slower than the shorts)." | P016 E084, P015 E001 |
| 10-15 01:09 | The user asks for a different voice. The assistant picks **`af_heart`**: "Kokoro's top-rated voice"; patch `VOICE = {"af_heart": 1.0}  # the shorts use am_michael; af_heart is Kokoro's top-rated voice`. | P005 E037, E059 |
| 01:14 | `FileNotFoundError: … kokoro\voices\af_heart.bin`. Only 7 voices were installed: `am_adam, am_fenrir, am_michael, am_onyx, am_puck, bm_george, bm_lewis`. | P005 E074, P004 E001 |
| 01:14 | It falls back to **`am_fenrir`**: `VOICE = {"am_fenrir": 1.0}  # the shorts use am_michael; fenrir is a deeper voice of the same (C+) grade`. The user is told: "A different narrator: Kokoro am_fenrir, deeper than the shorts' voice, same quality, free." | P004 E004, P003 E036 |
| 04:22 | The user rejects fenrir: "i dont want to use that voice". | P001 E056 |
| 04:22–04:28 | Auditions: samples of the opening in 7 local voices, then 4 more downloaded. | P001 E059, P000 E013–E022 |
| 04:31 | The user: "we're gonna go with lewis or george". | P000 E023 |
| 04:32–04:50 | `swapvoice.py` builds George and Lewis versions of the 2-min slice with no picture re-render. | P000 E026–E039 |
| (this run) | The user: "I guess we'll go with Lewis". | current request |

### 2.2 Audition data

Sample text (both sentences of the old hook), synthesized at **speed 0.95**: "In the ruins of an old town in southern Turkey, there is a tomb with no one inside it. It was built for a young man the whole Roman world had been told was its future."

| Voice | Kokoro grade (as reported to the user) | Sample length | Notes from the transcript |
|---|---|---|---|
| am_michael | C+ | 11.9 s | The Shorts voice |
| am_fenrir | (C+) | 11.2 s | "current film voice"; rejected |
| am_puck | C+ | 10.9 s | "The only one here as good as the shorts voice" |
| **bm_george** | **C** | **11.9 s** | British |
| **bm_lewis** | **D+** | **11.6 s** | British |
| am_onyx | D | 10.1 s | |
| am_adam | F+ | 10.7 s | |
| af_heart | A | 10.9 s | "Kokoro's best voice overall" |
| af_bella | A− | 11.1 s | |
| bf_emma | B− | 10.3 s | "British. My pipeline uses American pronunciation rules, so the vowels may sound slightly mixed" |
| af_nicole | B− | 16.6 s | "Very soft and slow, almost a whisper" |

The assistant's note: "All four are female; Kokoro's male voices top out at C+." (P000 E003). Samples are in `output\voice_samples\` on the user's PC (11 files).

### 2.3 Voice files

- Source (from `HANDOFF.md`, quoted at P000 E010): "**Kokoro TTS weights** (Apache-2.0). The official source is the HuggingFace repo `onnx-community/Kokoro-82M-v1.0-ONNX`"; `voices/*.bin`. On the laptop: `KOKORO_DIR` = `C:\Users\heath\YearByYear\kokoro` (`kokoro-fp32.onnx`, patched `kokoro-fp32-dur.onnx`, `voices\`).
- Download command used for the extra voices: `curl -sfL -o $D/$v.bin "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/voices/$v.bin"`. Validation: each file is 522,240 bytes = 130,560 float32 values (510×256), finite, max |x| < 50, and no duplicates (md5).
- The loader is `np.fromfile(MODELS / "voices" / f"{name}.bin", dtype=np.float32).reshape(-1, 1, 256)`. It accepts a `{name: weight}` blend. Kokoro outputs `SR = 24000`, and `music.py` resamples the voice to 48 kHz.

### 2.4 Caveat on British voices

During the auditions the pipeline phonemized with **American** misaki rules. The assistant said so for bf_emma: "My pipeline uses American pronunciation rules, so the vowels may sound slightly mixed". The George and Lewis slices went through the same pipeline, so the Lewis the user heard on 10-15 was a **British voice reading American phonemes**. (In this environment `year-1-ad/src/tts.py` now has a `british=` flag, and `longform-gaius/src/narrate.py` calls `Narrator(S.VOICE, british=True)`. That is a change made after the transcript, so the cold open will sound slightly different from the slice the user approved.)

### 2.5 Speed and how lines were fitted

- Long-form `SPEED = 0.95`; the Shorts `SPEED = 1.0` (HANDOFF §8: "Voice **Kokoro `am_michael`, speed 1.0**, lead-in 1.2 s").
- `swapvoice.py` (P000 E026): "every line keeps its start time … a take that would run into the next line is re-read slightly faster". Rule: `room = next_start - start - 0.15`; if too long, `sp = min(1.3, SPEED * (len/room) * 1.02)`.
  - George: a5 at 0.98, a7 at 0.99, a8 at 0.98.
  - Lewis: a1 at 0.99, a1b at 0.99, a5 at 0.97.
  - Assistant: "A few were read a hair faster (speed 0.97–0.99 instead of 0.95) to fit their slots. Effects tied to specific words, like the crack on 'walk away', may land a fraction of a second off. The final render will time them to whichever voice you pick."
- Slice masters, first 120 s only (`measure_tp` returns LUFS, dBTP): `bm_george master (-14.0, -5.0)`, `bm_lewis master (-14.0, -3.0)`. Output files: `slice_0-2min_1080p_bm_george.mp4` and `slice_0-2min_1080p_bm_lewis.mp4` (about 137 MB each).

---

## 3. Pronunciation overrides

Syntax is misaki inline: `[Word](/phonemes/)`, in **US misaki notation**. Capital vowel letters are misaki diphthongs: `I` = /aɪ/, `A` = /eɪ/, `O` = /oʊ/, `W` = /aʊ/, `Y` = /ɔɪ/. `narrate.py --probe` prints per-line phonemes for checking.

| Name | Override | Reads as | Origin, notes |
|---|---|---|---|
| Gaius | `[Gaius](/ɡˈIəs/)` | GUY-us | Series standard (HANDOFF §8, 1 AD). The long-form defines `GAIUS = "[Gaius](/ɡˈIəs/)"`. |
| Gaius's | `[Gaius's](/ɡˈIəsᵻz/)` | GUY-us-iz | Shorts 2 AD fix: "'Gaius's' phonemized as a doubled s → Explicit override `/ɡˈIəsᵻz/`". The long-form instead writes `f"{GAIUS}'s mother"` and relies on `narrate.py` merging the split possessive ("possessive split off a name override: merge it back"). Its sound was never re-checked in the long-form. |
| Lucius | `[Lucius](/lˈusiəs/)` | LOO-see-us | Series standard |
| Limyra | `[Limyra](/lˈɪməɹə/)` | LIM-ih-ruh | Fixed in the 4 AD short (P031 E076): "One pronunciation fix: Limyra should be 'LIM-ih-ruh', not 'li-MY-ra'." misaki's default was `lɪmˈIɹə`. |
| Artagira | `[Artagira](/ˌɑɹtəɡˈIɹə/)` | ar-tuh-GUY-ruh | From the 3 AD short; probe confirmed `ˌɑɹtəɡˈIɹə` (P015 E004) |
| Lollius | `[Lollius](/lˈɑliəs/)` | LOL-ee-us | From the 2 AD short (HANDOFF suggestion); probe `mˈɑɹkəs lˈɑliəs` |
| Velleius | `[Velleius](/vəlˈAəs/)` | vuh-LAY-us | 2 AD short. Script v2/v3 cut Velleius as a named character. |
| Allia | `[Allia](/ˈæliə/)` | AL-ee-uh | Long-form v1. v3 replaced it with "the darkest day in Rome's history". |
| AD / BC | `[AD](/ˌAdˈi/)`, `[BC](/bˌisˈi/)` | "A D", "B C" | Series standard |
| **Lycia** | none | misaki: `lˈɪʃiə` (LISH-ee-uh) | Accepted as-is in both the 4 AD short and the long-form probe. |
| **Pandateria** | none | never synthesized | New in script v2/v3 ("banished her to Pandateria"). Needs a probe and probably an override. |
| Other v3 names never narrated: Vipsania, Postumus, Agrippa, Marseille, Pisa, Rhodes, Syria | none | not probed | Probe these with `--probe` before the full narration. |

The full series list in HANDOFF §8 (to "reuse exactly"): `[AD](/ˌAdˈi/) [BC](/bˌisˈi/) [Gaius](/ɡˈIəs/) [Lucius](/lˈusiəs/) [Aemilius](/imˈɪliəs/) [Paullus](/pˈɔləs/) [Han](/hˈɑn/) [Yuanshi](/juˈɛn ʃˈɜɹ/) [Seres](/sˈɪɹiz/) [Musa](/mˈusə/) [Strabo](/stɹˈAbO/) [Chang'an](/ʧˌɑŋˈɑn/) [Wang Mang](/wˈɑŋ mˈɑŋ/) [Zhou](/ʤˈO/) [Dionysius Exiguus](/dˌIənˈɪsiəs ɛɡzˈɪɡjuəs/)`. Later Shorts added `[Massilia](/məsˈɪliə/)`, `[Suetonius](/swɪtˈOniəs/)`, `[Elbe](/ˈɛlb/)`, `[Cimbri](/sˈɪmbɹI/)` and others.

The local `script_coldopen.py` in this environment already defines `GAIUS` and `LIMYRA` with these exact strings.

---

## 4. How narration was timed

### 4.1 `narrate.py` (long-form v1)

Quoted at P010 E026:

- `LEAD_IN = 1.2  # seconds of picture before the first word`
- Each line is synthesized separately: `u = n.synth(text, speed=SPEED)`. The take is trimmed (`trim(a, thresh=0.004)`, keeping 20 ms before and 60 ms after) and faded (8 ms). Then a per-line **pause after** is appended: `LINES = [(id, scene, text, pause_after_seconds), …]`.
- Output: `build/narration.wav` (float) and `build/timeline.json`, holding line `start`/`end` plus per-word `{"w","s","e"}` and phonemes. Everything else keys off this through `timeline.TL`: `T.s(id)`, `T.e(id)` and `T.w(id, "word")`, used by shots and music cues.
- `film_end()` = "last narration line + 0.45 s + end card. Shared by render.py and music.py". `END_CARD = 9.0` for long-form (the Shorts use 4.1), and `music.py` sets `DUR = film_end()`.

### 4.2 Pauses

- v1: ordinary lines 0.3–0.6 s. Chapter endings were raised to **4.6 s** "room for a chapter card after the last line of each chapter", and the hook end to **5.0 s** (`lf_setup.py`, P015 E021).
- Rework hook pauses (P005 E059): h1 0.6, h2 0.7, h3 0.6, h4 0.9, h5 1.1, h6 ("This is the story of Gaius Caesar.") 4.2.
- `respace.py 0.42 0.6` (P004 E045) rebuilt the narration **without re-synthesizing**: +0.42 s after ordinary lines and +0.6 s after chapter endings, with the hook (`h*`) untouched. Reason: "The new narration runs about 11:20, short of the 12–15 min target … add ~0.4s pauses between lines outside the opening hook". Result: `respaced: 707.26s`, film 714.29 s (11:54).
- The local cold-open script now uses `LEAD_IN = 3.2  # torch crackle and drone before the first word` and pauses of 0.45–1.6 s, with 4.0 s after the last line.

### 4.3 Measured timings (am_fenrir, the rework hook)

From P004 E042:

```
   1.20  5.30s [h1] In the ruins of an old town in southern Turkey, there is a tomb with no one inside it.
   7.10  4.55s [h2] It was built for a young man the whole Roman world had been told was its future.
  12.35  8.75s [h3] His name was on coins all across the empire. At twenty-one, he dined with the King of Parthia, on an island in the middle of the Euphrates.
  21.70  4.71s [h4] He was heir to everything. And at twenty-two, he asked to walk away from all of it.
  27.32  3.02s [h5] A few months later, he was dead. He never made it home.
  31.44  1.71s [h6] This is the story of Gaius Caesar.
```

Script v3 replaced this hook (see §5.4). The **v3 cold open has never been narrated** in the transcript.

### 4.4 Line-level fix tools

- **`revoice.py <ids>`** (P010 E037): "Re-voice single narration lines in place, without moving any other line. The new take starts where the old one did; the pause after it grows or shrinks so the next line keeps its start." It refuses a take that does not fit: `assert dur <= room` with `room = next_start - t - 0.25`. It was used for b6 ("twelfth") and d9 ("on his birthday"), then checked by reading the phonemes back.
- **`swapvoice.py <voice> <tmax>`** (P000 E026): puts a new voice on the existing timeline (see §2.5).
- **QA:** `qa_asr.py` (pocketsphinx WER, dry voice against the mix; "treat it as a relative measure only") and `qa_bed.py` (per-line voice-over-bed dB; 5 AD reference "at least 13.2 dB, median 16.4 dB. Below about 10 dB a line risks being masked").

### 4.5 Length

v1: 1,715 → 1,818 words, narration 700 s, film **12:18.7** (738.67 s). Rework (fenrir + respace): 11:54. v2/v3 script: "About 2,100 words, roughly 13 minutes with the new voice and pauses."

---

## 5. Music plan

### 5.1 Instrument palette (inherited from the Shorts; all synthesized in `music.py`)

From HANDOFF §8 "Music palette":

| Element | Detail |
|---|---|
| Pads | D minor / Dorian additive pads with low drones |
| Rome | Karplus–Strong lyre arpeggios |
| Parthia | Ney flute in D Phrygian dominant |
| Rhythm and impacts | Frame drums for momentum; booms on title hits |
| Sound effects | Whooshes on camera flights; chisel taps for inscriptions; singing bowls for omens |

The primitives in `music.py` (1 AD, reused): `pad(freqs, dur, attack, release, bright, voices=3, detune)` (additive, detuned, slow LFO), `pluck()` (Karplus–Strong via numba `_ks`), `gong()` (inharmonic ratios 1, 1.52, 2.03…), `bowl(f, dur)` (singing bowl, partials 1, 2.71, 5.15, 8.3 with beating), `drum()` (pitch-dropping frame drum plus skin noise), `boom(dur, f0)` (sub-sweep, crack and tail), `riser()`, `whoosh()`, `chisel()`, `shimmer()`, `wind()`, `ney()`, `reverb_ir()`/`reverb()`, and `CHORDS` (Dm, Bb, Gm, A, F, C, Am, Dm9, Asus, Eb, Am7).

### 5.2 Long-form v1 score (`srcdl/composeLF1.py`, P014 E055)

Intent (P014 E054): "giving Gaius his own lyre theme that recurs across the title, Augustus's letter, and the ending, plus distinct instrumental colors for each chapter (Parthian flute, drums at Artagira, sparse strings at Limyra)."

```python
# Gaius's theme (D minor), and its tender major form for the letter
THEME = ["D4", "F4", "A4", "G4", "F4", "E4", "D4", None, "C4", "D4", "F4", "E4", "D4"]
THEME_MAJ = ["F4", "A4", "C5", "Bb4", "A4", "G4", "F4", None, "E4", "F4", "A4", "G4", "F4"]
```

New local helpers: `drone(t0, t1, note="D2", gain)`, a sine with 2nd and 3rd partials and a 0.07 Hz wobble with 4 s attack and release; `lyre(t0, notes, step, gain)`; `arps()`; `drums()`; and `card(t0)` for the chapter-card sound.

| Chapter | Harmony and colour | Key cues |
|---|---|---|
| Cold open | D2 drone; D-A-E pad; ney on the Euphrates line; waves | `bowl(392,7)` + `boom(4.0,42)` on "dead"; Dm→Bb; `riser(1.4)` into the title; **`boom(5.0, 50)` + `shimmer(5.0,1397)` on "Gaius"**; Dm9 pad; THEME on lyre |
| I. The boy who was bought | "warm, F major": F-C-Bb-F-Dm-F-Am-F-C-Dm | arpeggios; frame drums under the standards' return; `clink` on "bought"; 3 clinks on "bronze"; shimmer on "Caesars"; chisel taps on "handwriting"; `gong(98)` on "died"; low D-A-Eb cluster on "Remember that name" |
| II. Prince of youth | "C major, brighter" | waves on "sailed"; `gong(110)` at the consulship; shimmer on "shield"; **26 random coin clinks** on "Huge numbers" |
| III. The mother | "D minor, sparse, cold"; D2 drone; Dm-Gm-Dm9-Bb-A | `boom(3.5,45)` on "cracked"; waves and wind for the island exile; `bowl(233)` on "rather"; sparse lyre |
| IV. Into the East | "Phrygian colour, ney": Dm-Eb-Dm-Gm-A-F-F-C | ney D-Eb-F#-G-A; low drums; three bowls for the three sources (659/587/523); dark A1-Bb1 cluster at the dinner; `boom(3,48)` on "head"; **THEME_MAJ on lyre under the letter** |
| V. The island in the river | Dm9-Gm-Dm-Eb-Dm-A | 30 s of waves; ney on A (A-Bb-C#-D); shimmer on "notable"; `boom(3,44)` on Lollius "dead"; bowl on Lucius "died"; falling lyre A-F-D-A |
| VI. Artagira | "drums, tension, impact"; A1 drone; Dm-Bb-A-Dm | drums 70/85 Hz to just before "struck"; `riser(2.4)` on "close"; **on "struck": `boom(5.0, 38)` at 0.85 + `whoosh(0.8)`**; faster drums for the siege; F pad and shimmer for "victory"; `bowl(233)` on "But the wound…" |
| VII. The man who wanted to disappear | "(ash)"; D2 drone; Dm9-Bb-Gm-Dm, low brightness | `bowl(784)` on "give"; very sparse lyre; waves for the ship |
| VIII. Limyra | "(sea, lamp, solemn decree)" | waves; `bowl(294,9)` on "died" (later lowered to 0.3); `gong(82)` on "snatched"; `boom(4,40)` on "Allia"; wind; THEME fragment |
| IX. The man who was left | Dm-Bb-Gm-Eb-Dm-F-Bb-Dm9 | bowl on "sons"; `gong(73)` on "Tiberius"; shimmer cascade; coin clinks; **full THEME on lyre**; end card pad `[D2 A2 D3 F3 A3 E4]` + `bowl(1175, 7)` + `boom(4.0, 48)` |

The v1 chapter card sound was `whoosh(1.6, up=False)` + `bowl(587, 6)`. The rework changed it (P004 E033) to:

```python
        sfx.add(t0, boom(3.5, 34), 0.4)             # a stone door closing on the chapter
        sfx.add(t0 + 0.25, shimmer(4.0, 880), 0.18)
```

### 5.3 Rework re-cue of the hook (P005 E059, `lf_rework1.py`)

```python
    drone(0.0, T.s("h6") + 2.0, "D2", 0.35)
    music.add(0.3, pad([hz("D3"), hz("A3"), hz("E4")], T.s("h3"), attack=3.0, release=2.0, bright=0.2), 0.3)
    sfx.add(T.s("h2") - 0.2, shimmer(5.0, 1175), 0.45)
    music.add(T.w("h3", "twenty-one") - 0.4, ney([...]), 0.45, pan=0.3)
    sfx.add(T.w("h3", "Euphrates") - 1.0, waves(8.0), 0.45)
    chords([("Dm", T.s("h4"), T.w("h4", "walk")), ("Bb", T.w("h4", "walk"), T.e("h4") + 0.6)], 0.5, 0.45)
    sfx.add(T.w("h4", "walk") - 0.05, boom(4.0, 38), 0.6)
    sfx.add(T.w("h5", "dead") - 0.05, bowl(392, 7), 0.5)
    sfx.add(T.w("h5", "dead"), boom(4.0, 42), 0.4)
    sfx.add(T.s("h6") - 1.4, riser(1.4), 0.45)
    sfx.add(T.w("h6", "Gaius") - 0.05, boom(5.0, 50), 0.6)
    sfx.add(T.w("h6", "Gaius"), shimmer(5.0, 1397), 0.7)
    chord("Dm9", T.s("h6") - 0.3, T.s("a1") + 1.0, 0.55, 0.45)
    lyre(T.w("h6", "Gaius") + 0.3, THEME, 0.42, 0.3)
```

The picture was synced to these words: "Rome cracks apart on 'walk away from all of it', and a lamp goes out on 'he was dead'" (P003 E036).

### 5.4 The target plan: script v3 MUSIC show notes (P000 E061, 07:50Z; v2 at P000 E054 has the same cues)

| Where | MUSIC note (verbatim) |
|---|---|
| Cold open, start | "Night. A torch moves slowly through the ruins at Limyra … **MUSIC: one low drone and the crackle of the torch.**" |
| Cold open, title | "the title is carved into the stone and catches gold as the light passes. **MUSIC: a single deep hit on 'Gaius Caesar'.**" |
| I, open | "Rome in carved relief, warm morning light. **MUSIC: hopeful.**" |
| I, adoption | "the scales tip; the bronze lands; the boys' names are cut into the stone as the light hits them. **MUSIC: the theme rises in full for the first time. This is the first big moment, so make it land hard.**" |
| II, open | "**MUSIC: the warmth drains out.**" |
| II, coins | "the coin of the two brothers … struck again and again and pouring across the frame. **MUSIC: proud, bright.**" |
| III, end (Julia) | "the light drifts away from Julia's name and leaves it in darkness. **MUSIC: a long held note, then silence.**" |
| IV, the letter | "the letter on papyrus, writing itself in warm lamplight. **MUSIC: the theme, tender, in a major key, the only time we hear it this way.**" |
| V, Lollius | "Lollius's name plaque goes dark. **MUSIC: drops to nothing, then one low note.**" |
| VI, open | "night. A fortress wall carved in stone, torches flickering along it. **MUSIC: low, tense, building.**" |
| VI, the strike | "a flash of red light across the stone. **MUSIC: cut to total silence on 'struck', then one deep boom. This is the biggest moment in the film; give it room.**" |
| VIII, death | "**MUSIC: silence; only wind.**" |
| VIII/IX, ending | "the wreath, with its last few leaves falling. **MUSIC: the theme, alone, unresolved.**" |
| Last frame | "the light passes over the ruins one last time and goes out. **MUSIC: the series bell at the very end.**" |

The v3 cold open text, which is what the 30-second deliverable covers:

> Near the southern coast of Turkey, among the ruins of an ancient town, stands a tomb built for a Roman prince.
> The young man it was built for was supposed to inherit the Roman world. His grandfather, Augustus, the master of that world, had planned his entire life for him: his name, his titles, his future. Rome even put his name on its coins.
> And then, at twenty-two, with all of it finally within reach, he asked to walk away.
> He never made it home.
> This is the story of Gaius Caesar: the boy who was given everything, except a choice.

### 5.5 The "series bell"

- **What it is in code:** the Shorts' end card in every `srcdl/composeN.py` (2 AD to 6 AD):
  ```python
  te = T.e("nx2") + 0.45
  music.add(te + 0.3, pad([hz(n) for n in ["D2", "A2", "D3", "F3", "A3", "E4"]], DUR - te, attack=1.2, release=2.0, bright=0.4), 0.6)
  sfx.add(te + 0.3, bowl(1175, 5), 0.6)
  sfx.add(te + 0.3, boom(4.0, 48), 0.5)
  ```
  So the "bell" is a **singing bowl at 1175 Hz (≈ D6)** struck with a 48 Hz boom, over a D minor(add 9) pad.
- Long-form v1 used the same gesture: `bowl(1175, 7), 0.45` + `boom(4.0, 48), 0.4` at `T.e("j10") + 0.4`.
- The user (P006 E057): "it's nice that we have the continuity, like the little bell at the end … I need it to be different." Script v3 keeps it as the only carry-over ("the series bell at the very end").

### 5.6 The "deep hit on 'Gaius Caesar'"

In v1 and the rework it was implemented as: `riser(1.4)` ending on the title line, then `boom(5.0, 50)` at gain 0.6, 50 ms before the word "Gaius", plus `shimmer(5.0, 1397)` at 0.7, a Dm9 pad, and the lyre THEME starting 0.3 s after "Gaius" (step 0.42 s). v3 asks for "**a single** deep hit". v1 stacked a shimmer and the theme on top of it.

### 5.7 Drones, torch crackle and silence beats

- **Drones:** D2 under the cold open (gain 0.35, to 2 s after the title line), under "The Mother" (0.32) and under "The Man Who Wanted to Disappear" (0.3); A1 under Artagira (0.35).
- **Torch crackle:** not in the music bus. It is the `fire` bed in `ambience.py`: brown noise low-passed at 180 Hz, plus about 7 clicks per second, 4 ms bursts high-passed at 1800 Hz. Region `("h1", "h3", {"wind": 0.8, "fire": 0.5, "crickets": 0.3})` covers the tomb. v3 wants exactly "one low drone and the crackle of the torch".
- **Silence beats in v3:** after Julia ("a long held note, then silence"); Lollius ("drops to nothing, then one low note"); **"struck" (total silence, then one deep boom)**; the death at Limyra ("silence; only wind").
- In **v1, none of these were real silences.** The drone and pads ran through "struck" (the drums stopped 0.2 s before it, then a boom and whoosh). `target_ratio_gain` also keeps a floor bed in gaps.

---

## 6. SFX and ambience

### 6.1 SFX vocabulary in the long-form score

| Sound | Used for |
|---|---|
| `clink` | coins, "bought", the bronze on the scales |
| `chisel` taps | handwriting and inscriptions |
| `bowl` | omens, deaths, sources, "rather" |
| `gong` | deaths and solemn turns ("died", consulship, "snatched", "Tiberius") |
| `boom` | "cracked", "head", "dead", "struck", "Allia", title, end |
| `riser` | into the title, into "close" at Artagira |
| `whoosh` | the strike; v1 chapter cards |
| `waves` | Rhodes, the island exile, the Euphrates, the ship |
| `wind` | the island, Limyra |
| `shimmer` | gold and glory moments |
| `drum` | standards, Parthia, Artagira |

### 6.2 `ambience.py` (P004 E010)

"Place ambience for the long-form: synthesized beds (no samples, no downloads), keyed to narration lines. Each region (from the start of one line to the start of another) gets a mix of beds; regions crossfade over 1.5 s. build(n, sr) returns a stereo float32 array at about -30 dBFS RMS; music.mix() ducks it lightly under the voice."

```python
REGIONS = [
    ("h1", "h3", {"wind": 0.8, "fire": 0.5, "crickets": 0.3}),   # the tomb at night
    ("h3", "h4", {"river": 0.6, "fire": 0.25}),                  # Euphrates
    ("h4", "h6", {"room": 0.6, "wind": 0.3}),
    ("a1", "a2", {"birds": 0.5, "air": 0.6}),
    ("a2", "b1", {"room": 0.7, "fire": 0.15}),
    ("b1", "b5", {"sea": 0.7, "air": 0.3}),                      # Rhodes
    ("b5", "c1", {"air": 0.6, "birds": 0.4}),
    ("c1", "c3", {"room": 0.7}),
    ("c3", "c5", {"sea": 0.6, "wind": 0.5}),                     # Pandateria
    ("c5", "d1", {"room": 0.6}),
    ("d1", "d4", {"wind": 0.5}),
    ("d4", "d8", {"sea": 0.5, "air": 0.3}),
    ("d8", "d9", {"room": 0.6, "fire": 0.35}),                   # the dinner
    ("d9", "e1", {"room": 0.7, "fire": 0.15}),                   # the letter
    ("e1", "e6", {"river": 0.7, "fire": 0.3}),                   # Euphrates summit, campfires
    ("e6", "e8", {"crickets": 0.5, "river": 0.3}),
    ("e8", "f1", {"wind": 0.5}),
    ("f1", "g1", {"wind": 0.7, "fire": 0.45}),                   # Artagira, torches
    ("g1", "g7", {"wind": 0.6}),
    ("g7", "i4", {"sea": 0.8, "wind": 0.6}),                     # the voyage, Lycia
    ("i4", "i9", {"room": 0.7}),                                 # Pisa decree
    ("i9", "j1", {"wind": 0.5, "crickets": 0.4}),
    ("j1", "j10", {"room": 0.7, "fire": 0.12}),
]
GAIN = {"wind": 1.0, "air": 1.0, "room": 1.0, "sea": 0.9, "river": 0.8, "fire": 0.7, "crickets": 0.6, "birds": 0.8}
```

The comments are mine, from the assistant's thinking at P004 E007: "wind and torch crackle at the tomb, river and campfire at the Euphrates, sea sounds for Rhodes, Pandateria and the Lycia voyage, night crickets, Roman birdsong, and room tone for the letter scenes."

Bed recipes:

| Bed | Recipe |
|---|---|
| wind | band-passed brown plus white noise (120–900 Hz) with a slow LFO |
| air | 200–3000 Hz hiss |
| room | brown noise low-passed at 260 Hz |
| sea | swells from three slow sines (0.083–0.143 Hz) cubed, with body below 1.1 kHz and spray at 2.5–9 kHz |
| river | 350–2600 Hz noise at 18 Hz LFO, plus 9 bubble chirps per second |
| fire | low rumble plus HP clicks (see §5.7) |
| crickets | 4.6 kHz triple pulses |
| birds | FM chirps at 2.2–4.8 kHz |

Left and right are decorrelated.

Wired into `mix()` (P004 E012):

```python
    import ambience
    amb = ambience.build(N, SR)
    amb = highpass(amb.T, 40).T
    amb = amb * target_ratio_gain(nar, amb, 24.0, 12.0)[:, None]
    s = s + amb
```

The region ids are those of the **old** script (h1–h6, a1…j10). The v3 script has different lines, so the regions must be re-keyed.

---

## 7. Mix and loudness

### 7.1 `mix()` in the long-form `music.py` (P010 E035, before ambience was added)

```python
    nar = highpass(nar, 75)
    nar = nar + 0.12 * bandpass(nar, 2500, 6000)   # ~+1 dB presence
    nar = nar / (np.abs(nar).max() + 1e-9) * 0.7
    ir = reverb_ir(3.8)
    m = reverb(music.x, ir, 0.38) * 0.42
    s = reverb(sfx.x, reverb_ir(2.4, 5000), 0.25) * 0.55
    m = highpass(m.T, 45).T
    s = highpass(s.T, 32).T
    m = m * target_ratio_gain(nar, m, 14.5, 6.0)[:, None]
    s = s * target_ratio_gain(nar, s, 16.5, 1.0)[:, None]
    vo = np.stack([nar, nar], -1)
    master = vo * 1.0 + m + s
    # gentle bus limiting
    peak = np.abs(master).max(); master = master / peak * 0.95
    over = np.abs(master) > 0.8
    master[over] = np.sign(master[over]) * (0.8 + 0.15 * np.tanh((np.abs(master[over]) - 0.8) / 0.15))
    fade[-int(0.8 * SR):] = np.linspace(1, 0, int(0.8 * SR))
```

The mix writes `mix_premaster.wav`, `music_stem.wav` and `sfx_stem.wav` (48 kHz float). The voice is dry and centred, with no compressor. HANDOFF §8: "**No compressor on the voice.** It hurt intelligibility."

`target_ratio_gain(voice, bed, speech_db, gap_db)`: "Gain curve for a music/SFX bed so that, perceptually (>150 Hz), it sits `speech_db` under the voice while she speaks and at most `gap_db` under typical voice level in gaps." It ducks fast and recovers slowly (`y + (x - y) * 0.08` per 50 ms hop).

### 7.2 Ducking history

| Stage | Music | SFX | Why |
|---|---|---|---|
| 1 AD (HANDOFF) | 11 / 5 | 13 / 0 | "Music sits about 18–20 dB under the voice in the speech band" |
| 2 AD onward (Shorts) | 13 / 6 | 15 / 1 | "Bed about 2 dB louder than 1 AD's: ASR WER on the mix was 0.605 … → WER 0.568" (P039 E072) |
| **Long-form v1** | **14.5 / 6** | **16.5 / 1** | "Raising the ducking margins slightly for long-form" (P013 E000) |
| Long-form ambience | 24 / 12 | | P004 E012 |

`qa_bed.py` on long-form v1:

- Before the change: "min 10.0 median 17.7".
- After: "min 10.1 median 18.9". Lines d4, e9 and i3 stayed at about 10 dB. The assistant's note: "Those three lines plateau at ~10 dB regardless of music level—an artifact of long pauses dragging down their average, not a mix issue".

### 7.3 Mastering (`master.py` functions, inline recipe)

```python
i0, _ = master.measure_i(src)
g = -14.0 - i0 + 0.4
ffmpeg -af f'volume={g:.2f}dB,alimiter=limit=0.74:attack=4:release=60:level=false:latency=true' -c:a pcm_f32le mix_limited.wav
i, _ = master.measure_i(lim)
ffmpeg -af f'volume={-14.0-i:.2f}dB' -c:a pcm_f32le mix_final.wav
assert tp <= -1.0 and abs(i2 + 14) <= 0.3
```

- First attempt with `master.pre_limit` (ceiling `limit=0.79`): "pre-gain +7.0 dB; final -14.0 LUFS, true peak -0.9 dBTP", which failed the assertion. With 0.74: "-14.0 LUFS, true peak -1.3 dBTP" (P013 E054). Rework slice: "-14.0 LUFS, true peak -1.8 dBTP".
- `LONGFORM.md`: "With a limiter ceiling of 0.74 this lands at about −1.3 dBTP." `master.loudnorm()` (two-pass `loudnorm=I=-14:TP=-1:LRA=11`) exists but was not used.
- HANDOFF target: "Master to **−14.0 LUFS**, true peak **≤ −1 dBTP**, LRA about 2.5–3 LU."
- `render_all.sh` refuses to master if the mix length doesn't match the film: `assert abs(d - film_end()) < 0.2`.

### 7.4 Audio in deliverables

| Deliverable | Audio |
|---|---|
| 4K SDR / HDR10 masters (`hdr.py encode`) | `-c:a aac -b:a 320k -ar 48000` |
| `finalize.py fallback` (1080p SDR) | AAC 320k |
| Phone preview (≤ 30 MiB) | AAC 64k |
| 2-min slice | AAC 256k |
| Final 4K file (ffprobe) | `codec_name=aac|profile=LC` |

---

## 8. Code approach vs the Shorts' `music.py`

- **Same engine.** The long-form workspace (`C:\Users\heath\YearByYear\Longform\lf01-gaius\src`) is a copy of the Shorts' `src/`, kept outside the repo. `LONGFORM.md` step 1: "Copy the previous film's `src/` and replace `script_data.py`, `lf_scenes.py` (the shots), `render.py` SHOTS and `srcdl/composeLFN.py` (the score)."
- **Score by splicing:** the new `compose()` is written to `srcdl/composeLF1.py`, then
  ```python
  i=s.index('def compose():'); j=s.index('def loudness_env')
  s=s[:i]+new+'\n\n'+s[j:]
  ```
  (P014 E057). The Shorts do the same with `srcdl/composeN.py`.
- **What differs from the Shorts' `music.py`:**
  1. `DUR = film_end()` with `END_CARD = 9.0` (a 12-minute buffer, `mixed (35456160, 2)`).
  2. A new compose with the Gaius THEME/THEME_MAJ, `drone()`, `lyre()`, `arps()`, `drums()` and `card()` helpers, and per-chapter keys.
  3. Ducking of 14.5/6 and 16.5/1.
  4. The `ambience.py` bed, ducked 24/12.
  5. The chapter card sound is a "stone door" `boom(3.5, 34)` + `shimmer(4.0, 880)`.
  6. Hook cues re-keyed to new line ids and words.
- **Narration tools added:** `revoice.py`, `respace.py` and `swapvoice.py` (all in `src/`), plus `SPEED = 0.95` and the `VOICE` changes in `narrate.py`.
- **Workflow (LONGFORM.md):**
  - "4. **Music.** Run `python music.py`. It writes `mix_premaster.wav`; ducking is driven by the narration."
  - "5. **Audio master.** Run the `master.pre_limit` + gain steps to reach −14 LUFS with true peak at or below −1 dBTP."
- **What did not change:** every instrument is still procedural (no samples or downloads), there is no orchestral library, and the theme is still Karplus–Strong lyre with additive pads. The user's verdict after v1 was "the audio needs work" and "too similar to our shorts". The rework changed the voice, the ambience, the chapter sound and the hook cues, but **not the instrument palette**.

---

## 9. Open points, gaps and contradictions in the transcript

1. **No final voice in the transcript.** It ends with "Tell me George or Lewis". Lewis comes only from the current request. Lewis is graded **D+** in Kokoro's own table and George **C**; the user chose by ear.
2. **British voice, American phonemes.** The slice the user heard used US G2P. If `british=True` is now used, the overrides (US notation, e.g. `lˈɑliəs` and rhotic `ɑɹ` in Artagira) may need British equivalents, or should be checked by ear.
3. **v3 is not narrated.** Every timing in the transcript (hook at 1.2/7.1/12.35/21.7/27.32/31.44 s) belongs to the old hook.
4. **Silence and "total silence on 'struck'"** are not implemented anywhere. v1 had a drone, pads, ambience and a ducking floor under that moment.
5. **"Single deep hit"** (v3) vs v1's boom + shimmer + riser + lyre stack.
6. **Bell.** The user praised the continuity but asked for the film to be "different". v3 keeps only the bell.
7. **Ambience regions** are keyed to the old line ids, and there is no region for Pandateria under that name in v3 (it is region c3–c5 in the old script).
8. **Pandateria, Vipsania, Postumus and Lycia** have no overrides, and the v3 names were never probed.
9. **Possessive "Gaius's"**: the Shorts needed `/ɡˈIəsᵻz/`; the long-form relied on the merge logic.
10. **Word-locked effects** in the George/Lewis slices were timed to fenrir ("may land a fraction of a second off").

---

## 10. Implications for the 30-second cold open (analyst notes, not from the transcript)

- Voice `bm_lewis` at speed 0.95, as `script_coldopen.py` already has. Probe "Gaius" and "Limyra" under British G2P before rendering (the v3 cold open names no other proper nouns except Augustus, Turkey and Rome).
- The v3 cues map onto the cold open as follows:
  - before the first word: torch crackle (`fire`) + wind + a single low D drone (`LEAD_IN 3.2` gives it room);
  - on "walk away": the crack/boom used in the rework;
  - "He never made it home.": the lamp-out beat, close to silence;
  - "Gaius Caesar": ONE deep boom, then the lyre THEME entering under "the boy who was given everything, except a choice."
- "More dramatic" is the user's explicit new ask, and `target_ratio_gain`'s gap floor flattens swells. Hits and swells probably need to sit in narration gaps, or bypass the gap ducking for marked beats, so they actually land. The mix still has to hit −14 LUFS and ≤ −1 dBTP.
