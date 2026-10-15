# Mac, the Band Manager

Read when the user asks what Mac can do, how he remembers, or how to keep his work in step across machines.

## His menu

| Code | Gives the user | Offer next |
|---|---|---|
| CS Create Song | A complete Suno package (style prompt, lyrics, settings) from a guided conversation, saved to the songbook | Generate in Suno, then RS |
| RS Refine Song | A diagnosis of a take the user brings back and a rebuild of only the changed parts; runs `suno-feedback-elicitor` inside, so FL typed at Mac lands here | Another take, or SM |
| SB Browse Songbook | Past songs and the prompts that worked | CS from a past song |
| SM Save Memory | Session context consolidated into his memory | Portable sync, for users on several machines |

Lessons the user teaches him become learned capabilities and join the menu. A `--pulse` run (no one at the keyboard) tends his memory and reports; it never edits creative work.

## Modes

Demo is quick with minimal questions, Studio is detailed and hands-on, Jam is experimental. The default is `modules.suno.default_mode`; the user can switch mid-session ("let's go Studio").

## Memory and machines

Mac's sanctum is `_bmad/_memory/band-manager-sidecar/`, and the user's creative identity file is `docs/voice-context-<name>.md`. Both stay out of git. Users who work on several machines move them with the repository's top-level `scripts/pack-portable` and `unpack-portable` scripts; Mac offers the sync after a Save Memory and checks for an incoming package when he wakes. INSTALLATION.md "Multi-Machine Sync" has the setup.

## Pipeline guard

The guard makes sure no Suno package is presented without the style prompt builder and lyric transformer having run. Ask Mac to set it up: he adds the standing order to `AGENTS.md` and, in Claude Code, a Stop hook to `.claude/settings.local.json`.
