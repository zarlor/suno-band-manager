# Playlist Sequencing Methodology

How to evaluate a playlist and recommend an order: the per-track variables, the seam-by-seam transition discipline, the rules that bind any placement (spacing, cause and effect, locked arcs), the review gates, and the thematic read. The whole-album shape (energy arcs, key positions, variety, encore) is in `references/album-craft.md`, for full sequences. The script JSON these sections read is documented in `uv run {skill-root}/scripts/playlist-sequencing-data.py --help`; it is the input to these decisions and never makes them.

**Contents:** Scaling the Job · Per-Track Variables · Transition Discipline · Similar Songs Need Distance · Cause and Effect at the Seam · Locked Arcs · What the Methodology Doesn't Capture · Process for Reviewing a Playlist · Thematic Verification

## Scaling the Job

Skip the arc models (`references/album-craft.md`) when:
- Reordering 1-2 adjacent tracks with no upstream/downstream impact
- The user has a fixed sequence and wants only sonic-transition feedback within it
- The playlist has four or fewer tracks. There is no front, peak, and close to balance, so surface any locked pair and reason about the few seams directly.

The gates, the seam rules and the thematic read still apply to every job.

## Per-Track Variables

For each track in the playlist, gather and reason about all ten of these. Earlier variables tend to dominate when conflicts arise — but every variable matters and a "perfect score" on one (e.g., Camelot) doesn't override a poor score on another (e.g., tempo).

1. **BPM** (measured) — the script's tempo: Beat This! when the PyTorch audio tools are on, librosa otherwise (the report says which)
2. **Felt BPM** (human-verified) — the *perceived* tempo, often half or double the measured value (more often with librosa than Beat This!). **Felt BPM is what governs listening experience**, so verify it by ear before trusting raw numbers. The usual misreads: speed metal reads half-time, doom and sludge read double-time, power ballads overcount, and slow contemplative songs (felt 70-80) read about 150-160. With librosa tempo, each track also carries a second reading started from a slow tempo (`bpm_librosa_slow_prior`) and how it relates to the default (`librosa_prior_relation`). A `double` (shown as `117.5 / 60.1 (halftime?)`) is a likely halftime ambiguity; both numbers are candidates and neither is the felt tempo. The script flags tracks in the danger ranges, and tracks whose two librosa readings are a `double`, with `felt_bpm_check` until a `felt_bpm:` is recorded. A run's `tempo_source_note` says when Beat This! was asked for but librosa read the tempo, and why.
3. **Overall key + Camelot code** — the dominant key center
4. **Entry key + Camelot code** (first 30 sec) — the key the track *opens* in. May differ from overall.
5. **Exit key + Camelot code** (last 30 sec) — the key the track *ends* in. May differ from overall and from entry.
6. **Energy level** (1-10 scale) — average loudness/intensity. Useful for identifying peaks and valleys.
7. **Intro energy %** — sparse vs. explosive opening. Critical for transition-from-previous-track evaluation.
8. **Outro energy %** — fade vs. hard ending. Critical for transition-into-next-track evaluation.
9. **Loudness** (ITU-R BS.1770) — integrated LUFS, loudness range (LRA), and loudness by thirds. The **seam step** (next track's entry loudness minus this track's exit loudness: the first and last 15 s, silence trimmed, in LU) catches volume jumps that Camelot and BPM can't see. Entry/exit loudness and **entry/exit tempo** (first and last 30 s) show how a track actually begins and ends, which an average or a last-third reading can hide — e.g. a quiet vocal ending followed by a band swell. Reference catalog: median seam about 2.5 LU; smooth < 3, noticeable < 6, big jump ≥ 6.
10. **Dynamic character** — FLAT / MODERATE / DYNAMIC / HIGHLY-DYNAMIC. A "mid-tempo" song with HIGHLY-DYNAMIC character feels very different from a "mid-tempo" song with FLAT character — the listener's experience hinges on this, not just on BPM.

Plus three contextual variables that aren't measurable from audio alone:

11. **Mood/feel** — captured from Listening Notes in the songbook entry, Gemini blind analysis, or the user's articulation.
12. **Sonic palette / arrangement density** — instrumentation profile (acoustic vs. dense metal, brass-led vs. guitar-led, etc.).
13. **Lyrical narrative position** — what the song "means" in the album's story; what came before, what's coming next.

## Transition Discipline

The transition between two adjacent tracks is the actual moment the listener experiences. Per-track variables exist; transitions are *the experience*.

**Exit key matters more than overall key.** A track that's "overall in C minor" but ends in G minor will transition into the next track via G minor, not C minor. Use exit-Camelot of track N → entry-Camelot of track N+1 as the actual transition assessment. The script's `transition_to_next` field already does this.

**Camelot moves.** The wheel puts the 24 keys on a clock: number = position, A = minor, B = major. The script reports each seam's `key_relation`:
- **same** (8A→8A): seamless, but monotonous if overused.
- **relative** (8A→8B): a mood shift on the same harmonic center. Minor to major lifts; major to minor darkens.
- **adjacent** (8A→7A or 9A): the most common professional move; one scale note changes.
- **two-step** (8A→10A): an energy boost, more noticeable. Use it sparingly.
- **distant**: risks an audible clash. Use it for intentional contrast.
- **parallel** (A minor→A major): same tonic, other mode. The wheel puts these far apart, but the ear hears one harmonic center, a deliberate emotional pivot. Name it as a pivot, not as a clash.

`key_compat` (compatible / near / distant) grades the same thing in three steps. Both fields describe the key relationship only. Neither is the seam's verdict.

**Camelot is a key-relationship tool, not a measure of how smooth a seam is.** It cannot see:
- **Tempo gaps.** A compatible key move with a 20 BPM jump sounds worse than a small key clash at the same tempo. Tempo usually outranks key.
- **Genre and style register.** Power-pop crashing into a slow heavy track or a piano lament sounds abrupt whatever the keys.
- **Energy and dynamic level.** A sustained-high banger next to sustained-low melancholy won't blend, even with aligned keys.
- **Loudness.** See the loudness step below.
- **Production aesthetic.** A warm analog mix next to a modern compressed one is a seam of its own.

So describe the **listening experience** (smooth / fluid / abrupt / jarring) as the primary criterion, and name tempo, register, and energy gaps alongside the key relation when they're significant. A key-compatible seam with a 70+ BPM gap is "key-compatible but tempo-jarring," not "the strongest option." Camelot is reliable when the songs also share a tempo pocket and a genre; it breaks down as those diverge.

*Example of the failure:* a 152 BPM power-pop track had a slot open where three seams in a row were key-compatible, next to two heavy tracks felt at about 78. The writer rejected it by ear as abrupt. A slot with rougher keys but neighbors closer in tempo and energy sounded less jarring and won. What it shows: the "Camelot trade-off" framing was wrong. The reason was that the song sounded less abrupt there, and the proposal should say so.

**BPM transition tolerance:** <3% smooth, 3-6% noticeable, >6% requires intentional contrast. Halftime/double-time pairs (e.g., felt 70 and felt 140) share a pulse grid and can mix coherently even though the felt-tempo difference is dramatic — but treat this as a *deliberate* breath-in / breath-out move, not a "smooth" transition.

**Intro/outro % bridges the dynamic side of the transition.** A track ending at 70% energy into a track starting at 15% creates a dramatic drop — fine if it's intentional (act break), jarring if it's mid-act. The 15% intro after a high outro reads as a hush or a reset; the listener's ear interprets the gap.

**The loudness step is the seam's volume in absolute terms.** Intro/outro % is relative to each track's own peak, so two tracks can both "end at 70%" and still land 8 LU apart at the seam. The script's `loudness_step_lu` (next track's entry loudness minus this track's exit loudness, over the first and last 15 s) measures that directly: < 3 LU smooth, 3–6 LU noticeable, ≥ 6 LU a big jump. A big step reads the same way as a dramatic energy drop — deliberate at an act break or a hush-then-hit, a volume problem mid-act — so weigh it with the arc, not against it. A large jump *up* into a loud opener is the one listeners most often hear as "the next song is too loud."

## Similar Songs Need Distance

Tracks that cover similar **thematic** ground (e.g., two songs about "knowing nothing," two songs about a parent, two songs drawing on the same local folklore) should be separated in the playlist so each hits fresh. Adjacency blurs them into one long meditation; spacing lets each song carry its own weight.

This is distinct from the same-key rule and the sonic-palette rule — a track can be sonically and harmonically distinct from its neighbor but cover the same lyrical territory.

## Cause and Effect at the Seam

When one song is the cause of another (an overload and the shutdown it causes, a betrayal and its aftermath), never fix a key or tempo seam by handing the effect straight into its cause. The listener hears the story run backwards, and that thematic jar is worse than the musical one it fixed. The constraint binds the seam only. Apart, the two songs can sit in either order, and seam quality ranks freely among the placements that respect it. Don't stretch it into a rule about global running order.

## Locked Arcs

A locked arc is a run of two or more tracks the writer positioned to read as a unit: a love → loss → grief → healing run, a three-act story, a musical movement that depends on adjacency. The block may move as a unit; the songs inside it never reorder and never split. Surface the arcs before proposing any reorder. If a reorder needs to break one, stop and ask, because the arc's emotional logic is the writer's call, not yours (headless: decline the break and log it).

Arcs come from the playlist YAML's optional `locked_arcs:`, from the user, or in headless runs from `--locked`. `uv run {skill-root}/scripts/validate-sequence.py {docs}/{band-slug}-playlist.yaml` reports each one as intact, split, or out of order; pass `--locked "A > B"` for arcs the user names that aren't in the YAML yet.

## What the Methodology Doesn't Capture

**Listening experience is the ultimate arbiter.** The variables feed it; none of them replaces it (see "Transition Discipline").

**Felt-tempo lock vs. raw-BPM lock.** Three tracks at "136 measured" don't necessarily lock at felt-136 — one of them may be felt-68 with halftime detection. Verify felt BPM before claiming tempo continuity across tracks. A seam the script marks `pulse_pair` (about 2:1) shares a pulse grid; treat it as a deliberate breath, not a smooth handoff.

**Genre-outlier placement.** A power-pop track in a doom-metal album won't have a Camelot-AND-tempo-AND-genre-perfect placement anywhere. Pick where the listening experience is *least jarring*, accept that no slot is ideal, and document the trade-off rather than pretending it's seamless.

**The narrative dimension is non-data.** No script measures whether two adjacent tracks are thematically coherent. That's the user's call (or the orchestrating agent's judgment based on lyrical content + writer voice context). Don't treat the data analysis as sufficient — sonic flow and thematic flow are independent and both must work.

## Process for Reviewing a Playlist

Three gates run in order. The checks between them are independent.

1. **Surface locked arcs** — what cannot move? Run `uv run {skill-root}/scripts/validate-sequence.py` on the current order (with `--locked` for any arc the user named that isn't in the YAML) and state the arcs up front.
2. **Settle felt BPM and read the theme, before drafting any option.**
   - Felt BPM: for each track with `felt_bpm_check`, ask the user when uncertain, and record the answer as `felt_bpm:`.
   - Thematic read: for every song involved (the one being placed and every neighbor in play), read its entry before any thematic claim. See "Thematic Verification" below. Scale the read to the job:
     - A 1-2-track placement: read the handful of entries directly.
     - A catalog-scale pass: delegate the read to a subagent that returns only a compact per-song summary (one or two lines each: the actual theme, any surface-vs-actual inversion, a load-bearing quote in context). Don't read every entry into the parent context, where they compact out before the recommendation forms.
     - No subagents available: use `{docs}/song-thematic-dossier.md` entries where they exist (compact, and cross-band). Otherwise read the entries in batches and write the per-song summary to `theme-summary.md` in the sequencing workspace as you go, so it survives compaction. The read is never skipped for lack of a subagent.
3. **Recommend, then surface trade-offs.** Propose specific moves with named justifications across several variables. Don't just say "swap X and Y" without naming what each variable says. Every move trades something; don't call it "cleaner" when it "trades A-jarring for B-jarring."

Checks between gates 2 and 3, in any order:
- **Act structure** — narrative acts, their thematic functions, tracks per act.
- **Energy arc** and **key positions** (full sequences) — `references/album-craft.md`.
- **Transitions** — each seam on the full variable stack (key relation, felt tempo, intro/outro %, loudness step, sonic palette, theme). Flag the worst.
- **Clusters** — felt-tempo cousins scattered that could be a deliberate block; thematic cousins adjacent that should be spaced (`runs[]` helps).

The output isn't a metrics dump — it's an opinionated proposal grounded in the variables, with explicit acknowledgment of what's locked, what's a judgment call, and where the user's ear should be the tiebreaker. Write the proposal narrative, and any persisted companion/proposal document, in the user's language.

## Thematic Verification — MANDATORY before any placement recommendation

The trigger is the act of recommending a placement, however the question arrived. Placement math (Camelot distance, BPM delta) never substitutes for the thematic read, and running the math first is no license to treat the theme as color commentary added afterward: a song once got paired with a neighbor on a title-chain association instead of the neighbor's documented theme. Read the theme before drafting any option.

**Before making any thematic claim about a song in a placement recommendation, read the song's songbook entry at `{songbook_folder}/{band-slug}/{song-slug}.md`**, or its entry in the consolidated `{docs}/song-thematic-dossier.md`, which distills the songbook plus the writer's direct quotes across every band in the project. Either is acceptable, but read one of them. Don't infer a song's theme from its title, its surface imagery, or fragments pulled out of context: songs whose surface suggests one register often turn out to be the opposite when read in full.

**Documented examples where surface inference produced inverted reads:**

| Title | What the surface suggests | What the song actually is | Placement consequence |
|---|---|---|---|
| *Harbor Lights* | nostalgic seaside comfort | surveillance — the lights are hunting, not welcoming | pairs with tension, not with warmth |
| *Sunday Driver* | leisurely, contented | a funeral procession; the slow tempo is grief | never a light palate-cleanser slot |
| *Paper Cut* | a minor hurt | signing divorce papers — the small injury IS the large one | belongs at an emotional low point, not as filler |
| *The Long Way Home* | a scenic-route journey song | avoidance — circling because home can't be faced | closes nothing; it withholds resolution |
| *Bright Side* — line "I never made the papers" | regret at obscurity | the OPPOSITE — relief; anonymity is the bright side | an affirmation track, safe as a closer |
| *Glass Bottom* | fragility, something about to break | clarity — you can finally see what you're floating over | a turn, not a collapse |
| *Signal Fire* | warmth, a beacon, rescue | a warning that arrives too late to act on | raises tension into the next track |

**Why surface inference fails so reliably:** poets don't telegraph. Any writer who works in paradox-as-structure, surprising juxtapositions, and imagery that resolves only in full context defeats a surface read — and songs like these are the norm in a serious catalog, not the exception. A title or a line fragment is a bad summary of what a song does. The songbook entry — which carries the lyrics, the writer's stated intent, the production direction, and the catalog notes — is the authoritative source.

**Thematic-verification discipline:**

- For every adjacent song in a placement recommendation: read the full songbook entry. Don't skim. Don't grep for theme keywords. Don't rely on the title or what's in the cross-reference table.
- For the song being placed: same rule. Even if you've been workshopping it across many turns, verify the WIP/songbook captures the actual final theme before claiming what the song does.
- When pulling a line as evidence for a thematic claim, quote enough surrounding context that the line's actual function in the song is clear. A line in isolation almost always misleads.
- If you don't have time to read the songbooks properly, you don't have time to make a placement recommendation. Ask the user for time, or surface placements with sonic analysis only and flag that thematic verification is pending.

## Where Things Live

- `{docs}` is the folder holding `{band_profiles_folder}` (default `{project-root}/docs`); the playlist is `{docs}/{band-slug}-playlist.yaml`.
- The sequencing JSON archive (the re-eval baseline) and the Markdown companion: their paths come from the playlist's `album:`, so read them from the run's `artifacts` block.
- One song's deeper audio read (sections, vocal placement, beat grid): invoke the `suno-feedback-elicitor` skill.
- The playlist schema keys this skill reads and the audio-folder layout: `references/playlist-input.md`.
