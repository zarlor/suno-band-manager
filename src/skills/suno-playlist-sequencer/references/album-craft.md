# Album Craft

The whole-playlist layer for a full sequence or re-sequence: the shape the order makes, above the seam-by-seam transitions. The seam rules, locked arcs, cause and effect and the thematic read in `references/playlist-sequencing-methodology.md` still bind every move made here. `{docs}` is the folder holding `{band_profiles_folder}` (default `{project-root}/docs`).

## Arc shape

Name the shape the album actually has (an inverted U, a W of three peaks with valleys to breathe, a front-loaded double peak with a contemplative descent) rather than forcing one model onto it. A shape you describe is a finding; a shape you impose moves songs for the model's sake. The closer has to resolve, which is a separate test from being the strongest or loudest song.

For an album-as-set, a final stretch usually reads as a breath-catcher followed by a closing run that resolves. If the stretch lacks that launch (mid-energy throughout), call it what it is, say a "contemplative descent" or an "extended fade close", rather than a broken encore.

## Key positions

Positions **1, 4, 7 and 10** are load-bearing: put the strongest songs there. Track 2 confirms the promise track 1 made, so 1 → 2 can't misfire. Past 10 the pattern extends (13, 16, ...) but thins, because the listener is inside the album by then rather than judging it. The first three or four tracks decide whether a streaming listener stays, so the front needs to be the most immediately compelling, not the loudest.

## Runs and variety

The script's `runs[]` lists same-key runs longer than two and tempo-bucket runs (slow under 90, mid 90-125, up 125+, felt BPM where recorded). A run is a fact; whether it is deliberate is your call.

- **Same key:** keep consecutive runs to two, three with a stated reason. A long same-key run makes the eventual key change land harder than a varied stretch would.
- **Tempo:** a deliberate slow block of three or four felt-tempo-matched tracks is a real album convention (doom, ambient, a contemplative interlude) when the palette and mood shift across it. Flag accidental runs, not intentional ones.
- **Palette:** adjacent songs with the same instrumentation, density or intro character blur together; contrast is a choice, not a side effect.

## Catalog pass

When energy shape informs the arc, run `uv run {skill-root}/scripts/batch-full-analysis.py --audio-dir {docs}/audio/{band-slug}` for energy shifts, section boundaries and dynamic character. A `partial` status lists `failed[]`; name them.

## Publishing as a Suno album

Suno's Albums (2026-10-05, OFFICIAL) can publish a sequence on the platform: own songs only, LP or EP is just a label, and track order stays editable afterwards. **Publishing an album publishes every unpublished song in it at once**, and the publish screen says this can't be undone (VENDOR). So the sequence and the track list are settled here first; tell the user which tracks are still private before they publish, since publishing makes them public.
