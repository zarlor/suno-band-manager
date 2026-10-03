# Per-Band Playlist YAML (the canonical playlist source)

Each band owns exactly **one** canonical playlist file, `{docs}/{band-slug}-playlist.yaml`, where `{docs}` is the parent of `{band_profiles_folder}` (`docs/` by default). Other skills read it from that location, so it does not move per band.

The slug matches the band profile filename: `docs/band-profiles/iron-meridian.yaml` pairs with `docs/iron-meridian-playlist.yaml`. This file is the single source of truth for the band's track sequence. **Do not copy the track list anywhere else.** Other files (sidecar narrative, voice context, ordering doc) reference this YAML or derive from it.

**Who owns what.** This skill creates the file when a band is created and makes simple edits to it: adding a published track, renaming one, fixing a `file:` name. **Order changes and album-craft sequencing belong to the suno-playlist-sequencer skill.** It reads this file, checks proposed orders (locked arcs included) and rewrites the `tracks:` list.

## Schema

```yaml
album: "<Band display name>"
audio_dir: "docs/audio/<band-slug>"   # optional — the band's audio folder (see "Audio folder layout")
locked_arcs:                          # optional — runs whose order must not change
  - ["<Song A>", "<Song B>", "<Song C>"]
  - "<Song D> > <Song E>"
tracks:
  - name: "<Song title (must match the songbook entry's frontmatter title)>"
    file: "<exact filename in the band's audio folder, e.g. My Song.mp3>"
    felt_bpm: 72                      # optional — the tempo the owner hears
  - name: "<next song>"
    file: "<next file>"
  # ...
```

Each track needs two fields. `name` is the human-readable song title and must match the songbook entry's frontmatter `title`. `file` is the audio filename, relative to the band's audio folder; it is the input to the suno-playlist-sequencer skill's `playlist-sequencing-data.py`. The optional top-level `audio_dir` names that folder.

Optional fields read by the suno-playlist-sequencer skill:

- **`felt_bpm`** (per track, a positive number): the tempo the owner actually hears. Audio analysis often reads a track at half or double time. When `felt_bpm` is recorded, `playlist-sequencing-data.py` uses it to correct that track in its tempo and seam math, and stops raising `felt_bpm_check` for it. That check flags a measured tempo in the half/double-time danger range with no felt tempo on record.
- **`locked_arcs`** (top level, a list): runs of tracks that must stay together and in this order. Write each item as a list of track names, or as one `"A > B > C"` string; a run needs at least two tracks. The sequencer's `validate-sequence.py` rejects any proposed order that splits a locked arc or reorders it.

## Audio folder layout (per band)

Each band's audio lives in its own folder, `docs/audio/{band-slug}/`, using the same slug as the band profile and the playlist YAML. That way two bands can publish the same title (one lyricist writing for several bands, or a band re-recording its catalog) with no filename collisions and no suffix conventions.

- `playlist-sequencing-data.py --playlist docs/{band-slug}-playlist.yaml` looks for each `file:` in this order: the `--audio-dir` flag, the YAML's `audio_dir:`, `docs/audio/{band-slug}/` if that folder exists, then the legacy flat `docs/audio/`.
- A playlist whose filename is not a band slug (for example, a thematic playlist drawn from one band) sets `audio_dir:` explicitly. A playlist that mixes bands sets `audio_dir: "docs/audio"` and writes each `file:` with its band folder (`band-slug/Song.mp3`).
- `analyze-audio.py`, `batch-full-analysis.py`, `audio-files-manifest.py` and `verify-audio-files.py` scan `docs/audio/` recursively and label files by band-folder path (`{band-slug}/Song.mp3`). The verifier treats the folder as part of a file's identity, so one band's file never satisfies another band's manifest entry.
- `audio-deep-analysis.py` archives a band-folder file to `docs/audio-analysis/songs/{band-slug}/{song-slug}.json`.
- A flat `docs/audio/` keeps working everywhere. Per-band folders are recommended once a project has a second band.

## Bootstrapping

If a band already has songbook entries but no playlist YAML, scaffold one:

```bash
uv run scripts/scaffold-playlist.py {band-slug} --from-songbook --project-root {project-root}
```

This writes the playlist YAML with the discovered song titles and the `audio_dir:` key already filled in. The `file:` fields are left as empty strings; fill them in from the band's audio folder (`docs/audio/{band-slug}/`). The user reviews it, fills in the filenames, sets the order and saves. The script reads `band_profiles_folder` and `songbook_folder` from module config, so a relocated songbook is still found.

For a brand-new band with no songbook entries yet, run it without `--from-songbook` to write an empty template.

## Auto-creation on band profile creation

When the suno-band-profile-manager skill creates a band profile, it scaffolds this playlist YAML in the same write batch. Once a band without a playlist YAML has any songbook entries, `validate-profile.py` flags it.

## The `playlist:` block in band profile YAML is invalid

A band profile YAML must NOT contain a `playlist:` block, and `validate-profile.py` warns on any profile that has one. Authoritative track-list data lives in `docs/{band-slug}-playlist.yaml`. Notes on sequencing history belong in a band-specific ordering doc (`docs/{band-slug}-playlist-ordering.md`), if the band keeps one.

## Workflow rules (apply in the same write batch)

- **On song publish:** update the band's `docs/{band-slug}-playlist.yaml` alongside the songbook entry.
- **On track reorder:** edit the playlist YAML first (through the suno-playlist-sequencer skill). The sequencer's per-album companion, `docs/{band-slug}-playlist-sequencing.md`, refreshes from it on the next run.
- **On track removal or rename:** update the YAML, the songbook (if renaming), the sidecar narrative and any ordering doc together.
- **On band deletion:** the profile manager archives the playlist YAML together with the profile and decision log. Songbook entries stay where they are.

For the album-craft method that uses this file, see the suno-playlist-sequencer skill's `references/playlist-sequencing-methodology.md`.
