# The Songbook Entry

A song's durable record: what went into Suno, what came back, and where the song stands. The catalog scripts (`regenerate_index_sections.py`, `songbook_catalog.py`, `validate_sanctum.py`, `genre_coverage.py`) parse it, so the parts named below keep their names. `{songbook_folder}` is the wake's `config` value, a full path.

## When it is written

An interactive Create Song presents a package and writes no entry. The entry is created when the owner keeps a take (the post-publish pass), or by a headless Create Song run asked for `save_to_songbook`. An entry that already exists is creative work: change it with the owner's say-so (Law 3), and in a headless run stage the change and report it.

## Path

`{songbook_folder}/{band-slug}/{song-slug}.md`. `{band-slug}` is the band profile's file name without `.yaml`; `{song-slug}` is the title in lowercase with hyphens.

The catalog scripts leave out an entry whose `band_profile` names no band profile. So when the song has no profile, offer to create one with the `suno-band-profile-manager` skill before writing the entry; a headless run skips the write and says so in `warnings`.

## Frontmatter

The file opens with a `---` YAML block:

| Key | Value |
|-----|-------|
| `title` | The song's title, quoted |
| `band_profile` | The band slug, same as the folder |
| `status` | `wip` until the keeper is downloaded or published, then `published` |
| `date` | ISO date. The publish date, unless `published` is also given |
| `published` | ISO publish date, only when `date` keeps the day work started |
| `source_wip` | The `docs/wip-*.md` file the song grew from, when there is one |

Keep bracketed text out of unquoted values (a list such as `[ST, CC]` is fine; an item holding `[Spoken]` breaks the YAML and the entry drops out of the catalog).

## Body

- `## Lyrics` — the lyrics as pasted, the writer's spacing intact.
- `## Style Prompt` — the prompt in a code block; the catalog reads the first code block under this heading.
- `## Exclude Styles` — as pasted, or a line saying the tier has no field.
- `## Settings` — one table row or bullet per control, named as on the Create screen (Model, Voice, Persona, Custom Model, Vocal Gender, Lyrics Mode, Duration, Max Mode, Weirdness, Style Influence, Audio Influence, Variety, Personalize), so the catalog can tally them.
- `## Generation Log` — dated lines: what was generated, what was kept, measured numbers.
- One bold status line. `**Status: WIP**` while unpublished. At publish: ``**Status: LOCKED — Published <YYYY-MM-DD>. <one-line description>. Audio at `docs/audio/<band>/<file>`.**``

The validator needs `status: published` in the frontmatter and a `LOCKED` or `PUBLISHED` status line to agree, the frontmatter publish date to match the line's, and the audio file the line names to exist.
