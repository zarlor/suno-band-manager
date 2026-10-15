# Playlist Sequencing Methodology

How to judge a playlist and recommend an order: the variables, the seam-by-seam transition discipline, the rules that bind any placement (spacing, cause and effect, locked arcs), the review gates and the thematic read. The whole-album shape is in `references/album-craft.md`, for full sequences. `{docs}` is the folder holding `{band_profiles_folder}` (default `{project-root}/docs`); the playlist is `{docs}/{band-slug}-playlist.yaml`. The script JSON these sections read is documented in `uv run {skill-root}/scripts/playlist-sequencing-data.py --help`; it is the input to these decisions and never makes them. One song's deeper audio read (sections, vocal placement, beat grid) belongs to the `suno-feedback-elicitor` skill: invoke it.

**Contents:** Scaling the Job · Variables · Transition Discipline · Similar Songs Need Distance · Cause and Effect at the Seam · Locked Arcs · Process for Reviewing a Playlist · Thematic Verification

## Scaling the Job

Skip the album-craft layer when reordering one or two adjacent tracks with no wider impact, when the user's sequence is fixed and they want only seam feedback, or when the playlist has four or fewer tracks (no front, peak and close to balance). The gates, the seam rules and the thematic read still apply to every job.

## Variables

Weigh every variable for each track and seam. Earlier ones tend to dominate in a conflict, but a perfect score on one (a compatible key) never overrides a poor score on another (a tempo jump).

- **Felt BPM** governs the listening experience, and measured tempo misreads it, more often with librosa than Beat This!. The usual misreads: speed metal reads half-time, doom and sludge read double-time, power ballads overcount, slow contemplative songs (felt 70-80) read about 150-160. With librosa tempo, a `librosa_prior_relation` of `double` (shown as `117.5 / 60.1 (halftime?)`) means both readings are candidates and neither is the felt tempo. `felt_bpm_check` marks the tracks to confirm by ear until a `felt_bpm:` is recorded.
- **Keys:** overall, entry (first 30 s) and exit (last 30 s), each with its Camelot code. They can differ.
- **Energy:** level 1-10, intro % and outro % (sparse or explosive opening, fade or hard ending), and dynamic character (FLAT to HIGHLY-DYNAMIC). Two mid-tempo songs feel nothing alike when one is FLAT and the other HIGHLY-DYNAMIC.
- **Loudness** (BS.1770): integrated LUFS, range, by thirds, and entry/exit loudness and tempo (first and last 15 s and 30 s), which show how a track actually begins and ends where an average hides it, say a quiet vocal ending into a band swell.
- **Not measurable from audio:** mood (the songbook's Listening Notes, an outside listening read, or the user), sonic palette and arrangement density, and the song's place in the album's story.

## Transition Discipline

The seam between two tracks is what the listener experiences; per-track numbers only feed it.

**Exit key into entry key.** A track that is overall in C minor but ends in G minor hands off in G minor. The script's `transition_to_next` already compares exit to entry.

**Key relation.** The script names each seam's `key_relation` on the Camelot wheel (number = position, A = minor, B = major): **same** (seamless, monotonous if overused), **relative** (8A→8B, a mood shift on one center: minor to major lifts, major to minor darkens), **adjacent** (the common professional move), **two-step** (an energy boost, use sparingly), **distant** (risks a clash, for intentional contrast), and **parallel** (A minor → A major): far apart on the wheel, but the ear hears one tonic, so name it as a deliberate emotional pivot, not a clash. `key_compat` (compatible / near / distant) grades the same thing in three steps. Both describe the key relationship only; neither is the seam's verdict.

**Camelot is a key-relationship tool, not a measure of how smooth a seam is.** It cannot see:
- **Tempo gaps.** A compatible key move with a 20 BPM jump sounds worse than a small key clash at the same tempo. Tempo usually outranks key.
- **Genre and style register.** Power-pop crashing into a slow heavy track or a piano lament sounds abrupt whatever the keys.
- **Energy and dynamic level.** A sustained-high banger next to sustained-low melancholy won't blend, even with aligned keys.
- **Loudness.** See the loudness step below.
- **Production aesthetic.** A warm analog mix next to a modern compressed one is a seam of its own.

So describe the **listening experience** (smooth / fluid / abrupt / jarring) as the primary criterion, and name tempo, register and energy gaps beside the key relation when they're significant. A key-compatible seam with a 70+ BPM gap is "key-compatible but tempo-jarring," not "the strongest option." Camelot is reliable when the songs also share a tempo pocket and a genre; it breaks down as those diverge.

*Example of the failure:* a 152 BPM power-pop track had a slot open where three seams in a row were key-compatible, next to two heavy tracks felt at about 78. The writer rejected it by ear as abrupt. A slot with rougher keys but neighbors closer in tempo and energy sounded less jarring and won. What it shows: the "Camelot trade-off" framing was wrong. The reason was that the song sounded less abrupt there, and the proposal should say so.

**Tempo.** Under 3% change is smooth, 3-6% noticeable, over 6% needs intentional contrast. Verify felt BPM before claiming tempo continuity: three tracks at "136 measured" may include one felt at 68. A seam the script marks `pulse_pair` (about 2:1) shares a pulse grid and can mix coherently, but treat it as a deliberate breath in or out, not a smooth handoff.

**Energy and loudness.** A 70% outro into a 15% intro is a dramatic drop: right at an act break, jarring mid-act. Intro and outro % are relative to each track's own peak, so two tracks can both "end at 70%" and still land 8 LU apart; `loudness_step_lu` (next entry minus this exit, over the first and last 15 s) measures that: under 3 LU smooth, 3-6 noticeable, 6 or more a big jump (a reference catalog's median seam is about 2.5 LU). Weigh a big step with the arc, as you would an energy drop. A large jump up into a loud opener is the one listeners most often hear as "the next song is too loud."

**Genre outliers.** A power-pop track on a doom album has no slot that is perfect on key, tempo and genre. Pick where the listening experience is least jarring, and document the trade-off rather than calling it seamless.

**Sonic and thematic flow are independent, and both must work.** No script measures whether two adjacent songs belong together in meaning; that comes from the thematic read below.

## Similar Songs Need Distance

Songs covering similar thematic ground (two about "knowing nothing", two about a parent, two drawing on the same local folklore) are spaced apart so each hits fresh; adjacency blurs them into one long meditation. This is separate from key and palette: two songs can be sonically and harmonically distinct and still cover the same lyrical territory.

## Cause and Effect at the Seam

When one song is the cause of another (an overload and the shutdown it causes, a betrayal and its aftermath), never fix a key or tempo seam by handing the effect straight into its cause. The listener hears the story run backwards, and that thematic jar is worse than the musical one it fixed. The constraint binds the seam only. Apart, the two songs can sit in either order, and seam quality ranks freely among the placements that respect it. Don't stretch it into a rule about global running order.

## Locked Arcs

A locked arc is a run of two or more tracks the writer positioned to read as a unit: a love → loss → grief → healing run, a three-act story, a musical movement that depends on adjacency. The block may move as a unit; the songs inside it keep their order and stay together. Surface the arcs before proposing any reorder. If a reorder needs to break one, stop and ask, because the arc's emotional logic is the writer's call, not yours (headless: decline the break and log it).

Arcs come from the playlist YAML's optional `locked_arcs:`, from the user, or in headless runs from `--locked`. `uv run {skill-root}/scripts/validate-sequence.py {docs}/{band-slug}-playlist.yaml` reports each one as intact, split, or out of order; pass `--locked "A > B"` for arcs the user names that aren't in the YAML yet.

## Process for Reviewing a Playlist

Three gates run in order. The checks between them are independent.

1. **Surface locked arcs**: run `validate-sequence.py` on the current order (with `--locked` for any arc the user named that isn't in the YAML) and state the arcs up front.
2. **Settle felt BPM and read the theme, before drafting any option.**
   - Felt BPM: for each track with `felt_bpm_check`, ask the user when uncertain, and record the answer as `felt_bpm:`.
   - Thematic read: for every song involved (the one being placed and every neighbor in play), read its entry before any thematic claim, per "Thematic Verification" below. Scale the read to the job:
     - A one- or two-track placement: read the handful of entries directly.
     - A catalog-scale pass: delegate the read to a subagent that returns only a compact per-song summary (one or two lines each: the actual theme, any surface-vs-actual inversion, a load-bearing quote in context). Entries read into the parent context compact out before the recommendation forms.
     - No subagents available: use `{docs}/song-thematic-dossier.md` entries where they exist (compact, and cross-band). Otherwise read the entries in batches and write the per-song summary to `theme-summary.md` in the sequencing workspace as you go, so it survives compaction. The read happens either way.
3. **Recommend, then surface trade-offs.** Propose specific moves, naming what each variable says. Every move trades something; call it "trades A-jarring for B-jarring", not "cleaner".

Checks between gates 2 and 3, in any order:
- **Act structure**: narrative acts, their thematic functions, tracks per act.
- **Energy arc** and **key positions** (full sequences): `references/album-craft.md`.
- **Transitions**: each seam on the full stack (key relation, felt tempo, intro/outro %, loudness step, palette, theme). Flag the worst.
- **Clusters**: felt-tempo cousins scattered that could be a deliberate block; thematic cousins adjacent that should be spaced (`runs[]` helps).

The output is an opinionated proposal grounded in the variables, saying what's locked, what's a judgment call, and where the user's ear should break the tie, written in the user's language.

## Thematic Verification (before any placement recommendation)

The trigger is the act of recommending a placement, however the question arrived. Placement math (Camelot distance, BPM delta) never substitutes for the thematic read, and running the math first is no license to treat the theme as color commentary added afterward: a song once got paired with a neighbor on a title-chain association instead of the neighbor's documented theme. Read the theme before drafting any option.

**Before making any thematic claim about a song, read its songbook entry at `{songbook_folder}/{band-slug}/{song-slug}.md`**, or its entry in `{docs}/song-thematic-dossier.md`, which distills the songbook plus the writer's direct quotes across every band. Either will do; read one. A title, its surface imagery or a fragment out of context is not the theme: songs whose surface suggests one register often turn out to be the opposite when read in full.

**Documented examples where surface inference produced inverted reads:**

| Title | What the surface suggests | What the song actually is | Placement consequence |
|---|---|---|---|
| *Harbor Lights* | nostalgic seaside comfort | surveillance — the lights are hunting, not welcoming | pairs with tension, not with warmth |
| *Sunday Driver* | leisurely, contented | a funeral procession; the slow tempo is grief | never a light palate-cleanser slot |
| *Paper Cut* | a minor hurt | signing divorce papers — the small injury is the large one | belongs at an emotional low point, not as filler |
| *The Long Way Home* | a scenic-route journey song | avoidance — circling because home can't be faced | closes nothing; it withholds resolution |
| *Bright Side* — line "I never made the papers" | regret at obscurity | the opposite — relief; anonymity is the bright side | an affirmation track, safe as a closer |
| *Glass Bottom* | fragility, something about to break | clarity — you can finally see what you're floating over | a turn, not a collapse |
| *Signal Fire* | warmth, a beacon, rescue | a warning that arrives too late to act on | raises tension into the next track |

**Why surface inference fails so reliably:** poets don't telegraph. A writer who works in paradox-as-structure, surprising juxtapositions and imagery that resolves only in full context defeats a surface read, and such songs are the norm in a serious catalog. The songbook entry, carrying the lyrics, the writer's stated intent, the production direction and the catalog notes, is the authoritative source.

- Read the full entry of every adjacent song in the recommendation, not a skim, a keyword grep, the title or a cross-reference table.
- For the song being placed, the same: even after many turns of workshopping it, check that the songbook captures the final theme before saying what the song does.
- When a line is evidence for a thematic claim, quote enough around it that its function in the song is clear; a line alone almost always misleads.
- With no time to read the entries properly, there is no time for a placement recommendation: ask for the time, or give the sonic placement only and say the thematic read is pending.
