# Workshop Capture Discipline — Verbatim Material to Durable File Before Discussion

Verbatim creative material goes into the song's WIP file before you discuss it. Conversation doesn't survive, and session transcripts are no fallback — they are per-machine, outside the portable sync and version control — so the WIP file is the only durable record, for your own swings, an external LLM's and the owner's writing alike.

**Triggers:** you draft a lyric swing, structural sketch or image fragment inline, whether or not it looks like a keeper; the owner pastes lyric or prose from outside this conversation (another LLM such as Gemini or ChatGPT, their own writing in another tool, an old draft); shares an image of a lyric, structure or fragment; dictates a swing to keep; describes a swing done elsewhere and asks to fold it in; points at any external-agent output for the workshop, even "just to show direction".

**Steps, before responding to or with the material:**

1. Capture it with the script, which finds or creates the WIP file (`docs/wip-{title}-fragments.md`, or `--file` for the songbook entry being workshopped), appends the material byte for byte under "Swings tried", attributed and dated, and checks nothing else in the file moved: `uv run {skill-root}/scripts/capture_wip.py "{project-root}" --title "{working title}" --source "{who wrote it}" --label "Swing N — {anchor}" --framing "{what prompted it, which iteration}"` with the material on stdin through a quoted heredoc (`<<'SWING'`, so backticks and `$` stay literal; no temp file). Hand it the text exactly as written or pasted, never a cleaned-up copy.
2. Before you critique it or draft against it, read the band profile the song belongs to: its line-length, voice and genre rules hold for every swing, yours and the owner's.
3. Once a critique is given, attach it to the same entry: `... --label "Swing N — {anchor}" --critique "{the critique}"`, giving the entry's whole label (a refusal lists the file's entries). Every swing gets its critique there, yours included.
4. Then respond. If the script refuses, say so and capture by hand the same way before going on. A swing you draft goes into the response and the WIP in the same turn, not rewritten at session close, when swings have blurred or the session may already be gone.

**Line lengths come from the script, never by ear.** The capture's JSON carries `line_syllables`, one count per line.

- Count your own draft first with `--dry-run` (it writes nothing), and capture or show it only once every line meets the profile's rule; a swing of yours that breaks the rule is reworked first.
- A count quoted in a critique is copied from that output, never typed from memory.
- A critique that calls the owner's lines too short or too long names the profile's figure.

**Your own lines are swings too.** A counter-swing goes to the WIP, and so does any line you offer inline in a reply.

**A captured entry is never edited.** A correction to it is another `--critique` note, not a change to the file (`sed`, a rewrite): the script checks that nothing else in the file moved, and a hand edit breaks the record that check protects.

A "swings tried" section carries each rejected swing's text with the critique that followed: "Tried image-driven angle, rejected for incoherence", or a label like "Swing 4 — 'Same voice X' anchor, rejected", is not the material. Rejected swings are part of the song's record; the owner needs the text to decide later whether to come back to an approach.

**Before a portable sync pack (`pack-portable.sh`):** if the session involved workshop activity — your swings, pasted material, the owner's shared writing — confirm every swing it referenced is in a WIP verbatim, not just described, whether or not the workshop produced a winner.

_The incident behind this rule: `memory/incidents/workshop-capture.md` (read it only when auditing or questioning the rule)._
