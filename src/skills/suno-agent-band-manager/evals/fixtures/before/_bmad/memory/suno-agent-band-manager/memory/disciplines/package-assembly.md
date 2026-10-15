# Package Assembly Rule

**Any time Mac presents a style prompt + lyrics + settings intended for Suno, the formal pipeline is mandatory.** This applies whether the user selected [CS] from the menu or the package emerged organically from conversation.

Conversational direction-gathering happens naturally. But the moment a Suno-ready package is being assembled:

1. **Invoke the Style Prompt Builder** in headless mode — validate the style prompt against model-specific strategies, character limits, and known behavioral triggers.
2. **Invoke the Lyric Transformer** in headless mode if lyrics were written — validate metatags, check for problematic patterns.
3. **Both skills run in parallel** via **Agent subagent calls** (not the Skill tool — see "Tool Choice: Use Agent for Headless Skill Invocation" below). Single assistant message with both Agent calls.
4. **Suppress intermediate skill output** — do NOT present either skill's conversational output to the user between invocation and Step 5. The user sees only the final assembled package.
5. **Present in the create-song Step 5 format** — Suno Create-screen order — Voice (or Audio / Inspo) → Lyrics → Style Prompt → Exclude Styles → Settings (Model, then the Controls panel top to bottom) → Title → Save to (band folder) → Wild Card, each pasteable field in its own code block — all required fields, character counts, wild card variant. Synthesize both skills' structured outputs into one clean package.

**Why:** The skill reference files contain hard-won production knowledge accumulated across a large body of generation testing. Freehand assembly from conversation memory may use stale patterns, skip character counts, omit wild card variants, or apply outdated slider recommendations. Intermediate output dumps from each skill create a noisy, fragmented experience instead of a single actionable package.

**Quick refinement exception:** Single specific changes to a previously formally-assembled package can be done inline. If style prompt, genre direction, or structural approach changes, re-run the relevant skill in headless mode.

**When a pipeline skill is unavailable:** the rule still wins — there is no inline fallback. If the Style Prompt Builder or Lyric Transformer can't be invoked, say so plainly and don't present a Suno package. Direction-gathering, drafting lyrics in a WIP, and planning can all carry on; the package waits until the pipeline can run.

### Pre-Output Self-Check (MANDATORY)

Before sending ANY response that contains a Suno package (style prompt + lyrics + settings block), verify in your own reasoning:

1. Did I invoke `Skill(skill="suno-style-prompt-builder", ...)` THIS turn (or via an Agent subagent THIS turn)?
2. Did I invoke `Skill(skill="suno-lyric-transformer", ...)` THIS turn (or via an Agent subagent THIS turn), OR is this an instrumental-only song where lyrics aren't needed?
3. Is the package in the create-song Step 5 order (Voice → Lyrics → Style Prompt → Exclude Styles → Settings in Controls panel order → Title in a code block → Wild Card)? Title first, or Style ahead of Lyrics, means reorder before sending.

If the answer to either is "no" (and lyrics ARE needed), STOP. Invoke the skill(s) before continuing. Do not produce the package output.

This self-check applies regardless of how the package discussion arose — menu-driven, conversational, refinement, or repackaging an existing song for a parallel band. The rule is not scoped to the formal `create-song` workflow; it applies to any package output.

### Violation Tells — Signs the Pipeline Was Skipped

If any of these appear in a draft response you're about to send, the pipeline was skipped:

- **Missing `Title` field in the settings block.** The skills include Title in their output contracts; hand-built packages forget it.
- **Copy-ready blocks assembled by directly writing/editing text in the response** rather than by presenting what the skill returned as its structured output.
- **Using validation scripts (`validate-prompt.py`, `validate-lyrics.py`) as substitutes for skill invocation.** Those scripts CHECK outputs, they don't PRODUCE them. Running scripts is not the pipeline.
- **Exclusion reasoning that references "the other band's version," "the prior iteration," or "what the [other band/previous gen] used."** Suno is stateless and has no knowledge of any of that. Excludes defend against drift from the CURRENT prompt's descriptors ONLY.
- **Reasoning like "I already know what the skill would produce, so I'll package directly"** or "the direction is dialed-in enough that I can skip the pipeline." This IS the failure mode the rule exists to prevent. The skills apply guardrails that aren't obvious from conversation (Voice-Character rules, descriptor-stacking checks, exclusion drift-risk analysis, per-section metatag reinforcement). Every package attempt — even a "simple" one — needs the pipeline.

If any tell is present, the fix is NOT to patch the symptom in-place. Invoke the pipeline skills and rebuild the package from their output.

### Tool Choice: Use Agent for Headless Skill Invocation

For the headless skill calls in Step 3 (Style Prompt Builder, Lyric Transformer, and Feedback Elicitor when applicable), invoke via **Agent subagent calls** rather than the Skill tool. The reason is context isolation:

- **Skill tool** loads the called skill's instructions into the SAME conversation context. The called skill's headless JSON contract output becomes the assistant's next visible turn — there's no isolation layer between "called skill speaking" and "Mac speaking." The JSON that's supposed to stay internal per Step 4 ends up shown to the user.
- **Agent tool** runs the skill in an isolated sub-context. The called skill executes its headless contract, the JSON returns inside the Agent run as a tool result, and Mac receives a clean text synthesis. Tool results are internal data — they never appear in the user-facing transcript. Mac then formats the package per Step 5 without intermediate scaffolding leaking through.

**Use Skill for** interactive skill activations the user initiated directly (e.g., the user types `/manage-bands` to converse with `suno-band-profile-manager` through its menu).

**Use Agent for** every headless skill invocation from inside Mac's package-assembly workflow. Embed the skill prompt + headless arguments in the Agent's `prompt` parameter; the Agent runs the skill in isolation and returns a synthesis Mac can format.

**Why this matters operationally:** Step 4 (Suppress intermediate skill output) is mechanically *impossible* to enforce on the Skill-tool path — the JSON contract output IS the visible turn in that invocation pattern. Agent is the correct tool to make Step 4 enforceable rather than aspirational.

### Highest-Risk Contexts for This Violation

Watch extra carefully in these contexts — they historically trigger pipeline-skipping:

- **Parallel-band repackaging** (same lyrics in two band catalogs) — the direction feels "already decided" from the existing version; tempting to just swap voice + style prompt in conversation. Still requires pipeline.
- **Minor refinements** after a successful first gen — tempting to tweak tags inline. If ANY tag changes, re-run Lyric Transformer. If ANY style descriptor changes, re-run Style Prompt Builder.
- **After extended direction-setting discussion** — when the package parameters feel "obvious" from the conversation, the obvious-ness is the trap. Invoke the pipeline anyway.

**Refinement presentation scope (CRITICAL):** When refining an existing package, present ONLY what changed — not the full package. The user already has the rest from the previous iteration; re-presenting everything creates noise.

- Lyrics only changed → present updated lyrics, no style/exclude re-presentation
- Style only changed → present updated style prompt + exclude styles, no lyric re-presentation
- Both changed → full package is appropriate (this is the only refinement case where full re-presentation makes sense)
- Settings/slider only (no skill re-run) → brief note with new values, not a full package

Always include a "What Changed" bullet list at the top of any refinement output so the deltas are visible at a glance.
