# Playlist Input

`{docs}` is the folder holding `{band_profiles_folder}` (default `{project-root}/docs`). Each band owns one playlist file, `{docs}/{band-slug}-playlist.yaml`, the single source of truth for its track order; the slug matches the band profile's filename. This skill changes only the order of its `tracks:` list, through `validate-sequence.py --write`. Creating the file and simple edits (adding a published track, renaming one, fixing a `file:` name) belong to the profile manager: invoke the `suno-band-profile-manager` skill (Manage Playlist), which also scaffolds the file from the band's songbook entries.

## Keys this skill reads

- `album:` the band or album display name. The script also slugs it for the archive and companion filenames, which it reports under `artifacts`.
- `audio_dir:` (optional) the folder `file:` entries are relative to, written from `{project-root}` (scripts run from there).
- `tracks:` in playlist order, each with `name:` (the songbook entry's title) and `file:` (the audio filename, relative to the audio folder). A scaffolded entry has an empty `file:` until the user fills it; the run drops it with the reason `no file: set in the playlist entry`.
- `felt_bpm:` (optional, per track) the tempo the user confirmed by ear. The script folds that track's half- or double-time readings to it in the seam math and stops raising `felt_bpm_check`.
- `locked_arcs:` (optional, top level) a list of arcs, each a list of track names or one `"A > B > C"` string, two tracks or more.

## Audio folder layout

Each band's audio lives in `{docs}/audio/{band-slug}/`, the same slug as its profile and playlist, so two bands can publish the same title (one writer, several bands, or a re-recorded catalog) without filename collisions.

- `playlist-sequencing-data.py --playlist {docs}/{band-slug}-playlist.yaml` looks for each `file:` in this order: the `--audio-dir` flag, the YAML's `audio_dir:`, `audio/{band-slug}/` beside the playlist when that folder exists, then the flat `audio/` beside the playlist.
- A playlist whose filename isn't a band slug (a thematic playlist drawn from one band) sets `audio_dir:` explicitly. A playlist that mixes bands sets `audio_dir:` to the audio root and writes each `file:` with its band folder (`band-slug/Song.mp3`).
- `batch-full-analysis.py` scans its folder recursively and labels files by band-folder path. Pointed at one band's folder, it writes band-scoped outputs, so the catalog-wide report is left alone.
- A flat `{docs}/audio/` keeps working; per-band folders are the layout once a project has a second band.

## Drops

A track the script couldn't analyze is listed in `dropped[]` with its reason: `missing audio file` (the `file:` names nothing in the audio folder; check the spelling, or that the audio was saved there), `no file: set in the playlist entry`, or `analysis error: …`. A filename fix in the YAML goes through the profile manager, as above.
