# Headless Contract

Load this when the skill runs with `--headless` / `-H`. The Band Manager agent calls it this way for every package with lyrics, so the return must be complete without a conversation. The workflow steps in `SKILL.md` still apply; this file covers the inputs, the defaults that replace questions, what is written, and what comes back.

## Modes

| Flag | Runs | Returns |
|------|------|---------|
| `--headless` (`--headless:transform` is the same mode) | Steps 1-4 with the defaults below | Transform return |
| `--headless:analyze` | Step 1 only | Analysis return |
| `--headless:refine` | Refinement (below) | Transform return, with `adjustments_applied` |

**Input** (structured): `text` (the source; required except for refine), and optionally `options` (codes), `profile`, `direction` (genre, mood, energy), `reference_tracks`, `language`, `model`, `section_cues` (per-section instructions from the style map, for cues that restate it word for word), and `song_path` (the songbook entry, when one exists). Check `options` with `validate-options.py` before starting.

## The Writer's Spacing

The spacing contract in `SKILL.md` holds without a user to catch a slip. `transformed_lyrics` carries the writer's indentation, internal spacing, line breaks and blank lines verbatim. The transformer adds metatags, section tags and blank lines at section breaks, plus the edits it reports in `changes`; every other character stays as given.

Before returning, `spacing-check.py` must show no high findings, and every line edit it lists must appear in `changes`. If Suno's lyrics field needs a flat copy (for example, spacing pushes the text over the budget), return it in `flat_copy_lyrics` from `spacing-check.py --flatten` and add a caveat. `transformed_lyrics` stays the spaced, canonical version.

## Defaults That Replace Questions

Record each one you apply in `decision_log`.

- **Options:** ST + CC + RA + CD. Pre-structured input → RA + CD. Short input → ST + a short-poem strategy. Over ~2,500 characters → drop CC.
- **Non-Latin or mixed script** (`analyze-input.py` `script_type`): non-Latin lines get structure and arc work only; no syllable, rhyme or cliche checks. Add a caveat.
- **Oversized input:** focus on the single strongest section that fits the budget and return `complete_with_caveats`. Block only if even that section is over the 5,000 hard limit.
- **Band profile:** record which state applied (not found, malformed, or no voice fields) and proceed without what's missing.
- **Narrative section labels:** translate them to Suno direction and record the original labels.

## Transform Return

Map `transformation_summary` straight from `assemble-summary.py`'s JSON `metrics`; don't compute any of it.

```json
{
  "status": "complete | complete_with_caveats | blocked",
  "reason": "one line, only when blocked",
  "caveats": ["degraded: syllable-counter.py failed, counts are estimates"],
  "transformed_lyrics": "complete lyrics with metatags, writer's spacing intact",
  "flat_copy_lyrics": "only when needed: a paste aid, not the canonical lyrics",
  "transformation_summary": {
    "sections": ["Verse 1", "Chorus", "Verse 2", "Chorus", "Bridge", "Final Chorus"],
    "section_count": 6,
    "estimated_duration": "2:45-3:30",
    "transformations_applied": ["ST", "CC", "RA", "CD"],
    "syllable_range": "6-10",
    "character_count": 1850,
    "lyric_character_count": 1640,
    "metatag_character_count": 210,
    "character_budget": "1850/3000 (62%)"
  },
  "changes": [{"code": "RA", "lines": [7, 8], "detail": "split line 7 at the breath"}],
  "cliche_report": {"flagged": 3, "replaced": 2, "kept": ["phrase"]},
  "validation_result": {"status": "pass", "findings": []},
  "spacing_check": {"status": "pass", "line_edits": 4},
  "source_hash": "analyze-input.py metrics.source_hash, or unavailable",
  "decision_log": [
    {"assumption": "non-Latin lines 5-8 → structure only", "basis": "analyze-input.py script_type"},
    {"assumption": "band profile 'x' not found → no voice constraints", "basis": "missing file"}
  ],
  "intentional_keeps": [{"keep": "cliche 'broken heart'", "reason": "central to the poem's thesis"}],
  "decision_log_path": "path written, or null",
  "adjustments_applied": [{"type": "section-restructure", "status": "applied | partial | skipped", "detail": "..."}]
}
```

`adjustments_applied` appears on refine only.

**Analysis return** (`--headless:analyze`): `status`, `reason`, `decision_log`, `source_hash` and `analysis`. The `analysis` object holds `structure`, `emotional_arc`, `hooks`, the `analyze-input.py` metrics, a syllable summary, and `recommended_codes` with a one-line rationale each. Transform fields are left out.

**Status.** `complete` is a clean run. Use `complete_with_caveats`, and say why in `caveats`, when lyrics come back but are qualified:
- the voice-preservation read flagged a real risk;
- a script failed and figures are estimates;
- oversized input was focused down;
- non-Latin or mixed script forced structure-only work;
- a flat copy was needed.

`blocked` means no source text, no section that fits the hard limit, or options that cannot be reconciled. Give a one-line `reason` and still return `decision_log`.

## Where Keeps Are Written

A song's decision log sits beside its songbook entry: `{songbook_folder}/{band-profile-or-untitled}/{song-title}.decision-log.md`. It is the writer's data. It records the structural decisions and **intentional keeps**: a cliche kept on purpose, a hedge or certainty level the writer insisted on, a line they refused to lose. It is append-only; each run adds a `## Session YYYY-MM-DD (transform | refine)` heading with one bullet per decision or keep.

- **`song_path` given:** append this run's session to the log beside it and return the path in `decision_log_path`.
- **No `song_path`** (for example, the pipeline before the song is saved): write nothing. Return `decision_log` and `intentional_keeps`; the caller appends them as a session when it saves the songbook entry.

## Refinement

For `--headless:refine`, or an adjustment spec from the Feedback Elicitor, skip the full pipeline and apply targeted changes.

1. **Read the decision log first** if one exists beside the song (`{song-title}.decision-log.md`, or an older `.decision-log.md` in that folder). It says why earlier choices were made and which keeps were intentional, so refinement doesn't quietly undo a kept cliche or an insisted-on hedge. If an adjustment contradicts a logged keep, don't apply it: mark it `skipped` with the conflict in `detail`, and add a caveat. (Interactively, raise the conflict before applying.)
2. Apply each adjustment.
3. Run the Step 4 checks. `spacing-check.py` compares against `source_lyrics`, the writer's current version.
4. Append the session to the log (per the rules above) and return the transform contract.

```json
{
  "source_lyrics": "the current lyrics text",
  "adjustments": [
    {"type": "section-restructure", "detail": "add a bridge between chorus 2 and final chorus"},
    {"type": "line-rewrite", "lines": [3, 4], "reason": "too wordy, needs tighter phrasing"},
    {"type": "metatag-change", "section": "Chorus", "add": "[Energy: building]"},
    {"type": "rhythmic-fix", "section": "Verse 2", "detail": "lines too long for vocal phrasing"}
  ],
  "context": {"band_profile": "profile-name", "original_intent": "dreamy indie folk song about loss", "model_used": "v6"},
  "song_path": "optional: the songbook entry"
}
```

Run `{workflow.on_complete}` (if non-empty) just before returning.
