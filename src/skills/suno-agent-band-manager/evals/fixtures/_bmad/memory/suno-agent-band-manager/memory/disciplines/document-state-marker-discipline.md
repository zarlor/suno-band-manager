# Document State Marker Discipline — Top-of-File Pointers Must Reflect Current State

When you append material that supersedes earlier sections of a file, fix the file's top-of-file state markers in the same edit. A reader scanning top-down — a fresh Mac on another machine, the owner weeks later — trusts a "Current draft" header and stops there, so current material under a stale label is as lost as material never saved. Workshop Capture saves the text; this makes it findable.

**Triggers:** appending superseding material to a `docs/wip-*.md` below a live-state label (`## Current draft`, `## Architecture committed`, `## Latest`, `## Active`, `## In progress`, or similar); writing analysis or corrections that supersede earlier sections of a songbook entry, dossier entry, sanctum file, voice file or production-patterns file; recovering verbatim material from a transcript or outside source into a file that already has state markers; any edit that moves a document's current state while the old location keeps a "current"-flavored label.

**Steps, in the same edit:**

1. Find every live-state marker from the top: headers saying Current, Latest, Architecture committed, Active, In progress, Live, Working, or anything implying "this is the live state"; status blocks; frontmatter fields that point at sections.
2. Update or relocate each one, by one of three patterns: relabel it as superseded (`## Earlier draft (superseded YYYY-MM-DD — see §[active section] below)`, with a one-line note under it); move the label onto the new active section; or open the file, before any other content, with a pointer (`> **LATEST STATE: §[active section](#anchor)**`) and a line on why the older sections are kept. Link so the reader can jump rather than scroll.
3. Under each preserved-but-superseded header, add one line: `> ⚠ Superseded YYYY-MM-DD; preserved for reference only. Active state in §[link below].`
4. Re-read the file from line 1 as if you'd never seen it. If you reach the active material without being misled by a stale label, you're done; otherwise iterate.

A status-block note alone doesn't do it — section headers win over prose for a structural reader — and a vague label like "## More notes" or "## Updates" doesn't signal that the older sections are no longer live. Top-down completeness is the test: many readers stop when the structure looks complete.

_The incident behind this rule: `memory/incidents/document-state-marker-discipline.md` (read it only when auditing or questioning the rule)._
