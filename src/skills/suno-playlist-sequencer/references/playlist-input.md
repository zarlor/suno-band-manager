# Playlist Input

What the sequencing script reads, and what to do when a run can't analyze the whole playlist. `{docs}` is the folder holding `{band_profiles_folder}` (default `{project-root}/docs`). Each band owns one playlist file, `{docs}/{band-slug}-playlist.yaml`, the single source of truth for its track order; the slug matches the band profile's filename. This skill changes only the order of its `tracks:` list, through `validate_sequence.py --write`. Creating the file and simple edits (adding a published track, renaming one, fixing a `file:` name) belong to the profile manager: invoke the `suno-band-profile-manager` skill (Manage Playlist), which also scaffolds the file from the band's songbook entries; the user then fills in the audio filenames. If that skill isn't installed, offer to add it (the `bmad` skill installs this module's skills); if the user would rather go on now, draft a minimal file with the keys below (`album:`, and `tracks:` with a `name:` and a `file:` each), show it, and write it once they confirm.

## Keys this skill reads

- `album:` the band or album display name. The script also slugs it for the archive and companion filenames, which it reports under `artifacts`; without the key it names them after the playlist file (`{band-slug}`), so two bands never share an archive.
- `audio_dir:` (optional) the folder `file:` entries are relative to: an absolute path, or one written from `{project-root}`, which the script resolves through `--project-root {project-root}`.
- `tracks:` in playlist order, each with `name:` (the songbook entry's title, unique in the playlist, because every script looks a track up by name) and `file:` (the audio filename, relative to the audio folder). A scaffolded entry has an empty `file:` until the user fills it.
- `felt_bpm:` (optional, per track) the tempo the user confirmed by ear, as a positive number (`72`, not `"72"`). The script folds that track's half- or double-time readings to it in the seam math and stops raising `felt_bpm_check`.
- `locked_arcs:` (optional, top level) a list of arcs, each a list of track names or one `"A > B > C"` string, two tracks or more.

## Audio folder layout

Each band's audio lives in `{docs}/audio/{band-slug}/`, the same slug as its profile and playlist, so two bands can publish the same title without filename collisions.

- `playlist_sequencing_data.py` looks for each `file:` in this order: the `--audio-dir` flag, the YAML's `audio_dir:`, `audio/{band-slug}/` beside the playlist when that folder exists, then the flat `audio/` beside the playlist.
- A playlist whose filename isn't a band slug (a thematic playlist drawn from one band) sets `audio_dir:` explicitly. A playlist that mixes bands sets `audio_dir:` to the audio root and writes each `file:` with its band folder (`band-slug/Song.mp3`).
- `batch_full_analysis.py` scans its folder recursively and labels files by band-folder path. Pointed at one band's folder, it writes band-scoped outputs, so the catalog-wide report is left alone.
- Both scripts read `.mp3`, `.wav`, `.flac`, `.ogg` and `.m4a` files, in any letter case.

## When the run comes up short

- **Drops.** Each `dropped[]` entry was not analyzed, with its reason: `missing audio file` (the `file:` names nothing in the audio folder; check the spelling, or that the audio was saved there), `no file: set in the playlist entry`, or `analysis error: …`. Name each one and confirm before sequencing: fix the file, or go on knowingly without it.
- **`felt_bpm_ignored[]`.** Each entry's `felt_bpm:` isn't a positive number (a quoted `"72"`, a zero), so the seams used that track's measured tempo. Name each one; once the value is corrected in the YAML, re-run.
- **`artifacts.archive.status` `kept-prior`.** The drops would have erased analyzed tracks from the re-eval baseline, so the script kept the prior archive, and the file on disk still holds the earlier run's measurements. Once the user accepts the shorter list, re-run with `--force-archive`.
- **`artifacts` status `skipped`.** That run passed `--no-archive` or `--no-companion`, so the file on disk is from an earlier run, or absent.
- **Exit 3, with an `artifacts` status `error`.** The analysis ran and its report printed, but the archive or the companion could not be written; the `reason` and stderr say why. Work from the printed report, tell the user which file is out of date, and settle the cause before sign-off re-runs the script.
- **Exit 1.** The `error` names the reason: a mistyped flag, an unreadable playlist, two tracks sharing a name, or no track analyzed, in which case nothing was written and the prior archive is untouched.
- **Exit 2.** The audio dependencies are missing. Say so, and sequence from the archive already on disk, saying the numbers come from its last run.
- **Fully degraded** (no dependencies, no archive): help install them, or work on narrative grounds only (locked arcs, theme spacing, act logic) and say plainly that the sonic layer is unverified rather than estimating it.
