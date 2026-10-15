# Per-Band Playlist YAML (the canonical playlist source)

Each band owns exactly **one** canonical playlist file, `{docs}/{band-slug}-playlist.yaml`, where `{docs}` is the parent of `{band_profiles_folder}` (`docs/` by default). Other skills read it from that location, so it does not move per band.

The slug matches the band profile filename: `docs/band-profiles/iron-meridian.yaml` pairs with `docs/iron-meridian-playlist.yaml`. This file is the single source of truth for the band's track sequence; any other file that lists the tracks (Mac's memory, voice context, an ordering doc) drifts from it, so they reference it instead of copying it.

**Who owns what.** This skill creates the file when a band is created and makes simple edits to it: adding a published track, renaming one, fixing a `file:` name. Order changes and album-craft sequencing belong to the suno-playlist-sequencer skill, which checks proposed orders and rewrites the `tracks:` list; invoke it for those.

## Schema

```yaml
album: "<Band display name>"
audio_dir: "docs/audio/<band-slug>"   # optional — the band's audio folder; each file: is relative to it
locked_arcs:                          # optional, sequencer-owned — runs whose order must not change
  - ["<Song A>", "<Song B>", "<Song C>"]
  - "<Song D> > <Song E>"
tracks:
  - name: "<Song title (must match the songbook entry's frontmatter title)>"
    file: "<exact filename in the band's audio folder, e.g. My Song.mp3>"
    felt_bpm: 72                      # optional, sequencer-owned — the tempo the owner hears
  - name: "<next song>"
    file: "<next file>"
  # ...
```

Each track needs two fields. `name` is the human-readable song title and must match the songbook entry's frontmatter `title`. `file` is the audio filename, relative to the band's audio folder (`audio_dir`, by default `docs/audio/{band-slug}/`), and is what the sequencer analyzes. `felt_bpm` and `locked_arcs` are the sequencer's: keep them intact when editing a track, and leave their values to it.

## Bootstrapping

`scripts/scaffold-playlist.py {band-slug} --project-root {project-root}` writes the file: an empty template for a new band, or with `--from-songbook` the band's published songbook entries as tracks with empty `file:` fields to fill in from the audio folder. The album name is the profile's `name`. It reports `exists` and changes nothing when the file is already there.

Once a band without a playlist YAML has any songbook entries, `validate-profile.py` flags it.

## No `playlist:` block in the profile

Track data lives only in the playlist YAML, so `validate-profile.py` warns on any profile that carries a `playlist:` block. Notes on sequencing history belong in a band-specific ordering doc (`docs/{band-slug}-playlist-ordering.md`), if the band keeps one.

## Workflow rules (apply in the same write batch)

- **On song publish:** add the track to the band's playlist YAML alongside the songbook entry.
- **On track reorder:** the suno-playlist-sequencer skill rewrites the order.
- **On track removal or rename:** update the YAML, the songbook (if renaming), Mac's memory files and any ordering doc together.
- **On band deletion:** the profile manager archives the playlist YAML together with the profile and decision log. Songbook entries stay where they are.
