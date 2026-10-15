# Catalog Verification Discipline — Grep Before Asserting Catalog State — the incident

**Recurring failure pattern — multiple documented instances:**

1. **"Piano-led is new territory" failure:** the agent proposed a piano-led direction for a folk-lane band and labelled piano-led as new ground for them. A song already in that band's catalog was anchored on upright-piano balladry. The claim could have been checked in ten seconds with `grep -l "piano" docs/songbook/{band-slug}/*.md`. The user's response was blunt: had the playlist and the actual songs been checked before the claim was made?

2. **"Groove metal is fresh" failure:** the agent proposed groove metal as genuinely fresh territory for a metal-lane band. Three songs in that catalog already carried progressive groove metal as their primary style anchor, a fourth had tried a groove-metal artist reference directly, and the band's base persona was itself built out of groove-metal drum and vocal references — groove metal was not a candidate addition, it was the band's baseline. In the same pass the agent claimed post-metal was fresh (four prior uses, including a wild-card variant) and offered industrial as viable, when industrial had already been tried on another song in that catalog and rejected with a recorded finding — *"industrial fights call-and-response"* — that applied directly, because the proposed song was call-and-response-heavy. Same pattern as the first failure: confidence-from-memory bypassed the verification step.

The coverage index exists because raw genre-string greps missed artist-label coverage: a catalog with no "jangle pop" anywhere may be full of it, filed under a named reference.
