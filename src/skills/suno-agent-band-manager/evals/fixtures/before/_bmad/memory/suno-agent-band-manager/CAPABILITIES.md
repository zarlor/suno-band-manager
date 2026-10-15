# Capabilities

## Built-in

_Generated from Mac's `assets/menu.csv` (the same source as the menu)._

| Code | Name | What it does | Runs |
|------|------|--------------|------|
| [CS] | Create Song | Create a complete Suno-ready song package with style prompt + lyrics + parameters through guided creative conversation. | `references/create-song.md` |
| [RS] | Refine Song | Bring back a Suno take: diagnose what's off and rebuild the changed parts of the package (uses the Feedback Loop inside). | `references/refine-song.md` |
| [SB] | Browse Songbook | Browse past songs and successful prompts from your creative history. | `references/browse-songbook.md` |
| [SM] | Save Memory | Save current session context to Mac's memory for next time. | `references/save-memory.md` |
| [MB] | Manage Bands | Create, edit, list, duplicate, or delete band identity profiles with genre, vocal direction, and writer voice. | skill: `suno-band-profile-manager` |
| [WV] | Analyze Writer Voice | Extract writing voice patterns from samples and store in a band profile. | skill: `suno-band-profile-manager` |
| [HC] | Profile Health Check | Assess profile completeness and quality beyond structural validation. | skill: `suno-band-profile-manager` |
| [MP] | Manage Playlist | Scaffold or edit a band's canonical playlist YAML: add, reorder, or rename tracks. | skill: `suno-band-profile-manager` |
| [SP] | Build Style Prompt | Generate model-aware Suno style prompts with creativity modes, wild card variants, and exclusion prompts optimized for your chosen model tier. | skill: `suno-style-prompt-builder` |
| [TL] | Transform Lyrics | Transform poems and text into Suno-ready structured lyrics with metatags and cliche detection. | skill: `suno-lyric-transformer` |
| [AL] | Analyze Lyrics | Analyze raw text for song structure potential without transforming — returns structure analysis, syllable patterns, and character budget. | skill: `suno-lyric-transformer` |
| [AA] | Analyze Audio | Measure a render's tempo, key and loudness, plus a section map against its lyrics when the PyTorch audio tools are on. | skill: `suno-feedback-elicitor` |
| [PS] | Sequence Playlist | Order tracks into an album-craft playlist: energy arcs, Camelot transitions, locked arcs, encore design, with per-move rationale. | skill: `suno-playlist-sequencer` |

Typing FL or "feedback loop" routes to [RS] Refine Song, which runs the feedback skill inside it.

## Learned

_Capabilities the owner taught Mac. Prompts live in `capabilities/`; rows here appear on Mac's menu._

| Code | Name | Description | Source | Added |
|------|------|-------------|--------|-------|

## How to Add a Capability

Tell Mac "I want you to be able to do X" and you build it together. Mac loads `references/capability-authoring.md` (and holds the prompt-quality canon while authoring), saves the prompt to `capabilities/`, and registers it here.

