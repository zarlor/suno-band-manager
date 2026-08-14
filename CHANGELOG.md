# Changelog

All notable changes to the Suno Band Manager module are documented here.

---

## [2.2.0] - 2026-08-14

A platform-currency release. Suno changed materially over the summer — download caps and download-bound commercial rights arrive 2026-09-03, Studio 2.0 shipped, model retirement is announced, and new control surfaces (Duration slider, Lyricist, the My Taste wand) landed — so the module's entire Suno knowledge layer was re-researched from primary sources and refreshed, then validated end-to-end. The release also **de-identifies the public repo**: teaching examples now use an invented multi-style cast rather than one creator's catalog. No workflow, schema, or memory-store changes.

### Upgrade at a glance (existing installs)

- **Nothing to migrate.** Band profiles, songbooks, voice-context files, playlists, WIPs, and the memory store are untouched and fully compatible. No config changes, no new dependencies — the `uv run` convention from v2.1.0 is unchanged.
- **Heads-up for your own Suno workflow:** from **September 3, 2026**, song downloads are capped per tier (Free 7 lifetime / Pro 20 per month / Premier 60 per month) and commercial rights attach to *permitted downloads*, not just to a paid tier. The refreshed docs walk through the consequences — pick your keeper *before* downloading; a song's stems share its single download.
- **If you consume `tier-features.py` output programmatically:** its JSON is now **version 3.0.0** — `download_quality` was removed and new fields were added (`downloads`, `commercial_use`, `stem_modes`, `studio_version`, and others). Human/skill use is unaffected.
- **Teaching examples changed names.** If you'd internalized the docs' old example songs, the lessons are identical — the illustrative songs are now fictional and span folk, metal, synthwave, brass-fusion, Americana, and trip-hop.

### Suno platform reference refresh (research sweep of 2026-08-13)

Documentation only — no skill behavior, script, schema, or memory change. The module's Suno reference docs were last validated in April 2026 and had drifted materially from the platform.

- **Download caps and download-bound commercial rights** (effective 2026-09-03: Free 7 lifetime, Pro 20/month, Premier 60/month, Studio exports exempt) are now documented across the tier matrix, Mac's platform reference, the Studio reference, and the feedback parameter map, together with the workflow consequence: selection happens before download, because downloads are now a budget.
- **Studio 2.0** (shipped 2026-08-13, still Premier-only) is documented — MIDI and MIDI-as-prompt, chat bar, custom plugins, wavetable synth, effects, automation, 32-bit export. The Studio 1.x feature names (Remove FX, Alternates, Quick Replace, Warp Markers, EQ, Context Window, Sounds Mode, Stem Cover, Heal Edits, MILO-1080, and Studio's 12-track stem *export* framing) are marked **archived** rather than deleted, mirroring Suno's own "Studio 2.0" vs "Studio Archive" help split. Note that Auto Split's up-to-12-stems output is current and unaffected — it is the Studio-side 12-track export framing that is archived. **Take Lanes and comping also survived** and are documented as current. The Studio time-signature "not sent to generative models" claim is downgraded to unverified for 2.0.
- **Model retirement** is recorded as announced-but-unspecified: no official version list, no date, and no official word on what happens to Voices, Custom Models, or Personas built on retired models. Extends and Covers of older songs will run on the new models.
- **Corrections:** Personas were never discontinued — they live inside the Voices menu. Every "Personas replaced by Voices" claim in the reference docs (including the profile schema, where it was load-bearing) is corrected. Stem separation is now three named modes with credit costs. Audio upload is 8 min free / 30 min paid. Replace Section's Pro availability is re-confirmed, with our local audible-seams finding kept beside it.
- **New control surfaces documented:** the v5.5 web Duration slider (with its hard-cutoff, rushed-delivery, and premature-end-then-restart failure modes, and the Auto-then-Custom+buffer workflow) and the ending-repair decision tree.
- **Provenance work:** style and lyric character limits are flagged as community-attested with no official Suno documentation; the 5-8 descriptor count is flagged as non-consensus; the vendor-promoted colon-modifier tag syntax is documented as **CONTESTED / do-not-adopt**; the artist-name guardrail gains an official Suno citation. Our unreplicated local findings ([Refrain] in heavy lanes, vocable punctuation, "live"-family crowd noise, Replace Section seams) keep their local attribution.

### Local findings promoted into the public reference docs

Findings previously held only in internal notes are now documented with neutral attribution and honest grading (LOCAL-CONFIRMED for multi-generation testing, LOCAL-OBSERVED for fewer data points):

- **`[Refrain]` for quiet repeating sections in heavy genres** — `[Chorus]`'s peak-default is overridable in restrained lanes but dominant in heavy ones; the retag plus prompt-level role assignment plus an `anthemic chorus` exclude is the working fix. Community sources now replicate the *problem*; the fix remains ours.
- **The "live" word family triggers crowd noise** on v5.5 in any form. The `raw live recording` row was removed from the descriptor-effects table — it was actively recommending a known failure trigger — and replaced with `unpolished room sound` / `natural room ambience`.
- **Compound meter buys feel, not meter** — style-side 6/8 and 12/8 signals move sway and tempo while the subdivision stays 4/4, across the full escalation from genre words to `[6/8]` tags. The previous "inconclusive" note and the `[6/8]` lever in the counter-genre example are updated accordingly.
- **Repeated vocables need every member punctuated** when the count matters (A/B tested).
- **Time-based lyric instructions ("lyrics begin at 0:00") are not reliably parsed** — downgraded from HIGH confidence to harmless-but-never-load-bearing, with crop as the only deterministic fix.
- **Per-voice Audio Influence profiling can land above the community ceiling** (one voice, clean at 85% where 55% showed artifacts), alongside Suno's official escalation path: raise Audio Influence first, then rebuild the profile from a clean acapella.

### Primary-source pass (r/SunoAI) folded in

A fourth research report reached primary sources directly and **resolved two conflicts in the module's favour**: My Taste *can* be disabled (the existing controls line was right; an aggregation-based claim to the contrary was wrong), and Lyricist exists (silence in community discussion is not absence of the feature). It also added: the negation-inside-standalone-brackets backfire and hyphen-prefix excludes; compound pipe-delimited tags; the ghost-vocal mumbling mechanism and its fixes; the dots-as-lyrics instrumental trick; within-track degradation past ~2 minutes; ad-lib suppression levers; duration-slider adherence and its Custom-style requirement; Studio 2.0 day-one field reports; and a further weakening of plain-text BPM adherence. Ending control is now presented as a genuine split between vendor-guide consensus and primary-source reliability reports, with our own toolkit as the trusted baseline.

### Script and skill surfaces brought in line

The refresh reached past the reference docs to the two surfaces that were still contradicting them:

- **`suno-band-profile-manager/scripts/tier-features.py` rewritten** to match its reference twin, restoring the script-is-authoritative relationship the doc asserts. Adds `downloads` (caps, reset behavior, Studio exemption, accounting rules), `commercial_use` (bound to a permitted download), `stem_modes` (three named modes with credit costs and Premier-only Advanced Split), `studio_version`, `audio_upload_max`, `credits_included`, `duration_slider_available`, `replace_section_available`, `last_validated`, and a `notes` block carrying the pricing-display ambiguity, the model-retirement notice, the character-limit provenance, and the archived Studio 1.x names. **Removes `download_quality`** — downloads are gated by count, not bitrate. Corrects credit math (5/song, 10/generation-for-2), Premier's 10,000 credits, audio upload (8 min free / 30 min paid), and Pro's model access. Output `version` bumped to 3.0.0 since fields were removed. Companion test extended from 15 to 27 cases, including a guard that archived Studio 1.x names never resurface as current features (final full-module validation state below).
- **Two SKILL.md instruction surfaces corrected** — `suno-feedback-elicitor` (Studio is Premier-only rather than "Pro/Premier", stems as Auto Split with credit cost, Song Editor naming plus the local audible-seams caveat, Warp Markers and Alternates routed to outcomes instead of archived tool names, within-track degradation, softened Weirdness ceiling and ending-tag promise, a stale reference pointer) and `suno-style-prompt-builder` (Studio never on Pro, Song Editor naming with the seams caveat, the "live" word-family crowd-noise trigger added to the dangerous-words guidance, Voices timbre-drop and the official raise-then-rebuild escalation, character-limit provenance, model-retirement caveat).

Source of record: `docs/suno-research-sweep-2026-08-13.md` (four reports).

### Independent validation pass — all findings fixed

The refreshed module was run through the BMad Builder validation method (structural validate-module: **pass, zero findings**) plus an independent cross-file consistency sweep, which surfaced 2 blockers, 4 should-fix items, and 6 nits — every one a contradiction *between* files that no per-file review would catch. All twelve are fixed:

- **Voices Audio Influence guidance consolidated to a single source of truth** (`model-prompt-strategies.md`) — it had drifted into three incompatible versions across six files, including a stale "above 70% is counterproductive" absolute and a divergent numeric scale. Every other site now restates briefly and points to the source, with the Persona-slot vs Voice-slot range distinction preserved everywhere.
- **A broken activation command fixed** — one SKILL.md documented a customization-resolver invocation that could not execute; all five skills now carry the identical, working form.
- **Take Lanes un-archived** — current Studio docs show Take Lanes and comping survived into 2.0; docs, the tier script, and a new bidirectional test guard were corrected together.
- **`suno-feedback-elicitor` restructured to the BMB v2 skill shape** its sibling already followed (persona scaffolding folded into design rationale, Overview first), with the ruling recorded in its decision log.
- Ending-control guidance now presents the genuine vendor-consensus vs primary-source split; the Advanced Split credit cost carries its verified mechanism (each extraction returns the chosen stem plus its complement — 20 credits total per stem).

### Live-UI verifications (Pro account, 2026-08-14)

Three open questions were closed by direct observation and are graded as such in the docs: **Lyricist is present at Pro** (via the lyrics panel's "Help me write lyrics" helper → "+Lyricist"; free-tier gating remains unverified), the **My Taste wand pre-fills the Styles field with ordinary editable text** (a drafting shortcut, not a hidden generation layer — corroborating that explicit prompts always win), and the **Duration slider's 10-second-to-6-minute range** is confirmed (the 5-second increment granularity remains community-attested). Also newly documented as observed-but-untested: the taste profile's **Genre Overrides** free-text field.

### Validation state at release

Full module suite: **506 tests passing** (up from 493 at v2.1.0 — new tier-features coverage including regression guards against archived-feature and personal-data reintroduction). Structural module validation: pass, zero findings. Both skills edited this release hold their **Good** quality grades under the BMB skill-quality principles.

### De-identification of the public module

The repo is depersonalized ahead of this release. Every git-tracked file — root manifests, reference docs, scripts, test fixtures, decision logs, and this changelog's own history — had the owner's name, band identities and their shorthands, song titles and their revealed meanings, Voice clone names, and catalog specifics removed or replaced.

- **Findings and pedagogy are unchanged.** Only the personal wrappers moved: a production result that used to read "confirmed on [band]'s [song]" now reads "confirmed in production testing," and prompt-text evidence (the actual descriptors that were tested) is preserved verbatim because it is not personal.
- **Teaching examples were rewritten, not dropped.** The thematic-discipline rules in `creed.md` and `playlist-sequencing-methodology.md` depend on title-versus-meaning pairs where the surface read inverts; those now use invented songs (*Harbor Lights*, *Sunday Driver*, *Paper Cut*, *The Long Way Home*, *Bright Side*, *Glass Bottom*, *Signal Fire*) that teach the same lesson.
- **Examples now span multiple styles** — folk, metal, synthwave, brass-fusion, Americana, trip-hop — rather than one catalog's lanes, so the docs read as universally applicable.
- **One functional fix fell out of it:** `genre-coverage.py` had project-specific band names hardcoded in its stopword set. Band-name filtering is now derived at runtime from the band being scanned (`band_stopwords()`), which is both depersonalized and portable to any project.
- **Test fixtures** were renamed to a fictional cast; apostrophe-handling coverage was deliberately preserved by choosing a replacement name that still contains an apostrophe.
- The Mac persona and its NOLA character stay — that is authored module fiction, not user data — as does the GitHub handle in repository URLs.

---

## [2.1.0] - 2026-06-27

A focused maintenance release that standardizes the module's entire Python script layer on **`uv run`**, getting ahead of the BMad v6.9.0 heads-up that **v7 will standardize every Python-running skill on `uv run`** (memlog and other working-memory primitives depend on it). This is about *how* scripts are invoked — nothing about song creation, profiles, lyrics, feedback, sequencing, or the memory store changes. All `docs/` content is untouched and fully compatible.

### Upgrade at a glance (existing installs)

- **Install `uv`** if you don't already have it: `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux/WSL) or `pip install uv`. Every script now runs via `uv run`, which reads each script's PEP 723 inline metadata and **auto-provisions its dependencies** (`pyyaml`, and optionally `librosa`/`numpy`) — no virtualenv to manage, no manual `pip install`.
- **Nothing else changes for you.** Band profiles, the songbook, the voice-context file, `mac-preferences.md`, playlists, WIPs, and the memory store all keep working exactly as before. The standing orders (`CLAUDE.md` / `AGENTS.md` / `GEMINI.md`) now tell the agent to invoke scripts with `uv run`, so existing sessions just work once `uv` is present.
- **Graceful fallback retained:** if `uv` is unavailable, dependency-free (stdlib-only) scripts still run under plain `python3`; only scripts that need third-party deps require `uv` (or a manual dep install).
- **Re-run `suno-setup`** to pick up the new **uv preflight** — it checks for `uv` up front and offers install guidance before running anything.

### Every directly-invoked script standardized on `uv run`

The module previously used a two-tier convention: `uv run` for dependency-bearing scripts, plain `python3` for the stdlib-only ones (with an "(or `uv run` if deps are missing)" parenthetical). That split is now collapsed into one consistent rule, matching the coming v7 standard.

- **31 script shebangs** moved to `#!/usr/bin/env -S uv run --script` (joining the 8 already on it), so direct execution routes through `uv` too. The two deliberate exceptions are noted below.
- **All documented invocations** across every `SKILL.md`, reference doc, the in-script `Usage:` examples, and the `PULSE-template.md` now use `uv run scripts/<name>.py`; the redundant fallback parentheticals were removed.
- **PEP 723 completeness** — the three scripts whose inline metadata omitted an explicit `dependencies` line (`genre-coverage.py`, `reconcile-sidecar.py`, `scaffold-playlist.py`) now declare it, so `uv run <script>.py` is unambiguous everywhere.
- **One "Running the scripts" note per skill** — each skill's `## Scripts` section now states the `uv run` convention and the fallback once (DRY) instead of scattering it across invocations.

### suno-setup uv preflight

`suno-setup` now checks for `uv` on PATH before its first script call and, if it's missing, surfaces install guidance (`curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`) — the "install and set up uv" step BMad v6.9.0 calls out. Dependency-free scripts can still fall back to `python3`, but `merge-config.py` needs `pyyaml`, so the preflight makes the requirement explicit up front.

### Docs + standing orders

- `README.md` and `INSTALLATION.md` gained a `uv` prerequisite / requirement callout; the audio-analysis sections now note that `uv run` auto-provisions `librosa`/`numpy`.
- A new **"Script Execution — `uv run` (MANDATORY)"** section was added to the `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` standing orders (loaded every session, so the live agent always knows the runner + fallback).
- The INSTALLATION troubleshooting entry that wrongly claimed Mac's scripts have "no pip dependencies" was corrected (several declare `pyyaml`), and `_shared/audio_deps.py`'s missing-dependency message now leads with `uv run`.

### Deliberate exceptions

- **The `pipeline-guard.py` Stop/PreToolUse hook stays on `python3`.** It fires on every tool call, so it is kept off `uv` to avoid per-invocation startup latency. The code in `configure-guard.py` that writes the hook command is unchanged.
- **BMad-owned scripts are untouched.** The `resolve_customization.py` references (a BMad *core* script, not part of this module) remain `python3` with their existing by-hand fallback; they'll align when BMad ships them uv-ready.

### Marketplace manifest fix

`.claude-plugin/marketplace.json` now lists **all seven skills** — `suno-playlist-sequencer` (added in v2.0.0) had been missing from the plugin manifest's `skills` array and is now included.

### Validation

Full test suite green via `uv run`: **493 tests pass** (436 + 57 librosa-dependent), with smoke tests confirming stdlib invocation, `pyyaml` auto-provisioning, and direct `uv run` shebang execution.

---

## [2.0.0] - 2026-06-18

A major release. The whole module is brought up to the **BMad Module Builder v2 (BMB v2) standard**: every workflow skill modernized, a new dedicated playlist-sequencing skill extracted, and the Mac agent rebuilt as a v2 **autonomous sanctum agent** whose memory store now stays bounded instead of growing without limit. The only thing that touches existing installs is the memory layout — and it **auto-migrates losslessly on first activation** (details below). All `docs/` content is untouched and fully compatible.

### Upgrade at a glance (existing installs)

- **Your memory store auto-migrates, backup-first, on first activation.** Mac detects the old v1 store, backs it up (directory **and** tarball), and migrates it in place before doing anything else. Nothing is lost; rollback is restoring the backup. No manual steps. (Full detail under "Automatic, safe v1→v2 sidecar upgrade" below.)
- **`docs/` is unchanged** — band profiles, the songbook, the voice-context file, `mac-preferences.md`, playlists, and WIPs all keep working exactly as before. The migration only reshapes the memory store under `_bmad/_memory/band-manager-sidecar/`.
- **Re-run `suno-setup`** after updating, so the new `suno-playlist-sequencer` skill gets linked and the capability menu picks up its **[PS] Sequence Playlist** entry.
- **Version reconciliation:** the module version, `.claude-plugin/marketplace.json`, and `package.json` were all aligned to `2.0.0` (they had drifted to 1.8.3 / 1.7.2 / 1.6.7 respectively).

### The workflow skills → BMB v2 standard

All five non-agent skills (`suno-band-profile-manager`, `suno-style-prompt-builder`, `suno-lyric-transformer`, `suno-feedback-elicitor`, `suno-setup`) were brought to the BMB v2 bar — graded against the same `skill-quality-principles` the builder validates against, then remediated end-to-end across two passes (standard conformance, then the opportunity findings).

- **Path + structure hygiene** — bare skill-root paths throughout (the old `./references/…` / `./scripts/…` forms are gone), a stamped `## Conventions` block in every skill, and the canonical source-tree shape.
- **v2 customization surface** — each creative skill ships a minimal `customize.toml` (`persistent_facts` glob + activation hooks) with the resolver activation step; hardcoded writable paths now reference the existing `band_profiles_folder` / `songbook_folder` config variables instead of literals.
- **Headless contracts** — `status` / `reason` / `decision_log` discipline across the skills so an automated caller gets a machine-readable result, not prose.
- **Decision-Log Workspaces, open-floor openings, and expert quick-win lanes** added where a skill produces a revisable artifact or runs a guided conversation.
- **Determinism pushed into scripts** — character/critical-zone/trigger validation, genre-signal detection, syllable/section counting, and the dangerous-word / scream-trigger tables now live in tested scripts (and shared constants in `_shared/suno_constants.py`), leaving the prompts the judgment calls only.
- **Script hygiene** — PEP 723 inline deps, structured JSON output, exit codes, and unit tests across the script layer.
- **Agent-shape removed from workflow surfaces** — the `Identity` / `Communication Style` / `Principles` blocks were folded into Overview/design-rationale on the skills where they were re-teaching LLM-native behavior (and preserved where the voice genuinely serves the craft).

Defects fixed in the same effort:

- **Lyric Transformer** — the headless contract and the compaction-survival state marker required a `sha256` that no script computed (an LLM can't produce one by hand, so the field was being fabricated or skipped, silently breaking the change-tracking that refinement and version-bumping key on). `analyze-input.py` now emits it from stdlib `hashlib` and the workflow reads it from the JSON.
- **Lyric Transformer** — `validate-options.py` / `assemble-summary.py` carried a `CODE_DESCRIPTIONS` table that had drifted from `SKILL.md`'s canonical option codes (the `RE` rhyme-enhancement code was being outright rejected as invalid). Reconciled, with a drift-guard test so it can't silently diverge again.
- **Band Profile Manager** — interactive Create was hand-serializing the profile YAML, contradicting the new "never hand-serialize — `apply-profile.py` owns the write" invariant; Create now routes through the same deterministic writer as Edit/Duplicate. Output paths became config-var-driven through the scripts (`--profiles-dir` / `--docs-dir`, backward-compatible). The schema gained an optional `voices:` list so the documented multi-Voice strategy has a real structural home, and the model-preference enum was corrected (bare `v5.5` → `v5.5 Pro`, the value the validator actually accepts).

### New skill — `suno-playlist-sequencer`

The album/playlist-sequencing apparatus — the album-craft methodology plus the `playlist-sequencing-data.py` / `batch-full-analysis.py` librosa scripts — was **extracted out of `suno-feedback-elicitor` into its own skill.** The principle: a lean agent orchestrates, and each workflow owns one job — single-song feedback and album sequencing are different jobs. `suno-feedback-elicitor` is now cleanly single-song scope; Mac routes album/tracklist work ("sequence my playlist", "order my album", "plan my tracklist") to the new skill. The shared `STUDIO-EDITOR-REFERENCE.md` (referenced by three skills) also moved to `_shared/references/` so no workflow reaches into the agent's internals.

### Mac → BMB v2 autonomous sanctum agent

The Mac agent was rebuilt to the v2 agent standard. The builder's detector now correctly recognizes Mac as a memory/autonomous agent — it previously mis-classified him as *stateless*, because he shipped no `agent_type` and no `assets/` templates despite running a heavily-exercised bespoke memory store.

- **Declared identity** — a metadata-only `customize.toml` `[agent]` block with `agent_type = "autonomous"` (Mac is a memory agent **with** PULSE).
- **v2 sanctum vocabulary** — the memory store is now `INDEX.md` (a thin map) / `MEMORY.md` (curated) / `PERSONA.md` / `CREED.md` / `BOND.md` / `CAPABILITIES.md` / `PULSE.md`, scaffolded by a new `init-sanctum.py` from `assets/*-template.md`.
- **Bounded memory (the big practical win)** — a two-tier model: raw per-session logs live in `sessions/YYYY-MM-DD.md` (not loaded on rebirth) and are curated up into a tight `MEMORY.md`. The always-loaded store dropped from **533 lines / 145 KB** (≈48× its own health threshold — perpetually red and ignored) to a curated **~100 lines**; the memory-health check is GREEN again.
- **Sharded CREED** — a slim always-loaded core (Mission, the Three Laws, the Sacred Truth, and the Package Assembly Rule core, all marked INVARIANT) plus capability-scoped discipline shards loaded on demand and a non-loaded incident-narrative log. The root `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` standing-orders now defer to the agent's own `activation.md` instead of force-loading the full ~12 K-token authored creed on every activation — recovering that cost per rebirth while keeping the Package Assembly guarantee true (the rule lives in the always-loaded core).
- **Headless + a narrow autonomous PULSE** — the headless route SKILL.md had only advertised is now actually implemented (per-capability contracts + structured returns), and a tightly-scoped maintenance PULSE was added: on an autonomous wake it validates the store and refreshes derived sections and **reports-and-stages** for the next session — it never edits creative content (Law 3 is a hard line).
- **Wired-in tooling + craft fixes** — the built-but-unused `genre-coverage.py` is now wired into the publish path and the catalog-verification self-check; a species-mission line and save-as-you-go First-Breath resilience were added; and a published-track name that had leaked into the refine template was replaced with a placeholder.
- **The bespoke machinery was preserved, not regressed** — `validate-sidecar.py`'s integrity checks, the post-unpack `reconcile` gate, ground-truth derived-section regeneration, portable cross-machine sync, the loaded-first `access-boundaries.md`, and the fixed New-Orleans persona all carry forward intact. This was selective adoption of the v2 *shape* on top of the bespoke *rigor* — not a rip-and-replace.

### Automatic, safe v1→v2 sidecar upgrade on first activation

Before this change, an existing user updating to the v2 version hit a gap: their
`band-manager-sidecar/` directory already existed (in the old v1 layout), so
activation treated it as "not a first run," tried to load the 7 v2 files, found
them absent, and fell into the "damaged sanctum → offer re-scaffold" fallback — a
fresh empty sanctum that would orphan the user's real `index.md` memory. Nothing
auto-migrated.

Now:

- **`pre-activate.py` distinguishes four sidecar states** instead of a single
  first-run boolean: `absent` (no dir → genuine first run → scaffold), `v1` (dir
  with the old `index.md`, no v2 markers → needs migration), `v2` (`MEMORY.md`
  present → normal load), and `damaged` (dir with neither `index.md` nor
  `MEMORY.md` → re-scaffold fallback). It emits `sidecar_format` and
  `needs_migration` in its JSON. `first_run` is retained for back-compat (it
  equals the `absent` case).

- **On first activation after updating, Mac auto-detects the pre-v2 store and
  upgrades it backup-first.** Interactive: Mac tells you he found a memory store
  from a previous version and offers to upgrade it ("want me to upgrade it now?
  I'll back it up first"); on yes he runs the upgrade and tells you where the
  backup landed. Headless: the upgrade runs automatically (backup-first, no
  prompt) before routing.

- **The upgrade is backup → migrate → verify → swap, with abort-on-loss.**
  `migrate-sidecar-to-v2.py --in-place` copies the live sidecar to a timestamped
  `.sidecar-backup-pre-v2-{YYYYMMDD-HHMMSS}/` directory **and** a matching
  `.tar.gz` before touching anything, migrates into a temp staging dir, and runs
  the content-accounting verify. It only swaps the new layout into the live
  location if verify passes with **all** source content present. If verify can't
  account for any content, it ABORTS — no swap, the original is left fully intact
  (Law 3: never lose content). It's idempotent: an already-v2 store is a no-op, an
  absent sidecar is a no-op, safe to re-run.

- **Rollback is trivial:** restore the timestamped backup directory (or extract
  the tarball) over `band-manager-sidecar/`. Both live right next to the sidecar
  under `_bmad/_memory/`.

### Compatibility notes

- **`docs/` files are unchanged and fully compatible.** Band profiles, the
  songbook, the voice-context file, `mac-preferences.md`, playlists, and WIPs all
  live under `docs/` and are untouched by the sanctum migration — the upgrade only
  reshapes the memory store under `_bmad/_memory/band-manager-sidecar/`.

- **An old portable-sync archive unpacked on the new version is also caught.** If
  you unpack a pre-v2 sync archive (its sidecar is in the v1 layout), the v1 store
  is detected and migrated on the next activation, the same backup-first way —
  nothing special to do.

### What to verify after upgrade

Once Mac reports the upgrade is done, the store should come up clean:

- `python3 scripts/validate-sidecar.py` → **PASS** (no errors against songbook /
  band-profile ground truth).
- `python3 scripts/check-memory-health.py <sanctum-path>` → **GREEN** (file sizes
  within v2 thresholds).

If anything is off, your original store is in the timestamped backup — restore it
and report the issue.

## [1.8.3] - 2026-06-08

### Highlights

A tooling patch from a production session: a lyric-transformer section-tag fix that was breaking song structure, plus a new genre-coverage index that grounds "what has this band done / what's actually fresh" in a maintained source of truth instead of the agent's memory.

### Lyric Transformer — intensity words are NOT section tags (`[Heavy]` intro-skip fix)

Added to `src/skills/suno-lyric-transformer/references/metatag-reference.md`. A production session surfaced that `[Heavy]` — an intensity/feel word used as a section header — is not a recognized Suno section tag and **mis-parses the song structure**: Suno skipped the `[Intro]` entirely and started on the `[Heavy]` section on multiple generations. The transformer's validator (`validate-lyrics.py`) had flagged `[Heavy]` as unrecognized on every build, but the flag had been overridden because the tag once appeared in an older songbook entry. Changing it to `[Verse]` made the structure parse correctly.

The rule added: intensity/feel words (`[Heavy]`, `[Loud]`, `[Soft]`, `[Quiet]`) are never section tags — carry the intensity via descriptor tags (`[Energy: ...]`, `[Vocal Style: ...]`) on a recognized section, or use `[Bridge]` when the section needs to be harmonically/energetically new. **If the validator flags a section tag as unrecognized, it is invalid — map it to a recognized tag; do not override the flag because it appeared in an old entry.**

### New — `genre-coverage.py`: per-band genre coverage index

Added `src/skills/suno-agent-band-manager/scripts/genre-coverage.py`. Generates a per-band coverage map (`docs/{band}-genre-coverage.md`) of genre anchors AND artist/reference territory, derived from every published style prompt **and the band-profile catalog** (`reference_tracks` + per-song `genre_applied`) with hard filters against stat/lyric noise. The point: ground every "X is fresh / never done / let's add some variety" claim in a maintained, source-derived index instead of the agent's memory — which had repeatedly produced wrong novelty claims (asserting a genre was new to a band when the catalog already covered it under an artist label, e.g. "90s alt" living as Counting Crows / Wilco). Regenerate on every publish, alongside the playlist sequencing companion.

## [1.8.2] - 2026-06-07

### Highlights

A slider-discipline patch for the Style Prompt Builder. A production session surfaced the builder anchoring its Weirdness / Style Influence recommendations to a band profile's stored `sliders:` default instead of choosing per-song from slider behavior — which defeats the entire purpose of the sliders as the per-song differentiator.

### Style Prompt Builder — sliders are a per-song decision, not a profile default (fix)

Added to `src/skills/suno-style-prompt-builder/references/model-prompt-strategies.md` (Slider Guidelines). During a metal-lane build, the builder recommended Weirdness 55 by reasoning *"above the profile's 45 default"* — anchoring to the band profile's stored slider value rather than the song's needs. The song was a dissonant, harmonically-locked, counter-genre piece that actually wanted Weirdness ~75: high enough to stop Suno normalizing the dissonance back toward polished heaviness (the documented default-Weirdness counter-genre behavior), capped under the 80 structural-breakdown cliff to protect a load-bearing `[End]`. The user's direction was emphatic: never rely on a presumed band default — the sliders are where per-song differences get made, and they are meant to be used.

The rule: a band profile's stored `sliders:` values (if any) are a weak fallback for a bare Demo only — never the per-song anchor, and never a baseline to nudge up/down from. For every real song, Weirdness and Style Influence are chosen fresh from the slider-behavior table + song type + counter-genre needs, justified by what each slider actually does. Audio Influence remains the one slider commonly left at a standard value (~25% for Personas).

Known follow-up (not in this patch): band profile YAMLs that carry stale `sliders:` defaults (e.g. a stored `weirdness: 45` in a catalog that actually runs 55–75) should be corrected via the band profile manager so they stop misanchoring future builds.

## [1.8.1] - 2026-05-08

### Highlights

A discipline-rule patch. Two new rules added to the agent's creed after production sessions surfaced two distinct corruption pipelines for durable files. Both rules are sister disciplines to the existing Workshop Capture Discipline (v1.8.0) — same family of fidelity rules, different triggers.

### Hedge Preservation Discipline — Match the User's Certainty Level, Don't Promote It (NEW behavioral rule)

Added to `src/skills/suno-agent-band-manager/references/creed.md` after a sixth-instance discipline failure 2026-05-08. A user shared a hedged production observation — in shape, *"it seemed like the hyphenated form was more consistent at holding that as a longer note."* Two hedges in one sentence (SEEMED, plus MORE CONSISTENT, comparative). The agent captured it into a durable findings file as *"the hyphenated form DOES hold the vowel… reliably worked"* — promoting both hedges to firm assertions in a single summarization pass. The user caught the promotion, and the deeper pattern behind it: summarization that firms up hedged language is not helpful polish, it is a change of meaning, and users who communicate precisely experience it as a recurring friction.

The rule preserves the user's hedge level verbatim when reflecting back, summarizing, or capturing to durable file. Hedges (*seems to*, *appears to*, *more consistent*, *in cases like*, *sometimes*, *my impression is*) are scope markers, not politeness markers — promoting them changes the meaning. The mechanical step before any durable write: identify each hedge in the source language, confirm the destination text preserves each hedge verbatim. **Quote rather than paraphrase** when capturing user observations; verbatim quotes inside formatted blocks with date attribution let the user's certainty level travel through quotation losslessly.

A module-wide audit pass fixed approximately 33 hedge-promotion findings across 18 files (songbook entries, dossier preamble, sidecar narrative, the voice-context file, suno-production-patterns, model-prompt-strategies, metatag-reference). Notable corrections:

- **Bass-forward Suno limitation reframed** from categorical *"Suno cannot reliably produce bass-forward rock or metal"* to scoped *"On Suno v5.5, our prompt approaches have not produced bass-forward rock or metal mixes — whether this is a model-level limitation or a prompt-strategy limitation we haven't cracked is not yet established."* The scoping came from the user's own hedged phrasing — that it *seemed*, at least on v5.5, that bass-forward never worked with the prompts tried, and that this was all that could reliably be said. Same scoped wording propagated across all module locations for consistency.
- **Dossier preamble rewritten** to declare every entry's top-block as Mac synthesis by default (3-tier authority hierarchy mirroring the creed). Higher-leverage than annotating ~25 individual entries with "Mac reading:" prefixes.
- **N=1/N=2 promotions softened** catalog-wide: "CONFIRMED" → "single-song observation," "validated" → "working hypothesis," "always include" → "default ingredient," "the rule" → "tendency observed."
- **Corrected thematic framing propagated** to both bands' versions of one track (an agent-authored misread had been overriding the writer's own framing).
- **Dossier corrections propagated verbatim** (speakers / letters / title-as-metaphor) into both bands' songbook entries for a second track.
- **Affirmation-theme paragraph added** to a third track's entries, correcting a "regret-shaped" misread.
- **Verbatim/synthesis split** applied to a fourth entry, with "Mac reading:" attribution separating agent interpretation from the writer's words.

### Document State Marker Discipline — Top-of-File Pointers Must Reflect Current State (NEW behavioral rule)

Added to `creed.md` as a sister rule to Workshop Capture Discipline after surfacing on a second machine following a sync. The recovery pass wrote seven verbatim workshop swings into that song's WIP fragments.md` under a properly-labeled new section. Workshop Capture Discipline was satisfied — the verbatim content was there, fully labeled, with critique. But the file's top-of-file structure still carried `## Architecture committed` and `## Current draft` as authoritative live-state labels for the older session's material. When a fresh Mac opened the file after sync, it read top-down, hit those labels as authoritative, treated those sections as the workshop's current state, and never scrolled past them to find the recovered swings. The user reported: *"the top of the file has 'current draft' with the information it last had that your swings section was not labeled in a way where it would bother looking past the 'current draft' section."*

The corrected understanding: Workshop Capture is necessary but not sufficient. Saving verbatim content is a different operation from updating the structural pointers that tell readers where the verbatim content lives. Both must happen in the same edit. The mechanical step: identify all top-of-file state markers, relabel each as superseded with a pointer to the active section, OR relocate the label to the new active section, OR add a top-of-file callout pointer. Verify with a fresh-reader test — re-read the file from line 1 as if you've never seen it before; if you reach the new active material without being misled, done.

The affected WIP file was restructured per the new rule as part of this patch: `## Architecture committed` → `## Architecture committed (earlier session — superseded; preserved for reference)`; `## Current draft` → `## Earlier draft (superseded — see the later session section below for the active workshop state)`; top-of-file callout block added pointing at the active section.

### Why both rules matter

Workshop Capture (v1.8.0), Hedge Preservation, and Document State Marker form a three-rule family protecting durable-file integrity. Workshop Capture says *save the verbatim content to the durable file.* Hedge Preservation says *preserve the user's certainty level when capturing observations.* Document State Marker says *and update the structural pointers so the verbatim content is findable.* All three fire on different triggers and check different things, but they're the same family of fidelity rules. Each rule was added after a specific documented failure case in production. Together, they close three of the failure modes that turn a durable workshop or reference file into a corrupted record over time.

## [1.8.0] - 2026-05-06

### Highlights

A consolidation release. Three months of post-v1.7.2 work bundled together: the multi-machine audio drift class fully closed (manifest tooling shipped + robustness pass after production false positives), the Suno-doesn't-actually-shift-tempo foundational principle propagated through the prompt + lyric reference docs, a sweeping module reference cleanup that fixed eight propagation gaps and removed seventeen narrative-cruft passages, and a new **Thematic Discipline** rule across the agent's creed and the playlist sequencing methodology that forbids inferring song themes from titles or fragments — read the full songbook entry or don't make the claim.

### Thematic Discipline — Read the Songbook Before Making Thematic Claims (NEW behavioral rule)

A new mandatory discipline added to two reference docs after a production session surfaced a pattern of inverted thematic reads from title/fragment inference. Mac kept making placement recommendations and thematic-cluster claims based on what songs *seemed* to be about from their titles, surface imagery, or lyric fragments pulled out of context — and getting them inverted at high rates. Most embarrassing example: pulling a single "I never made it big"-shaped line from a track and labeling it "regret-shaped" when the song's full statement was the OPPOSITE — pride in the choice, an affirmation whose title means "I'd be damned if I DIDN'T live this way."

Other documented inverted reads now in the discipline rule as warning examples (titles genericized for the public repo — the rule carries illustrative title/meaning pairs rather than catalog specifics):
- A title suggesting regional decline → actually a moral-complicity metaphor
- A title suggesting funeral weight → actually a theatrical horror piece
- A title suggesting cemetery imagery → actually narrative misdirection, where the loss is a departure rather than a death
- A title suggesting observation → actually a contentment thesis
- A title suggesting longing → actually a legacy concern

The two doc updates:

- **`src/skills/suno-agent-band-manager/references/creed.md`** — new "Thematic Discipline" section after Research Discipline. Loaded on every Mac activation. Forbids title/fragment inference. Lists documented inverted-read examples. Mandatory rule: "if there isn't time to read the songbooks properly, there isn't time to make the thematic claim."
- **`src/skills/suno-feedback-elicitor/references/playlist-sequencing-methodology.md`** — added MANDATORY thematic-verification step (new step 4 in the playlist review process) and full "Thematic Verification" section with the same documented misreads + Mac discipline rules. The methodology already named theme as a placement variable; this addition makes Mac actually verify the theme by reading instead of inferring.

**Why it matters:** poets don't telegraph. The songbook entry — which carries the lyrics in full context, the writer's stated intent, and the catalog notes — is the authoritative source for what a song does. A title or a fragment is a bad summary, and surface inference produces wrong reads at high enough rates to need a hard rule.

### Module Reference Documentation Cleanup — Update Gaps + Leanness Pass

A `/bmad-module-builder validate` audit pass found eight propagation gaps where upstream corrections hadn't reached all downstream reference docs, and a systemic pattern of narrative cruft ("Why this file exists" subsections, post-correction residue, supersession framing) that read more like commit messages than operational reference. Fixed in a single pass.

**Update gaps closed:**

- **Voice Gravity → Voice-Character correction propagation** — the v1.7.0 correction (`Voice clones don't carry trained genre gravity; they capture vocal character that Suno adapts to the genre prompt`) had landed in `model-prompt-strategies.md` but missed `profile-schema.md`, where the band-profile-creation guidance was still emitting the retracted "trained genre gravity" framing into every new band profile. Profile-schema's six Voice-aware rules rewritten to use the corrected mechanic. Residue references in `creed.md` ("Voice Gravity rules" → "Voice-Character rules") and `refine-song.md` ("voice gravity setting" → "Voice character settings") corrected too.
- **Feedback-elicitor coverage of v1.7.1+v1.7.2 audio-analysis evolution** — the JSON archive layer + companion auto-refresh (v1.7.1) and the audio-files-manifest + verify-audio-files multi-machine drift tooling were silent in this skill's own docs even though the scripts live inside it. Added to `SKILL.md` Scripts section, `references/README.md` Scripts table, and `references/gemini-audio-analysis.md` librosa-script invocation guidance.
- **Tempo-shift finding propagation** — the Suno-doesn't-actually-shift-tempo principle (now in `metatag-reference.md` and `model-prompt-strategies.md`) was missing from `suno-parameter-map.md`, `suno-style-prompt-builder/SKILL.md`, and `SUNO-REFERENCE.md`. Added.
- **`create-song.md` Parallel Execution Pattern** — flipped to Agent-primary per the v1.7.0 creed update. Skill tool removed as primary because Agent is the correct tool for headless skill invocation (context isolation requirement for Step 4 — Suppress intermediate skill output).

**Leanness pass — narrative cruft removed across multiple files:**

- "Why this file exists" / "Why this convention exists" subsections in `profile-schema.md` and `reconcile.md` removed. The schema and the convention itself are the existence proof; self-justification adds narrative without action.
- Post-correction residue ("a prior version of this doc said X, but that was overstated") in `model-prompt-strategies.md` and `metatag-reference.md` removed. Reference docs should describe what IS, not the journey.
- Supersession framing ("this supersedes earlier guidance") restructured to keep the diagnosis without the commit-message frame.
- "Last validated" change-history enumerations in `model-prompt-strategies.md` and `suno-parameter-map.md` trimmed.
- Audit meta-commentary in `save-memory.md` ("This audit should normally find nothing" / "Layer 1 of the WIP-sync fix" jargon) replaced with one-line action.
- Trailing observation-date narrative in `creed.md` removed.

Plus: the agent-internal `references/README.md` ASCII architecture chart converted to mermaid (matching the top-level README's mermaid conversion). 25 edits across 14 files; 0 findings on re-validation.

**Why this matters for the marketplace install:** the corrections that landed upstream weren't reaching every downstream doc; new band profiles were still being created with retracted Voice Gravity framing. Single-pass cleanup propagates everything correctly across the module's reference layer.

### `verify-audio-files.py` — Robustness improvements (v1.2.0)

Two robustness improvements after production use on a multi-machine multi-band project surfaced false positives.

**Filename normalization (v1.1.0):** Pure string-equality matching against manifest filenames produced false positives when the same audio existed under different filename conventions across machines — `Foo.mp3` vs `Foo-Redux.mp3` vs `Foo (NSFW).mp3`, em-dash vs ascii hyphen vs equals-sign-as-separator, repeated underscore-hyphen runs. Verifier now normalizes filenames for fuzzy song-identity matching (strips version qualifiers like `-Redux` / `-v2` / `-alt`, parentheticals, normalizes unicode dashes/equals, collapses repeated separators, lowercases). Band suffixes are explicitly NOT normalized away because they distinguish different bands' gens of the same poem (e.g. `Song Title.mp3` from one band vs `Song Title-Acoustic.mp3` from another are different audio files of the same lyrics). When a fuzzy match is used, the result includes `filename_variant: true` and a `local_filename` field so users can choose to standardize.

**Size tolerance (v1.2.0):** Suno's MP3 downloads carry per-download ID3 metadata variance (timestamps, cover art presence, encoded-by strings) that produces small byte differences across machines and download events even for the SAME audio gen. Production-confirmed 2026-05-02: fresh re-downloads from Suno of the same canonical gens still differ from the canonical-machine manifest by ±44 to ±500 bytes for most tracks. Without tolerance, every track flagged as `size_mismatch` after sync. New `--tolerance-bytes` flag (default 1024) absorbs this metadata noise; matched entries within tolerance include a `delta_bytes` field and `within_tolerance: true` so the variance is visible without escalating to mismatch. Real different gens typically differ by tens of KB or more (cover art differences register around 10-60KB; full re-renders register much larger).

**Net effect on a real project (66-file catalog):** Without v1.1+v1.2 fixes, `verify-audio-files.py` reported 28 size_mismatches + 6 missing + 5 extras (false-positive heavy). With both fixes: 4 real size_mismatches + 1 missing + 2 extras. The 4 remaining mismatches are real different gens worth surfacing; the 1 missing is a deliberately-not-on-this-machine file; the 2 extras are stale local files superseded by re-downloads at different canonical filenames. Substantially less noise; substantially more actionable.

### Multi-Machine Audio File Verification — `audio-files-manifest.py` + `verify-audio-files.py`

Closes the multi-machine audio drift class observed 2026-04-29: one machine's local copy of a track analyzed as 4:34 / C minor / 143.55 BPM while the version published from the other machine was 3:49 / D# minor / 95.7 BPM — a different generation under the same canonical filename. Audio MP3s are too large to ship in the portable-sync archive (small-files tar.gz), so they stay machine-local; this means two machines can have different audio for the same playlist filename without anything detecting it. v1.7.1's per-song JSON archive layer can surface mismatches once both machines have analyzed every song, but creating those archives is on-demand and the JSONs themselves don't carry a file-identity field.

Two new scripts in `src/skills/suno-feedback-elicitor/scripts/`:

- **`audio-files-manifest.py`** — generates `docs/audio-files-manifest.yaml` with `name + size_bytes + mtime_iso` for every audio file in `docs/audio/`. Default output is YAML to disk; `--stdout` prints to stdout, `--format json` outputs JSON, `--audio-dir`/`--output` accept overrides. Run on the canonical machine after publishes/regens. Manifest travels in the portable sync archive (small, well under 100 KB even for hundreds of tracks).

- **`verify-audio-files.py`** — reads `docs/audio-files-manifest.yaml`, walks `docs/audio/`, reports three failure modes as JSON: `missing` (manifest entry has no local file), `size_mismatch` (local file exists but bytes differ — different gen), `extra` (local file with no manifest entry — orphan/abandoned gen). Optional `--playlist-context` flag joins per-band playlist YAMLs in to enrich each mismatch entry with playlist position so the report can be presented in playlist order. Exit code 0 if all match, 1 if mismatches detected, 2 on errors.

**Why size, not hash:** size is fast (single `os.stat`, no read), and Suno gens are byte-for-byte non-deterministic across re-encodings — file size is a high-confidence mismatch detector for the "different gen of same song" case without the cryptographic-checksum overhead. We don't need a security guarantee; we need a reliable "did the audio change?" signal.

**Why not extend per-song JSON archives with file size:** that path requires every song to have an existing per-song JSON, which currently gets created only on-demand when a song is analyzed (one of 64 LV+SF tracks has a per-song JSON locally). A separate single-file manifest is simpler to bootstrap and verify against, and it doesn't depend on having previously run deep analysis on every track.

`portable-manifest.example.yaml` updated with `docs/audio-files-manifest.yaml` in the playlist-artifacts section so users adding the multi-band patterns also pick up the audio manifest pattern.

**Workflow:**
1. On canonical machine (whichever has the latest published audio after each publish/regen): `python3 audio-files-manifest.py PROJECT_ROOT`
2. Pack portable sync — manifest travels with it
3. On non-canonical machine after unpack: `python3 verify-audio-files.py PROJECT_ROOT --playlist-context`
4. Report lists which files are missing, wrong-gen, or extra; user re-downloads the wrong-gen files from Suno

### `portable-manifest.example.yaml` — Updated for v1.7.1 + v1.7.2 file patterns

The example manifest now suggests per-band playlist YAML pattern, per-band sequencing companion pattern, and the v1.7.1 audio-analysis JSON archive directory in its commented-out playlist artifacts section. Users who copied earlier versions of the example to their own `portable-manifest.yaml` should review the updated example and add the new patterns — without them, the per-band YAMLs (v1.7.2), the auto-refreshed sequencing companions (v1.7.1+v1.7.2), and the JSON archives (v1.7.1) won't sync between machines and you'll see the same drift class the architecture was designed to fix.

The new generic patterns (`docs/*-playlist.yaml`, `docs/*-playlist-ordering.md`, `docs/*-playlist-sequencing.md`, `docs/audio-analysis/**/*.json`) work for any current or future band — no need to enumerate each band by name.

### Suno Knowledge — Foundational Principle: Suno Does Not Actually Shift Tempo Within a Song

Production-confirmed 2026-04-29 across multiple catalog tracks whose style prompts explicitly requested "tempo changes" or "tempo shifts". librosa-measured BPM is steady end-to-end despite clear felt-shifts between lucid and dense sections. **What Suno actually produces** when a prompt asks for tempo shifts is **arrangement-density variation** — instrumentation pullback to create a halftime *feel*, compression to create a double-time *feel* — not actual BPM changes. The underlying tempo stays absolutely constant.

This refines existing guidance that already documents "Suno delivers a single steady BPM per song" by making the foundational claim explicit: **"tempo changes" / "tempo shifts" in style prompts are arrangement directives, not tempo directives.** The practical implication is that prompt builders and lyric transformers should plan for one underlying BPM per song and use rhythm nouns + density framing to vary perceived feel within that fixed grid.

- **`src/skills/suno-lyric-transformer/references/metatag-reference.md`** — added a "Foundational principle" paragraph in the Tempo Control section explicitly framing this. Adds production-confirmation reference and points to the `audio-analysis-reference.md` Felt BPM Corrections table for catalog examples.
- **`src/skills/suno-style-prompt-builder/references/model-prompt-strategies.md`** — extended item 15 (Perceived tempo is controlled through lyrics) with the same foundational-principle framing and the practical implication that "tempo changes" in a style prompt is an arrangement directive, not a tempo directive.

### Net effect of v1.8.0

Multi-machine projects can now reliably detect audio drift after sync (manifest tooling + robustness). The Suno-doesn't-actually-shift-tempo principle is propagated everywhere it's relevant. The module's reference docs are aligned across upstream corrections — no more orphaned retracted framings. And Mac has a hard rule against surface-inference of song themes. The module ships with a tighter, more honest reference layer.

---

## [1.7.2] - 2026-04-29

### Multi-Band Architecture — Per-Band Playlist YAML as Single Source of Truth

Closes a multi-band drift problem discovered while reviewing a project's second band's playlist: the first band had a per-band playlist YAML as its single source of truth, but the second band never had one. LV's track sequence got duplicated across the band profile YAML's `playlist:` block, voice-context narratives, sidecar references, and was different in each location — drifting independently as new tracks published. The module convention had not picked a winner; per-band YAML was the right answer but wasn't documented or scaffolded.

A second symptom: `playlist-sequencing-data.py --companion` wrote to a single global path `docs/playlist-sequencing-data.md`, so running the script for two different bands meant the second run overwrote the first.

A third symptom: project-specific band names were hardcoded in `validate-sidecar.py` and `regenerate-index-sections.py` band-display lookups — module users with different band names would not see correct output.

### Added — Module Code

- **`src/skills/suno-band-profile-manager/scripts/scaffold-playlist.py`** (new) — bootstraps a `docs/{band-slug}-playlist.yaml` for a band. Default mode writes an empty template; `--from-songbook` pre-populates track names from the band's existing songbook entries (audio filenames left as TODO). Solves the multi-band onboarding gap for both new bands (created via the profile manager) and existing bands (which can self-heal if they pre-date this convention).

- **`src/skills/_shared/companion_writer.py`** — canonical companion path resolution becomes per-album for scripts whose output is per-album (currently `playlist-sequencing-data`). `CANONICAL_COMPANION` entries can now be either a fixed string (catalog-wide scripts) or a callable that takes the album name and returns the path. `resolve_companion_path()` accepts an optional `album` argument; passes it to the callable. Apostrophe-aware slugify handles names like "Rider's Hymn" → `riders-hymn`.

- **`src/skills/_shared/json_archiver.py`** — `_slugify()` strips apostrophes (straight + curly) before the alphanumeric replace so a name like "Rider's Hymn" → `riders-hymn` instead of `rider-s-hymn`.

- **`src/skills/suno-feedback-elicitor/scripts/playlist-sequencing-data.py`** — passes album name to `resolve_companion_path()`. Companion now writes to `docs/{band-slug}-playlist-sequencing.md` instead of the single global `docs/playlist-sequencing-data.md`. Multiple bands no longer overwrite each other.

- **`src/skills/suno-band-profile-manager/scripts/validate-profile.py`** — adds a check: if the band has any songbook entries at `docs/songbook/{band-slug}/`, then `docs/{band-slug}-playlist.yaml` MUST exist (helpful fix message points to scaffold-playlist.py). Also flags the deprecated in-profile `playlist:` block with a migration message. Bumped to v2.1.0.

- **`src/skills/suno-agent-band-manager/scripts/validate-sidecar.py`** — band-name → slug mapping is now derived dynamically from `docs/band-profiles/*.yaml` files at runtime instead of a hardcoded dict. Generic across projects.

- **`src/skills/suno-agent-band-manager/scripts/regenerate-index-sections.py`** — same fix: replaced hardcoded `BAND_DISPLAY` dict with a runtime `band_display_map(project_root)` function that derives display names from band profile YAMLs. Falls back to a Title-Cased version of the slug when a profile is missing or doesn't carry a `name:` field.

### Added — Module Documentation

- **`src/skills/suno-band-profile-manager/references/profile-schema.md`** — new "Per-Band Playlist YAML" section documents the file convention (`docs/{band-slug}-playlist.yaml`), schema (album + tracks: name, file), bootstrapping via scaffold-playlist.py, auto-creation expectation on band profile creation, deprecation of the in-profile `playlist:` block, and workflow rules (publish/reorder/remove all touch this file in same write batch).

- **`src/skills/suno-band-profile-manager/SKILL.md`** — band creation flow now explicitly includes the playlist YAML scaffolding step ("Scaffold the per-band playlist YAML in the same write batch").

- **`src/skills/suno-feedback-elicitor/references/playlist-sequencing-methodology.md`** — added "Per-Band Playlist YAML" section establishing the canonical input file convention, scaffolding command, and per-band auto-output paths.

- **`src/skills/suno-agent-band-manager/references/capabilities.md`** — added a "Per-band playlist YAML convention" subsection clarifying that multi-band projects keep each band's playlist independent at `docs/{band-slug}-playlist.yaml` and produce per-band auto-outputs that don't collide.

- **`src/skills/suno-agent-band-manager/references/reconcile.md`** — authoritative source table updated: playlist order & track numbers authoritative source becomes `docs/{band-slug}-playlist.yaml` (was: ordering doc). Stale-reference search location list now explicitly includes the canonical YAML, the script-generated companion, and notes the band profile YAML must NOT carry a `playlist:` block.

- **`src/skills/suno-agent-band-manager/references/save-memory.md`** — passive "did the playlist YAML get updated" check converted to enforced "REQUIRED, not optional — the per-band playlist YAML is the single source of truth for the band's sequence; not updating it means the next session pulls a stale playlist."

- **`src/skills/suno-agent-band-manager/references/creed.md`** — new **Multi-Band Discipline** principle: each band has exactly one canonical `docs/{band-slug}-playlist.yaml`; all other playlist references derive from or reference this file rather than duplicating its track list. Activation-loaded for Mac so the rule fires on every session.

### Why two releases in two days

v1.7.1 (yesterday) shipped JSON archives + auto-refreshing companion docs to close one drift class (script output never written back to canonical companion). The fix worked for single-band projects but exposed a multi-band class: companion paths weren't per-album, and the broader convention question (should each band have its own playlist YAML, and how does a new band get one?) wasn't answered. v1.7.2 closes that gap structurally rather than waiting until accumulating more entries.

---

## [1.7.1] - 2026-04-29

### Audio Analysis — Persistent JSON Archives + Auto-Refreshing Companion Docs

Closes a long-running drift problem where audio-analysis script output never made it back to the canonical companion `.md` files. Sessions ran `playlist-sequencing-data.py` / `batch-full-analysis.py` / `analyze-audio.py`, used the JSON for the immediate question, and never refreshed the human-readable summary docs. Sync-archive carried the stale `.md` files between machines, so a fresh laptop session would pull a version of "the catalog state" months out of date and have to re-run analyses that had already been done. Today's desktop session diagnosed this when `docs/playlist-sequencing-data.md` was 35 days old and missing all four 2026-04-29 SF regens.

**Two new layers, both default-on:**

1. **JSON archive layer** — every analysis script now writes its full structured output to a persistent path under `docs/audio-analysis/`. The archives are the durable raw-data layer; future sessions can read the archive directly instead of re-running the script to ask a different question of the same audio. Layout:

   ```
   docs/audio-analysis/
     songs/<song-slug>.json          ← audio-deep-analysis.py per-song archive
     playlists/<album-slug>.json     ← playlist-sequencing-data.py per-playlist archive
     catalog/<YYYY-MM-DD>-summary.json   ← analyze-audio.py dated catalog snapshot
     catalog/<YYYY-MM-DD>-deep.json      ← batch-full-analysis.py dated catalog snapshot
   ```

2. **Companion `.md` auto-refresh layer** — every analysis script that has a canonical summary doc now refreshes it automatically. The doc is rewritten between `<!-- AUTOGEN-START: ... -->` / `<!-- AUTOGEN-END -->` markers; hand-curated content outside the markers (e.g. the Felt BPM Corrections + LLM BPM Comparison sections in `docs/audio-analysis-reference.md`) is preserved across refreshes. Title + generation timestamp live inside the markers and refresh with each run.

Both layers default ON. Pass `--no-archive` to skip the JSON write; `--no-companion` to skip the MD refresh; `--archive PATH` / `--companion PATH` to override the canonical paths. JSON-to-stdout still works for piping/Skill-based callers — archive + companion happen IN ADDITION.

### Added — Module Code

- **`src/skills/_shared/companion_writer.py`** — marker-based MD-companion-file refresh helper. Provides `update_companion()` that writes new content between AUTOGEN markers, with three modes: `created` (file didn't exist, created with markers), `refreshed` (file had markers, content between them replaced, hand-curated sections outside markers preserved), `wrapped` (file existed without markers, existing content preserved below the new AUTOGEN block as a one-shot migration).

- **`src/skills/_shared/json_archiver.py`** — JSON archive writer for analysis output. Provides `write_archive()` + `archive_path()` + `resolve_archive_arg()` for the per-script flag handling. Knows the canonical archive layout under `docs/audio-analysis/{songs,playlists,catalog}/`.

- **`--archive` and `--companion` flags** added to four analysis scripts in `src/skills/suno-feedback-elicitor/scripts/`:
  - `playlist-sequencing-data.py` — archive at `docs/audio-analysis/playlists/<album>.json`, companion at `docs/playlist-sequencing-data.md`
  - `batch-full-analysis.py` — archive at `docs/audio-analysis/catalog/<YYYY-MM-DD>-deep.json`, companion at `docs/catalog-analysis-report.md`
  - `analyze-audio.py` — archive at `docs/audio-analysis/catalog/<YYYY-MM-DD>-summary.json`, companion at `docs/audio-analysis-reference.md` (preserves hand-curated Felt BPM + LLM Comparison sections)
  - `audio-deep-analysis.py` — per-song archive at `docs/audio-analysis/songs/<song-slug>.json` (no companion — there's no aggregate doc for per-song deep analysis)

  Each flag accepts `--archive` / `--companion` (use canonical path), `--archive PATH` / `--companion PATH` (use explicit path), or `--no-archive` / `--no-companion` (skip).

### Suno Knowledge — Production-Tested Findings (folded upstream)

Findings from 2026-04-28 and 2026-04-29 production sessions folded into module reference docs:

- **`model-prompt-strategies.md` → "Brass-Out-At-Outro Limitation"** (new subsection under Three-Phase Dynamic Arc). Documents the platform limitation: brass-fade-out instructions in section tags or style prompts are unreliably honored for brass-band-fusion genres across both v5 Pro and v5.5 Pro. Two production tests on the same source song (SF swamp-metal funk-fusion 2026-03-23 + LV Galactic-style modern NOLA funk-rock-brass fusion 2026-04-28) confirmed identical failure mode despite v5.5 Pro's improved prompt accuracy + in-bracket per-section instrumentation tags + stacked absence descriptors. Pure prompt-side techniques cannot reliably engineer brass-fade-out for brass-band-fusion genres. **Tier-availability correction (2026-04-29):** Initial framing claimed Replace Section was Studio-only — that was wrong. Replace Section IS available at Pro tier in the Legacy Editor / Song Editor, but with documented quality limitations (melody drift on long sections, audio degradation when chained, no prior-gen reuse, best on single-line/short-phrase spots) that make it an unreliable fallback for the brass-out outro use case specifically. Premier (Suno Studio) tier offers more surgical tools (12-track stem extraction, Remove FX, Quick Replace variants) but is the $24/mo upgrade. Architects-around guidance + 8th LV dynamic archetype emergence noted.

- **`model-prompt-strategies.md` → "Brass-Band Gravity — Aggressive Counter-Emphasis Required"** (new subsection under First-Genre Dominance). Documents that brass-band genre gravity is exceptionally strong — single-mention guitar/rhythm-section descriptors get buried in observed gens even when present in the critical zone. Production-confirmed pattern table shows progressive counter-emphasis attempts; only "Guitar-driven" framing + multiple explicit guitar mentions in the critical zone (3 mentions in 200 chars) successfully surfaces guitar in the mix. Counter-intuitive guidance: this LOOKS like over-correction but is the right level for brass-band gravity specifically.

- **`gemini-audio-analysis.md` → Camelot framework limitations** (expanded DJ Harmonic Mixing subsection). Documents that Camelot perfection is NOT a comprehensive transition-smoothness measure — it tracks key relationships only and does not capture tempo gaps, genre/style register, energy/dynamic level, or production aesthetic. Production-confirmed (a placement decision, 2026-04-28) where "Camelot-perfect" placement options were rejected in favor of a Camelot-rougher position because the listening experience was less jarring. Practical placement-evaluation rule: describe the listening experience as the primary criterion; Camelot is one input among many; flag tempo / genre-register / energy gaps explicitly when significant. Camelot is reliable for same-genre / same-tempo placements but breaks down when other dimensions diverge.

- **`STUDIO-EDITOR-REFERENCE.md` → Replace Section transition-seam quality limitation** (new "Production-Tested Limitation" subsection). Documents that even at Replace Section's documented sweet-spot scale (single-word / short-phrase target), the operation can produce audible transition seams at the section boundaries. Production-confirmed 2026-04-29 (a single-word `-ing` suffix fix): both returned variations correctly fixed the targeted word but both produced obviously audible joins where new replacement section met surrounding original audio. Replace Section's localized-fix value is bounded by transition-quality, not just section size. Practical takeaway: evaluate transition smoothness alongside content correctness; if seams are obvious, fall back to Cover or full re-gen with phonetic anchor (which produce single-coherent audio without seams). Also notes 4 credits / 2 variations observed in production vs 5 credits in Suno's documentation (verify current cost via UI).

- **`metatag-reference.md` → Mid-Word Vowel Anchoring with English-Word Fragments** (new subsection under Pronunciation / Phonetics). Documents the technique of respelling only the broken syllable of a mispronounced word with an unambiguous English-word fragment that encodes the target vowel sound. Distinct from Stretched Words guidance (which covers dramatic vowel elongation); this covers non-stretched mid-word fixes for normal-tempo delivery. Production-confirmed 2026-04-29 on a track containing a Latin phrase — `ad infinitum` → `ad in-fih-nigh-tum` rendered correctly with the long-i sound coming from the English word `nigh` (rhymes with high/sigh/thigh). Lowercase `nigh` verified working in actual gen. Subsection includes a vowel-anchor catalog (long-i / long-a / long-o / long-e / long-u variants), how-to-apply steps, and a capitalization clarification (ALL CAPS on a phonetic-anchor syllable adds loudness, not different pronunciation — `nigh` and `NIGH` are pronounced the same).

---

## [1.7.0] - 2026-04-26

### Script Reorganization + Portable Behavioral Preferences + Suno Knowledge Doctrine Fixes

Two structural threads land in this release:

1. **Script reorganization** addressing community-marketplace feedback ([bmad-code-org/bmad-plugins-marketplace#7](https://github.com/bmad-code-org/bmad-plugins-marketplace/pull/7)). Previously the module had a top-level `scripts/` folder with six scripts that didn't follow the BMad plugin install convention — skills land at `.claude/skills/{skill-name}/`, but top-level `scripts/` had no install path. Investigation showed that 4 of the 6 scripts are agent-skill-internal in practice (only ever invoked from within `suno-agent-band-manager`'s flow) and were never truly "shared" — they had simply not been placed inside the skill that owns them. They've now been moved into the agent skill's `scripts/` folder. The remaining 2 scripts (`pack-portable.{sh,ps1}`, `unpack-portable.{sh,ps1}`) are user-facing entry points that need a stable project-root path for direct user invocation, so they stay at top-level `scripts/` with documentation flagging the marketplace-install gap.

2. **Portable behavioral-preferences file + production-tested Suno-knowledge corrections** (originally tracked as the v1.6.8 unreleased work — now folded into v1.7.0). Mac had been saving user-articulated behavioral feedback (no-disclaimed-restraint, no-false-dichotomy, no-piano-forward defaults, voice-character-not-genre-gravity, etc.) to per-machine agent memory caches that don't travel via portable sync — so corrections articulated on one machine never reached the other. Fixed structurally: behavioral preferences now live in a portable file the sync carries; Suno platform knowledge corrections folded upstream into module reference docs.

### Added — Script Reorganization

- **Agent-internal scripts moved into `src/skills/suno-agent-band-manager/scripts/`** — `validate-sidecar.py`, `regenerate-index-sections.py`, `reconcile-sidecar.py`, `pipeline-guard.py` now live with the skill that owns them. Previously top-level `scripts/`. Path references updated across the agent's reference files (`activation.md`, `init.md`, `memory-system.md`, `save-memory.md`, `creed.md`) to use the skill-relative `./scripts/X.py` convention (matches the existing `pre-activate.py` / `validate-path.py` / `check-memory-health.py` invocation pattern in the same skill).

- **`pack-portable.sh` / `pack-portable.ps1` updated** to call `validate-sidecar.py` at the new agent-skill location (`$PROJECT_ROOT/.claude/skills/suno-agent-band-manager/scripts/validate-sidecar.py`).

- **`unpack-portable.sh` / `unpack-portable.ps1` updated** to call `reconcile-sidecar.py` at the new agent-skill location.

- **`suno-setup` SKILL.md `--guard-script-path` argument** updated from `scripts/pipeline-guard.py` to `.claude/skills/suno-agent-band-manager/scripts/pipeline-guard.py` so the Stop-hook command written into user `.claude/settings.local.json` points at the new location.

- **`module_greeting` in `src/skills/suno-setup/assets/module.yaml`** expanded with a brief pointer to `pack-portable.sh` and a note for marketplace-install users — surfaces the multi-machine workflow at install completion when users are most likely to read the greeting.

- **`INSTALLATION.md` "Multi-Machine Sync" section** clarifies that pack/unpack scripts are user-facing entry points distinct from agent-internal scripts, with explicit guidance for marketplace-install users on how to obtain `pack-portable.sh` / `unpack-portable.sh` (clone the repo separately, or copy the two files from the GitHub repo into their project's `scripts/` folder). Future installer release may auto-deposit these.

- **`INSTALLATION.md` Pipeline Guard section** updated with the new `pipeline-guard.py` path.

### Added — Portable Behavioral Preferences

- **`docs/mac-preferences.md` — new portable file** for user-specific Mac behavioral preferences (communication style, pacing rules, framing rules, conversation discipline). Loaded on activation by the agent. Distinct from the voice file (which covers the user as a writer/creator) and from per-machine agent memory (which doesn't travel via portable sync).
- **`activation.md` — Step 6b** added: load `docs/mac-preferences.md` if present and apply for the session.
- **`memory-system.md` — `docs/mac-preferences.md` section** added (placed before `index.md` section). Documents what goes in the file, why it lives in `docs/` rather than per-machine agent caches, when to write entries, and what does NOT belong (Suno platform knowledge → module refs upstream; musical preferences → patterns.md / voice file; band/catalog policies → band profiles / voice file).
- **`save-memory.md` — Step 2c** added: behavioral preference writes scan, ensuring corrections articulated mid-session were appended to `docs/mac-preferences.md` per "Sync at the point of change."
- **`portable-manifest.example.yaml`** includes `docs/mac-preferences.md` in default include list.

### Changed — Suno Knowledge Corrections (production-tested patterns folded upstream)

- **`metatag-reference.md` — paren-spacing rule REVERSED.** A prior version recommended "no space before opening paren tightens coupling: `word(echo)` not `word (echo)`." That was based on a single-song experimental finding (one band's version of one track, March 2026) that got mis-promoted to a general rule. Verified across catalog April 2026 — every working parenthetical-backing-vocal song uses spaces before the paren. The no-space form caused `(blasting)` to be skipped on one song's bridge across multiple generations until spaces were added. Catalog-standard is `word (echo)` (with space). Doc now reflects this and explains the prior-rule provenance.
- **`metatag-reference.md` — paren-at-end-of-line rule** added with broken-and-fixed example. Mid-line parens (text after the closing paren on the same line) get dropped inconsistently. If the sentence continues past the paren, break the line after the closing paren.
- **`metatag-reference.md` — long-paren-fold-back data point** added. Long parentheticals (~10+ syllables) pull as primary vocal even with triple-reinforcement; short parens (1-4 syllables) land as backing-vocal interjections reliably. Boundary is approximate.
- **`metatag-reference.md` — `[Whispered, vulnerable]` context-dependent caveat** added. Reliable in folk-intimate / acoustic-singer-songwriter / ballad contexts; in theatrical-horror / voodoo-rock / dramatic-narrative contexts it can pull spoken-word delivery. Use `[Vocal Style: soft, sung]` in those genres — the explicit `sung` token defeats the spoken-word drift.
- **`metatag-reference.md` — Stretched Words section** added under Word-Formatting Effects. Documents vowel-collapse drift on hyphenated stretched words (`to-o-o-lling` → "tooling") and disambiguation techniques (insert `h`, alt-vowel spelling, double-consonant anchor, re-articulate with ellipses). An April 2026 production data point supplies the example.
- **`metatag-reference.md` — Section-tag content rule** added under Section Structure Tags. Em-dashed descriptive labels (`[VERSE 1 — THE ROOM]`) burn character budget for nothing — Suno has no training on them. Use parameterized syntax (`[Verse 1: hushed, tense]`) for direction Suno can act on. Applies equally to cross-band conversions.
- **`model-prompt-strategies.md` — Voice Gravity section CORRECTED.** A prior version framed v5.5 Voice clones as carrying "trained genre gravity" pulling generations toward a trained baseline. That framing was overstated. Voice cloning trains on vocal samples and captures vocal character (timbre, lilt, vibrato, attack patterns, dynamics behavior) — character is genre-neutral; Suno adapts character to the genre prompt. Section renamed to "v5.5 Voice-Character Principle" and rewritten to reflect that the captured character is what the Voice carries, the case study validates correct Audio Influence + don't-duplicate-Voice-descriptors + specify-arrangement-explicitly (NOT "voice has genre gravity"), and Voice direction should be framed as **"the captured character fits X register well"** rather than "fighting the Voice's trained gravity toward Z."

### Migration

None required. The script reorganization is transparent to users:

- **Existing dev clones** continue to work — the moved scripts are still in the repo, just at a different path. Reference files and pack-portable shell scripts have all been updated to the new paths in the same release. After pulling v1.7.0, the Stop-hook command in `.claude/settings.local.json` will need to be re-run via `python3 .claude/skills/suno-setup/scripts/configure-guard.py` (or the suno-setup skill) to update the path string from `scripts/pipeline-guard.py` to `.claude/skills/suno-agent-band-manager/scripts/pipeline-guard.py`. The hook entry can also be edited manually.
- **Marketplace-install users** get the moved scripts as part of the agent skill install (no change needed). For pack/unpack-portable, see the new INSTALLATION.md "Multi-Machine Sync" guidance — the marketplace install path doesn't currently deposit top-level `scripts/`, so users wanting portable sync need to copy `pack-portable.{sh,ps1}` and `unpack-portable.{sh,ps1}` from the GitHub repo manually until a future installer feature lands.
- **No user data changes.** `docs/` and `_bmad/` are untouched.

### Version Bumps

- `src/skills/suno-setup/assets/module.yaml`: 1.6.7 → 1.7.0
- `.claude-plugin/marketplace.json`: 1.6.7 → 1.7.0

### Marketplace Submission

The community module entry on [bmad-code-org/bmad-plugins-marketplace](https://github.com/bmad-code-org/bmad-plugins-marketplace) (`registry/community/suno-band-manager.yaml`) will be updated to point at the v1.7.0 commit SHA via a new PR so marketplace consumers see the script-reorganized version. Brian (BMad maintainer) flagged the shared-content question on PR #7 after the original merge at v1.6.7; this release addresses that feedback structurally.

---

## [1.6.7] - 2026-04-22

### Drift Protection — Round Three, plus Research Refresh

v1.6.5 and v1.6.6 put the drift-protection machinery in place (validators, regenerators, reconciliation on unpack, cross-reference scanning). Real sessions since then surfaced three gaps in the machinery itself — one of which made v1.6.5 effectively unusable without hand-editing — and a fourth at the doctrine level where the module's definition of "sync" still treated cross-file consistency as a milestone-reconciliation step rather than an edit-time invariant. This release closes all four, and folds in the production-knowledge work that piled up across the same sessions (counter-genre prompting research, wordless-chant intro technique, Package Assembly Rule hardening, a CRITICAL rule on what exclusions are actually for).

### Root Cause — Issue #31 (sync at point of change)

Issue #18 added `reconcile.md` as a milestone-propagation protocol (title changes, publishes, playlist reorders, profile edits). Issue #31 is the orthogonal gap: **non-milestone edits** — creating a new reference file, bumping a catalog count in the sidecar, marking a source closed — never trigger `reconcile.md` and create drift windows in every file that references them. `save-memory.md` Step 6's "Companion files audit" caught drift eventually, but was operating as the **primary sync mechanism** rather than a backstop, leaving files out of sync for the entire session between the edit and the save.

The doctrine-level fix: treat cross-file consistency as an invariant maintained at every write-boundary, not as a milestone reconciliation step.

### Added

- **`creed.md` — new foundational principle: "Sync at the point of change."** Joins the three existing principles (Always output everything / Meet them where they are / The magic is iteration) as a top-level rule. When editing a file, check in the same write-batch whether any other tracked file references what just changed (counts, descriptions, status markers, cross-references, file paths, companion-files tables) and update those references immediately. Audit-at-save-time is explicitly reframed as a backstop, not the primary sync mechanism. Drift windows between edit and save are unacceptable because the session may be interrupted or handed off at any point.

- **`regenerate-index-sections.py` → `--migrate` flag.** New `migrate_section()` helper locates a `## Recently Published` or `## Catalog Status` heading, finds the end of the section (next `##` heading or EOF), and wraps the body content with the required `derived:*:start/end` marker pairs in-place. One-command migration for pre-v1.6.5 sidecars and for any sidecar that somehow slipped through First Breath without markers. Migration is idempotent (skips sections that already have markers), safe under `--dry-run` (no writes), and aborts without partial writes when a heading is missing entirely (prints which heading is missing and exits 1).

- **`init.md` — `index.md` template baked into First Breath.** New sidecars are born already-migrated, with both `derived:recently-published:start/end` and `derived:catalog-status:start/end` marker pairs wrapping stub content. The template also gives the agent a concrete structure for User Preferences, Current Work, Pending / Parked Work, and Session History so First Breath output is consistent across sessions.

- **`validate-lyrics.py` — HIGH-confidence standalone-tag allowlists.** Three new recognized sets mirrored from `metatag-reference.md`: `VALID_STANDALONE_MOODS` (16 tags), `VALID_STANDALONE_ENERGY` (10 tags), `VALID_TIMING_RHYTHM` (9 tags). Wired into the existing invalid-metatag check as an `is_standalone` gate alongside `is_section` / `is_vocal_cue` / `is_descriptor`. Eliminates a class of false-positive findings that had been eroding trust in the validator.

- **`creed.md` → Package Assembly Rule: Pre-Output Self-Check (MANDATORY) + Violation Tells + Highest-Risk Contexts.** Before sending any response containing a Suno package, verify in reasoning that both `suno-style-prompt-builder` and `suno-lyric-transformer` were invoked *this turn* (or lyrics aren't needed). Violation Tells enumerate the concrete signs the pipeline was skipped: missing Title field, hand-assembled copy-ready blocks, using validation scripts as pipeline substitutes, prior-iteration framing in exclusion reasoning, "I already know what the skill would produce" reasoning. Highest-Risk Contexts call out parallel-band repackaging, minor refinements after a successful first gen, and extended direction-setting discussions — historically the contexts that trigger pipeline-skipping.

- **`model-prompt-strategies.md` — Counter-Genre Prompting section** (fixes #28). Four additions from session-14 research (2026-04-20, 15+ 2025-2026 sources surveyed):
  - *First-Genre Dominance* (under Genre Keyword Ordering) quantifies position 1 holding the strongest single signal, with genre + subgenre tags collectively carrying ~60-70% of arrangement output. Explains why counter-genre work requires the counter-target in position 1, not buried at position 3-4.
  - *Default Weirdness Normalizes Counter-Genre Prompts* (under Slider Guidelines) documents v5.5's "accept then normalize" behavior and prescribes Weirdness 60-70 for counter-genre prompts. Explicitly supersedes the prior conservative-Weirdness-for-accessibility guidance, which was self-imposed caution and not grounded in evidence.
  - *Counter-Genre Prompting* (new top-level section) with four subsections: Displacement-Budget Descriptors (role-slot filling with structurally-incompatible descriptors), Triple-Signal Tempo Stacking, 6/8 and 12/8 Compound Meter as a tempo-perception lever, and a Synthesis full-example prompt deploying all techniques.
  - *Community Research Sources* expanded with HookGenius Complete Suno Prompt Guide 2026, HookGenius Tempo BPM Guide, HookGenius Negative Prompting Guide, JG BeatsLab 7 v5.5 Behaviors, Blake Crosley v5.5 Reference, and Suno Studio 1.2 release notes.

- **`metatag-reference.md` — Wordless-chant intro + doubled-word parentheticals.** Production-tested guidance from one band's generation of a call-and-response track: doubled-word parentheticals as ritualistic/trance backing technique, the exclamation-separator fix for single-word truncation, inline vs. line-separated parenthetical semantics, and a new *Establishing Non-Default Vocal Arrangements* subsection documenting the wordless-chant intro as the reliable lever when group backing vocals fail to establish on V1. `model-prompt-strategies.md` gets a paired exception: non-default vocal arrangements earn position 1 in the style prompt ahead of even genre.

### Changed

- **`save-memory.md` Step 6 — "Companion files audit" reframed as a backstop.** Previous wording implied the audit **was** the sync. New framing is explicit: the audit should normally find nothing; if it catches drift, that means a point-of-change sync was missed — fix the drift now AND note which edit missed the sync as a behavioral gap to correct going forward. Audit-time fixes are tolerated, not planned.

- **`save-memory.md` Step 5 — pre-write sync check before chronology.** Before writing the session summary to `chronology.md`, scan the session's writes for cross-referenced updates that didn't land in the same batch as their triggering edit (new `docs/` files → voice file Companion Files table; songbook add → playlist YAML + voice catalog; sidecar Key Files path change → doc references; WIP COMPLETED → sidecar Pending / Parked). The chronology write is the last narrative write of the session and is the correct moment to self-check that cross-file invariants held at each edit, not just at save time.

- **`create-song.md` Step 7 — sync at each sub-step write, not just at the Step 7 aggregate.** Per the new creed principle, Post-Publish Reconciliation is explicitly reframed as a milestone backstop. Concrete expectations at publish time: songbook entry write → voice catalog count + Companion Files entry in the same batch; playlist YAML edit → playlist ordering doc in the same batch; WIP COMPLETED → sidecar Pending / Parked drop in the same batch; title finalized → all in-session references updated in the same batch as the rename.

- **`refine-song.md` — new Sync-at-Write for Refinements section.** Refinement edits that touch **published** song attributes (key/tempo/Camelot, voice clone, voice gravity, playlist position, renames) propagate in the same write batch as the triggering edit. Refinements that touch only the current-iteration package (not yet in the songbook) are scoped out — nothing references them yet.

- **`regenerate-index-sections.py` — clearer missing-markers error.** Previous message said "See v1.6.5 release notes for migration guidance" — a cold trail from an error the agent routinely hits. New message names the `--migrate` flag as the one-command fix and points directly at the CHANGELOG 1.6.5 migration block for the exact template. `save-memory.md` Step 4a updated in parallel so the agent, on hitting the missing-markers error mid-session, reaches for `--migrate` instead of hand-editing markers in.

- **`regenerate-index-sections.py` and `validate-sidecar.py` — YAML parse errors no longer silent** (fixes #29). `regenerate-index-sections.py::parse_song()` now prints a stderr WARNING with file path + exception detail before returning None, naming the common cause (flow-sequence values with inner brackets like `[ST + CC; added [Spoken] outro]`) and pointing to issue #29. `validate-sidecar.py::parse_song()` signature changed to return `(Song|None, error_msg|None)`; `load_all_songs()` returns `(songs, parse_findings)` and converts each YAML parse error into a `songbook_drift` error-severity Finding so the pre-pack sync-gate blocks instead of silently hiding the song. Previously: songs with bracket-inner YAML quietly vanished from Recently Published + Catalog Status and the validator still reported PASS.

- **`creed.md` → Package Assembly Rule: Exclusion drift-risk CRITICAL RULE.** Excludes defend against drift risks that the CURRENT style prompt's own descriptors might introduce — nothing else. Suno is stateless; it has no knowledge of prior gens, other bands' renderings of the same lyrics, or the broader catalog. Exclusion reasoning that references "the other band's version," "the prior iteration," or "what [other band/previous gen] used" is a violation tell.

- **Root `CLAUDE.md` / `GEMINI.md` / `AGENTS.md`** trimmed to a brief cross-tool reinforcement pointing to `creed.md` as authoritative on the Package Assembly Rule. Single source of truth, no duplicated content.

### Fixed

- **Issue #27** — `validate-lyrics.py` flagged HIGH-confidence standalone bare-bracket tags (e.g. `[Low Energy]`, `[Driving]`, `[Half-Time]`, `[Building]`, `[Haunting]`) as unrecognized metatags, producing noisy false-positive findings. Now matches `metatag-reference.md`.
- **Issue #28** — counter-genre prompting knowledge from session-14 research (2026-04-20) was not reflected in the module. Now documented in `model-prompt-strategies.md`.
- **Issue #29** — songbook entries using `transformations_applied` flow-sequence YAML with inner square brackets silently failed YAML parsing and got excluded from derived sidecar sections, with validator still reporting PASS. Silent failure replaced with surfaced WARNING + blocking `songbook_drift` error.
- **Issue #30** — v1.6.5's derived-section markers were never written by any codepath in the module: First Breath (`init.md`) wrote narrative `index.md` without markers, and `pre-activate.py`'s scaffold intentionally skipped `index.md`. Every new sidecar was born un-migrated and hit the missing-markers error the first time the regenerator ran. Fixed three ways: markers baked into the First Breath template, new `--migrate` flag for one-command in-place migration, better error message naming `--migrate` as the fix.
- **Issue #31** — cross-file sync was treated as milestone-reconciliation-only; non-milestone edits created drift windows that `save-memory.md` Step 6 caught as primary sync rather than backstop. "Sync at the point of change" principle now formalized in `creed.md`, `save-memory.md` Step 6 reframed as backstop, sync-at-write expectations added to `create-song.md` Step 7 and `refine-song.md`.

### Migration

None required. All changes are additive or wording-level:
- Existing installs with pre-v1.6.5 sidecars that still lack derived-section markers can now run `python3 scripts/regenerate-index-sections.py "{project-root}" --migrate` for a one-command fix — no more hand-editing markers in.
- Existing installs that already have markers get a clean no-op from `--migrate`.
- `validate-lyrics.py` allowlist expansion only removes false positives; no existing lyrics break.
- `validate-sidecar.py` now surfaces YAML parse errors that were previously silent — this may cause a pre-pack sync-gate block on installs with bracket-inner YAML values that were silently being dropped. Fix by quoting the offending value; the surfaced message names the fix.

### Version Bumps

- `package.json`: 1.6.6 → 1.6.7
- `src/skills/suno-setup/assets/module.yaml`: 1.6.6 → 1.6.7
- `.claude-plugin/marketplace.json`: 1.6.6 → 1.6.7
- `INSTALLATION.md`: 1.6.6 → 1.6.7

### Verification

- **Issue #30 end-to-end** — fresh pre-v1.6.5 sidecar with both headings → `--migrate` wraps both sections, regenerator rewrites between markers, exit 0; re-running `--migrate` on already-migrated sidecar → clean no-op ("No changes needed"); sidecar missing one heading → `--migrate` aborts with clear message naming the missing heading, no partial writes; `--migrate --dry-run` → prints regenerated sections, does not write; production sidecar (already migrated) → `--migrate --dry-run` is a clean no-op.
- **Issue #29 exact repro** — songbook entry with `transformations_applied: [ST + CC; added [Spoken] outro]` → `validate-sidecar` emits `songbook_drift` error and exits 1; `regenerate-index-sections` emits stderr warning and continues.
- **Issue #27 smoke test** — lyrics using `[Low Energy]`, `[Driving]`, `[Half-Time]`, `[Building]`, and `[Haunting]` all pass cleanly; prior false positives eliminated.
- **First Breath template** — new sidecars scaffold with both marker pairs in place; regenerator runs clean on first save.
- **Package Assembly Rule self-check** — Pre-Output Self-Check language validated against the creed-as-authoritative architecture; root `CLAUDE.md`/`GEMINI.md`/`AGENTS.md` point at the creed with no duplicated content.

### Scope Note

This release adds **one new script flag** (`regenerate-index-sections.py --migrate`), **extends two scripts** (`validate-lyrics.py` standalone-tag allowlists; `validate-sidecar.py` + `regenerate-index-sections.py` YAML-error surfacing), and **updates seven reference docs** (`creed.md`, `save-memory.md`, `create-song.md`, `refine-song.md`, `init.md`, `model-prompt-strategies.md`, `metatag-reference.md`) plus the three root standing-orders files (`CLAUDE.md` / `GEMINI.md` / `AGENTS.md`). User data (`docs/`, `_bmad/`) is not part of the module and remains untouched by the module upgrade. No user migration required — pre-v1.6.5 sidecars have an opt-in one-command path via `--migrate`.

---

## [1.6.6] - 2026-04-16

### Drift Protection — Round Two

A follow-on to v1.6.5's Sidecar Drift Protection release. v1.6.5 closed the largest drift gap (index sections vs. songbook ground truth), but three smaller classes of drift surfaced in sessions afterward:

1. **Forward-intent cross-references.** Markdown files referencing other docs files that were never actually created — `` `docs/catalog-meta-observations.md` `` mentioned declaratively in a WIP draft, but the target file doesn't exist on disk. The v1.6.5 validator scanned songbook frontmatter/body agreement and audio file existence; it didn't scan prose for markdown cross-references.
2. **Unpack-side sidecar drift.** The pre-pack validator gates sync on the source machine, but after unpack on the receiving machine the sidecar still reflects the receiving machine's prior local state. Freshly-arrived WIP notes, session-context edits, and songbook updates don't automatically make it into the sidecar narrative — the agent has to remember to integrate them, and often didn't.
3. **Machine-specific absolute paths in access-boundaries.** The scaffold template wrote a `{project-root}/...` placeholder that users or agents sometimes expanded to an absolute `/home/.../bmm/...` path during edits, making the file non-portable. Paths in `access-boundaries.md` are conceptually relative to project root; absolute paths were vestigial.

This release closes all three.

### Added

- **`scripts/reconcile-sidecar.py`** — post-unpack reconciliation helper. Lists every `docs/**/*.md` file whose mtime is more recent than the sidecar's `index.md` (likely integration candidates), runs `validate-sidecar.py` to surface drift, and produces a punch list for the agent to walk through with the user. Exits 1 when reconciliation is needed, 0 when clean. `--format json` for programmatic consumption. Does not edit files — reconciliation itself is the agent's job.

- **`scripts/validate-sidecar.py` → `check_markdown_cross_references()`** — new check that scans every `.md` file under `docs/` for inline-code references (`` `docs/X.md` ``) and markdown-link references (`[text](X.md)`, `[text](../path/to/X.md)`) and verifies each target exists on disk. Reports findings with category `cross_reference_missing`, severity `warning`. Dual-anchor resolution (tries both parent-relative and project-root-relative) so the user convention of writing `` `docs/X.md` `` from inside a file already in `docs/` still resolves correctly. Skips external URLs, anchor-only references, self-references, glob/wildcard patterns, and anything inside fenced code blocks.

### Changed

- **`scripts/unpack-portable.sh` and `unpack-portable.ps1`** — automatically invoke `reconcile-sidecar.py` after extraction. The reconcile report prints to stderr so the agent reading the script output sees the punch list without parsing it out of a JSON stdout channel. Bypass with `BMAD_SKIP_RECONCILE=1` (or `$env:BMAD_SKIP_RECONCILE=1` on PowerShell). The reconcile call never fails the unpack — reconciliation is advisory, and the integration decisions belong to the agent and user.

- **`src/skills/suno-agent-band-manager/scripts/pre-activate.py → scaffold_sidecar()`** — `access-boundaries.md` scaffold now writes bare relative paths (`_bmad/_memory/band-manager-sidecar/`) instead of the `{project-root}/` placeholder form. Paths are all conceptually relative to project root; the placeholder was a convention artifact that sometimes got expanded to absolute paths during edits. Includes a one-line header clarifying the convention: *"All paths below are relative to the project root."*

  `validate-path.py` continues to handle both bare-relative and `{project-root}/` forms, so existing installs with the legacy placeholder keep working unchanged. Only new scaffolds change.

- **`src/skills/suno-agent-band-manager/references/activation.md` step 5** — sync package handling now requires post-unpack sidecar reconciliation before proceeding to the main menu. Previously the step said "reload affected files" which was soft and easy to skip. The new language is explicit: run `reconcile-sidecar.py`, walk every `newer_files` entry and every validator finding with the user via the Handoff Checkpoint Pattern, integrate approved changes into the narrative sections of `index.md`, regenerate derived sections, and only then proceed into the normal activation flow.

- **`src/skills/suno-agent-band-manager/references/memory-system.md`** — new *Post-Unpack Reconciliation* section documents the mandatory protocol. *Access Control* section now documents the path convention (relative to project root, no placeholder, no absolute paths — validator resolves both forms for back-compat).

- **`src/skills/suno-agent-band-manager/references/save-memory.md` step 7** — reconciliation check now also covers `cross_reference_missing` warnings from the validator. If broken cross-references are detected, surface them to the user and resolve (create target file, rephrase as future-intent, or remove the reference) before packing. The class of drift described in issue #23 gets caught automatically at save time now, not just at unpack time.

### Fixed

- **Issue #23** — `validate-sidecar.py` didn't catch declarative references to docs files that were never created. Now flagged as `cross_reference_missing` warnings.
- **Issue #25** — no post-unpack reconciliation meant the sidecar narrative could silently lag behind freshly-arrived file content. Now the agent gets a punch list automatically and the protocol requires reconciliation before proceeding.
- **Issue #26** — access-boundaries scaffold emitted `{project-root}/` placeholder paths that sometimes got expanded to absolute machine paths, breaking portability. Scaffold now writes bare relative paths. Existing files with the placeholder form keep working.

### Migration

None. All changes are additive or internal:

- Existing installs with `{project-root}/` paths in `access-boundaries.md` continue to work — `validate-path.py` normalizes both forms.
- Existing sidecars work unchanged — the reconcile script is new tooling, not a schema change.
- The cross-reference check runs automatically as part of `validate-sidecar.py`; findings are warnings, not errors, so existing drift surfaces but doesn't block syncs.

### Version Bumps

- `package.json`: 1.6.5 → 1.6.6
- `src/skills/suno-setup/assets/module.yaml`: 1.6.5 → 1.6.6
- `.claude-plugin/marketplace.json`: 1.6.5 → 1.6.6
- `INSTALLATION.md`: 1.6.5 → 1.6.6

### Verification

- **Cross-reference check on current test harness:** 7 legitimate drift findings surfaced in the test project — broken references to `outreach-tracker.md`, `sessions/2026-04-10.md`, `case-state.md`, `identity-and-context.md`, `docs/wip-contentment-poem-brainstorm.md`, `wip-categories-fragments.md`, `back-woods-rushin-city-slow.md`. Zero false positives. All legitimate — this is exactly the class of drift issue #23 described.
- **Glob-pattern filtering:** `per-candidate/*.md` glob references correctly skipped (intent-references, not single-file lookups).
- **Scaffold output:** fresh project scaffolds `access-boundaries.md` with bare relative paths and no `{project-root}/` strings anywhere in the file.
- **Back-compat:** `validate-path.py` unit-tested against a boundaries file containing both `docs/X/` and `{project-root}/docs/X/` forms — both resolve identically.
- **Unpack script:** `unpack-portable.sh` runs `reconcile-sidecar.py` automatically after extraction on Linux; report prints to stderr with the stale-files punch list.
- **Reconcile script edge cases:** returns exit 0 with `status: no_sidecar` when no sidecar exists (nothing to reconcile); returns exit 1 with populated `newer_files` when docs files are newer than `index.md`; returns exit 0 with `status: clean` when sidecar is in sync.

### Scope Note

This release adds **one new script** (`reconcile-sidecar.py`), **extends one script** (`validate-sidecar.py` gains `check_markdown_cross_references()`), and **updates two scripts + three reference docs** (`unpack-portable.sh`, `unpack-portable.ps1`, `pre-activate.py`, `activation.md`, `memory-system.md`, `save-memory.md`). User data (`docs/`, `_bmad/`) is not part of the module and remains untouched by the module upgrade. No user migration required.

---

## [1.6.5] - 2026-04-13

### Sidecar Drift Protection

A structural release that eliminates a class of bug where the Mac sidecar `index.md` could silently drift out of sync with the authoritative songbook. The drift was discovered in a real session: `index.md` still listed a published song as WIP and omitted another published track entirely — yet the catalog status section had been updated in the same save cycle. That partial-update pattern motivated the fix.

### Root Cause

`index.md` mixed two categories of facts and treated them identically:

1. **Derivable facts** — catalog count, which tracks are published, publish dates, catalog roster. These have an authoritative source (songbook frontmatter + body Status markers + playlist YAMLs). They should be machine-derived.
2. **Narrative facts** — current work focus, pending threads, session history, next steps. These live only in the narrator's head. They need to be hand-written.

Both were hand-written. When the save-memory workflow ran, Mac read the conversation and narratively updated the sections he remembered touching. Sections he didn't touch silently kept stale values. Nothing compared the written index against the ground truth, so drift accumulated invisibly. Similar drift was independently found in a songbook file's frontmatter `notes:` block and body `**Status:**` marker (both still said WIP for a song that had been published two days earlier).

### Added

- **`scripts/validate-sidecar.py`** — read-only validator that scans `docs/songbook/**/*.md`, `docs/band-profiles/*.yaml`, `docs/*-playlist.yaml`, and `_bmad/_memory/band-manager-sidecar/index.md`, then reports drift as structured findings (JSON or text output). Checks:
  - Songbook internal consistency — frontmatter `status`/`date` vs. body `**Status:**` marker
  - Audio file existence for published songs
  - Sidecar Recently Published list vs. songbook ground truth
  - Sidecar Catalog Status counts vs. actual songbook counts
  - Playlist YAML track count vs. songbook count

  Exit 0 on clean, 1 on errors (for CI-friendliness). Warnings (pre-existing content gaps like missing body markers on older songs) do not fail the run. Standalone CLI with `--format json` and `--warn-only` flags.

- **`scripts/regenerate-index-sections.py`** — writer-side companion to the validator. Reads songbook + playlist ground truth, derives the Recently Published and Catalog Status sections, rewrites them in-place in `index.md` between HTML comment markers:

  ```markdown
  <!-- derived:recently-published:start -->
  ...auto-generated content...
  <!-- derived:recently-published:end -->
  ```

  Narrative sections (Current Work, Pending / Parked Work, Session History, etc.) are preserved unchanged — only the derivable sections are rewritten. `--dry-run` prints without writing.

### Changed

- **`scripts/pack-portable.sh` and `pack-portable.ps1`** — run `validate-sidecar.py` before packing. A non-zero exit from the validator blocks the pack, preventing stale sidecar state from propagating to other machines via the sync archive. Warnings do not block. Bypass via `BMAD_SKIP_VALIDATE=1` (or `$env:BMAD_SKIP_VALIDATE=1` on PowerShell) for emergency syncs. Missing validator script or Python interpreter falls through gracefully with a note so older installs keep working. Cross-platform parity: both shell and PowerShell scripts implement the same gate with the same bypass semantics.

- **`src/skills/suno-agent-band-manager/references/save-memory.md`** — Step 4 now updates only narrative sections of `index.md`; Step 4a invokes `regenerate-index-sections.py` to rewrite derivable sections; Step 4b invokes `validate-sidecar.py` to confirm cleanliness before finalizing the save. Step 7 reconciliation narrowed to cross-file drift since sidecar-level drift is covered automatically by 4b.

### Fixed

- **A songbook entry — frontmatter/body drift cleanup.** Frontmatter said `status: published` with a publish date, but the `notes:` block and body `**Status:**` marker both still described WIP state (a plan to re-test with a different Voice clone when credits returned). The song had actually been published a day later after A/B testing — the softer clone's wild card variant with "driving rock band weight" took the published slot. All three locations now agree. This drift is what motivated the release.

### Migration (one-time, per project)

Existing projects need to add the derived-section markers to `index.md` on first upgrade:

```markdown
## Recently Published

<!-- derived:recently-published:start -->

...existing content...

<!-- derived:recently-published:end -->

## Catalog Status

<!-- derived:catalog-status:start -->

...existing content...

<!-- derived:catalog-status:end -->
```

The regenerator reports clearly if markers are missing and exits without modifying the file, so a missed migration can't corrupt the index.

### Impact

| Previously | After v1.6.5 |
|---|---|
| `index.md` Recently Published and Catalog Status hand-written → could silently skip updates | Regenerated from songbook ground truth every save → can't drift |
| No mechanism to detect sidecar inconsistency | Validator reports drift with exit code + JSON for CI |
| Stale sidecar could propagate to other machines via sync | Pre-sync gate blocks packs that fail validation |
| Songbook internal drift (frontmatter vs. body marker) invisible | Validator surfaces it as structured findings |
| Windows and Linux/macOS used independent sync paths | Both platforms run the validator identically |

### Verification

- **Validator on current state:** 0 errors, 14 warnings — all warnings are pre-existing content gaps (older songbook entries in one band missing body `**Status:**` markers, and a 2-track count mismatch between that band's playlist YAML and its songbook directory). These are legitimate drift findings; the validator correctly flags them as warnings rather than blocking errors since they predate v1.6.5.
- **Regenerator dry-run:** produces clean Recently Published list (7 most recent published songs) and Catalog Status (per-band counts + playlist integration) from songbook frontmatter alone.
- **Pre-sync gate on Linux:** packs correctly when validator passes; `BMAD_SKIP_VALIDATE=1` bypass works.
- **Cross-platform parity:** bash and PowerShell implementations of the pre-sync gate inspected side-by-side for identical exit semantics and bypass behavior.

### Version Bumps

- `package.json`: 1.6.4 → 1.6.5
- `src/skills/suno-setup/assets/module.yaml`: 1.6.4 → 1.6.5
- `.claude-plugin/marketplace.json`: 1.6.4 → 1.6.5
- `INSTALLATION.md`: 1.6.4 → 1.6.5

### Additionally (reference doc refinements)

Two small in-flight documentation refinements are also folded into this release since they were already staged:

- **`SUNO-REFERENCE.md` — Credit model clarifications.** Replaces the older "generate 3-5 versions" framing with budgeting in **Creates** (10 credits, 2 songs per press) to match how users actually think about Suno spending. Adds an explicit credit-cost row to the tier comparison table, a dedicated "Credit model" paragraph explaining that 50 credits/day = 5 Creates = 10 songs to evaluate, and a note on the 50 bonus credits/day that refresh on all tiers. Updates the Common Pitfalls table entries to reference Creates rather than individual generations. No behavior change — it's a framing update that brings the reference in line with how Pro users budget sessions.

- **`persona.md` — Adds "Dawlin'" to the NOLA vocabulary list.** Captures the distinctive Yat/Marigny/Bywater/9th Ward pronunciation (the `aw` diphthong) as separate from generic Southern "darlin'" so Mac uses the correct form.

### Scope Note

This release adds **two new scripts** (`validate-sidecar.py`, `regenerate-index-sections.py`) and **modifies several existing module files** (`pack-portable.sh`, `pack-portable.ps1`, `save-memory.md`, plus the two reference doc refinements above). User data (`docs/`, `_bmad/`) is not part of the module and remains untouched by the module upgrade. One-time project migration (adding derived-section markers to `index.md`) is the only user-facing action required.

---

## [1.6.4] - 2026-04-11

### pack-portable.sh Bug Fixes (Linux/macOS)

A bugfix release for the bash portable-sync packer. Two distinct bugs caused users to silently lose files from their sync archives. PowerShell users were unaffected by the core bugs (the PS1 implementation was already correct) but get a small parity consistency fix.

### Fixed

- **`pack-portable.sh` manifest parser silently ignored every pattern.** The sed extraction pulled manifest lines with their original leading indentation intact (`  - "docs/..."` with 2-space YAML indent), but the shell parameter expansion `${line#- }` only strips `- ` from the very start of a string — it does not handle leading whitespace. Result: every pattern in every manifest became garbage text, every glob matched zero files, and `pack-portable.sh` returned `{"status": "empty", "message": "No portable files found to pack."}` with no diagnostic. Users following `portable-manifest.example.yaml` (which demonstrates standard 2-space YAML indentation) would hit this immediately on their first manifest run.

  **Fix:** Replaced the shell-expansion parser with a robust sed one-liner that strips leading whitespace + `- `, inline `# ...` comments, and surrounding quotes (both `"` and `'`) in a single pass. Manifests with standard YAML indentation, inline comments, and either quote style now parse correctly.

- **`pack-portable.sh` default band-profiles pattern silently excluded top-level files.** The default pattern `docs/band-profiles/**/*.yaml` used `find -path` for matching. In `find -path`, `*` matches any sequence including `/` (there is no special `**` globstar), so the pattern was functionally equivalent to `docs/band-profiles/*/*.yaml` — it required a literal `/` between `band-profiles/` and the `*.yaml` tail, which meant files had to be in a SUBDIRECTORY of `band-profiles/`. Every band profile following the standard convention (files placed directly in `docs/band-profiles/`, like `{band-slug}.yaml`) was silently excluded from the default pack.

  **Fix:** Refactored `add_glob` in the bash script to match the PowerShell version's recursive `**` handling — when a pattern contains `**`, the script splits at the first `**`, uses the prefix as a base directory and the suffix as a filename filter, and calls `find -name -type f` (which naturally includes the starting directory). This matches standard shell globstar semantics and the PowerShell implementation, producing identical cross-platform behavior for patterns like `docs/band-profiles/**/*.yaml`, `docs/songbook/**/*.md`, and `docs/inspiration/**/*.txt`. Non-`**` patterns continue to use `find -path` unchanged.

### Changed (parity / consistency)

- **`pack-portable.ps1` manifest parser now handles single-quoted YAML patterns.** The previous regex `^\s*-\s*"?([^"#]+?)"?\s*(#.*)?$` excluded only `"` and `#` from the capture group, so manifest entries using single quotes (`  - 'docs/file.md'`) would capture the single quotes as part of the pattern and fail to match files. The parser is now a two-step approach (match the payload between `- ` and optional `#`, then `.Trim().Trim('"').Trim("'")`) that handles whitespace, inline comments, and both quote styles identically to the bash implementation. This is a minor consistency fix — the PS1 implementation was already correct for the common double-quoted YAML case used in `portable-manifest.example.yaml`.

### Impact

- **Linux/macOS users** using `pack-portable.sh` WITH a manifest — were hitting silent empty-pack failures. **Fixed.** Existing manifests that follow `portable-manifest.example.yaml` formatting now work correctly without modification.
- **Linux/macOS users** using `pack-portable.sh` WITHOUT a manifest (defaults only) — were silently losing their top-level band profiles from the pack. **Fixed.** Defaults now capture both top-level and nested band profiles via `docs/band-profiles/**/*.yaml` with the new recursive handler.
- **Windows users** using `pack-portable.ps1` — were not hitting either core bug (the PS1 implementation used separate correct logic paths for both). **Single-quote edge case in the manifest parser fixed** as a consistency improvement. Existing double-quoted manifests are unaffected.
- **`portable-manifest.example.yaml`** — no changes needed. The existing example is correct and now works on both platforms as advertised.

### Verification

- **With manifest (Linux):** 54 files packed from a real project manifest including band profiles, companion docs, playlist artifacts, and session findings. All customized inclusions present.
- **Without manifest, defaults only (Linux):** 42 files packed, including both top-level band profiles. Before the fix, band profiles were silently excluded.
- **PowerShell:** regex change validated by inspection for single-quote handling. No behavior change for double-quoted patterns.

### Version Bumps

- `package.json`: 1.6.3 → 1.6.4
- `src/skills/suno-setup/assets/module.yaml`: 1.6.3 → 1.6.4
- `.claude-plugin/marketplace.json`: 1.6.3 → 1.6.4
- `INSTALLATION.md`: 1.6.3 → 1.6.4

### Scope Note

This is a **bash and PowerShell script-only release** — no reference doc changes, no schema changes, no new files created. Safe drop-in replacement for v1.6.3. Existing `portable-manifest.yaml` files do not need to be updated; they will start working correctly on Linux/macOS with no changes.

---

## [1.6.3] - 2026-04-10

### v5.5 Voice Gravity Principle + Production Observations

An additive findings release capturing new knowledge discovered during a live Voice track production session (song: *Observation*, an adult alternative / heartland southern rock track using a v5.5 Voice clone trained on soft rock / folk material). No bug fixes, no API changes — three reference files gain new production-validated guidance.

### Added

- **`suno-style-prompt-builder/references/model-prompt-strategies.md`** — Major expansion of the "Getting the best voice clone" section and new subsection "The v5.5 Voice Gravity Principle" with six practical rules and a validated case study. Key additions:
  - **Voice Gravity Principle:** v5.5 Voice clones carry trained genre gravity and pull generations toward their training baseline on their own. When a song's target genre differs from the Voice's trained direction, the style prompt must actively fight against that gravity rather than describing the target.
  - **Six practical rules:** (1) drop descriptors the Voice already delivers, (2) load descriptors pulling against the Voice's direction, (3) Style Influence 65+ for Voice-genre mismatch, (4) never specify Vocal Gender when a Voice is active, (5) Voice-aware exclusion strategy (drop harsh-vocal protections when the clean Voice can't produce them), (6) Audio Influence floor caution for non-Professional Voices.
  - **Consistency-vs-variety resolution:** Reconciles the apparent tension between JG BeatsLab's "consistency within a clip wins" and HookGenius's "three clips across moods helps" — both are correct at different scales. Consistency within a single sample, variety across multiple Voice profiles.
  - **Re-recording guidance:** 20-30 sec optimal length per clip, Professional skill level mandatory (not cosmetic — cannot be changed after recording), preserve vocal quirks rather than smoothing them, sibilance mic-technique solution (off-axis positioning 15-30°).
  - **Validated case study:** Documents the specific iteration path from a failed first attempt (folk-descriptors-duplicating-Voice + Audio Influence 20% + keyboards + unhurried tempo) to the working solution (heartland southern rock + overdriven guitar + Audio Influence 55% + keyboards killed + rock urgency).

- **`suno-style-prompt-builder/references/model-prompt-strategies.md`** — Three new entries in the Genre Term Behavior Table:
  - **`heartland rock`** — safe rock term for Voice tracks (no harsh vocal trigger)
  - **`southern rock`** — safe vocal-wise; may pull slide/steel guitar (exclude if unwanted)
  - **`heartland southern rock`** — validated combined term for Voice tracks needing rock presence without metal pull

- **`suno-lyric-transformer/references/metatag-reference.md`** — New subsection "Isolated parentheticals as performed speech" documenting production observation that parentheticals placed on their own indented lines (not attached as `word(echo)`) are often delivered as **spoken interjections** rather than sung backing vocals. Works with v5.5 Voices despite the docs cautioning against spoken-word use — brief interjections are a different case from sustained `[Spoken Word]` sections.

- **`suno-band-profile-manager/references/profile-schema.md`** — Expanded "Voices (v5.5)" Notes for Downstream Skills bullet with the six Voice Gravity Principle rules (profile-schema form) and a new "Multi-profile Voice strategy" note explaining how profiles can reference multiple Voice IDs for projects with several Voice recordings (e.g., "Narrative Rock," "Ballad Intimate," "Speak-Sing Confessional"), with consistency-within-sample + variety-across-samples as the guiding principle.

### Sources

- [JG BeatsLab — Suno v5.5 Voices Tested (Day One Findings)](https://www.jgbeatslab.com/ai-music-lab-blog/suno-v5-5-voices-tested)
- [HookGenius — Suno v5.5 Guide: Voices, Custom Models & My Taste](https://hookgenius.app/learn/suno-v5-5-guide/)
- [Suno Knowledge Base — Use Your Voice in Suno](https://help.suno.com/en/articles/11362369)
- [Suno — How to Use Suno AI Voice Cloning (2026 Guide)](https://suno.com/hub/ai-voice-cloning)
- Production observation from *Observation* song iteration (2026-04-10) — validated fix path documented as case study

### Version Bumps

- `package.json`: 1.6.2 → 1.6.3
- `src/skills/suno-setup/assets/module.yaml`: 1.6.2 → 1.6.3
- `.claude-plugin/marketplace.json`: 1.6.2 → 1.6.3
- `INSTALLATION.md`: 1.6.2 → 1.6.3

### Scope Note

This is a **reference-file-only release** — no script behavior changes, no new files created, no schema changes. Purely additive documentation of production-validated Voice-track findings. Safe to pull as a drop-in replacement for v1.6.2 with no migration needed.

---

## [1.6.2] - 2026-04-10

### Reference File Consolidation & Broken Link Cleanup

A small architectural cleanup that addresses the v1.6.1 known follow-up. The marketplace PR ([bmad-code-org/bmad-plugins-marketplace#7](https://github.com/bmad-code-org/bmad-plugins-marketplace/pull/7)) is being updated to point at this release.

### Removed

- **Three root-level reference duplicates** — `SUNO-REFERENCE.md`, `USAGE.md`, and `STUDIO-EDITOR-REFERENCE.md` previously existed both at the repo root and inside `src/skills/suno-agent-band-manager/references/`. They had silently drifted out of sync between releases (the v1.6.0 wording fix only landed in some copies, requiring the v1.6.1 sync). The `src/skills/suno-agent-band-manager/references/` versions are now the **only** canonical copies, eliminating the drift class entirely.

### Updated

- **`README.md`** — Markdown links to the reference docs now point at the canonical `src/skills/suno-agent-band-manager/references/...` paths. Added `USAGE.md` to the references directory tree (it was already there on disk; the diagram just hadn't listed it).
- **`INSTALLATION.md`** — Aider command updated to read the canonical paths:
  ```bash
  aider \
    --read src/skills/suno-agent-band-manager/references/SUNO-REFERENCE.md \
    --read src/skills/suno-agent-band-manager/references/USAGE.md
  ```
- **`CLAUDE.md` / `GEMINI.md` / `AGENTS.md`** — cross-reference list updated to use the canonical USAGE.md path.

### Fixed (pre-existing broken links discovered during the audit)

- **`src/skills/suno-feedback-elicitor/references/suno-parameter-map.md`** — `[STUDIO-EDITOR-REFERENCE.md](../../STUDIO-EDITOR-REFERENCE.md)` resolved to `src/skills/STUDIO-EDITOR-REFERENCE.md`, which has never existed at that path. Now points at `../../suno-agent-band-manager/references/STUDIO-EDITOR-REFERENCE.md`.
- **`src/skills/suno-band-profile-manager/references/tier-features.md`** — Same broken pattern, same fix.

These had been broken since the references/ folder layout, but were never noticed because nothing automatic exercised the markdown links.

### Marketplace Submission

The community module PR will be rebased to point at the v1.6.2 commit SHA so reviewers see the consolidated version with no drift risk.

---

## [1.6.1] - 2026-04-10

### Cross-Platform Hardening & Stale Reference Cleanup

A follow-up release to v1.6.0 closing two open issues that surfaced after the marketplace submission. The marketplace PR ([bmad-code-org/bmad-plugins-marketplace#7](https://github.com/bmad-code-org/bmad-plugins-marketplace/pull/7)) is being updated to point at this release.

### Fixes

- **Fixes #21** — **Gemini CLI: skills not discoverable and activation protocol not followed.** Two layered fixes:
  - **`link-skills.sh` and `link-skills.ps1`** now create symlinks in `.gemini/skills/` in addition to `.claude/skills/` and `.agents/skills/`. Gemini CLI's glob does not always follow symlinks under `.agents/skills/`, so a native scan path is required for reliable skill discovery.
  - **New standing-order files at the repo root** — `CLAUDE.md`, `GEMINI.md`, `AGENTS.md` (identical content) — make the skill activation discipline explicit and tool-agnostic. They mandate: running pre-activate scripts, reading persona/creed/capabilities/activation/memory-system reference files, presenting the dynamic menu from script output (not improvising from `SKILL.md` text), loading voice context before greeting, and the Suno Pipeline Rule. Previously, this discipline lived only inside individual `SKILL.md` files in a declarative style that Claude Code's harness compensated for but Gemini CLI / Codex CLI / OpenCode interpret more literally. The standing-order files are auto-loaded by each respective LLM CLI on every session.
  - The deeper imperative-style refactor of individual `SKILL.md` files (a recommendation in the issue) is intentionally deferred to a future release — the standing-order approach addresses the symptom directly with much less surface area to maintain.

- **Fixes #22** — **Inconsistent character limit guidance and stale research findings across module.** Comprehensive sweep of remaining stale references after the v1.6.0 wording fixes:
  - **Synced three duplicate file pairs** — `SUNO-REFERENCE.md`, `USAGE.md`, and `STUDIO-EDITOR-REFERENCE.md` exist as both top-level files (read by Aider via `--read`) and inside `src/skills/suno-agent-band-manager/references/`. They had drifted out of sync, causing the v1.6.0 wording fix to land in only one copy of each pair. All three pairs are now identical and reflect the canonical v5.5 critical-zone wording.
  - **Updated three stale "4-7 descriptors" references** to "5-8 descriptors" — the v1.4.1 HookGenius update changed the sweet spot but didn't propagate to `src/skills/suno-style-prompt-builder/SKILL.md`, `src/skills/suno-style-prompt-builder/references/README.md`, or `src/skills/suno-agent-band-manager/references/README.md`.
  - The two specific complaints in issue #22 about `suno-parameter-map.md` lines 372/375 and `SKILL.md` lines 116/162 were verified as **false alarms** — those lines are correctly scoped to v4 Pro (which DOES have a 200-char hard limit) and the Exclude Styles input field (separate constraint), respectively. No edits needed.

### Known Follow-Ups

- **Duplicate file pairs** between root and `src/skills/suno-agent-band-manager/references/` (`SUNO-REFERENCE.md`, `USAGE.md`, `STUDIO-EDITOR-REFERENCE.md`) are kept in sync manually as of v1.6.1. A future release should consolidate to a single canonical location and update Aider documentation accordingly.

### Marketplace Submission

The community module PR ([bmad-code-org/bmad-plugins-marketplace#7](https://github.com/bmad-code-org/bmad-plugins-marketplace/pull/7)) will be rebased to point at the v1.6.1 commit SHA so reviewers see the cross-platform-hardened version.

---

## [1.6.0] - 2026-04-09

### BMad Plugins Marketplace Submission

This release packages the module for submission to the [BMad Plugins Marketplace](https://github.com/bmad-code-org/bmad-plugins-marketplace) as a community module under `design-and-creative` / `audio`. Version `1.6.0` consolidates the unreleased v1.5.0/v1.5.1/v1.5.2 work plus marketplace-prep cleanup.

### Marketplace Packaging

- **Added `.claude-plugin/marketplace.json`** at repo root, registering all six skills (suno-agent-band-manager, suno-band-profile-manager, suno-style-prompt-builder, suno-lyric-transformer, suno-feedback-elicitor, suno-setup) under the BMad Builder distribution format.
- **Module quality validation pass** — Re-ran `bmad-module-builder` Validate Module against `src/skills`. All structural checks pass; CSV registration audited against actual skill behavior.

### Privacy & Repo Hygiene

- **Expanded `.gitignore`** — `docs/`, `.claude/`, `.gemini/`, `.agents/`, `_bmad/`, `_bmad-output/`, and `portable-manifest.yaml` are now properly excluded so personal user content (voice files, songbook, band profiles, audio, WIP files) stays out of the repo.
- **Removed `docs/{band-slug}-playlist.yaml`** from tracked files. Personal album content should never have been tracked.
- **Genericized personal references** in source: `analyze-audio.py` docstring, `memory-system.md` example name, `reconcile.md` companion-file pattern guidance now uses dynamic discovery via the voice file's Companion Files table rather than hardcoded family-history wildcards.

### Cross-Platform Support

- **PowerShell counterparts** for all three shell utilities:
  - `link-skills.ps1` — Windows symlink installer (uses Developer Mode or elevation)
  - `scripts/pack-portable.ps1` — Windows portable archive creator
  - `scripts/unpack-portable.ps1` — Windows portable archive extractor
- **`INSTALLATION.md` Windows guidance** — bash and PowerShell command pairs for Standalone, BMad Method, and Update flows. Updated Windows symlink troubleshooting note.

### Portable Sync Improvements

- **`pack-portable.sh` defaults trimmed** to documented module conventions only (`docs/voice-context-*.md`, `docs/songbook/**/*.md`, `docs/band-profiles/**/*.yaml`, `docs/wip-*.md`). User-specific patterns moved to manifest examples.
- **New `portable-manifest.example.yaml`** at repo root — copy to `portable-manifest.yaml` and customize. Clearly documents the manifest format with commented examples for companion files, playlist artifacts, session findings, and other custom patterns.
- **New "Multi-Machine Sync" section** in `INSTALLATION.md` explaining the pack/unpack workflow and manifest customization.

### CSV Registration Fixes

- **`suno-feedback-elicitor`** — cleared the `before` column. Previously it duplicated the `after` column (`suno-style-prompt-builder:build-style-prompt,suno-lyric-transformer:transform-lyrics`), creating a logical cycle. Feedback elicitor runs *after* the builders; the iteration loop back during refinement is implicit in the refine flow, not a CSV ordering relationship.
- **`suno-lyric-transformer`** — removed `analyze` from the Transform Lyrics (TL) headless args list. The dedicated Analyze Lyrics (AL) row is the canonical analyze entry; TL now cleanly maps to `transform|refine`.
- **`suno-style-prompt-builder`** — enriched description to surface wild card variants, exclusion prompts, and creativity modes (previously a generic "model-aware Suno style prompts" line that hid these capabilities).

### Version Drift Resolved

Three different version values were floating across the module before this release:

- `module.yaml` was at `1.4.0`
- `package.json` was at `1.4.1`
- Latest git tag was `v1.5.2`

All four locations now sync to `1.6.0`: `module.yaml`, `package.json`, `.claude-plugin/marketplace.json`, and the `INSTALLATION.md` config example.

### Includes Unreleased Work from v1.5.0 / v1.5.1 / v1.5.2

The intermediate v1.5.x tags shipped without changelog entries. Notable work folded into this release:

- **Pipeline guard hook (v1.5.1)** — Stop hook script `scripts/pipeline-guard.py` enforces mandatory skill invocation; blocks responses containing a Suno package when `suno-style-prompt-builder` and `suno-lyric-transformer` weren't run during the session.
- **State reconciliation (v1.5.2)** — `reconcile.md` workflow for detecting and fixing stale references across docs and sidecar files when authoritative data changes.
- **Cross-platform pipeline guard setup (v1.5.2)** — `suno-setup` offers to configure the Stop hook and AGENTS.md standing order automatically.
- **NOLA voice / section tag guidance / cross-skill references (v1.5.0)** — Reference doc updates for vocal direction patterns and metatag conventions.
- **Dual-voice limitation documentation** — Suno v5/v5.5 cannot reliably produce two distinct same-gender voices; documented workarounds (Persona OFF + Replace Section, gender contrast, nu-metal/metalcore framing).
- **Bidirectional companion files audit** — Stale file reference detection in `reconcile.md`.
- **Pipeline guard transcript parsing fix** — Now correctly parses nested `tool_use` entries.
- **Package assembly headless mode** — Parallel execution and suppression of intermediate output when running the full pipeline non-interactively.
- **Refinement presentation cleanup** — Show only what changed in refinement output, not the full package.

---

## [1.4.1] - 2026-04-06

### Suno v5.5 Community Research Update

Comprehensive reference documentation update integrating independent community testing results from JG BeatsLab, HookGenius (1000+ prompt analysis), AudioNewsRoom, JackRighteous, BlakeCrosley, GenxNotes, and others. All findings sourced and linked for independent verification.

### Corrections

- **v5.5 model codename** — Fixed from "chirp-crow" (that's v5) to the correct "chirp-fenix"
- **Voices Audio Influence ranges** — Corrected based on JG BeatsLab testing. Real sweet spot is 40-60%, not 55-70%. Quality degrades above 70%; at 85% resemblance only reaches ~70% with increasing artifacts. Updated across SUNO-REFERENCE, model-prompt-strategies, and suno-parameter-map.
- **Style Personas are NOT gone** — Clarified that Personas coexist with Voices in the v5.5 Voices tab. The button changed but both features remain available.
- **Descriptor count sweet spot** — Updated from "4-7" to "5-8" based on HookGenius 1000+ prompt analysis across all reference files and quick-reference tables.

### New Findings — v5.5 Features

- **Voices Skill Level dropdown** — Beginner/Intermediate/Advanced/Professional setting is NOT cosmetic; actively reshapes model interpretation. Always use Professional for most stable results.
- **Voices limitations** — Directional influence, not true reproduction. Not suitable for spoken word/narration (drifts toward singing). Realistic for demos and pre-production.
- **My Taste magic wand / Style Augmentation** — Documented the wand icon in Create form that auto-generates personalized style prompts. Manual prompts always override. Can be viewed/edited/disabled from avatar menu.
- **Custom Model training best practices** — WAV at 44.1kHz preferred, 8-12 consistent tracks sweet spot, auto-normalization pipeline (RMS leveling, DC offset removal, spectral masking, onset detection, key/scale estimation), overfitting mitigation guidance.
- **Custom Model prompt strategy shift** — With Custom Models, priority changes from genre-first to mood/production-first. Formula: MOOD + PRODUCTION TEXTURE + ENERGY/TEMPO + INSTRUMENTS + VOCAL DIRECTION.
- **Custom Model consent/privacy** — Grants Suno permission to use data for global model training (not optional, not private).

### New Findings — Style Prompt Strategies

- **"Cinematic" as universal modifier** — Consistently elevates production quality across every tested genre.
- **Production tags most underused** — Adding even one meaningfully improves distinctiveness.
- **Conflicting tags produce bland compromise** — Opposing descriptors cancel out, not creative tension.
- **Callback phrasing during Replace/Extend** — "Continue same chorus energy" anchors consistency.
- **Style Influence above ~80 plateaus** — Rarely improves accuracy, can reduce vocal phrasing variation.

### New Findings — Extend Drift Solutions

- **Weirdness strongest during Extend/Bridge** — Primary cause of style drift. Keep conservative during Extend.
- **Anchor note restating** — Restate genre, mood, key, instrument palette with each extension.
- **Forbidden element phrasing** — "No new hooks/drums/riffs" more effective than positive instruction alone.
- **2-3 extension chain limit** — Quality degrades beyond that. Cover feature re-synthesizes to clean signal path.
- **Persona instability with Extend** — Personas historically unreliable during Extend operations.
- **Extend Anti-Drift Toolkit** — 7-technique ranked guide added to suno-parameter-map.
- **Genre-specific outro templates** — Gospel, Rock, Lo-fi, EDM, Reggae ending patterns.

### New Findings — Metatags

- **Asterisk sound effect syntax** — `*rainfall*`, `*vinyl crackle*` etc. confirmed working as inline sound effects. Exception to "no asterisks" rule.
- **New Effect tags** — `[Effect: Bitcrusher]`, `[Effect: Autopan]`, `[Effect: Sidechain]`
- **`[Callback: ...]` upgraded** — HIGH reliability for Extend/Replace workflows (community-validated). Experimental for standard generation.
- **Ending tag variants** — `[Soft End]`, `[Dramatic End]`, `[Instrumental End]`, `[Slow Fade Out]`, `[Fast Fade Out]`, `[Instrumental Fade Out]`, `[Cinematic Fade Out]`
- **Noodling-prevention combo** — `[Outro] descriptive text [End]` stacking more effective than either alone.
- **Accelerando/Ritardando grid-loss warning** — Can lose rhythmic grid for remainder of track. BPM tag as recalibration anchor after disruption.
- **Three-layer vocal specification** — Character + Delivery + Effects for maximum vocal control.
- **Vocal delivery reliability tiers** — HIGH/MEDIUM/LOW classification from HookGenius 300+ tag testing.
- **Non-functional tags documented** — `[Bilingual]`, `[Spanglish]`, `[Live Version]`, `[Mono]`, `[Wide Stereo]`, `[Clean Lyrics]`/`[Explicit]` confirmed ineffective.
- **Falsetto confirmed LOW reliability** — Style prompt phrasing more effective than metatag.

### New Findings — Studio & Editing

- **Replace Section sweet spot 15-20 seconds** — Under 5 = disjointed, over 30 = model loses thread.
- **Heal Edits technique** — Apply on the following section after Replace to blend timbre shifts.
- **Remaster is full regeneration** — Not a filter. Instrumentals benefit more than vocals. "Improved fidelity with reduced soul." One pass usually sufficient.
- **Remove FX boosts loudness up to 5 LUFS** — Check levels after applying.
- **EQ for AI shimmer** — Roll off ultra-highs on stems with generation artifacts.
- **Genre-specific Warp Marker quantize** — EDM tight, Trap medium, Afrobeat light-medium, Soul/R&B light.
- **Credit waste prevention framework** — 0-50 learning, 50-80 discipline, 80+ stop and export.
- **Known bugs** — "Scratched CD" loop effect, Lyric Cache bug on Replace Section.
- **Aggressive mastering limiter** — Export raw stems for professional release.

### Documentation

- Added community research sources with URLs to SUNO-REFERENCE, model-prompt-strategies, metatag-reference, STUDIO-EDITOR-REFERENCE, and suno-parameter-map
- Updated validation dates across all reference files to April 6, 2026
- Created CHANGELOG.md

### Files Changed

- `suno-agent-band-manager/references/SUNO-REFERENCE.md`
- `suno-agent-band-manager/references/STUDIO-EDITOR-REFERENCE.md`
- `suno-style-prompt-builder/references/model-prompt-strategies.md`
- `suno-feedback-elicitor/references/suno-parameter-map.md`
- `suno-lyric-transformer/references/metatag-reference.md`
- `package.json`

---

## [1.4.0] - 2026-04-02

Update to BMB v1.5.0 standards, rename module from bmad-suno-* to suno-*.

---

## [1.1.3] and earlier

See git history for prior releases.
