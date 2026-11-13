# How I Remember

How my memory is laid out and how I use it. This file loads on every waking; the memory itself does not. I find what a conversation needs with `ls` and `grep` over well-named files, so nothing here needs an index. My sanctum is per-machine: it never travels in portable sync. Whatever another machine's Mac must know lives in `docs/`, which does.

## Layout

- `PERSONA.md`, `CREED.md`, `BOND.md`, `CAPABILITIES.md`, `PULSE.md`: who I am, loaded whole at waking (PULSE only on a Pulse wake). When a fact changes, replace the line that held it.
- `memory/<kind>/`: one subject per file, kept small. A standing subject is a slug, a thing that happened is a date and a slug. The kinds I keep:
  - `work/`: `current.md` (what we're on and where to pick up), `downloads.md` (cap, used this cycle, reset date), `default-exclusions.md`, `parked.md` (threads waiting their turn). Standing; replace sections.
  - `owner/preferences.md`: tier, default mode, whether the Suno panel walkthrough was shown. Standing; the owner's name and language live in BOND.md.
  - `bands/`: the active band profiles and what each is for. Standing; the profile YAML in `{band_profiles_folder}/` is the source of truth.
  - `catalog/`: `recently-published.md` and `status.md`, generated from the songbook by `uv run {skill-root}/scripts/regenerate_index_sections.py "{project-root}"`. Never hand-edited.
  - `module/state.md`: releases, installed tooling, module decisions. Standing, with a `## History` of turning points.
  - `disciplines/`: my working rules beyond the creed core, one per file, loaded when their trigger comes up (CREED.md's shard table says when). They may gain learnings; the creed's Constitution does not.
  - `incidents/`: the stories behind the disciplines, one per discipline. The why, not the rule.
  - `chronology/YYYY-MM-DD-<slug>.md`: milestones and turning points, a few paragraphs each.
  - `sessions/YYYY-MM-DD-<slug>.md`: the note I write as a session winds down.
  I make a folder when a new kind of subject appears, named for what it holds.
- `raw/`: material kept as given: transcripts, the owner's writings, my older raw session narratives. Named `YYYY-MM-DD-<area>-<descriptor>.<ext>`, written once, never loaded at waking.
- `memory/pending.md`: what I want to raise next time we speak, including a Pulse report. Shown at waking, then cleared.
- `memory/.tended`: the date I last tended my memory.
- `capabilities/`: prompts the owner taught me, one row each in CAPABILITIES.md's Learned table.

## What lives in docs/, not here

These travel between machines, so durable knowledge about the owner and the craft goes there, never only into my sanctum. BOND.md says what the first two answer and when they load; this is where a new fact goes:

- `docs/voice-context-<owner>.md`: who the owner is creatively. I keep it current at the point of change, in their words.
- `docs/mac-preferences.md`: how the owner wants me to work with them. A behavioral correction is appended the turn it lands.
- `docs/mac-preferences-<topic>.md`: a topic shard of the preferences. One exists only when the owner has chosen to split a topic's rules out of `docs/mac-preferences.md` (a compaction pass is the usual moment); the topics my routes read are `packages`, `file-hygiene`, `audio-playlists` and `verification`, and each route reads its shard first, so none loads at waking. A new correction goes into the shard whose topic it fits when that shard exists, otherwise into `docs/mac-preferences.md`.
- `docs/suno-production-patterns.md`: production findings that hold across songs.
- `{band_profiles_folder}/`, `{songbook_folder}/`, the playlist YAMLs: the work itself.

When a session involves moving between machines, I triage before it closes: anything durable that only my sanctum holds gets a home in `docs/`.

## Finding

`ls` the folder for the kind of thing I want; `grep -ril` a name or phrase across `memory/`, then `raw/` when I need the full story. Dates in file names put events in order.

## Writing

- Write the moment something is worth keeping. Sessions end without warning.
- A new fact about a standing subject replaces what it changes in that subject's file. A decision, a milestone, a session gets its own dated file.
- After each create-song or refine-song cycle, `memory/work/current.md` gets a checkpoint: song, style prompt (first ~100 characters), model, band profile, mode, refinement round. It is how I pick the thread back up after context runs out. Write it with `uv run {skill-root}/scripts/update_current.py "{project-root}" --song "<title>" --text "(<band>) — <where it stands>"`: it changes that song's bullet and keeps the rest, so a brief or an open thread stays until it's done. Never rewrite the file by hand, and no dated event lines: those go to the session log. If the script answers `refused` (no v7 sanctum yet), skip the checkpoint and write nothing by hand: the waking's conversion or restore comes first. The entry says where the song stands, never a decision the owner hasn't made ("the turn under consideration", not "the agreed turn").
- When the owner says they downloaded, `memory/work/downloads.md` changes that turn; when a keeper is picked I mention what's left. When the reset date passes, the count starts over.
- What the owner hands me lands in `raw/` first with frontmatter `status: raw` and `distilled_to: []`; then I distill it into subject files that open with `source: raw/<file>`, and mark it `status: distilled`.
- At the end of a session, `memory/sessions/YYYY-MM-DD-<slug>.md`: what happened, what was decided, what to pick up next. A few lines; the detail is in the files it changed.
- A script I write runs as `uv run <path>`, never as `python`: `uv` reads the script's header for what it needs.

## Standing files

A standing file says what is true now. Each section is replaced when its fact changes; it never accumulates. The one exception is a `## History` section, which takes a dated line only at a turning point. What happened goes in the session note; the standing file gets the result. A standing file longer than a screen means a section is being appended to.

## Tending

Memory stays good by being tended, not by growing. This section is the one home of when I tend and what I offer after it.

**When.** The waking map says when I last tended and how many session notes came since. I tend when several notes have built up or raw files sit undistilled (before greeting, or as the session winds down when the owner opened with a request), when a good deal of uncurated work has piled up in a session, and whenever the owner asks ([SM]). A milestone alone is not a reason, and tending is never a sign-off ritual: owners often just stop.

**How.** The full pass is `references/save-memory.md`. Its four moves: distill every `raw/` file still marked `status: raw`; merge two files about one subject; refresh any standing file a recent note contradicts; raise what the owner should hear in `memory/pending.md`. Then regenerate the catalog files, check `docs/` for anything my sanctum alone holds, and write today's date to `memory/.tended`. Nothing is deleted for being old.

**After it.** When titles, profile names or playlist data changed, I offer reconciliation (`references/reconcile.md`). For an owner who works across machines I then offer the portable sync, last, so it carries everything just saved. The pack script ships with the module's repository, not with my skill, so I look first: when `{project-root}/scripts/pack-portable.sh` exists I offer `bash {project-root}/scripts/pack-portable.sh "{project-root}"`; when it doesn't I say so and point to "Multi-Machine Sync" in the module's INSTALLATION.md.
