# Edit Profile

The outcome is the band's profile with exactly the requested change applied, its comments, key order and untouched entries intact, and the change recorded in its decision log. The field facts and tier gates are in the profile schema, loaded with this file.

Scripts run as `uv run {skill-root}/scripts/<name>.py … --project-root {project-root}`. Every write goes through `{skill-root}/scripts/apply_profile.py`: it keeps the owner's YAML comments (craft notes live there), key order and quoting, and adds to list fields instead of replacing them. A hand-written profile loses all three.

## Read the standing record first

Read the profile and `{band_profiles_folder}/{slug}.decision-log.md` together, and treat the request as a change against them:

- A request that contradicts a logged decision gets that conflict raised before anything is staged.
- When genre, mood or vocal fields change, check `known_limitations`, `known_working_patterns` and `generation_learnings` for collisions ("heads up: `known_limitations` says 'funk metal' triggers slap bass here") and suggest revisiting `style_baseline`. A months-old profile's hardest-won knowledge lives there; an edit that ignores it repeats a dead end.
- A tier change: run `uv run {skill-root}/scripts/tier_features.py <tier>` and offer the field changes the schema's Tier gates imply.
- A request touching 3+ fields: confirm the scope first.

## Stage, check, apply

Turn the request into an override mapping (nested keys by path), then:

1. Stage it: `uv run {skill-root}/scripts/apply_profile.py {slug} --set --stage {band_profiles_folder}/drafts/{slug}.yaml --project-root {project-root}`, overrides on stdin through a heredoc (no temp file under a fixed `/tmp` name). A list value says `--lists append` or `--lists replace`; the script refuses to replace a non-empty list silently, whatever shape the override has. A result with `unchanged: true` means the profile already says this: tell the user, delete the draft and stop, since there is nothing to approve.
2. Run `uv run {skill-root}/scripts/validate_profile.py {slug} --staged {band_profiles_folder}/drafts/{slug}.yaml --project-root {project-root}` and `uv run {skill-root}/scripts/diff_profiles.py {band_profiles_folder}/{slug}.yaml {band_profiles_folder}/drafts/{slug}.yaml` in parallel. Fix what the validator flags (and re-validate: the file you apply is the file that passed), then show the output of that diff command with `--text` added (its unified diff; the default JSON is for checking, not for showing) in a ```diff block in your reply — not a hand `diff`, and not a sentence saying the diff is clean.
   - **No go-ahead yet:** show the diff and stop; step 3 runs on the user's yes.
   - **The user already said go** ("go ahead and save it"): copy the profile to `{band_profiles_folder}/drafts/{slug}.prior.yaml` first, run step 3, and put the diff in the same reply that reports the save, with the undo: "Say undo and I'll put the old version back" (`uv run {skill-root}/scripts/apply_profile.py {slug} --save --force --in {band_profiles_folder}/drafts/{slug}.prior.yaml --project-root {project-root}`; the slug names the file to restore, since one derived from `name` misses a renamed band). Their go-ahead covers the change they asked for; the shown diff proves that's all that changed. Never say a diff was "shown above" unless it is in a reply the user has seen.
3. Apply: the same `--set` call without `--stage`. The script also updates the `# Last modified:` header and reports the old one as `last_modified_was`: name that change when you describe the save, never "comments unchanged". Delete the draft (a `.prior.yaml` stays while an undo is on offer; the next operation on this profile, or the user's sign-off, deletes it, along with the `{slug}.yaml.bak` an undo leaves beside the profile) and add a dated entry to the decision log naming the change and the user's reason in their words, or "no reason given" with nothing after it — never one you supply, not even as context ("fits the earlier decision to…"); an override also records the prior reasoning it replaces.

Done when the saved profile matches the confirmed diff, the log entry is written, and `{workflow.on_complete}` has run if it is set. The reply then ends in exactly this order:

1. The onward offer: "Your profile is saved. Want to build a style prompt or write lyrics for this band?"
2. The audit of this session's decision-log entries: each is in the profile, parked as a future idea, or explicitly set aside, so the user signs off on how their thinking was handled. Earlier sessions were audited at their own handoff.
3. "Anything else with your profiles, or are we good?" as the last line; a setup note or other aside goes above it.
