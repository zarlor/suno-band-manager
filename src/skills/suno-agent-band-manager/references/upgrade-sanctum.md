# Mac — Upgrading the Sanctum to a New Module Version

**Language:** Use `{communication_language}` for all output.

A module update ships new template and discipline text; it never reaches the sanctum on its own. The wake's `template_upgrade` says what is waiting (a warning names the counts). The same flow finishes a v2 conversion (`references/upgrade-v2.md`) and runs whenever the owner asks.

**The outcome:** the sanctum on the shipped format, with every line of the owner's, and every learning Mac wrote into his own files, carried into it. A template never replaces the owner's text; their lines are integrated, in their words, and the script checks each one landed before it writes.

## How the script decides

`upgrade-sanctum.py` compares three texts per section or discipline file: the live one, the one shipped now, and the base (the shipped text the sanctum last took, in `memory/.template-base.json`). Text nobody changed updates; the owner's edits and the template's merge when they touch different lines; text the owner changed and the template changed in the same place, or text with no base on record (a converted or pre-record sanctum), is **integrate**: Mac's job, below. A difference the owner made while the template stayed the same is theirs and is never proposed.

## Steps

1. **Plan.** `uv run {skill-root}/scripts/upgrade-sanctum.py --project-root "{project-root}" --format json`.

2. **Safe changes.** `--apply safe` writes missing folders and files, new sections, the regenerated roster, updates and clean merges. None of them can lose a line of the owner's. Tell the owner in a line what moved.

3. **Each integrate change.** It carries `owner_lines` (the lines the new template doesn't hold), the live-vs-template `diff`, a `template_diff` when a base is on record (what the module changed), and `incident` when the discipline's story file is missing. Read the live text and the new template, then write the new-format text: the new template's structure, wording and rules, with each owner line placed where the new format gives it a home.
   - **A rule, override or learning** stays in the section or discipline, verbatim with its hedges, date and quote. An override of a shipped default says it is an override and keeps the owner's words.
   - **A story** (a dated miss, the quote about what went wrong, the real songs behind an example) goes to `memory/incidents/<file>`. Write or extend that file first. When `incident` names a missing file, build it from the shipped story's structure with the owner's own cases in place of the illustrative ones.
   - **A preference the module now offers as a setting** (a `bmad setup suno` question): tell the owner the setting covers it and what value matches what they asked for. Only once it is set does the line drop, with that as its reason. Until then it stays in the text.
   - **Earlier shipped wording** that the new template restates or replaces may drop, listed with its reason. When it isn't plainly the module's old text, it is the owner's: keep it.

   Write the section (heading included) or the whole discipline file to a scratch file, the dropped lines to a JSON list of `{"line": ..., "why": ...}`, and run `--integrate <id> --text <file> [--also memory/incidents/<file>] [--dropped <file>]`. A refusal lists the lines it couldn't find: place them and run it again. Never list a line in `--dropped` to get past the check. The previous text lands in `raw/` as a distilled record of the integration, beside the usual backup.

4. **Show the owner what landed**, per change, in a few lines: which of their lines went where, and what dropped as old shipped wording. They correct; the correction goes in directly.

5. **Keep, on request.** When the owner wants their version exactly as it is instead of the new format, `--keep <id>`. It comes back, with the module's change shown, only when the template changes again.

6. **Note it** in the session note: what upgraded, what was integrated where.

## Headless and Pulse

No one is there to see an integration, so none happens: a headless run applies `--apply safe` (Pulse applies nothing, it never edits identity files) and puts a line in `memory/pending.md` naming the integrate changes, for the next live session.
