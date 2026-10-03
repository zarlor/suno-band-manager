# Durable Writes

What this skill writes outside the conversation, and how. Two stores: the song's iteration log (every round) and the band profile (only when a profile is in play).

## Iteration log

One markdown file per song, the canonical memory of multi-round refinement. `uv run scripts/feedback-log.py locate --band {profile} --title {title} --project-root {project-root}` returns its path, whether it exists, the last round and date, the next round number, and near-match candidates when the exact file is missing (the title may be fuzzy — pick among them). Each round goes under `## Round {n} — YYYY-MM-DD`; the entry format is in `references/output-template.md`.

## Band profile

Profile YAML is owned by the suno-band-profile-manager skill. Write through its `scripts/apply-profile.py` (`{suno-band-profile-manager}` below is that skill's installed directory), never by hand-editing YAML.

- **`generation_history`** — this round's snapshot, appended every round. Entry fields: `date`, `style_prompt`, `model`, `sliders`, `note` (the user's reaction in a line). The schema caps the list at 10, so the script trims the oldest:
  ```bash
  uv run {suno-band-profile-manager}/scripts/apply-profile.py {profile} --append generation_history \
    --append-json '{"date": "2026-10-03", "style_prompt": "...", "model": "v6", "sliders": {"weirdness": 55, "style_influence": 75}, "note": "..."}' \
    --max 10 --project-root {project-root} --profiles-dir {band_profiles_folder}
  ```
- **`generation_learnings`** — a durable pattern, only when a round generalizes across songs (e.g. "reverb on lead vocals always reads as 'too polished' for this band"). Offer it; on a yes, append it with the same script (`--append generation_learnings --append-json '"<pattern>"'`, no `--max`). One-song specifics stay in the iteration log.

If the script reports a failure, tell the user and leave the profile untouched rather than writing it by hand.

## Headless runs

A headless run writes the same records, so a caller such as the Band Manager's refine flow keeps the song's history without extra work:

- the iteration-log round (needs `--band-profile` or `--title`; with neither, skip it);
- the `generation_history` snapshot (only with `--band-profile`).

Record each write in `decision_log` and list the paths in `written_paths`. **`generation_learnings` is never written headless** — a durable pattern needs the owner's agreement, so return it in `suggested_profile_learnings` for the caller to offer.

With `--no-write`, write nothing durable: skip both writes, pass `--no-archive --no-companion` to any audio script, and return the round in `iteration_log` and the snapshot in `suggested_generation_history` for the caller to apply.
