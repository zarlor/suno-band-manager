# Poem-to-Song Strategies

What Suno does with a poem's shape, and the structures that work around it. Section line ranges live in `section-length-checker.py`.

## Let the Words Set the Length

A short song can be the right song: a 90-second track that lands every line hits harder than three minutes with filler, and short tracks give a playlist contrast. Don't pad for runtime, because Suno fills thin content with looping instrumental and the song turns aimless.

## Short Poem (`estimated_structure: short`, under 16 content lines)

Use one of these in place of Chorus Creation, since new padding lines become instrumental filler:

- **Split delivery:** the first half as Verse 1, an extracted chorus, the second half as Verse 2, the chorus again.
- **Double delivery:** the whole poem twice with different energy (clean first, heavy second) around an extracted chorus: `Verse 1 (full poem, clean)` → `Chorus` → `Verse 2 (full poem, heavy)` → `Final Chorus`. Works when the words change meaning under a different emotional lens.
- **Chorus extraction:** pull the strongest, most repeatable lines into a standalone chorus, so Suno has enough repetition to build a song on.
- **Thesis isolation:** build through the poem, then a solo or instrumental break, then only the thesis line in its own section: `Verse 1` → `Verse 2` → `Guitar Solo` → `Outro (thesis line only)` → `[End]`. For a poem with one line that deserves to land alone.

Name the strategy in the decision log. Keep `[Instrumental Break]` tags out of a short poem's lyrics: the tag asks Suno to noodle, and the song comes back mostly instrumental.

## Poems Without a Chorus (Through-Composed)

A single sustained meditation, or a poem whose power is in its progression, can stay continuous (`Verse 1` → `Verse 2` → `Bridge` → `Verse 3` → `Outro` → `[End]`). Carry the energy changes with descriptor tags and line density, and back the dynamic range in the style prompt. Put a hard `[End]` right after the final delivery: with no chorus to signal the structure repeating, Suno otherwise loops or trails off into instrumental.

## Structural Metaphor (Meter as Meaning)

Odd meter for unstable verses against 4/4 for the resolving chorus is a strong idea for prog and through-composed songs, but Suno moves feel and tempo, not meter: production testing (2026-07, three takes) got the sway and the slower pulse while the subdivision stayed 4/4. Offer it as aspiration only: at most one meter signal (`[Verse 1: 7/8]`), the rest in feel words that land (swung, rigid, accelerating, half-time), and a song whose point still works in 4/4. Style-side meter wording is the `suno-style-prompt-builder` skill's.
