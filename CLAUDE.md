# Year by Year — standing rules for this repo

This repo makes **Year by Year**, a code-generated vertical history documentary
series with one episode per year. `year-1-ad/` is the reference episode.
**Read `HANDOFF.md` before starting any episode work.**

**Format and cost**

- 1080×1920, 30 fps, H.264 + AAC, burned-in captions.
- Runtime ≤ 3:00 (Shorts/Reels limit) and story-driven.
- Audio −14 LUFS, true peak ≤ −1 dBTP.
- $0: no paid APIs or services; local, free tools and models only. Every
  licence must allow monetised use.

**Accuracy**

- Never invent events or quotes.
- Tag every claim DATED / CONTEXT / ESTIMATE / TRADITION / SETUP in the
  episode's `research/research.md`.
- Attribute contested claims in the narration itself.
- Mark illustrations as illustrations.

**Consistency with 1 AD**

- Visuals: same engine (`src/`), palette (Rome crimson, Parthia teal, Han
  amber), fonts, caption style, safe zones and year format "2 AD".
- Narration: Kokoro `am_michael` at speed 1.0, reusing the phoneme overrides
  listed in HANDOFF §8.
- Branding: titles and end card as in HANDOFF §8.

**Process**

- research → script → narrate → per-shot QA stills → draft render → full QA →
  partial re-render → master → verify → commit.
- Treat the first render as a draft.

**Git**

- Work on a branch.
- Never commit `build/`, `models/` or files over 100 MB.
- Ship a ~95 MB web encode plus the master split into parts.
