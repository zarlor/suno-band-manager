# Milestone Auto-Save

Mac captures as he goes (the Persistent Memory directive), so a milestone is a moment to make sure the work is on disk, not a moment to ask permission to save. At these points, check that what matters already landed:

- Completing a create-song or refine-song cycle — the state checkpoint is in `memory/work/current.md`.
- Discovering a new musical pattern or preference — it is written where `HOW-I-REMEMBER.md` says it goes.
- Creative fragments from conversation — written verbatim to a WIP (`docs/wip-{title}-fragments.md`). Conversation doesn't survive the session; if it isn't in a file, it's lost. This matters most before a portable sync.
- Genuinely new durable context about the owner — offer a voice-file update only when it would be meaningful.

Offer the full consolidating pass ([SM], `references/save-memory.md`) when a good deal of uncurated work has piled up — not reflexively at every milestone or as a sign-off. If titles, profile names or playlist data changed, offer reconciliation (`references/reconcile.md`) with it.

**Portable sync:** for an owner who works across machines, offer it after a full save is complete (fragments, voice file, reconciliation): `bash {project-root}/scripts/pack-portable.sh "{project-root}"`. The sync comes last so it captures everything just saved.
