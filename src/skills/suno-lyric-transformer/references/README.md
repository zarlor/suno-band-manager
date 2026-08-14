# Lyric Transformer — Reference Overview

> This file is a human-facing overview, not loaded at activation. The canonical, drift-free definitions live in `SKILL.md` and the two reference files beside this one — this overview points to them rather than restating them, so there is one source of truth per fact.

The Lyric Transformer converts poems, raw text, and rough lyrics into Suno-ready structured song lyrics with metatags, proper section architecture, and rhythmic consistency. It offers **eight** transformation options that users mix and match based on how much creative control they want to retain — from lightweight structure tagging to full rewrites — plus a Word Fidelity mode for writers who want their exact words preserved. It enforces Suno's character limits (5,000 hard limit on v4.5+, ~3,000 quality budget — community-attested figures, not officially documented by Suno), runs cliche detection by default (Suno's vocal engine amplifies cliches), and integrates with band-profile writer-voice data to maintain authentic voice.

## When to Use Directly vs. Through Mac

Use this skill directly when you have existing text (a poem, prose, rough lyrics) to turn into Suno-ready format. Use Mac (the orchestrating agent) when transformation is one step of a full song-creation workflow that also covers profile management, style-prompt building, or feedback refinement.

## Where the canonical definitions live

- **The eight transformation options** (ST, CE, CC, RA, RE, FR, CD, WF), their descriptions, default recommendations, and mutual-exclusion rules → `SKILL.md` › Step 2 "Full menu".
- **Headless mode** invocations and the output contract → `SKILL.md` › "Activation Mode Detection" and "Headless Output Contract".
- **Scripts** and what each produces → `SKILL.md` › "Scripts".
- **Suno tag syntax, vocal-delivery cues, character limits, production-tested findings** → `metatag-reference.md` (canonical, dated, confidence-graded).
- **Section roles, poem-to-song mapping, short-poem strategies** → `section-jobs.md`.

## Part of the Suno Band Manager Module

This skill is part of the Suno Band Manager module and works with any LLM CLI supporting the [Agent Skills](https://agentskills.io) standard. For the full guided experience, invoke Mac — the orchestrating agent — instead of using this skill directly.
