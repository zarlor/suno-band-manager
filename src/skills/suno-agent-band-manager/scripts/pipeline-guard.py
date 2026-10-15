#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Claude Code hooks for Mac: the pipeline guard (Stop) and the Dominion guard (PreToolUse).

**Stop hook (default).** When the assistant's last message carries a Suno
package, it checks three things, all from structure:

1. **Style Prompt Builder ran** when the package shows a style prompt, exclude
   styles or a wild card.
2. **Lyric Transformer ran** when the Lyrics section carries section tags
   (`[Verse]`, `[Chorus]`, ...). Auto-lyrics and instrumental packages pass.
3. **Package order** follows Suno's Create screen: Voice -> Lyrics -> Style
   Prompt -> Exclude Styles -> Settings -> Title -> Save to -> Wild Card.

A package is a message with a "Your Suno Package" heading, a Lyrics section
holding section tags, or a Style Prompt / Exclude Styles / Wild Card section
holding a code block -- so refine-song's lyrics-only update counts.

A skill counts as run only on structural evidence from the current turn (tool
calls after the owner's latest real prompt; tool results, skill bodies,
reminders and task notifications don't start a turn):

- a ``Skill`` tool_use naming it, in the main transcript or in the transcript
  of a subagent this turn spawned, heard back from, or messaged
  (``SendMessage``; then only what it did after the message counts);
- inside such a subagent: a Read of the skill's ``SKILL.md`` or a Bash run of a
  script in the skill's ``scripts/`` folder;
- the skill's headless return shape (JSON) in an Agent result -- the tool_result
  or the task notification: ``style_prompt`` with ``exclusion_prompt``,
  ``style_prompt_chars``, ``sliders`` or ``validation`` for the builder;
  ``transformed_lyrics`` with ``transformation_summary``, ``spacing_check``,
  ``source_hash`` or ``changes`` for the transformer. A ``blocked`` return
  doesn't count.

A skill that didn't run this turn isn't required when every section it owns
(style prompt, exclude styles and wild card for the builder; tagged lyrics for
the transformer) matches, whitespace-normalized, content it produced earlier
in the session: a field of its JSON return, or a section an earlier turn
presented after that skill ran in that turn. Any changed section still needs
the skill this turn.

What an Agent prompt says never counts. When the transcript, or a subagent
transcript the verdict depends on, can't be read, the guard can't tell: it
notes that on stderr and does not report a pipeline violation (the order check
still runs).

**PreToolUse hook (``--dominion``).** On Write/Edit while Mac is awake in the
session (a ``/suno-agent-band-manager`` command or a ``Skill`` call for it), a
target outside the sanctum is checked against the Dominion in the sanctum's
``CREED.md`` with ``validate-path.py``'s rules. A path the Dominion doesn't
allow gets an ``ask`` decision, so the owner approves or refuses the write.
When the sanctum, its CREED.md or ``validate-path.py`` is absent, or the
transcript can't be read, the hook stays silent (a note on stderr).

Both hooks read the Claude Code hook JSON on stdin, always exit 0, and are
installed by ``configure-guard.py``. Stdlib-only, run on bare ``python3`` so a
hook that fires on every turn stays fast.
"""

import argparse
import html
import json
import os
import re
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Claude Code hooks for Mac. Default (Stop hook): when the last "
            "assistant message holds a Suno package, block it unless "
            "suno-style-prompt-builder (style prompt, exclude styles or wild "
            "card shown) and suno-lyric-transformer (tagged lyrics shown) ran "
            "this turn -- judged from Skill tool calls, subagent transcripts "
            "and the skills' headless return shapes, never from prompt "
            "wording -- and unless sections follow Suno's Create-screen order "
            "(Voice, Lyrics, Style Prompt, Exclude Styles, Settings, Title, "
            "Save to, Wild Card). An unreadable transcript is not a violation: "
            "a note goes to stderr. --dominion (PreToolUse hook on "
            "Write/Edit): while Mac is awake, ask the owner before a write "
            "outside the sanctum that the CREED.md Dominion does not allow."
        ),
        epilog=(
            "Stop input: last_assistant_message, transcript_path, "
            "stop_hook_active; output on violation: {\"decision\": \"block\", "
            "\"reason\": ...}. PreToolUse input: tool_name, tool_input, "
            "transcript_path, cwd; output when not allowed: hookSpecificOutput "
            "with permissionDecision \"ask\". Exit code is always 0."
        ),
    )
    parser.add_argument(
        "--dominion",
        action="store_true",
        help="Run as the PreToolUse Dominion guard instead of the Stop pipeline guard",
    )
    return parser


STYLE_SKILL = "suno-style-prompt-builder"
LYRIC_SKILL = "suno-lyric-transformer"
AGENT_SKILL = "suno-agent-band-manager"
PIPELINE_SKILLS = (STYLE_SKILL, LYRIC_SKILL)
SANCTUM_REL = ("_bmad", "memory", AGENT_SKILL)
WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")


class TranscriptUnavailable(Exception):
    """The transcript the verdict depends on is missing or unreadable."""


def note(message: str) -> None:
    print(f"pipeline-guard: {message}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Package structure
# ---------------------------------------------------------------------------

# Lyrics carrying section tags are Lyric Transformer output. Auto-lyrics and
# instrumental packages show no tagged lyrics, so they need no transformer run.
SECTION_TAG_RE = re.compile(
    r"^\s*\[(?:Intro|Verse|Pre-Chorus|Chorus|Post-Chorus|Final Chorus|Bridge|"
    r"Outro|Hook|Refrain|Breakdown|Interlude|Instrumental Break|Solo|Drop|"
    r"Build)\b",
    re.IGNORECASE | re.MULTILINE,
)
INSTRUMENTAL_RE = re.compile(r"Instrumental \(no vocals\)", re.IGNORECASE)
FENCE_RE = re.compile(r"^\s*(```|~~~)", re.MULTILINE)
PACKAGE_TITLE_RE = re.compile(r"\bYour Suno Package\b", re.IGNORECASE)

HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)

# Package sections in Suno Create-screen order. Classification is by priority
# (first matching rule wins), so "Wild Card Style Prompt" is the wild card,
# not the style prompt.
PACKAGE_ORDER = (
    "Voice",
    "Lyrics",
    "Style Prompt",
    "Exclude Styles",
    "Settings",
    "Title",
    "Save to",
    "Wild Card",
)
STYLE_SECTIONS = ("Style Prompt", "Exclude Styles", "Wild Card")
_CLASSIFY = (
    ("Wild Card", re.compile(r"\bwild\s*card\b", re.IGNORECASE)),
    ("Exclude Styles", re.compile(r"\bexclu(?:de|sion)", re.IGNORECASE)),
    ("Style Prompt", re.compile(r"\bstyle prompt\b", re.IGNORECASE)),
    ("Lyrics", re.compile(r"\blyrics\b", re.IGNORECASE)),
    ("Settings", re.compile(r"^settings\b", re.IGNORECASE)),
    ("Save to", re.compile(r"^save to\b", re.IGNORECASE)),
    ("Title", re.compile(r"^(?:song\s+)?title\b", re.IGNORECASE)),
    ("Voice", re.compile(r"^(?:voice|persona|custom model|inspo)\b", re.IGNORECASE)),
)


def classify_heading(text: str) -> str | None:
    text = text.strip().strip("*").strip()
    for section, pattern in _CLASSIFY:
        if pattern.search(text):
            return section
    return None


def heading_blocks(message: str) -> list[tuple[str, str | None, str]]:
    """(heading text, package section or None, body up to the next heading)."""
    matches = list(HEADING_RE.finditer(message))
    blocks = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(message)
        heading = m.group(1).strip()
        blocks.append((heading, classify_heading(heading), message[m.end():end]))
    return blocks


def detect_suno_package(message: str) -> bool:
    """A package by structure: the package title heading, a Lyrics section with
    section tags, or a style-side section holding a code block."""
    for heading, section, body in heading_blocks(message):
        if PACKAGE_TITLE_RE.search(heading):
            return True
        if section == "Lyrics" and SECTION_TAG_RE.search(body):
            return True
        if section in STYLE_SECTIONS and FENCE_RE.search(body):
            return True
    return False


def package_sections(message: str) -> list[str]:
    """Package sections in the order their headings first appear."""
    seen: list[str] = []
    for _, section, _ in heading_blocks(message):
        if section and section not in seen:
            seen.append(section)
    return seen


def check_package_order(message: str) -> list[str]:
    """Return 'A should come before B' for each section that sits out of order."""
    sections = package_sections(message)
    rank = {name: i for i, name in enumerate(PACKAGE_ORDER)}
    problems = []
    for i, earlier in enumerate(sections):
        for later in sections[i + 1 :]:
            if rank[later] < rank[earlier]:
                problems.append(f"{later} should come before {earlier}")
    return problems


def needs_lyric_transformer(message: str) -> bool:
    """Tagged lyrics need the transformer; auto-lyrics and instrumentals don't.
    The Lyrics sections are read when there are any, else the whole message."""
    bodies = [body for _, section, body in heading_blocks(message) if section == "Lyrics"]
    text = "\n".join(bodies) if bodies else message
    if INSTRUMENTAL_RE.search(text):
        return False
    return bool(SECTION_TAG_RE.search(text))


def needs_style_builder(message: str) -> bool:
    """A shown style prompt, exclude list or wild card needs the builder.

    A package with no recognisable section headings is treated as a full
    package (the conservative reading), so it still needs the builder.
    """
    sections = package_sections(message)
    if not sections:
        return True
    return any(s in sections for s in STYLE_SECTIONS)


# ---------------------------------------------------------------------------
# Transcript reading
# ---------------------------------------------------------------------------


def _extract_tool_uses(entry: dict) -> list[dict]:
    """All tool_use items in a transcript entry (nested message.content[] or a
    flattened legacy tool_name/tool_input shape)."""
    tool_uses = []
    if entry.get("type") == "tool_use":
        tool_uses.append(entry)
    if entry.get("tool_name"):
        tool_uses.append({"name": entry.get("tool_name"), "input": entry.get("tool_input", {})})
    message = entry.get("message", {})
    if isinstance(message, dict):
        content = message.get("content", [])
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool_uses.append(item)
    return tool_uses


def _tool_results(entry: dict) -> list[dict]:
    message = entry.get("message", {})
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list):
        return []
    return [i for i in content if isinstance(i, dict) and i.get("type") == "tool_result"]


def _entry_text(entry: dict) -> str:
    message = entry.get("message", {})
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            i.get("text", "") for i in content if isinstance(i, dict) and i.get("type") == "text"
        )
    return ""


def _result_text(result: dict) -> str:
    content = result.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            i.get("text", "") for i in content if isinstance(i, dict) and i.get("type") == "text"
        )
    return ""


_NON_PROMPT_PREFIXES = (
    "<task-notification",
    "<local-command",
    "<system-reminder",
    "<teammate-message",
    "Another Claude session sent a message",
    "Stop hook feedback",
)


def is_owner_prompt(entry: dict) -> bool:
    """True when a transcript entry is a real prompt from the owner.

    Tool results, skill bodies and reminders (``isMeta``), background-task
    notifications, teammate (peer session) messages, subagent entries and
    Stop-hook feedback are not prompts, so they don't start a new turn.
    """
    if entry.get("type") != "user" or entry.get("isMeta") or entry.get("isCompactSummary"):
        return False
    if entry.get("isSidechain"):
        return False
    origin = entry.get("origin")
    if isinstance(origin, dict) and origin.get("kind") not in (None, "human"):
        return False
    if entry.get("promptSource") == "system":
        return False
    message = entry.get("message", {})
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, list):
        if any(isinstance(i, dict) and i.get("type") == "tool_result" for i in content):
            return False
    elif not isinstance(content, str):
        return False
    return not _entry_text(entry).lstrip().startswith(_NON_PROMPT_PREFIXES)


def read_entries(path: Path, needle: str | None = None):
    """Yield the dict entries of a JSONL transcript, streaming. With ``needle``,
    only lines containing it are parsed. Raises TranscriptUnavailable."""
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if needle is not None and needle not in line:
                    continue
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(entry, dict):
                    yield entry
    except (OSError, UnicodeDecodeError) as exc:
        raise TranscriptUnavailable(f"cannot read transcript {path}: {exc}") from exc


# ---------------------------------------------------------------------------
# Evidence that a skill ran
# ---------------------------------------------------------------------------

_DECODER = json.JSONDecoder()


def _json_objects(text: str) -> list[dict]:
    """Every top-level JSON object embedded in a text (fenced or bare)."""
    found = []
    for candidate in (text, html.unescape(text)) if "&" in text else (text,):
        i = 0
        while (i := candidate.find("{", i)) >= 0:
            try:
                obj, end = _DECODER.raw_decode(candidate, i)
            except ValueError:
                i += 1
                continue
            if isinstance(obj, dict):
                found.append(obj)
            i = end
        if found:
            break
    return found


def _shape_skill(obj: dict) -> str | None:
    if obj.get("status") == "blocked":
        return None
    if isinstance(obj.get("style_prompt"), str) and any(
        k in obj for k in ("exclusion_prompt", "style_prompt_chars", "sliders", "validation")
    ):
        return STYLE_SKILL
    if isinstance(obj.get("transformed_lyrics"), str) and any(
        k in obj for k in ("transformation_summary", "spacing_check", "source_hash", "changes")
    ):
        return LYRIC_SKILL
    return None


def skill_returns(text: str) -> list[tuple[str, dict]]:
    """(skill, object) for each pipeline-skill headless return in a text,
    nested ones included (the builder's wild card has the same shape)."""
    found: list[tuple[str, dict]] = []

    def walk(obj, depth):
        if isinstance(obj, dict):
            skill = _shape_skill(obj)
            if skill:
                found.append((skill, obj))
            if depth < 3:
                for value in obj.values():
                    walk(value, depth + 1)
        elif isinstance(obj, list) and depth < 3:
            for value in obj:
                walk(value, depth + 1)

    for obj in _json_objects(text):
        walk(obj, 0)
    return found


def skills_from_return(text: str) -> set[str]:
    """Pipeline skills whose headless return shape appears in an Agent result."""
    return {skill for skill, _ in skill_returns(text)}


# The returned fields a package shows verbatim, per skill.
RETURN_FIELDS = {
    STYLE_SKILL: ("style_prompt", "exclusion_prompt"),
    LYRIC_SKILL: ("transformed_lyrics", "flat_copy_lyrics"),
}


def normalize(text: str) -> str:
    return " ".join(text.split())


def _skill_from_skill_tool(tool_use: dict) -> set[str]:
    if tool_use.get("name") == "Skill":
        skill = (tool_use.get("input") or {}).get("skill", "")
        return {skill} if skill else set()
    return set()


def _skills_from_subagent_tool_use(tool_use: dict) -> set[str]:
    """Inside a subagent: the Skill tool, a Read of a pipeline skill's SKILL.md,
    or a Bash run of a script in its scripts/ folder."""
    skills = _skill_from_skill_tool(tool_use)
    name = tool_use.get("name")
    tool_input = tool_use.get("input") or {}
    if name == "Read":
        path = str(tool_input.get("file_path", "")).replace("\\", "/")
        skills |= {s for s in PIPELINE_SKILLS if path.endswith(f"/{s}/SKILL.md")}
    elif name == "Bash":
        command = str(tool_input.get("command", "")).replace("\\", "/")
        # `uv run .../<skill>/scripts/x.py`, or `cd .../<skill> && uv run scripts/x.py`
        if "scripts/" in command:
            skills |= {s for s in PIPELINE_SKILLS if re.search(rf"/{s}(?:/|\b)", command)}
    return skills


def _subagent_transcript(
    transcript_path: Path, agent_id: str | None, tool_use_id: str | None, name: str | None
) -> Path | None:
    """The subagent's own transcript, <session>/subagents/agent-<agentId>.jsonl:
    by agentId, else by the toolUseId (or, for a named teammate, the name) in
    its .meta.json."""
    folder = transcript_path.with_suffix("") / "subagents"
    if agent_id:
        candidate = folder / f"agent-{agent_id}.jsonl"
        if candidate.is_file():
            return candidate
    try:
        metas = sorted(folder.glob("agent-*.meta.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return None
    for meta in metas:
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        if (tool_use_id and data.get("toolUseId") == tool_use_id) or (name and data.get("name") == name):
            jsonl = meta.with_name(meta.name[: -len(".meta.json")] + ".jsonl")
            return jsonl if jsonl.is_file() else None
    return None


_NOTIFY_ID_RE = re.compile(r"<tool-use-id>\s*([^<\s]+)\s*</tool-use-id>")
_NOTIFY_TASK_RE = re.compile(r"<task-id>\s*([^<\s]+)\s*</task-id>")
_NOTIFY_RESULT_RE = re.compile(r"<result>(.*?)</result>", re.DOTALL)


class Turn:
    """What one turn (owner prompt to owner prompt) did in the main transcript."""

    def __init__(self):
        self.skills: set[str] = set()
        # key -> (Agent tool_use id or None, agentId/name hint, only-entries-since timestamp)
        self.agents: dict[str, tuple[str | None, str | None, str | None]] = {}
        self.packages: list[str] = []  # assistant texts that hold a package


class Session:
    def __init__(self, path: Path):
        self.path = path
        self.turns: list[Turn] = [Turn()]
        self.agent_ids: dict[str, str] = {}  # Agent tool_use id -> agentId
        self.agent_names: dict[str, str] = {}  # Agent tool_use id -> teammate name
        # Content the pipeline skills returned anywhere in the session, normalized.
        self.returned: dict[str, set[str]] = {STYLE_SKILL: set(), LYRIC_SKILL: set()}
        # Files the main conversation read in the session (any turn).
        self.reads: set[str] = set()

    def note_returns(self, text: str) -> set[str]:
        skills = set()
        for skill, obj in skill_returns(text):
            skills.add(skill)
            for field in RETURN_FIELDS[skill]:
                if isinstance(obj.get(field), str) and obj[field].strip():
                    self.returned[skill].add(normalize(obj[field]))
        return skills


def scan_session(transcript_path: str) -> Session:
    """One pass over the main transcript, split into turns. Raises
    TranscriptUnavailable when it is missing or unreadable."""
    if not transcript_path:
        raise TranscriptUnavailable("the hook input has no transcript_path")
    path = Path(transcript_path)
    if not path.is_file():
        raise TranscriptUnavailable(f"transcript not found: {path}")
    session = Session(path)

    for entry in read_entries(path):
        if is_owner_prompt(entry):
            session.turns.append(Turn())
            continue
        turn = session.turns[-1]
        sidechain = bool(entry.get("isSidechain"))
        for tool_use in _extract_tool_uses(entry):
            if sidechain:
                # Older Claude Code writes subagent entries inline.
                turn.skills |= _skills_from_subagent_tool_use(tool_use)
                continue
            turn.skills |= _skill_from_skill_tool(tool_use)
            tool_input = tool_use.get("input") or {}
            if tool_use.get("name") == "Read" and tool_input.get("file_path"):
                session.reads.add(str(tool_input["file_path"]).replace("\\", "/"))
            use_id = tool_use.get("id")
            if tool_use.get("name") in ("Agent", "Task") and use_id:
                turn.agents[use_id] = (use_id, None, None)
                if tool_input.get("name"):
                    session.agent_names[use_id] = str(tool_input["name"])
            elif tool_use.get("name") == "SendMessage" and use_id:
                # Continuing a teammate: only what it does from now on counts.
                target = str(tool_input.get("to") or tool_input.get("recipient") or "").lstrip("@")
                if target and target != "*":
                    turn.agents[f"send:{use_id}"] = (None, target, entry.get("timestamp"))
        for result in _tool_results(entry):
            use_id = result.get("tool_use_id")
            if not use_id:
                continue
            extra = entry.get("toolUseResult")
            if isinstance(extra, dict) and extra.get("agentId"):
                session.agent_ids[use_id] = str(extra["agentId"])
            if use_id in turn.agents:
                turn.skills |= session.note_returns(_result_text(result))
        text = _entry_text(entry)
        if entry.get("type") == "user" and text.lstrip().startswith("<task-notification"):
            m_use = _NOTIFY_ID_RE.search(text)
            if m_use:
                use_id = m_use.group(1)
                turn.agents.setdefault(use_id, (use_id, None, None))
                m_task = _NOTIFY_TASK_RE.search(text)
                if m_task:
                    session.agent_ids.setdefault(use_id, m_task.group(1))
                m_result = _NOTIFY_RESULT_RE.search(text)
                if m_result:
                    turn.skills |= session.note_returns(m_result.group(1))
        elif entry.get("type") == "assistant" and not sidechain and text and detect_suno_package(text):
            turn.packages.append(text)
    return session


def turn_evidence(session: Session, turn: Turn) -> tuple[set[str], list[str]]:
    """(skills that ran in the turn, subagents whose transcript couldn't be read)."""
    skills = set(turn.skills)
    unread: list[str] = []
    for key, (use_id, hint, since) in sorted(turn.agents.items()):
        if all(s in skills for s in PIPELINE_SKILLS):
            break
        if use_id:
            sub = _subagent_transcript(
                session.path, session.agent_ids.get(use_id), use_id, session.agent_names.get(use_id)
            )
        else:
            sub = _subagent_transcript(session.path, hint, None, hint)
        if sub is None:
            unread.append(hint or key)
            continue
        try:
            for entry in read_entries(sub):
                stamp = entry.get("timestamp")
                if since and isinstance(stamp, str) and stamp < since:
                    continue
                for tool_use in _extract_tool_uses(entry):
                    skills |= _skills_from_subagent_tool_use(tool_use)
        except TranscriptUnavailable:
            unread.append(hint or key)
    return skills, unread


def gather_evidence(transcript_path: str) -> tuple[set[str], list[str]]:
    """(skills that ran this turn, subagents whose transcript couldn't be read).
    Raises TranscriptUnavailable when the main transcript is missing or unreadable."""
    session = scan_session(transcript_path)
    return turn_evidence(session, session.turns[-1])


def check_skill_invocations(transcript_path: str) -> set[str]:
    """Skills that ran this turn (see gather_evidence). Raises TranscriptUnavailable."""
    return gather_evidence(transcript_path)[0]


_FENCED_RE = re.compile(r"^[ \t]*(```|~~~)[^\n]*\n(.*?)^[ \t]*\1[ \t]*$", re.MULTILINE | re.DOTALL)


def skill_sections(message: str, skill: str) -> list[tuple[str, str]]:
    """(section, content) for each piece of the message that only ``skill`` may
    produce: style-side sections for the builder, tagged lyrics for the
    transformer. Content is each code block in the section (for lyrics, each
    block holding section tags), or its whole body when it has none."""
    pieces = []
    for _, section, body in heading_blocks(message):
        if skill == STYLE_SKILL and section in STYLE_SECTIONS:
            pass
        elif (
            skill == LYRIC_SKILL
            and section == "Lyrics"
            and SECTION_TAG_RE.search(body)
            and not INSTRUMENTAL_RE.search(body)
        ):
            pass
        else:
            continue
        blocks = [m.group(2) for m in _FENCED_RE.finditer(body)]
        if skill == LYRIC_SKILL:
            # Lyrics are the tagged blocks; other blocks under the heading aren't.
            blocks = [b for b in blocks if SECTION_TAG_RE.search(b)]
        blocks = blocks or [body]
        pieces.extend((section, block) for block in blocks if block.strip())
    return pieces


def approved_content(session: Session) -> dict[str, set[str]]:
    """Normalized content each pipeline skill vouches for: what it returned
    anywhere in the session, plus the sections an earlier turn presented after
    that skill ran in that turn."""
    approved = {skill: set(texts) for skill, texts in session.returned.items()}
    for turn in session.turns[:-1]:
        if not turn.packages:
            continue
        skills, _ = turn_evidence(session, turn)
        for text in turn.packages:
            for skill in PIPELINE_SKILLS:
                if skill in skills:
                    approved[skill].update(normalize(c) for _, c in skill_sections(text, skill))
    return approved


def changed_sections(message: str, skill: str, approved: dict[str, set[str]]) -> list[str] | None:
    """Sections that differ from what ``skill`` already produced; None when the
    package has no section this skill owns (nothing to compare)."""
    pieces = skill_sections(message, skill)
    if not pieces:
        return None
    changed = []
    for section, content in pieces:
        if normalize(content) not in approved.get(skill, set()) and section not in changed:
            changed.append(section)
    return changed


def build_violations(
    message: str, skills_invoked: set[str] | None, approved: dict[str, set[str]] | None = None
) -> tuple[list[str], list[str]]:
    """(missing skills, order problems) for a detected package. With
    ``skills_invoked`` None (evidence unreadable) no skill is reported missing.
    A skill that didn't run this turn is not missing when every section it owns
    is unchanged from content it produced earlier in the session (``approved``)."""
    missing = []
    if skills_invoked is not None:
        if needs_style_builder(message) and STYLE_SKILL not in skills_invoked:
            missing.append(STYLE_SKILL)
        if needs_lyric_transformer(message) and LYRIC_SKILL not in skills_invoked:
            missing.append(LYRIC_SKILL)
    if approved is not None:
        missing = [s for s in missing if changed_sections(message, s, approved) != []]
    return missing, check_package_order(message)


PACKAGES_SHARD = "docs/mac-preferences-packages.md"


def unread_preferences_shard(input_data: dict, session: "Session | None") -> str | None:
    """The packages shard's path when it exists in the project and the session never read it."""
    if session is None:
        return None
    root = find_project_root(input_data)
    if root is None or not (root / PACKAGES_SHARD).is_file():
        return None
    if any(path.endswith(PACKAGES_SHARD) for path in session.reads):
        return None
    return PACKAGES_SHARD


def run_stop_hook(input_data: dict) -> dict | None:
    """The Stop-hook decision, or None to stay silent."""
    if input_data.get("stop_hook_active", False):
        return None
    message = input_data.get("last_assistant_message", "")
    if not message or not detect_suno_package(message):
        return None

    skills: set[str] | None
    approved = None
    try:
        session = scan_session(input_data.get("transcript_path", ""))
        skills, unread = turn_evidence(session, session.turns[-1])
    except TranscriptUnavailable as exc:
        note(f"{exc}; can't tell whether the pipeline skills ran, so no pipeline check.")
        skills, unread = None, []
    missing, _ = build_violations(message, skills)
    if missing:
        # Only sections changed since the skill last produced them need it now.
        approved = approved_content(session)
    missing, order_problems = build_violations(message, skills, approved)
    if missing and unread:
        note(
            "subagent transcript(s) unreadable for "
            + ", ".join(unread)
            + f"; can't tell whether {', '.join(missing)} ran, so no pipeline check."
        )
        missing = []

    reasons = []
    shard = unread_preferences_shard(input_data, session if skills is not None else None)
    if shard:
        reasons.append(
            f"PREFERENCES NOT LOADED: read `{shard}` in full before presenting a package. "
            "It holds the owner's package rules (moved out of docs/mac-preferences.md so it "
            "loads when a package is built), and this session hasn't read it."
        )
    if missing:
        changed = sorted({sec for s in missing for sec in (changed_sections(message, s, approved or {}) or [])})
        where = f" (changed or new: {', '.join(changed)})" if changed else ""
        reasons.append(
            f"PIPELINE VIOLATION: this package was presented without invoking "
            f"the required skill(s) this turn: {', '.join(missing)}{where}. "
            f"Invoke them now (headless, via Agent or the Skill tool), then "
            f"re-present the package with their validated output."
        )
    if order_problems:
        reasons.append(
            "PACKAGE ORDER: present sections in Suno's Create-screen order "
            "(Voice, Lyrics, Style Prompt, Exclude Styles, Settings, Title, "
            "Save to, Wild Card). Fix: " + "; ".join(order_problems) + "."
        )
    if reasons:
        return {"decision": "block", "reason": " ".join(reasons)}
    return None


# ---------------------------------------------------------------------------
# Dominion guard (PreToolUse)
# ---------------------------------------------------------------------------


def find_project_root(input_data: dict) -> Path | None:
    """The nearest folder holding _bmad/, from $CLAUDE_PROJECT_DIR or the hook's cwd."""
    for start in (os.environ.get("CLAUDE_PROJECT_DIR"), input_data.get("cwd")):
        if not start:
            continue
        here = Path(start).resolve()
        for folder in (here, *here.parents):
            if (folder / "_bmad").is_dir():
                return folder
    return None


_COMMAND_RE = re.compile(rf"<command-name>/?{re.escape(AGENT_SKILL)}</command-name>")


def mac_awake(transcript_path: str) -> bool:
    """True once the session has activated Mac (a /suno-agent-band-manager
    command or a Skill call for it). Raises TranscriptUnavailable."""
    if not transcript_path or not Path(transcript_path).is_file():
        raise TranscriptUnavailable(f"transcript not found: {transcript_path or '(none given)'}")
    for entry in read_entries(Path(transcript_path), needle=AGENT_SKILL):
        for tool_use in _extract_tool_uses(entry):
            if AGENT_SKILL in _skill_from_skill_tool(tool_use):
                return True
        if entry.get("type") == "user" and _COMMAND_RE.search(_entry_text(entry)):
            return True
    return False


def load_validate_path(script_dir: Path | None = None):
    """validate-path.py from beside this script, or None when it is absent."""
    path = (script_dir or Path(__file__).resolve().parent) / "validate-path.py"
    if not path.is_file():
        return None
    spec = spec_from_file_location("validate_path", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_dominion_hook(input_data: dict, script_dir: Path | None = None) -> dict | None:
    """The PreToolUse decision, or None to leave the write to normal permissions."""
    if input_data.get("tool_name") not in WRITE_TOOLS:
        return None
    tool_input = input_data.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not target:
        return None
    root = find_project_root(input_data)
    if root is None:
        note("no _bmad/ folder above the project dir; Dominion check skipped.")
        return None
    sanctum = root.joinpath(*SANCTUM_REL)
    creed = sanctum / "CREED.md"
    if not creed.is_file():
        note(f"no sanctum CREED.md at {creed}; Dominion check skipped.")
        return None
    target_path = Path(target)
    if not target_path.is_absolute():
        target_path = root / target_path
    target_path = target_path.resolve()
    if target_path == sanctum.resolve() or sanctum.resolve() in target_path.parents:
        return None
    validator = load_validate_path(script_dir)
    if validator is None:
        note("validate-path.py not found beside the guard; Dominion check skipped.")
        return None
    result = validator.validate_path(
        str(target_path), "write", validator.parse_boundaries(creed), project_root=str(root)
    )
    if result.get("allowed"):
        return None
    try:
        if not mac_awake(input_data.get("transcript_path", "")):
            return None
    except TranscriptUnavailable as exc:
        note(f"{exc}; can't tell whether Mac is awake, Dominion check skipped.")
        return None
    why = (
        f"a Deny Zone ({result.get('matched_rule')})"
        if result.get("reason") == "deny zone"
        else "not in its Write Access list"
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                f"Mac's Dominion (sanctum CREED.md): {target} is {why}. "
                "Write it only if the owner approves."
            ),
        }
    }


def main():
    args = build_parser().parse_args()
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        sys.exit(0)
    if not isinstance(input_data, dict):
        sys.exit(0)
    try:
        decision = run_dominion_hook(input_data) if args.dominion else run_stop_hook(input_data)
    except Exception as exc:  # a hook must never crash the turn
        note(f"internal error, check skipped: {exc!r}")
        decision = None
    if decision:
        print(json.dumps(decision))
    sys.exit(0)


if __name__ == "__main__":
    main()
