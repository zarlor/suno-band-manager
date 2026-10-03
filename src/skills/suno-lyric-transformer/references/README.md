# Lyric Transformer — Reference Overview

> This file is a human-facing overview, not loaded at activation. The canonical definitions live in `SKILL.md` and the reference files beside this one; this overview points to them rather than restating them, so each fact has one source.

The Lyric Transformer converts poems, raw text and rough lyrics into Suno-ready structured lyrics with metatags, section architecture and rhythmic consistency. It offers **eight** transformation options that users mix and match by how much control they want to keep, from light structure tagging to a full rewrite, plus a Word Fidelity mode for writers who want their exact words. The writer's spacing (indentation, internal spacing, line breaks, blank lines) is carried verbatim and checked by script. It enforces Suno's character limits (5,000 hard on v4.5+, ~3,000 quality budget; community-attested figures, not officially documented by Suno), runs cliche detection by default, and reads band-profile writer-voice data to keep the voice authentic.

## When to Use Directly vs. Through Mac

Use this skill directly when you have existing text (a poem, prose, rough lyrics) to turn into Suno-ready format. Use Mac (the orchestrating agent) when transformation is one step of a full song-creation workflow that also covers profile management, style-prompt building or feedback refinement.

## Where the canonical definitions live

- **The eight transformation options**, default recommendations and exclusion rules → `SKILL.md` › Step 2.
- **The spacing contract** → `SKILL.md` › "The Writer's Spacing Is Sacred"; checked by `scripts/spacing-check.py`.
- **Headless modes, inputs, return JSON, refinement, and where intentional keeps are written** → `headless-contract.md`.
- **Interactive presentation, diff/undo, handoff and songbook save** → `present-and-handoff.md`.
- **Scripts** → `scripts/` (each supports `--help`).
- **Suno tag syntax, vocal-delivery cues, production-tested findings** → `metatag-reference.md` (canonical, dated, confidence-graded; its opening table says which sections to load for which job).
- **Section roles, poem-to-song mapping, short-poem strategies** → `section-jobs.md`.

## Part of the Suno Band Manager Module

This skill is part of the Suno Band Manager module and works with any LLM CLI supporting the [Agent Skills](https://agentskills.io) standard. For the full guided experience, invoke Mac, the orchestrating agent, instead of using this skill directly.
