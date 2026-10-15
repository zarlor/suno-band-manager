# Band profiles

Read when the user asks what a band profile is for or how to maintain one.

A band profile is a YAML file in `modules.suno.band_profiles_folder` that every other skill reads: genre and sub-genre, vocal direction, instrumentation, model preferences, exclusion defaults, and the writer's voice. One profile per band; duplicate a profile to try a variant without touching the original.

| Operation | Gives the user | Offer next |
|---|---|---|
| Manage Bands | Create, list, load, edit, duplicate or delete (archived, never wiped) a profile | A style prompt or a song with Mac |
| Analyze Writer Voice | Voice patterns drawn from writing samples, stored in the profile so lyrics keep the writer's voice | `suno-lyric-transformer` |
| Profile Health Check | Completeness and quality beyond structural validation, with what to fill next | Edit the gaps |
| Manage Playlist | The band's playlist file (`docs/<band>-playlist.yaml`): add, reorder or rename tracks | `suno-playlist-sequencer` |

Every operation can also run headless (`--headless:create|edit|load|delete|duplicate|validate`) for scripted use.
