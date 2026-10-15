# Album Craft

The whole-playlist layer for a full sequence or re-sequence: the shape the order makes, above the seam-by-seam transitions. The seam rules, locked arcs, cause and effect, and the thematic read live in `references/playlist-sequencing-methodology.md` and still bind every move made here. Name the shape the album actually has rather than forcing one of these models onto it.

## Energy Arc Models

**Inverted-U (classic album):** Tempo and energy build through the front half, peak mid-album, descend toward the close. Valence/arousal (emotional intensity) often *dips* mid-album, creating a journey shape — the energy is high but the emotional weight gets heavier before lifting.

**W-shape (concert / featured-songs model):** Three peaks at the beginning, middle, and end of the playlist, with complementary songs providing variety in key/tempo/timbre/mood between the peaks. Two valleys between the peaks give the listener room to breathe. The W-shape works well when the playlist has clear "anchor" tracks at all three positions.

**Concert peak-end rule:** The audience remembers the best moment and the final moment most vividly. Open higher-than-average, allow a dip, close higher-than-average. The closer doesn't have to be the loudest track — it has to feel like a *resolution*.

A 6-act narrative structure naturally creates a W-shape if Acts I, IV, and VI hold the peaks; valleys land in Acts II and V. But the shape is descriptive, not prescriptive — if the album's emotional logic produces a different curve (front-double-peak with contemplative descent close, for example), name what it actually is rather than forcing the W.

## Key Positions

The methodology treats positions **1, 4, 7, and 10** as load-bearing. Strongest songs go here. Track 1 sets the tone; track 2 confirms the promise (so 1 → 2 cannot be a misfire); track 4 anchors the front; track 7 carries the listener into the middle; track 10 picks up the second half. The final track provides resolution — separate criterion from "strongest song."

For longer playlists (30+ tracks), the same logic extends: 1 / 4 / 7 / 10 / 13 / ... up to a closer that resolves. The pattern thins out past about position 10 because the listener is now inside the album rather than evaluating it from the outside.

**Streaming-era reality:** Front-loading with engaging material is more critical than ever. The first 3-4 tracks determine whether a listener stays with the album or skips. This doesn't mean the front needs to be the *loudest* — it means it needs to be the most *immediately compelling*.

## Sonic Palette Variety

Avoid placing two songs with similar instrumentation, arrangement density, or timbral character next to each other. The methodology's principle: contrast is essential for maintaining interest.

Specific anti-patterns:
- Two intricate intros back-to-back — the listener loses orientation
- Two acoustic stripped-back tracks adjacent — the album feels like it stalled
- Two power-pop bangers adjacent — the genre register collapses into a single mood
- Two slow contemplative tracks adjacent — unless deliberate ("breath section")

Variety is an active design choice, not a side effect of randomization.

## Tempo Variety

Categorize tracks into up-tempo / mid-tempo / slow buckets (`runs[]` counts them). Avoid placing too many from the same category adjacent. Two slow songs back-to-back loses listeners unless deliberate.

But: **a deliberate slow-tempo block is a real album convention.** Doom albums, ambient stretches, contemplative interludes — three or four felt-tempo-matched tracks in a row can be an immersive zone if the *sonic palette* and *mood* shift across them. The methodology cautions against accidental same-tempo runs, not against intentional ones.

## Same-Key Adjacency

3-4 songs in the same key consecutively gets boring. When you finally shift keys after too many same-key tracks, the change feels more jarring than a varied stretch would have. Limit same-key consecutive runs to 2 unless you have a specific reason to push to 3. The script's `runs[]` lists same-key runs longer than 2 and tempo-bucket runs (slow under 90, mid 90-125, up 125+; felt BPM where recorded). A run is a fact; whether it is deliberate is your call.

## Encore Structure

For album-as-concert-set framing: Act VI (or the final stretch) functions as a planned 3-5 song mini-set at high energy following a "breath-catching break." The break is often a single contemplative track that gives the listener room before the closing run.

**Anatomy of a working encore section:**
- Breath-catcher: low-mid energy, contemplative or stripped-back
- Encore launch: high-energy banger that re-engages the listener
- Encore middle: sustained energy with thematic coherence
- Encore close / resolution: doesn't have to peak louder; needs to *resolve*
- Optional post-encore coda: the singer alone on the empty stage — fade close

If your final stretch lacks this shape (e.g., averages mid-energy throughout with no clear launch), call it what it is: a "contemplative legacy descent" or "extended fade close" — a different valid shape, not a broken encore.
