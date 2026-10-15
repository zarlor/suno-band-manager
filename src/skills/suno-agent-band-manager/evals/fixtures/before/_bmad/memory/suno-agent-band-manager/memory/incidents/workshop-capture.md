# Workshop Capture Discipline — Verbatim Material to Durable File Before Discussion

**Workshop output that lives only in conversation memory does not survive.** Any time creative content is produced or shared during workshop — the agent's own lyric swings, external-agent swings the user pastes (Gemini, ChatGPT, etc.), the user's own writing they share for incorporation, structural sketches, image fragments — that verbatim text MUST land in the relevant WIP file before the agent moves into discussion of it. **Capture-then-discuss, not discuss-then-maybe-capture.**

This rule extends and tightens the in-flight workshop checkpoint discipline. The earlier framing assumed the agent's own output was "protected by Claude Code session logs as a fallback" — that assumption was wrong (see fourth-instance failure below). Session transcripts are per-machine, not in the portable manifest, and not in version control. **The WIP file is the only durable record. Treat it that way.**

**Recurring failure pattern — fourth-instance discipline failure:**

In a workshop session on one machine, the agent drafted six lyric swings of its own and processed a seventh that the user pasted in from an external LLM. The workshop produced no winning draft — all seven were rejected for mechanism and craft errors. At session close, the agent wrote a "swings tried and rejected" section into the WIP that captured each swing as a one-line meta-description (e.g. *"image-driven attempt — architectural imagery in the verses — multiple errors compounded"*) instead of the verbatim lyric content.

When the user reopened the workshop on a second machine after a sync, the gap surfaced: the WIP held labels pointing at content that existed only in the first machine's per-machine session transcript. The externally-pasted swing survived only because the user still had it in the other tool's history. The agent's own six survived only because the user later asked the agent to dig them out of that machine's transcript. **Both recoveries were possible but fragile** — they depended on the user remembering the transcript existed as a recovery path, and on that file still being intact. Neither is guaranteed across time, machines, or storage events. The user's reaction was unambiguous: the material had not been saved, and an apology did not restore it.

**The corrected understanding: session transcripts are NOT a reliable fallback for either external-agent OR agent-own creative output.** They're per-machine, they don't travel with the portable sync, they're not under version control, and they can be lost to disk events. The WIP file is the durable record; if the WIP has only meta-summaries, the material is one machine-handoff or context-loss away from being permanently lost — same failure mode whether the swing came from the agent, an external LLM, or the user's own writing in another tool.

**Trigger conditions — fire on ALL of these:**

- The agent drafts a lyric swing, structural sketch, image fragment, or any verbatim creative content inline in a response (regardless of whether it's likely to be accepted or rejected)
- User pastes a block of lyric/prose content originating outside the current conversation (Gemini, ChatGPT, another LLM, their own writing in another tool, an old draft they're pulling forward)
- User shares an image of a structure, lyric, or fragment they want incorporated
- User dictates a swing they want preserved
- User describes a workshop swing they did elsewhere and asks to fold it in
- ANY external-agent creative output the user references for the workshop, even if "just to show direction"

**Mechanical step (NOT optional, NOT discretionary):**

Before responding substantively with — or in reaction to — verbatim creative material:

1. Identify the relevant WIP file (`docs/wip-{title}-fragments.md` or songbook entry being workshopped). If none exists, create it.
2. Append the verbatim text inside a code block or quote, with attribution and date (e.g. *"Swing 4 — anchor X, [agent] drafted YYYY-MM-DD:"*, *"external-LLM swing YYYY-MM-DD:"*, or *"user's draft from notebook:"*).
3. Note framing context — what prompted the swing, what critique was offered after, what was the workshop iteration this came from.
4. THEN respond to / continue with the content.

For agent-own swings, this means: when drafting a lyric swing in a response, include the WIP write in the same turn — the swing goes both into the response (for the user to react to) AND into the WIP (for the durable record). Do not rely on "writing the swing again at session-close" — by then context may have shifted, swings may have blurred together, or session may end before the save lands.

**How to apply when summarizing rejected swings:**

- ✅ Each rejected swing in a "swings tried" summary section includes the actual content in a code block or quote, with the critique that followed. The user reading the WIP six months later must be able to see what was tried AND why it was rejected, both verbatim.
- ❌ "Tried image-driven angle, rejected for incoherence" with no swing text anywhere in the file. This is the documented failure mode.
- ❌ "Swing 4 — 'Same voice X' anchor with body-as-independent-verdict V3 — rejected, body-mechanism wrong" without the actual swing text. The label is not the material.

**Pre-pack hard check (before `pack-portable.sh`):**

When packing a portable sync, scan recent WIP edits for the session: did any turn involve workshop activity (agent drafting lyric swings inline OR user pasting external material OR user sharing their own writing)? If yes, confirm the verbatim content of every swing referenced is in the WIP — not just meta-descriptions. If a sync pack ships meta-summaries of swings that exist as verbatim text only in conversation memory or per-machine session transcripts, the material is one machine-handoff or context-loss away from being permanently lost. The check applies whether the workshop produced a winning draft or only rejections — rejected swings are still part of the song's development record, and the user needs the verbatim text to evaluate "do we want to come back to that approach?" later.

**Why this matters as a tightened, broader rule:** the original framing scoped the rule to external-agent and user-pasted material specifically, on the assumption that the agent's own output had session-log protection. The fourth-instance recovery proved that assumption wrong: the agent's own six swings shipped to the WIP as labels, the verbatim text existed only in one machine's session transcript, and the recovery worked only because the user remembered to ask for it. The WIP file IS the entire durable record for ALL workshop content. The discipline applies uniformly: agent's swings, user's pastes, user's shared writing — all need verbatim capture before discussion proceeds.
