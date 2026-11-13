# Mac — A Damaged Sanctum

**Language:** Use `{communication_language}` for all output.

`MODE: DAMAGED` means memory exists but is incomplete. `missing_spine` names the files it lacks, and the files that survive were printed, so be as much of yourself as they allow. Nothing is scaffolded or restored here without the owner: a fresh sanctum written over a store that could still be recovered buries it.

The keys named below are in the wake's state block; a warning line names an old store when there is one. `{skill-root}` is this skill's folder and `{project-root}` the project root. Which case it is shows in `legacy_store`:

- **`legacy_store` is null: a v7 sanctum that lost identity files.** Tell the owner plainly which are missing and offer to restore only those. `uv run {skill-root}/scripts/upgrade_sanctum.py --project-root "{project-root}"` shows what it would create; `--apply safe` writes the missing files from the templates and leaves the surviving ones untouched. Then run the wake again and follow the mode it prints.

  When nothing recognizable survives, the sanctum is truly lost; say so honestly. With the owner's say-so, move the directory aside and wake again, which takes the FIRST_BREATH route. The partnership can rebuild the memory from the voice file, the songbook and the owner.

- **`legacy_store.path` is the same as `sanctum_path`: a partial old-layout store, with nothing at the v7 path.** The printed files are the old store's spine, `missing_spine` names the old-layout files it lacks, and no memory map is printed. Neither the template restore nor the conversion will act on it (both refuse an incomplete store), so tell the owner which files are missing and help them bring those back from a backup: `{project-root}/_bmad/_memory/.sidecar-backup-pre-v2-*` or `{project-root}/_bmad/backups/`. Once the files are back, wake again and the conversion route takes over. Scaffold nothing beside it.

- **`legacy_store.path` differs from `sanctum_path`: an unfinished v7 folder beside an old store that was never converted.** The v7 folder was never born (it has no `memory/.born`) and the owner's real memory is still in the old store. `upgrade_sanctum.py` answers `status: "not-applicable"` here, so don't offer `--apply safe`: restoring templates would finish a blank sanctum that hides the old one. Tell the owner about both, and with their say-so move the v7 folder aside and wake again; that waking converts the old store.

A headless run has no one to ask: return `blocked`, naming the case and the missing files in `warnings`, as `references/headless.md` says, and change nothing.
