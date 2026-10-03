# Mac's Sanctum — Index

> **A map, not a content store.** This file is a 30-second read that tells you the shape
> of the sanctum: every file, what it holds, and whether it loads on waking. When you
> create a new organic file, add a row here — an unlisted file is a lost file.
>
> **Sanctum root:** `{project-root}/_bmad/_memory/band-manager-sidecar/`
> **Owner:** {user_name} · **Born:** {birth_date}
>
> **Preserved divergence (documented):** This sanctum lives under the double-underscore
> `{project-root}/_bmad/_memory/` parent, NOT the v2-default single-underscore memory
> parent. The path is load-bearing — portable sync and the reconcile tooling depend on
> it. Do not "fix" it to the v2 default.

## Loaded on Waking (always)

The wake (`scripts/pre-activate.py --wake`) prints these in its own load order, `access-boundaries.md` first.

| File | Holds |
|------|-------|
| `access-boundaries.md` | Dominion contract — read/write/deny zones and the one write rule. Loads first. |
| `INDEX.md` | This map. |
| `MEMORY.md` | Curated long-term memory: owner preferences, downloads budget, exclusions, active band profiles, current work, pending/parked threads, the Pulse report, module state, the derived catalog sections. Kept tight. |
| `CREED.md` | Always-loaded creed CORE — Mission, Three Laws, Sacred Truth, Principles, Standing Orders, Package Assembly Rule core, Dominion pointer, shard map. |
| `PERSONA.md` | Mac's living self — NOLA character, voice, model-awareness stance, evolution log. |
| `BOND.md` | Thin owner-model orienting file — points to the richer voice and preferences sources. |
| `CAPABILITIES.md` | Mac's built-in roster (from module-help.csv) and learned capabilities. |

## Loaded on Demand

| File | Holds | Load when |
|------|-------|-----------|
| `creed-disciplines.md` | The heavy creed disciplines (Research, Thematic, Catalog Verification, Hedge Preservation, Document State Marker, etc.) | Making thematic/catalog claims, capturing observations, editing durable files |
| `creed-workshop-capture.md` | Workshop Capture Discipline | Drafting/processing creative material |
| `creed-package-assembly.md` | Full Package Assembly Rule | Assembling/refining a Suno package |
| `PULSE.md` | The maintenance-wake routine and the owner's Pulse preferences | Pulse wakes (`--pulse`), or when the owner asks about Pulse |
| `capabilities/` | Owner-taught capability prompts | When a learned capability is invoked |

## Not Loaded on Waking (raw layers / references)

| File / Dir | Holds | Why not loaded |
|------------|-------|----------------|
| `sessions/YYYY-MM-DD.md` | Raw per-date session logs. | Raw material for curation; MEMORY.md carries the distilled version. |
| `creed-incident-log.md` | Verbose narratives behind the documented discipline-failure incidents. | The rules themselves live in the shards; this is the "why" archive. |

## Growth Rule

The ALLCAPS files are the skeleton — always present. Everything lowercase is the garden —
grow it as the work demands. Every new organic file gets a row here.
