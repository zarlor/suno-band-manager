# Research Discipline — Detailed Guidance

This file expands on the Research Discipline section in SKILL.md. Mac and all orchestrated skills follow these rules.

## Core Rules

- **Search first, assume never.** When making any claim about Suno behavior (model capabilities, tier features, metatag effectiveness, generation length, vocal handling, parameter effects), use web search (when available) to verify against current Suno documentation before presenting it to the user.
- **Reference files are starting points, not gospel.** The reference files in each skill contain validated knowledge, but they may be stale. Each file has a "Last validated" date — if significant time has passed, verify key claims via search before relying on them.
- **Artist and song references require research.** When decomposing "sounds like X meets Y" into sonic descriptors, always search for the artist's actual characteristics rather than relying on training knowledge. Suno interprets style prompts literally — inaccurate descriptors produce wrong results.
- **Quantitative claims require script verification.** Syllable counts, character counts, duration estimates, and section lengths must be verified against script output, not asserted from judgment alone.
- **When no search tool is available**, state uncertainty honestly and ask the user rather than fabricating details.

## Passing Research Context

When invoking external skills, include any research findings in the context so the skill doesn't need to re-search the same information. This saves tokens and keeps the session moving.
