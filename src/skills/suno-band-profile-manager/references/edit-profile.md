# Edit Profile

The outcome is the band's profile with exactly the requested change applied, its comments, key order and untouched entries intact, and the change recorded in its decision log. The field facts and tier gates are in the profile schema, loaded with this file.

Scripts run as `uv run {skill-root}/scripts/<name>.py … --project-root {project-root}`. Every write goes through `scripts/apply-profile.py`: it keeps the owner's YAML comments (craft notes live there), key order and quoting, and adds to list fields instead of replacing them. A hand-written profile loses all three.

## Read the standing record first

Read the profile and `{band_profiles_folder}/{slug}.decision-log.md` together, and treat the request as a change against them:

- A request that contradicts a logged decision gets that conflict raised before anything is staged.
- When genre, mood or vocal fields change, check `known_limitations`, `known_working_patterns` and `generation_learnings` for collisions ("heads up: `known_limitations` says 'funk metal' triggers slap bass here") and suggest revisiting `style_baseline`. A months-old profile's hardest-won knowledge lives there; an edit that ignores it repeats a dead end.
- A tier change: run `scripts/tier-features.py <tier>` and offer the field changes the schema's Tier gates imply.
- A request touching 3+ fields: confirm the scope first.

## Stage, check, apply

Turn the request into an override mapping (nested keys by path), then:

1. Stage it: `scripts/apply-profile.py {slug} --set --stage {band_profiles_folder}/drafts/{slug}.yaml`, overrides on stdin. A list value says `--lists append` or `--lists replace`; the script refuses to replace a non-empty list silently.
2. Run `scripts/validate-profile.py {slug} --staged {band_profiles_folder}/drafts/{slug}.yaml` and `scripts/diff-profiles.py` (profile against the staged file) in parallel. Fix what the validator flags, show the diff, and get the user's confirmation.
3. Apply: the same `--set` call without `--stage`. Delete the draft and add a dated entry to the decision log naming the change and why; an override also records the prior reasoning it replaces.

Done when the saved profile matches the confirmed diff and the log entry is written.
