# Document State Marker Discipline — Top-of-File Pointers Must Reflect Current State — the incident

**Recurring failure pattern — a workshop WIP, surfaced on a second machine after sync.** The recovery pass wrote the seven verbatim swings into the song's WIP file under a new section labelled `## [date] session — corrections that supersede the earlier architecture`, well down the file. Workshop Capture Discipline was satisfied — the verbatim content was there, fully labelled, with critique. But the file's top-of-file structure still read:

- `## Architecture committed` — the earlier machine's architecture
- `## Current draft` — the earlier machine's last committed draft
- `## What's working in the current draft` — analysis of that earlier draft

When a fresh agent opened the file after sync, it read top-down, hit `## Architecture committed` and `## Current draft` as authoritative live-state labels, treated those sections as the workshop's actual current state, and never scrolled past them to the recovered swings and corrections below. The user's report of the failure was precise: the top of the file still said "current draft" over the older information, and the newer swings section was not labelled in a way that would make a reader look past it. The Status block at the top mentioned the supersession in prose, but the section headers below kept the structure looking authoritative — and section headers win over prose for any reader doing structural scanning.

**The corrected understanding:** saving verbatim content is a different operation from updating the structural pointers that tell readers where it lives; both must happen in the same edit. Workshop Capture, Hedge Preservation and this rule are one family of fidelity rules for the durable file — save the verbatim content, keep the owner's certainty level, keep the pointers true — firing on different triggers.

**Why durable workshop files are the highest-cost site:** a workshop file may sit between sessions for weeks or months. When the user returns, or a fresh Mac on another machine reads it, structural pointers are the primary navigation aid. A "## Current draft" pointing at superseded material misleads every future reader on every future machine the same way — the corruption isn't local to one session.
