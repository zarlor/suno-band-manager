# Durable Writes

What this skill writes outside the conversation, and how. Two stores: the song's iteration log (every round) and the band profile (only when a profile is in play).

## Iteration log

One markdown file per song under `{workflow.feedback_history_output_path}`, the canonical memory of multi-round refinement: `{band-or-session}/{song-slug}.md`, where `{band-or-session}` is the band-profile name (or a session stamp `YYYYMMDD-HHMM` with no profile) and `{song-slug}` the kebab-cased title (or the same stamp when untitled). The script derives both, so never build the path by hand.

- **Locate:** `uv run {skill-root}/scripts/feedback-log.py locate --band {profile} --title {title} --history-dir {workflow.feedback_history_output_path}` returns the path, whether it exists, the last round and date, the next round number, the `stamp` it used, and near-match `candidates` when the exact file is missing (the title may be fuzzy — pick among them, and pass the chosen one's title from then on).
- **Open a round:** `uv run {skill-root}/scripts/feedback-log.py append --band {profile} --title {title} --history-dir {workflow.feedback_history_output_path} --text "<entry>" --snapshot '<json>'` writes the `## Round {n} — YYYY-MM-DD` heading, the prose entry and the snapshot, numbering the round from the log itself.
- **Add to the current round:** the same command with `--round last --text "<anchor>"` for a mid-elicitation anchor (a narrowed dimension, a reference, a locked keeper, a technical attempt) as it lands.
- With no profile or no title, pass `--stamp` with the `stamp` locate returned, so every write lands in the same session file.

**Entry.** The prose says what was tried this round and how the user reacted, in their words. The snapshot is the same round in machine-readable form; it doubles as the headless `iteration_log` payload, and the script sets its `round`:

```json
{"session_id": "{timestamp}", "feedback_type": "vague", "dimensions_adjusted": ["vocals", "production"], "key_changes": ["rawer vocals", "less reverb"], "user_intent": "dreamy indie folk", "reasoning_chain": "User said 'too polished' -> mapped to vocal production -> reduced reverb + added raw/intimate descriptors"}
```

## Band profile

Profile YAML is owned by the `suno-band-profile-manager` skill, which keeps comments, key order and the schema's caps; hand-edited YAML loses them.

- **`generation_history`** — this round's snapshot, every round. Invoke the `suno-band-profile-manager` skill with `--headless:append {profile} generation_history`, passing the entry as its one JSON entry: `{"date": "2026-10-03", "style_prompt": "...", "model": "v6", "sliders": {"weirdness": 55, "style_influence": 75}, "note": "<the user's reaction in a line>"}`. It trims the oldest past the schema cap of 10 and returns `field`, `appended`, `trimmed` and `length`.
- **`generation_learnings`** — a durable pattern, only when a round generalizes across songs (e.g. "reverb on lead vocals always reads as 'too polished' for this band"). Offer it; on a yes, invoke the same skill with `--headless:append {profile} generation_learnings` and the pattern string as the entry. One-song specifics stay in the iteration log.

A `blocked` return names the problem in `reason`: tell the user and leave the profile as it is.

## Headless runs

A headless run writes the same records, so a caller such as the Band Manager's refine flow keeps the song's history without extra work:

- the iteration-log round (needs `--band-profile` or `--title`; with neither, skip it);
- the `generation_history` snapshot (only with `--band-profile`).

Record each write in `decision_log` and list the paths in `written_paths`. **`generation_learnings` is never written headless** — a durable pattern needs the owner's agreement, so return it in `suggested_profile_learnings` for the caller to offer. `--headless:analyze` writes nothing (no round happened).

With `--no-write`, write nothing durable: skip both writes, pass `--no-archive --no-companion` to any audio script, and return the round in `iteration_log` and the snapshot in `suggested_generation_history` for the caller to apply.
