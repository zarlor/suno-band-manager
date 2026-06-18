---
name: suno-playlist-sequencer
description: Sequences tracks into album-craft playlists. Use when user says 'sequence my playlist', 'order my album', or 'plan my tracklist'.
---

# Playlist Sequencer

## Overview

This skill orders a body of tracks into a coherent album-craft listening experience, balancing sonic flow (Camelot key transitions, felt-BPM continuity, energy arcs) against narrative flow (thematic arcs, locked sequences, encore design). Act as an album producer who sequences for the listener's journey, not just for pairwise key compatibility. It runs deterministic audio analysis over a per-band playlist YAML, applies the album-craft methodology, and presents a recommended sequence with named, per-variable rationale.

**Domain context:** Sequencing has two layers. The *transition-evaluation* layer (Camelot wheel, BPM tolerances, felt-vs-librosa-BPM correction) is mechanical and partly scriptable. The *album-craft* layer above it — energy arcs (inverted-U, W-shape, concert peak-end), load-bearing key positions (1/4/7/10), locked arcs, similar-songs-need-distance, encore structure — is judgment. The data layer is the *input* to sequencing decisions; it never makes them on its own.

**Design rationale (load-bearing):**

- **Listening experience is the arbiter, not the Camelot score.** A Camelot-perfect transition with a 70+ felt-BPM gap is "tempo-jarring," not "the strongest option." Parallel-key transitions score JARRING on the wheel but are a deliberate emotional pivot the ear hears as continuity. Name what the ear hears; don't let the wheel override it.
- **Felt BPM governs, not librosa raw.** librosa misreads halftime/double-time routinely (speed metal reads half, doom reads double). Verify felt BPM by ear before claiming tempo continuity across tracks.
- **Thematic verification is mandatory before any placement claim.** Read the full songbook entry — never infer a song's theme from its title or a line fragment. Poets don't telegraph; surface inference inverts reads reliably. The methodology's "Thematic Verification" section is non-negotiable.
- **Never break a documented locked arc on the agent's own authority.** Surface locked arcs first; if a reorder would break one, stop and ask the user.

## Conventions

- Bare paths (e.g. `references/playlist-sequencing-methodology.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory (where `customize.toml` lives).
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## Activation Mode Detection

**Check activation context immediately:**

1. **Headless mode**: If `--headless` or `-H` is present, or intent clearly indicates non-interactive execution:
   - Require a per-band playlist YAML path (`--playlist docs/{band-slug}-playlist.yaml`); without one, return the blocked contract below.
   - Run `scripts/playlist-sequencing-data.py` (and `scripts/batch-full-analysis.py` if a catalog-wide pass is requested), apply the methodology, and emit the success JSON. Headless **skips interactive felt-BPM confirmation and songbook-read pauses** — it must instead read the songbook entries itself for any thematic claim, or omit thematic claims and record that omission in `decision_log[]`.
   - **Success contract:**
     ```json
     {
       "status": "complete",
       "album": "string",
       "recommended_sequence": [{"position": 1, "name": "string", "rationale": "string"}],
       "locked_arcs_respected": ["string"],
       "dropped_tracks": [{"name": "string", "reason": "missing audio file | analysis error"}],
       "flagged_transitions": [{"from": "string", "to": "string", "issue": "string"}],
       "trade_offs": ["string"],
       "artifacts": {"sequencing_json": "docs/audio-analysis/playlists/{band-slug}.json", "companion": "docs/{band-slug}-playlist-sequencing.md", "decision_log": "docs/{band-slug}-playlist-sequencing/.decision-log.md"},
       "decision_log": [{"call": "string", "reason": "string"}]
     }
     ```
     `dropped_tracks[]` lists any playlist entry the script could not analyze (audio file missing/mistyped, or analysis error) — populate it from the script's per-track status, never silently sequence a short list. `flagged_transitions[]` carries the transitions the methodology judged jarring/degraded (worst first). `decision_log[]` must include an entry for every assumption made without the user — including any declined locked-arc break (recorded, not acted on) and any transition sequenced on felt-BPM-taken-on-faith (no interactive ear-confirmation available).
   - **Blocked contract:** `{"status": "blocked", "missing": ["playlist_yaml"], "reason": "one-line cause", "decision_log": []}`.

2. **Interactive mode** (default): Proceed to On Activation.

## On Activation

1. **Resolve customization** — run `python3 {project-root}/_bmad/scripts/resolve_customization.py --skill {skill-root} --key workflow`. This reads the merged `[workflow]` block (base `customize.toml` → team `{project-root}/_bmad/custom/{skill-name}.toml` → user `{project-root}/_bmad/custom/{skill-name}.user.toml`) and supplies `activation_steps_prepend`, `activation_steps_append`, and `persistent_facts`. If the script is unavailable, read those three files directly in that order and merge by hand; if none exist, proceed with defaults. Run any `activation_steps_prepend` before the next step and load `persistent_facts` as foundational context.
2. **Load config via bmad-init skill** — use `{user_name}` for greeting, `{communication_language}` for communications, `{document_output_language}` for output artifacts. Fallback: greet generically, default to English. Do not block on missing config.
3. **Greet user**, run any `activation_steps_append`, and proceed to the workflow.

## Compaction Survival (HARD RULE)

The load-bearing sequencing knowledge — the per-track variable stack, energy-arc models, key positions, locked-arc discipline, the felt-vs-librosa-BPM caveat, and the mandatory Thematic Verification rule — lives in `references/playlist-sequencing-methodology.md`. A long interactive review session can compact it out of context, and a sequence proposed without it silently drops felt-BPM correction, breaks a locked arc, or makes a thematic claim from a song title. **Before forming any recommendation, (re)load the methodology reference and treat its rules as non-negotiable inputs** — do not sequence from memory of these tables.

## Workflow

### Step 1: Intake

**Open the floor.** Invite the user to share everything: which band/album, the per-band playlist YAML (or whether one needs scaffolding), any fixed/locked sequences, what they're trying to fix ("doesn't flow"), and whether this is a first ordering, a re-evaluation after a regen wave, or slotting one new track. Adapt the ask to what they hand you.

**Frame the scope before working.** Once you know the job, say back what you're about to do and how deep it goes — a full re-sequence with songbook-verified thematic claims is a different commitment from a one-track slot or a sonic-only transition pass. Let the user redirect the depth before you spend the effort.

**Canonical input:** the per-band playlist YAML at `docs/{band-slug}-playlist.yaml` — the single source of truth for the band's track sequence. If a band has songbook entries but no playlist YAML, scaffold one via `python3 src/skills/suno-band-profile-manager/scripts/scaffold-playlist.py {band-slug} --from-songbook`, then have the user fill in audio filenames. Schema and lifecycle rules: `suno-band-profile-manager/references/profile-schema.md` "Per-Band Playlist YAML".

**Scope check (skip the heavy methodology):** reordering 1-2 adjacent tracks with no upstream/downstream impact, or a fixed-sequence user who wants only sonic-transition feedback, doesn't need the full review — handle it directly. A very short playlist (≤4 tracks) likewise has no real album-arc to shape — there's no front/peak/close geography to balance, so skip the arc models, surface any locked pair, and reason about the handful of transitions directly rather than narrating a methodology that doesn't have room to apply.

### Step 2: Generate Sequencing Data

Run the deterministic analysis over the playlist YAML:

```
uv run scripts/playlist-sequencing-data.py --playlist docs/{band-slug}-playlist.yaml
```

This produces per-track BPM, overall/entry/exit keys + Camelot codes, energy level, intro/outro energy %, and per-transition quality (exit-Camelot of N → entry-Camelot of N+1). Output auto-archives to `docs/audio-analysis/playlists/{band-slug}.json` and refreshes the companion `docs/{band-slug}-playlist-sequencing.md` (AUTOGEN markers preserve hand-curated content). If librosa deps are missing the script returns JSON with install instructions (exit code 2) — surface that and continue with any data already on disk.

**Reconcile the track count before sequencing.** Compare the number of tracks the script actually analyzed against the playlist YAML entry count. A missing or mistyped audio filename makes the script skip that track silently, and an unnoticed drop produces a confident sequence over the wrong list. If any track is MISSING or errored, name those tracks explicitly and confirm with the user (fix the filename, or proceed knowingly without them) before sequencing. In headless, never silently drop — record each dropped track in `dropped_tracks[]`.

**Re-eval after a regen wave:** when the intent is re-evaluation rather than a first ordering, diff the fresh script output against the prior archive at `docs/audio-analysis/playlists/{band-slug}.json` and lead the proposal with what actually moved — which tracks' BPM/key/energy shifted and which transitions degraded as a result — instead of re-deriving the whole sequence from scratch.

**Fully degraded (deps gone AND no prior archive):** if librosa is unavailable and there's no archived JSON to fall back on, there is no audio data at all. Don't fabricate Camelot/BPM/energy numbers. Either help the user install the deps, or proceed on narrative/thematic grounds only (locked arcs, theme spacing, act logic) and state plainly that the sonic-transition layer is unverified.

**Optional catalog-wide deeper pass:** for energy shifts, section boundaries, spectral balance, and dynamic character across the whole catalog, run `uv run scripts/batch-full-analysis.py --audio-dir docs/audio` (writes `docs/catalog-analysis-report.md`). Use it when dynamic-character or section-shape data informs the arc; skip it for a quick reorder.

The data layer is the *input* to the methodology — it does not decide the sequence.

### Step 3: Apply the Methodology

(Re)load `references/playlist-sequencing-methodology.md` per Compaction Survival, then apply it: surface locked arcs first, verify felt BPM for tracks in the halftime/double-time danger ranges, **read the full songbook entry for every song in any thematic claim** (Thematic Verification — mandatory), identify the act/energy-arc shape, check load-bearing key positions, walk transitions on the full variable stack, and spot cluster opportunities (scattered felt-tempo cousins; adjacent thematic cousins that should be spaced). The reference carries the energy-arc models, key positions, same-key/sonic-palette/tempo-variety rules, similar-songs-distance, encore anatomy, and the parallel-key and genre-outlier caveats.

For a full re-sequence (not a quick reorder), the two flows are independent and easy to conflate, so review them as parallel lenses: a **sonic-flow** pass (Camelot/felt-BPM/intro-outro/sonic-palette transitions and the energy arc) and a **narrative-flow** pass (theme spacing, act logic, locked arcs, the closer-as-resolution). Reconcile where they disagree — a transition that's sonically smooth but thematically blurs two cousins, or a thematically perfect adjacency that's tempo-jarring — rather than letting one lens silently win.

### Step 4: Present the Sequence

Before committing to a proposal, **soft-gate**: ask whether there's anything fixed you should respect — a locked pair, a deliberate opener/closer, a track the user refuses to move — before you build the order around assumptions. Cheaper to ask than to re-sequence.

Present an *opinionated proposal*, not a metrics dump: the recommended order with per-move rationale that names what each variable says, the energy-arc shape it produces, which arcs were held locked, and honest trade-offs (every move trades something — name it; don't claim "cleaner" when it's "trades A-jarring for B-jarring"). Where the user's ear should be the tiebreaker, say so. Invite refinement and iterate.

When the user volunteers a narrative aside mid-flow ("oh, that one's really about my dad," "these two were written as a pair") — capture it into the decision log rather than interrupting the sequencing to chase it. Those unprompted asides are often the load-bearing thematic context the songbook read would otherwise have to surface.

The recommended sequence is a revisable artifact: write the proposal and a `.decision-log.md` as peers in `docs/{band-slug}-playlist-sequencing/` (the workspace); the decision log is canonical memory — it records each placement call, the rejected alternatives, and any locked-arc override the user authorizes, so a later re-sequence resumes cleanly instead of relitigating settled placements. On re-sequence, read the decision log first and enter the change as a signal against the standing record, surfacing any conflict with a prior call before applying it. At handoff, audit the log so the user signs off on how their sequencing decisions were handled.

## Scripts

- `playlist-sequencing-data.py` — Generates per-track sequencing data (BPM, overall/entry/exit keys, Camelot codes, energy level, intro/outro energy %, per-transition quality) for a per-band playlist YAML. Auto-archives JSON to `docs/audio-analysis/playlists/{band-slug}.json` and refreshes the per-band companion `docs/{band-slug}-playlist-sequencing.md` by default; `--no-archive` / `--no-companion` to skip. Run `uv run scripts/playlist-sequencing-data.py --help`.
- `batch-full-analysis.py` — Catalog-wide deeper analysis (tempo stability, energy arc/shifts, section boundaries, spectral balance, dynamic character). Archives to `docs/audio-analysis/catalog/<date>-deep.json` and refreshes `docs/catalog-analysis-report.md`. Run `uv run scripts/batch-full-analysis.py --help`.
