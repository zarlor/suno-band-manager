# Catalog Verification Discipline — Grep Before Asserting Catalog State

**Never characterize what is or isn't IN the catalog without verifying via grep first.** This applies to claims about genre coverage, subgenre presence, style anchor history, artist-influence usage, voice-clone behavior across songs, and any "this is fresh territory" / "this hasn't been done" / "X is new for [band]" recommendations. The agent's confidence-from-memory is repeatedly wrong; the project files are the authoritative source.

**Recurring failure pattern — multiple documented instances:**

1. **"Piano-led is new territory" failure:** the agent proposed a piano-led direction for a folk-lane band and labelled piano-led as new ground for them. A song already in that band's catalog was anchored on upright-piano balladry. The claim could have been checked in ten seconds with `grep -l "piano" docs/songbook/{band-slug}/*.md`. The user's response was blunt: had the playlist and the actual songs been checked before the claim was made?

2. **"Groove metal is fresh" failure:** the agent proposed groove metal as genuinely fresh territory for a metal-lane band. Three songs in that catalog already carried progressive groove metal as their primary style anchor, a fourth had tried a groove-metal artist reference directly, and the band's base persona was itself built out of groove-metal drum and vocal references — groove metal was not a candidate addition, it was the band's baseline. In the same pass the agent claimed post-metal was fresh (four prior uses, including a wild-card variant) and offered industrial as viable, when industrial had already been tried on another song in that catalog and rejected with a recorded finding — *"industrial fights call-and-response"* — that applied directly, because the proposed song was call-and-response-heavy. Same pattern as the first failure: confidence-from-memory bypassed the verification step.

**Trigger conditions — fire on ALL of these regardless of how the surrounding question is framed:**

- "X is new territory" / "fresh territory" / "unique for [band]" / "hasn't been done" / "X would be the first Y"
- "X is unrepresented" / "X is missing from the catalog" / "X opens new lane"
- "X has been covered" / "X is in the catalog" / "X has been used N times"
- ANY characterization of catalog-state — what genres/subgenres/styles/influences/artists are IN or NOT IN the catalog
- ANY genre-direction recommendation that compares positively or negatively to existing catalog (this is the trigger most-often missed — "what would fit?" creative questions become catalog-state questions the moment the agent says "X hasn't been done")
- ANY claim of uniqueness, novelty, freshness, or non-overlap with existing work
- ANY assertion about what voice clones / band profiles / playlists / songbooks contain or don't contain

**Mechanical pre-check step (NOT optional, NOT discretionary):**

When generating a song-direction candidates list, recommendation, or comparison for any band, verify catalog state from disk BEFORE building the candidates.

**Start from the generated coverage index.** `uv run {skill-root}/scripts/genre-coverage.py` builds `docs/{band-slug}-genre-coverage.md` from the band-profile catalog's curated fields (genre, reference_tracks, style_alternatives, voice use_case, per-song genre_applied), labelled "Reference territory:" lines, and every songbook entry's style prompt verbatim. Reading it catches the artist-label coverage that raw genre-string greps miss: a genre is often already COVERED under an artist name rather than a genre string, so a catalog with no "jangle pop" anywhere may be full of it filed under a named reference. Don't judge staleness from memory: `uv run {skill-root}/scripts/genre-coverage.py "{project-root}" --band {band-slug} --check` exits 1 when the index is stale or missing, and then regenerate it — `uv run {skill-root}/scripts/genre-coverage.py "{project-root}" --band {band-slug} --timestamp "{today's date}"` — before you read it.

**The index is evidence of presence, not proof of absence.** It extracts and doesn't infer, so a direction described in words it doesn't carry can still be missing from it. A hit in the index settles "this has been done", but a miss never settles "this is fresh" on its own. Before any negative claim — "never done", "new territory", "unrepresented" — also run the multi-term grep below. If the script can't run at all, the grep is the whole check.

**Multi-term grep (the backstop before any negative claim).** Multi-term grep, not single-string:

1. **Genre/subgenre names** — both the literal label and adjacent variants (e.g., "groove metal," "groove-metal," "progressive groove," "post-metal," "post-hardcore," "stoner doom," "stoner-doom")
2. **Related artist names from the band's voice file influences** — if the user has documented influences in `docs/voice-context-*.md` or the band profile, grep for those artist names directly across the band's songbook
3. **Characteristic descriptors** — instrumentation, tempo character, production register (e.g., "down-tuned," "polyrhythmic," "mid-tempo crushing," "atmospheric prog," "halftime groove")
4. **Pre-existing-finding searches** — grep for relevant rejected-direction findings in songbook generation logs (e.g. a recorded "industrial fights call-and-response" finding from one song applies to every other call-and-response-heavy song in the catalog)

Build the candidates list FROM the verified gap-analysis, NOT from memory. If grep returns hits, the candidate is NOT fresh — refine to what's actually new (a fusion, a specific subgenre variant, a register-shift) or drop it.

**How to apply:**

- Before claiming any of the trigger phrases above, run grep first.
- Before comparing a proposed direction to "existing" catalog tracks, actually grep what's there. Don't say "doesn't exist in catalog" without confirming via grep.
- Before claiming what voice clones / band profiles / playlists contain, re-read the YAML / playlist files. Don't go from memory.
- **Confidence-from-memory is the signal to verify.** That confidence has been wrong repeatedly. The authoritative source is project files, not the agent's general-knowledge recollection.
- For "is this direction unique?" / "what genres might fit?" / "what hasn't been done?" questions, the FIRST step is checking (and if stale, regenerating) and reading the band's `docs/{band-slug}-genre-coverage.md` index, then the multi-term grep before saying anything is absent. Most of the time something adjacent exists; refine the claim to what's ACTUALLY new.
- **If a pre-existing finding rules out a direction** (e.g. a recorded *"industrial fights call-and-response"* result), that finding APPLIES when proposing the same direction for a song with the same characteristic. Search the catalog for relevant prior-art findings before recommending, not just for genre presence.

**Self-check before asserting:** Have I read the band's current (checked, regenerated if stale) `docs/{band-slug}-genre-coverage.md` index — and, for any claim that something is absent or fresh, grepped the catalog for the genres / artists / descriptors I'm about to characterize? If no, STOP and verify first. If the index or grep returned hits, REBUILD the assertion from the verified state — do not push through with the original framing.
