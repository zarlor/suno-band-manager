# Suno Band Manager knowledge

This document covers the skills of the `suno` module: what each one gives the user, when to recommend it, and what to offer next. The module turns a user's creative ideas (a poem, a feeling, a genre mashup) into Suno-ready song packages: a style prompt, structured lyrics and generation settings, built around reusable band identities.

## The skills

- `suno-agent-band-manager`: Mac, the Band Manager, a memory agent who remembers the user, their bands and their songs across sessions. He creates complete song packages (style prompt + lyrics + settings) through a creative conversation, refines a Suno take the user brings back, browses the songbook, and saves session memory. Recommend him for "make a song", "talk to Mac", or any request that spans more than one skill below; he runs them in the right order and assembles the package only through them. Afterwards offer a refinement once the user has generated in Suno, or sequencing once several songs exist. Details in `help/suno-agent-band-manager.md`.
- `suno-band-profile-manager`: creates and maintains band profiles (genre, vocal direction, writer voice, model preferences) that every other skill reads, analyzes a writer's voice from samples, health-checks a profile, and keeps a band's playlist file. Recommend it before the first song for a new band, or when output keeps drifting from the band's identity. Afterwards offer a style prompt or a song with Mac. Details in `help/suno-band-profile-manager.md`.
- `suno-style-prompt-builder`: a model-aware style prompt with creativity modes, wild-card variants and an exclusion prompt, within the chosen Suno model's character budget. Recommend it when the user wants only the Style field, or a prompt for a band without the full song conversation. Afterwards offer lyrics (`suno-lyric-transformer`) or the full package with Mac.
- `suno-lyric-transformer`: turns a poem or prose into structured lyrics with section metatags, keeping the writer's words and spacing; also analyzes a text's song potential without changing it (structure, syllables, character budget). Recommend it when the user has words and wants them singable. Afterwards offer a matching style prompt.
- `suno-feedback-elicitor`: translates "the chorus feels flat" into concrete prompt and lyric adjustments, and measures a render's tempo, key and loudness (plus a section map against the lyrics when the PyTorch audio tools are on). Recommend it when the user has a Suno take and wants a diagnosis on its own; Mac's Refine Song runs it inside. Afterwards offer the rebuilt style prompt or lyrics.
- `suno-playlist-sequencer`: orders a band's tracks into an album-craft sequence (energy arc, Camelot key transitions, locked arcs, encore) with a reason for every move. Recommend it once a band has a playlist file with several finished tracks. Afterwards offer to save the order back through the profile manager's Manage Playlist.

## Where things land

Band profiles go to the folder chosen at setup as `modules.suno.band_profiles_folder` (default `docs/band-profiles`), and a band's playlist file sits beside that folder in `docs/`. Saved songs and lyrics go to `modules.suno.songbook_folder` (default `docs/songbook`). Audio analysis lands in `docs/audio-analysis/`. Mac's memory lives in `_bmad/memory/suno-agent-band-manager/` (from module 4.0.0; on his first waking after the upgrade he converts the old `_bmad/_memory/band-manager-sidecar/` store, backup first). The other answers are `modules.suno.suno_tier` (which models Mac recommends), `modules.suno.default_mode` (demo, studio or jam) and `modules.suno.pytorch_audio_tools` (on or off). `bmad setup suno` shows and changes the answers.

## More detail

This document should be enough to route the user. Read a topic file only when the question is about its subject.

| Topic file | Read when the user asks about |
|---|---|
| `help/suno-agent-band-manager.md` | Mac's menu, his modes, memory and portable sync across machines, the pipeline guard |
| `help/suno-band-profile-manager.md` | What a band profile holds, writer-voice analysis, profile health checks, playlist files |
