# Document State Marker Discipline — Top-of-File Pointers Must Reflect Current State

**When appending superseding material to a workshop, songbook, or reference file, the top-of-file state markers MUST be updated or relocated in the same edit.** A stale "Current draft," "Architecture committed," or "Latest" header at the top of a file is a stop-signal: any future reader (LLM doing top-down scanning, the user revisiting the file, a fresh agent on another machine) will trust the structural label and stop reading before reaching the newer material below. The verbatim content can be perfectly captured (Workshop Capture Discipline satisfied) and still be effectively invisible if the structural pointer above it lies about where the live state lives.

**Recurring failure pattern — a workshop WIP, surfaced on a second machine after sync:**

The recovery pass wrote the seven verbatim swings into the song's WIP file under a new section labelled `## [date] session — corrections that supersede the earlier architecture`, well down the file. Workshop Capture Discipline was satisfied — the verbatim content was there, fully labelled, with critique. But the file's top-of-file structure still read:

- `## Architecture committed` — the earlier machine's architecture
- `## Current draft` — the earlier machine's last committed draft
- `## What's working in the current draft` — analysis of that earlier draft

When a fresh agent opened the file after sync, it read top-down, hit `## Architecture committed` and `## Current draft` as authoritative live-state labels, treated those sections as the workshop's actual current state, and never scrolled past them to the recovered swings and corrections below. The user's report of the failure was precise: the top of the file still said "current draft" over the older information, and the newer swings section was not labelled in a way that would make a reader look past it. The Status block at the top mentioned the supersession in prose, but the section headers below kept the structure looking authoritative — and section headers win over prose for any reader doing structural scanning.

**The corrected understanding:** Workshop Capture is necessary but not sufficient. Saving verbatim content is a different operation from updating the structural pointers that tell readers where the verbatim content lives. Both must happen in the same edit. A document with current verbatim material under a stale "Current draft" header is functionally equivalent to a document with no verbatim material at all — readers don't find it.

**Trigger conditions — fire on ALL of these:**

- Appending superseding material to a workshop file (`docs/wip-*.md`) below sections labeled `## Current draft`, `## Architecture committed`, `## Latest`, `## Active`, `## In progress`, or any similar live-state label
- Writing new analysis, observations, or corrections that supersede earlier sections in a songbook entry, dossier entry, sidecar narrative, voice file, or production patterns file
- Recovering verbatim material from a session transcript or external source into a file that already has top-of-file state markers
- Any file edit where the conceptual "current state" of the document moved to a new location but the original location still carries a "current"-flavored label

**Mechanical step (NOT optional, NOT discretionary):**

In the same edit that appends superseding material:

1. **Identify all top-of-file state markers.** Scan from the top: section headers containing "Current," "Latest," "Architecture committed," "Active," "In progress," "Live," "Working," or any framing that implies "this is the live state." Status blocks at the top of file. Frontmatter fields that point at sections.
2. **Update or relocate each one.** Three valid patterns:
   - **Relabel as superseded:** `## Current draft` → `## Earlier draft (superseded — see §[active section] below)` with a one-line explanatory note immediately below the header.
   - **Move the label:** delete the stale `## Current draft` and put `## Current draft` on the new active section.
   - **Add a top-of-file pointer:** before any other content, add a callout/blockquote: `> **LATEST STATE: §[link to active section]**` with one line explaining why the older sections below it are preserved.
3. **Add an explicit "do not treat as live" note** to each preserved-but-superseded section, immediately below its header. One line is enough: `> ⚠ Superseded YYYY-MM-DD; preserved for reference only. Active state in §[link below].`
4. **Verify with a fresh-reader test.** Re-read the file from line 1 as if you've never seen it before. Do you reach the new active material without being misled by a stale label? If yes, done. If no, iterate.

**How to apply:**

- ✅ Top-of-file pointer (callout block before any sections) when the active state is buried below preserved historical material. Pointer is the first thing the reader sees.
- ✅ Explicit "(superseded YYYY-MM-DD)" suffix on superseded section headers. Section header itself carries the supersession; reader can't miss it.
- ✅ One-line "⚠ this is preserved for reference only, see §X below" note immediately under each superseded header. Reinforces the supersession at the section-entry point.
- ✅ Hyperlinked pointer (`§[active section name](#anchor)`) so reader can jump rather than scroll-and-search.
- ❌ Relying on the Status block at top to communicate supersession while leaving section headers untouched. Section headers win over prose for structural readers.
- ❌ Saving verbatim swings/corrections under a properly-labeled new section while leaving "## Current draft" above it pointing at older material. The new section is invisible to anyone trusting the structure.
- ❌ Using vague labels like "## More notes" or "## Updates" for the superseding section — they don't signal "this is the live state, the older sections are not."
- ❌ Assuming the next reader will scroll the whole file. Many readers (LLMs and humans) read top-down and stop when the structure looks complete. Top-down completeness is the test.

**Sister rule to Workshop Capture and Hedge Preservation:** Workshop Capture says "save the verbatim content to the durable file." Hedge Preservation says "preserve the user's certainty level when capturing observations." Document State Marker says "and update the structural pointers so the verbatim content is findable." All three protect the durable file's integrity; they fire on different triggers and check different things, but they're the same family of fidelity rules.

**Why durable workshop files are the highest-cost site:** A workshop file may sit between active sessions for weeks or months. When the user returns (or a fresh Mac on another machine reads the file), structural pointers are the primary navigation aid. If a workshop file ships a labeled "## Current draft" pointing at superseded material, every future reader on every future machine will be misled in the same way. The corruption isn't local to one session — it propagates to every future read.
