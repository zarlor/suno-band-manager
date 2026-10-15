# Thematic Discipline — Read the Songbook Before Making Thematic Claims

**Never make a thematic claim about a song based on its title, surface imagery, or fragments-pulled-out-of-context.** Read the full songbook entry at `docs/songbook/{band-slug}/{song-slug}.md` before claiming what a song is about. This applies to placement recommendations, thematic clusters, narrative-arc analysis, and any other context where a song's meaning is being asserted.

**Why:** Poets don't telegraph. Songwriters routinely use paradox-as-structure, surprising juxtapositions, and imagery whose meaning resolves only in full context — so surface inference produces inverted reads at high rates. Illustrative misread patterns, each drawn from the same failure shape:

| Title | What the surface suggests | What the song actually is |
|---|---|---|
| *Harbor Lights* | nostalgic seaside comfort, coming home | surveillance — the lights are searching for the narrator, not welcoming them |
| *Sunday Driver* | leisure, taking it slow, contentment | a funeral procession; the slowness is grief, not ease |
| *Paper Cut* | a trivial hurt, something minor | the signing of divorce papers — the small injury IS the large one |
| *The Long Way Home* | a wandering, scenic-route journey song | avoidance; the narrator is driving in circles because they cannot face what is at home |
| *Bright Side* — line "I never made the papers" | regret at obscurity | the OPPOSITE — relief. Never being newsworthy is the bright side the title names |

The pattern to internalize: the title and the pulled line are the *least* reliable evidence about a song's meaning, and an inverted read is more likely than a vague one.

**Discipline rules:**
- For every song whose theme is being claimed: read the full songbook entry. Don't grep for theme keywords. Don't rely on what the title implies. Don't lean on cross-reference table summaries.
- When pulling a line as evidence for a thematic claim, quote enough surrounding context that the line's actual function is clear. A line in isolation almost always misleads.
- If there isn't time to read the songbooks properly, there isn't time to make the thematic claim. Ask for time, or surface only the analysis that doesn't require thematic verification (e.g., sonic analysis only) and flag that thematic verification is pending.
- This rule applies even when Mac has been workshopping a song across many turns — verify the songbook/WIP captures the actual final theme before asserting what the song does.

The suno-playlist-sequencer skill applies this rule to playlist work (its Thematic Verification step); route sequencing there rather than placing songs by title.

### Agent-summary vs. user-direct-framing distinction

Reading the songbook entry is necessary but not sufficient when the agent wrote the entry. **Songbook entries are the agent's writing — interpretations of conversations + framing decisions made when entries were drafted — NOT the user's direct articulation.** The agent re-reading the agent's own summaries closes the verification loop without catching the agent's original mis-framing.

**Recurring failure case (third-instance pattern):**

The agent proposed playlist placement for a song, citing the thematic content of the songs around it. First pass: shorthand thematic labels pulled from sidecar positional-note summaries (caught — that is the Thematic Discipline rule above). Second pass: read the full songbook entries — but those framings carried the agent's own prior interpretive lean, and the user corrected them:

- **A heavy-lane track** — agent's framing: "violence confession." User's actual framing: the narrator is a *mute component* in something violent; the song is about complicity, not confession. "Confession-style" was the agent's lean.
- **A mid-tempo track** — agent's framing, pulled from its own songbook summary: "a wistful memory piece." User's actual framing: it is an argument the narrator is *losing in real time* — present tense, not retrospect. "Memory piece" was the agent's lean.

Both songbook entries were written by the agent. Re-reading the songbooks did not catch the mis-framing, because the songbooks WERE the mis-framing — interpretive lean encoded into the canonical record.

**Hierarchy of authority for thematic claims:**

1. **User's direct framing** when articulated in conversation (current or recent) — AUTHORITATIVE
2. **User's direct quotes** preserved in songbook entries (in user's own words, marked as quotes with date) — AUTHORITATIVE
3. **Agent's summary descriptors** in songbook entries (the agent's interpretive synthesis from prior conversations) — SECONDARY; treat as agent-interpretation, NOT user-articulation; verify with user when the framing matters

**Trigger conditions for elevated verification:**

The Thematic Discipline rule (read the full songbook entry) applies for ANY thematic claim. The agent-summary-vs-user-direct-framing distinction applies SPECIFICALLY when:

- **Placement recommendations** comparing thematic content of multiple songs — user's direct framing of each song matters
- **Thematic-cluster claims** (e.g., grouping songs by shared mood, register, or thematic territory) — verify each component song's framing with user when load-bearing
- **"X is about Y" claims** about songs the agent wrote summary for — flag as agent-interpretation, not user-articulation
- **Cross-band thematic comparisons** — verify each band's version's framing with user
- **Any thematic claim load-bearing for a placement decision, recommendation, or cluster framing** — verify before asserting

**Mechanical step (NOT optional, NOT discretionary):**

Before making any thematic claim that's load-bearing for a recommendation:

1. Check if user has articulated the framing in current or recent conversation. If yes, use that.
2. If not, check if songbook entry has DIRECT QUOTES from user (in user's words). If yes, use those quotes.
3. If neither — agent's summary descriptors are the only source. **Flag explicitly** as "per the songbook summary (the agent's interpretation)" rather than asserting the framing as fact. When the framing is load-bearing for the recommendation, prefer to ASK the user to confirm the framing rather than committing to a recommendation built on agent-interpretation alone.

**When user corrects a framing mid-session:**

- User's framing wins immediately
- Update the songbook entry to reflect user's framing (in user's words where possible, with note: "Per [user] [date]: '...' [user's framing in own words]")
- Note the divergence in session chronology so the recurring pattern can be tracked
- Don't re-assert the original agent-framing in subsequent claims about that song

**Self-check before placement / cluster / thematic-comparison claims:**

- Have I grepped catalog state? (Catalog Verification Discipline)
- Have I read the full songbook entries? (Thematic Discipline as written above)
- **ARE THE SONGBOOK FRAMINGS USER-VERIFIED, or are they the agent's interpretations?** If agent's interpretations, flag explicitly and verify with user when the framing is load-bearing.

If any check fails, STOP. Re-verify before asserting. Do not push through.
