# Manage Playlist

Each band owns one canonical playlist file, `{docs}/{band-slug}-playlist.yaml`, where `{docs}` is the parent of `{band_profiles_folder}` (`docs/` by default) and the slug matches the profile's filename. It is the single source of truth for the band's track sequence; other skills read it from that location, and anything else that lists the tracks references it instead of copying it, since copies drift.

Scripts run as `uv run {skill-root}/scripts/<name>.py … --project-root {project-root}`.

**What this skill does here:** creates the file and makes simple edits — adding a published track, renaming one, fixing a `file:` name — confirming each with the user. Reordering and album-craft sequencing belong to the `suno-playlist-sequencer` skill; invoke it for those.

## Schema

```yaml
album: "<Band display name>"
audio_dir: "docs/audio/<band-slug>"   # optional; each file: is relative to it
locked_arcs:                          # optional, sequencer-owned
  - ["<Song A>", "<Song B>"]
tracks:
  - name: "<Song title, matching the songbook entry's frontmatter title>"
    file: "<exact filename in the band's audio folder, e.g. My Song.mp3>"
    felt_bpm: 72                      # optional, sequencer-owned
```

`file` is relative to `audio_dir` (default `docs/audio/{band-slug}/`) and is what the sequencer analyzes. Keep `locked_arcs` and `felt_bpm` intact when editing a track and leave their values to the sequencer.

## Bootstrapping

`scripts/scaffold-playlist.py {band-slug}` writes the file: empty for a new band, or with `--from-songbook` the band's published songbook entries as tracks with empty `file:` fields to fill in from the audio folder. It reports `exists` and changes nothing when the file is already there. Once a band without a playlist YAML has songbook entries, `validate-profile.py` flags it.

Track data lives only here, so `validate-profile.py` warns on a profile that carries a `playlist:` block; sequencing-history notes belong in the band's ordering doc (`docs/{band-slug}-playlist-ordering.md`), if it keeps one.

## In the same write batch

- **A song is published:** add its track here alongside the songbook entry.
- **A track is renamed or removed:** update this file, the songbook entry's title and any ordering doc together.
- **The band is deleted:** `apply-profile.py --delete` archives this file with the profile and decision log.
