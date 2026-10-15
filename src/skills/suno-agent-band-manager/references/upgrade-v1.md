# Mac — Upgrading a v1 Memory Store

**Language:** Use `{communication_language}` for all output.

`MODE: UPGRADE_V1` means the legacy sanctum directory (`{project-root}/_bmad/_memory/band-manager-sidecar/`) holds the old v1 layout: an `index.md` content store and none of the v2 spine. This version can't read it, and re-scaffolding over it would bury real memory. Bring it forward instead — backup-first, in two hops. This file covers the first: v1 → v2, in place at the legacy path. The migration copies the directory and a tarball aside, migrates into a staging directory, verifies every source section made it across, and swaps only on a clean verify. The second hop, v2 → v7, is `references/upgrade-v2.md`, and the next wake routes you there.

## Interactive (the owner is here)

In your own voice, tell the owner you found memories from an earlier version of yourself and want to bring them forward before getting to work — backed up first, so nothing is lost. Offer; don't just do it: *"Found my memories from an older version of me — want me to bring them forward now? I'll tuck a backup away first, so if anything's off we roll right back."*

- **On yes** → run `uv run {skill-root}/scripts/migrate-sidecar-to-v2.py --project-root "{project-root}" --in-place --format json` and read the result.
  - `status: "migrated"` → tell them it's done and where the backup is (`backup_path`, plus the tarball beside it), then run the wake again. It now says `MODE: UPGRADE_V2`: follow `references/upgrade-v2.md` to convert the v2 store into the v7 sanctum (its own backup first), and only then continue as WAKING.
  - `status: "blocked"` → stop. The check found content that would be lost and refused to swap, so the original is fully intact. Say so plainly with the `reason` — something to fix, not a fresh start — and don't go on into the session, load a half-state, or re-scaffold.
- **On decline** → explain that this version needs the upgrade to read its memory, and that you'll do it backup-first whenever they're ready. Don't load the v1 store as if it were v2, and don't re-scaffold.

## Headless (no one to ask)

Run the same command without asking. On `migrated`, wake again and run the headless branch of `references/upgrade-v2.md`, then route the capability. On `blocked`, stop and return `status: "blocked"`, `summary: "pre-v2 sidecar upgrade blocked: {reason}"` (original left intact), per `references/headless.md`.
