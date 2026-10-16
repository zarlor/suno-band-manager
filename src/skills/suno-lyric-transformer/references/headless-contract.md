# Headless Contract

Read this when the skill runs with `--headless` / `-H`. The Band Manager agent calls it this way for every package with lyrics, so the return must be complete without a conversation. The workflow steps in `SKILL.md` still apply; this file covers the inputs, the defaults that replace questions, what is written, and what comes back.

**Work silently and finish everything:** send no message before the reply: every tool call goes out with no words beside it (no "Now emitting…", no progress note), and run no background commands: every tool call finishes before you return, so nothing reports after the reply. Scratch files go in a fresh `mktemp -d` folder, never a fixed `/tmp` name another run could share.

## Modes

| Flag | Runs | Returns |
|------|------|---------|
| `--headless` (`--headless:transform` is the same mode) | Steps 1-4 with the defaults below | Transform return |
| `--headless:analyze` | Step 1 only | Analysis return |
| `--headless:refine` | Refinement (below) | Transform return, with `adjustments_applied` |

## Inputs

| Field | Notes |
|---|---|
| `text` | The source. Required except for refine |
| `options` | Codes, e.g. `["ST", "RA", "CD"]`. When given they win over `creativity_mode`. Check them with `validate-options.py` before starting |
| `creativity_mode` | `conservative` / `balanced` (default) / `experimental`; sets the default codes when `options` is absent (below) |
| `band_profile` | Profile name, read from `{band_profiles_folder}/{name}.yaml` (`profile` is accepted for older callers) |
| `direction` | Genre, mood, energy |
| `section_cues` | Per-section instructions from the style prompt's section map, e.g. `{"Verse 1": "riff continues under vocal, drums drive"}`. ST writes each into its section's tag verbatim (`[Verse 1 - riff continues under vocal, drums drive]`); a cue for a section the arc doesn't have goes in `decision_log` |
| `reference_tracks`, `language`, `model` | Optional context; `language` defaults to the source text's |
| `song_path` | The songbook entry, when one exists (decides where the decision log is written) |

## The Writer's Spacing

No user is there to catch a slip, so `transformed_lyrics` carries the writer's indentation, internal spacing, line breaks and blank lines verbatim; only tags, blank lines at section breaks and the edits reported in `changes` are added. Before returning, `spacing-check.py` must show no high findings, and every line edit it lists must appear in `changes`. If Suno's lyrics field needs a flat copy (for example, spacing pushes the text over the budget), return it in `flat_copy_lyrics` from `spacing-check.py --flatten` and add a caveat. `transformed_lyrics` stays the spaced, canonical version.

## Defaults That Replace Questions

Record each one you apply in `decision_log`.

- **Options:** `options` when given. Otherwise start from SKILL.md Step 2's defaults for this input (raw, pre-structured, short, over ~2,500 characters) and apply `creativity_mode`:

  | `creativity_mode` | Codes |
  |---|---|
  | `conservative` | The defaults with CE in place of CC: promote the writer's own lines rather than write a new chorus |
  | `balanced` | The defaults as they are |
  | `experimental` | The defaults, with ST taking structural liberties using the writer's own lines: reorder sections, repeat or split lines, call-and-response, unconventional forms (the Band Manager's Jam mode). The writer's words stay theirs: add FR or RE only when `direction` asks for a rewrite or new rhymes (owner, 2026-10-15) |

  The input-size rules still hold after the mode: a short input takes a short-poem strategy instead of CC, and over ~2,500 characters drops CC. Log the mode and the resulting codes in `decision_log`.
- **Non-Latin or mixed script** (`analyze-input.py` `script_type`): non-Latin lines get structure and arc work only; no syllable, rhyme or cliche checks (`--latin-only`). Add a caveat; the line count it gives is the length of the scripts' `skipped_lines`, not a count by eye. Latin-script non-English text: run the checks and caveat that they are tuned for English.
- **Oversized input:** focus on the single strongest section that fits the budget and return `complete_with_caveats`. Block only if even that section is over the 5,000 hard limit.
- **Band profile:** record which state applied (not found, malformed, or no voice fields) and proceed without what's missing.
- **Narrative section labels:** translate them to Suno direction and record the original labels.

## Transform Return

**The reply is the JSON object alone:** no text before or after it and no code fence, so a script can parse it. Anything worth saying goes in a field: `caveats` qualify the lyrics, `warnings` carry only setup notices (BMad not set up, one entry; a missing profile goes in `decision_log`), `decision_log` the calls made.

Copy `transformation_summary` as is from `assemble-summary.py`'s JSON, run on the exact lyrics you return (after the last edit; its `character_count` equals their length); don't compute any of it. Each `changes[].lines` is the `location.transformed_lines` that `spacing-check.py` reported for that edit (1-based lines of `transformed_lyrics`, tags and blanks counted), and an ST entry's lines are the `line` values of its `added_tag_lines`: never a count by hand. `transformed_lyrics` carries no trailing newline (the scripts count it that way). `cliche_report.flagged` is `cliche-detector.py`'s `metrics.total_cliches_found` (`cliche_report` is `null` when CD didn't run), and `validation_result` is the final `validate-lyrics.py` run's `status` and `findings`.

```json
{
  "status": "complete | complete_with_caveats | blocked",
  "reason": "one line, only when blocked",
  "caveats": ["degraded: syllable-counter.py failed, counts are estimates"],
  "warnings": ["BMad not set up here: config defaults used; run bmad setup suno"],
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
- the voice-preservation read flagged a real risk (whatever `decision_log` flags as a risk is also a caveat);
- a line that isn't the writer's was written (name it; it's also in `changes`);
- a length the writer asked for ("a whole song, not a sketch") isn't reached by `estimated_duration`;
- a script failed and figures are estimates;
- oversized input was focused down;
- non-Latin or mixed script forced structure-only work;
- a flat copy was needed.

**Before returning,** check the draft against these, since no one reviews it after you:
- Every `decision_log` entry that names a risk has its caveat, and the status is then `complete_with_caveats`.
- `estimated_duration` is `assemble-summary.py`'s figure. If the writer asked for a length it doesn't reach, the caveat says so with both figures; never claim a duration the script didn't estimate.
- Each `changes[]` entry has the lines of its own edit. An edit with no line left in the lyrics (a removed title line) has `"lines": []` and quotes the source line in `detail`.
- A section sung once is a verse, bridge or refrain, not `[Chorus]`: a chorus returns.
- A short poem uses one short-poem strategy from `section-jobs.md`, named in `decision_log`. A section-length finding never justifies padding (repeating a line to reach a minimum): leave the section short and say so in `decision_log`.
- A count in a caveat ("the hook is sung 7 times", "6 Japanese lines") is counted from the returned lyrics or a script's output, never estimated.
- An edit `spacing-check.py` didn't report as a line edit (a repeated section aligned as the writer's own) cites only the `added_tag_lines` line of the section it built (the tag, not the writer's lines under it).
- Each edit carries the code of what was done, whatever the mode: any section built from the writer's own lines (a chorus, a refrain, an outro repeating the closing line) is CE, a newly written chorus CC, and a caveat never says lines weren't repeated when a section repeats them. When that departs from the mode's codes, `decision_log` says why.
- The final `spacing-check.py` run compares the returned lyrics with the unmodified source (never a trimmed copy), and adds `--word-fidelity` only in WF mode (SKILL Step 4): a removed title line or any other reported edit is a change it would flag.

`blocked` means no source text (or a path the scripts can't read), no section that fits the hard limit, or options that cannot be reconciled (`validate-options.py` exit 1). Give a one-line `reason` and still return `decision_log`.

## Where Keeps Are Written

The decision log is `{song-title}.decision-log.md` beside the songbook entry, append-only, one `## Session YYYY-MM-DD (transform | refine)` heading per run with one bullet per structural decision and intentional keep.

- **`song_path` given:** if a log already sits beside it, read it before transforming and leave its intentional keeps standing (record each in `intentional_keeps`); then append this run's session and return the path in `decision_log_path`.
- **No `song_path`** (for example, the pipeline before the song is saved): write nothing. Return `decision_log` and `intentional_keeps`; the caller appends them as a session when it saves the songbook entry.

## Refinement

For `--headless:refine`, or an adjustment spec from the `suno-feedback-elicitor` skill, skip the full pipeline and apply targeted changes.

1. **Read the decision log first** if one exists beside the song (`{song-title}.decision-log.md`, or an older `.decision-log.md` in that folder). It says why earlier choices were made and which keeps were intentional, so refinement doesn't quietly undo a kept cliche or an insisted-on hedge. If an adjustment contradicts a logged keep, don't apply it: mark it `skipped` with the conflict in `detail`, and add a caveat.
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
