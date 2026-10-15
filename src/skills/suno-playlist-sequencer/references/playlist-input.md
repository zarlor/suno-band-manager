# Playlist Input

What the sequencing script reads, and what to do when a run can't analyze the whole playlist. `{docs}` is the folder holding `{band_profiles_folder}` (default `{project-root}/docs`). Each band owns one playlist file, `{docs}/{band-slug}-playlist.yaml`, the single source of truth for its track order; the slug matches the band profile's filename. This skill changes only the order of its `tracks:` list, through `validate-sequence.py --write`. Creating the file and simple edits (adding a published track, renaming one, fixing a `file:` name) belong to the profile manager: invoke the `suno-band-profile-manager` skill (Manage Playlist), which also scaffolds the file from the band's songbook entries; the user then fills in the audio filenames.

## Keys this skill reads

- `album:` the band or album display name. The script also slugs it for the archive and companion filenames, which it reports under `artifacts`.
- `audio_dir:` (optional) the folder `file:` entries are relative to, written from `{project-root}` (scripts run from there).
- `tracks:` in playlist order, each with `name:` (the songbook entry's title) and `file:` (the audio filename, relative to the audio folder). A scaffolded entry has an empty `file:` until the user fills it.
- `felt_bpm:` (optional, per track) the tempo the user confirmed by ear. The script folds that track's half- or double-time readings to it in the seam math and stops raising `felt_bpm_check`.
- `locked_arcs:` (optional, top level) a list of arcs, each a list of track names or one `"A > B > C"` string, two tracks or more.

## Audio folder layout

Each band's audio lives in `{docs}/audio/{band-slug}/`, the same slug as its profile and playlist, so two bands can publish the same title without filename collisions.

- `playlist-sequencing-data.py` looks for each `file:` in this order: the `--audio-dir` flag, the YAML's `audio_dir:`, `audio/{band-slug}/` beside the playlist when that folder exists, then the flat `audio/` beside the playlist.
- A playlist whose filename isn't a band slug (a thematic playlist drawn from one band) sets `audio_dir:` explicitly. A playlist that mixes bands sets `audio_dir:` to the audio root and writes each `file:` with its band folder (`band-slug/Song.mp3`).
- `batch-full-analysis.py` scans its folder recursively and labels files by band-folder path. Pointed at one band's folder, it writes band-scoped outputs, so the catalog-wide report is left alone.

## When the run comes up short

- **Drops.** Each `dropped[]` entry was not analyzed, with its reason: `missing audio file` (the `file:` names nothing in the audio folder; check the spelling, or that the audio was saved there), `no file: set in the playlist entry`, or `analysis error: …`. Name each one and confirm before sequencing: fix the file, or go on knowingly without it.
- **`artifacts.archive.status` `kept-prior`.** The drops would have erased analyzed tracks from the re-eval baseline, so the script kept the prior archive. Once the user accepts the shorter list, re-run with `--force-archive`.
- **Exit 1.** The `error` names the reason: an unreadable playlist, or no track analyzed, in which case nothing was written and the prior archive is untouched.
- **Exit 2.** The audio dependencies are missing. Say so, and sequence from the archive already on disk, saying the numbers come from its last run.
- **Fully degraded** (no dependencies, no archive): help install them, or work on narrative grounds only (locked arcs, theme spacing, act logic) and say plainly that the sonic layer is unverified rather than estimating it.
