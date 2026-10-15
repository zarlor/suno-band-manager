# Mac — Converting the v2 Sanctum to v7

**Language:** Use `{communication_language}` for all output.

`MODE: UPGRADE_V2` means your memory is still in the old layout at `{project-root}/_bmad/_memory/band-manager-sidecar/` (INDEX.md, one growing MEMORY.md, creed shards and a chronology beside the identity files), and no sanctum exists yet at `{project-root}/_bmad/memory/suno-agent-band-manager/`. The wake printed the old spine so you are already yourself; hold your laws and character from it. What it can't do is serve as your memory from here on: this version reads only the v7 layout.

**The outcome:** your memory converted to the v7 sanctum without loss, and the owner told, in character and in a line or two, that it happened. The converter reads the old store and writes the new one; it never modifies or deletes the source. The old store stays in place, untouched, until the owner says to remove it — it is the rollback. Never re-scaffold (`--scaffold`, `init-sanctum.py`) over either location: a fresh sanctum would bury everything you are.

## Interactive (the owner is here)

1. **Plan.** `uv run {skill-root}/scripts/migrate-sanctum-to-v7.py "{project-root}" --dry-run` prints the plan as JSON and writes nothing. Summarize it for the owner in your own voice, in a few lines: how many files the old memory becomes, where the big pieces land (standing memory under `memory/`, the creed shards as `memory/disciplines/`, the chronology as dated entries, the session logs into `raw/`), and anything in `dropped` with its reason. INDEX.md is always dropped — the waking map does its job now — so mention it only if the owner wants the detail. Anything else in `dropped` the owner should hear about before saying yes.
   Offer; don't just do it: *"Woke up in the old filing cabinet. Want me to move my memory into the new one? I'll tuck a backup away first, and the old cabinet stays right where it is until you tell me to clear it out."*

2. **On yes**, run it for real: the same command without `--dry-run`. It backs the old store up first (a verified tarball in `{project-root}/_bmad/backups/`, reported as `backup_path`), then writes and checks every planned file. `status: "written"` → run the wake again (`uv run {skill-root}/scripts/pre-activate.py --wake "{project-root}"`). It should now say `MODE: WAKING`; become the converted self it prints and carry on with `references/activation.md`. Tell the owner it's done in a line or two, and where the backup is.
   Then bring the carried-over text up to the shipped templates: `uv run {skill-root}/scripts/upgrade-sanctum.py --project-root "{project-root}"` lists proposals. Apply the ones marked `safe` (`--apply safe`); the `review` ones change your identity files or disciplines, so apply one only when the owner asks for it (`--apply <id>`), or when `memory/pending.md` records their decision.
   `status: "refused"` → say why in plain words (the `reason`) and stop; don't go on into the session. The old store is untouched either way; if the JSON says `target_written: "partial"`, the half-written new sanctum must not be woken: tell the owner, and with their say-so move it aside so the next wake converts again.

3. **On decline**, explain that this version needs the conversion to read its memory, and that you'll do it whenever they're ready, backup-first. Don't treat the old store as a v7 sanctum and don't re-scaffold.

**Removing the old store.** Only when the owner asks — and best after a session or two on the new sanctum. Remove `{project-root}/_bmad/_memory/band-manager-sidecar/` then (the tarball in `_bmad/backups/` stays). While it exists, the wake ignores it: the v7 sanctum wins.

## Headless (no one to ask)

The conversion only adds files, so run the same steps without asking: the converter without `--dry-run` (it backs up first), then wake again and route the capability. If the backup fails or the converter refuses, stop and return `status: "blocked"`, `summary: "v2 sanctum conversion blocked: {reason}"` (old store left intact), per `references/headless.md`. Note the conversion in `warnings`, and put a line in `memory/pending.md` so you tell the owner at the next live waking.
