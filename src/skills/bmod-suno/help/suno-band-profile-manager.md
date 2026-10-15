# Band profiles

Read when the user asks what a band profile is for or how to maintain one.

A band profile is a YAML file in `modules.suno.band_profiles_folder` that every other skill reads: genre and mood, vocal direction (or instrumental), a style baseline, model and tier, exclusion defaults, the writer's voice, and the band's accumulated learnings. One profile per band; duplicate a profile to try a variant without touching the original. Each band also keeps a decision log beside its profile, so the reasoning behind its choices survives months of edits. Use the skill directly for profile work on its own; talk to Mac when the profile work is part of making a song.

| Operation | Gives the user | Offer next |
|---|---|---|
| Manage Bands | Create, list, load, edit, duplicate or delete (archived, never wiped) a profile; edits keep the file's comments, key order and quoting, and list fields grow by append | A style prompt or a song with Mac |
| Analyze Writer Voice | Voice patterns drawn from 3-5 writing samples, stored in the profile so lyrics keep the writer's voice | `suno-lyric-transformer` |
| Profile Health Check | Completeness and quality beyond structural validation, with what to fill next, and this session's learnings recorded | Edit the gaps |
| Manage Playlist | The band's playlist file (`docs/<band>-playlist.yaml`): scaffold it, add a published track, rename one, fix a file name | `suno-playlist-sequencer` for reordering and album-craft sequencing, which it owns |

Every operation can also run headless (`--headless:create|edit|append|load|delete|duplicate|validate|scaffold-playlist`, bare `--headless` lists) for scripted use and for the other skills, which write a band's generation history and learnings through `append`.
