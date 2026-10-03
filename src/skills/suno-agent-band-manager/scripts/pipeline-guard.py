#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Stop hook guard: blocks a Suno package that skipped the pipeline or is out of order.

This script runs as a Claude Code Stop hook. When the assistant's last message
contains a Suno-ready package, it checks three things, all from structure:

1. **Style Prompt Builder ran this turn** when the message presents a style
   prompt or exclude styles (or is a package with no recognisable headings).
2. **Lyric Transformer ran this turn** when the message carries lyrics with
   section tags (`[Verse]`, `[Chorus]`, ...). Suno auto-lyrics packages and
   instrumental packages have no tagged lyrics, so they pass.
3. **Package order** follows Suno's Create screen: Voice -> Lyrics -> Style
   Prompt -> Exclude Styles -> Settings -> Title -> Save to -> Wild Card.

"This turn" means tool calls made after the owner's latest real prompt. Tool
results, skill bodies, system reminders and background-task notifications are
not prompts, so they don't reset the turn. An Agent (or legacy Task) call counts
as a skill invocation only when its prompt names the skill and says to invoke
it (``invoke``, ``headless`` or ``Skill tool``) -- a passing mention does not.

Usage: Configure as a Stop hook in .claude/settings.local.json:
    {
      "hooks": {
        "Stop": [{
          "hooks": [{
            "type": "command",
            "command": "python3 path/to/pipeline-guard.py",
            "timeout": 10
          }]
        }]
      }
    }

The script reads JSON from stdin (Claude Code hook input) and outputs a JSON
decision to stdout. It is stdlib-only and runs on bare ``python3`` so the hook
stays fast.
"""

import argparse
import json
import re
import sys


def build_parser() -> argparse.ArgumentParser:
    """Self-documentation for the Stop-hook interface.

    The script's real input is a Claude Code hook JSON payload on stdin
    (no positional args); argparse exists so `--help` documents what the
    guard checks and how to wire it up, satisfying the graceful-degradation
    contract (the LLM can perform the equivalent check from the help text
    when the hook can't run).
    """
    parser = argparse.ArgumentParser(
        description=(
            "Claude Code Stop-hook guard: reads the hook JSON payload on "
            "stdin and, when the last assistant message contains a Suno "
            "package, checks (1) suno-style-prompt-builder ran this turn if "
            "a style prompt or exclude styles are shown, (2) "
            "suno-lyric-transformer ran this turn if lyrics with section "
            "tags are shown (auto-lyrics and instrumental packages pass), "
            "and (3) the sections follow Suno's Create screen order: Voice, "
            "Lyrics, Style Prompt, Exclude Styles, Settings, Title, Save to, "
            "Wild Card. 'This turn' = tool calls after the owner's latest "
            "real prompt. Emits a JSON block decision on stdout on a "
            "violation; otherwise stays silent. Exit code is always 0 (a "
            "hook must not crash the turn)."
        ),
        epilog=(
            "Input (stdin JSON): last_assistant_message, transcript_path, "
            "stop_hook_active. Output (stdout JSON, only on violation): "
            "{\"decision\": \"block\", \"reason\": \"...\"}."
        ),
    )
    return parser


STYLE_SKILL = "suno-style-prompt-builder"
LYRIC_SKILL = "suno-lyric-transformer"
SKILL_NAMES_TO_DETECT = (
    STYLE_SKILL,
    LYRIC_SKILL,
    "suno-feedback-elicitor",
    "suno-band-profile-manager",
)

# An Agent/Task prompt only counts as a skill invocation when it names the
# skill AND asks for it to be run -- not when it merely mentions the name.
AGENT_INVOKE_RE = re.compile(r"\binvok|\bheadless\b|\bSkill tool\b", re.IGNORECASE)

# Lyrics carrying section tags are Lyric Transformer output. Auto-lyrics and
# instrumental packages show no tagged lyrics, so they need no transformer run.
SECTION_TAG_RE = re.compile(
    r"^\s*\[(?:Intro|Verse|Pre-Chorus|Chorus|Post-Chorus|Final Chorus|Bridge|"
    r"Outro|Hook|Refrain|Breakdown|Interlude|Instrumental Break|Solo|Drop|"
    r"Build)\b",
    re.IGNORECASE | re.MULTILINE,
)
INSTRUMENTAL_RE = re.compile(r"Instrumental \(no vocals\)", re.IGNORECASE)

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


def detect_suno_package(message: str) -> bool:
    """Check if the message contains a Suno-ready package."""
    patterns = [
        r"##\s*Style Prompt.*v\d",
        r"###\s*Copy-Ready:\s*Style Prompt",
        r"##\s*Copy-Ready Lyrics",
        r"##\s*Your Suno Package",
        r"###\s*Copy-Ready:\s*Exclude Styles",
        r"\|\s*Setting\s*\|\s*Value\s*\|.*\n.*Weirdness:",
        r"paste into Suno",
    ]
    return any(re.search(p, message, re.IGNORECASE | re.MULTILINE) for p in patterns)


def package_sections(message: str) -> list[str]:
    """Package sections in the order their headings first appear."""
    seen: list[str] = []
    for m in HEADING_RE.finditer(message):
        text = m.group(1).strip().strip("*").strip()
        for section, pattern in _CLASSIFY:
            if pattern.search(text):
                if section not in seen:
                    seen.append(section)
                break
    return seen


def check_package_order(message: str) -> list[str]:
    """Return 'A before B' strings for each section that sits out of order."""
    sections = package_sections(message)
    rank = {name: i for i, name in enumerate(PACKAGE_ORDER)}
    problems = []
    for i, earlier in enumerate(sections):
        for later in sections[i + 1 :]:
            if rank[later] < rank[earlier]:
                problems.append(f"{later} should come before {earlier}")
    return problems


def needs_lyric_transformer(message: str) -> bool:
    """Tagged lyrics need the transformer; auto-lyrics and instrumentals don't."""
    if INSTRUMENTAL_RE.search(message):
        return False
    return bool(SECTION_TAG_RE.search(message))


def needs_style_builder(message: str) -> bool:
    """A shown style prompt or exclude list needs the builder this turn.

    A package with no recognisable section headings is treated as a full
    package (the conservative reading), so it still needs the builder.
    """
    sections = package_sections(message)
    if not sections:
        return True
    return "Style Prompt" in sections or "Exclude Styles" in sections


def _extract_tool_uses(entry: dict) -> list[dict]:
    """Walk the transcript entry structure to find all tool_use items.

    Claude Code transcripts nest tool_use items inside
    entry.message.content[] for assistant messages. Older structures
    may place them at the top level. This helper handles both.
    """
    tool_uses = []
    # Top-level shapes (defensive)
    if entry.get("type") == "tool_use":
        tool_uses.append(entry)
    if "tool_name" in entry and entry.get("tool_name"):
        # Legacy/flattened shape: tool_name + tool_input
        tool_uses.append({
            "name": entry.get("tool_name"),
            "input": entry.get("tool_input", {}),
        })
    # Nested shape: entry.message.content[] with items of type "tool_use"
    message = entry.get("message", {})
    if isinstance(message, dict):
        content = message.get("content", [])
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool_uses.append(item)
    return tool_uses


_NON_PROMPT_PREFIXES = (
    "<task-notification",
    "<local-command",
    "<system-reminder",
    "Stop hook feedback",
)


def is_owner_prompt(entry: dict) -> bool:
    """True when a transcript entry is a real prompt from the owner.

    Tool results, skill bodies and reminders (``isMeta``), background-task
    notifications, peer messages and Stop-hook feedback are not prompts, so
    they don't start a new turn.
    """
    if entry.get("type") != "user" or entry.get("isMeta") or entry.get("isCompactSummary"):
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
        text = " ".join(
            i.get("text", "") for i in content if isinstance(i, dict) and i.get("type") == "text"
        )
    elif isinstance(content, str):
        text = content
    else:
        return False
    return not text.lstrip().startswith(_NON_PROMPT_PREFIXES)


def _skills_from_tool_use(tool_use: dict) -> set[str]:
    name = tool_use.get("name", "")
    tool_input = tool_use.get("input", {}) or {}
    if name == "Skill":
        skill_name = tool_input.get("skill", "")
        return {skill_name} if skill_name else set()
    if name in ("Agent", "Task"):
        prompt = f"{tool_input.get('description', '')} {tool_input.get('prompt', '')}"
        if AGENT_INVOKE_RE.search(prompt):
            return {sn for sn in SKILL_NAMES_TO_DETECT if sn in prompt}
    return set()


def check_skill_invocations(transcript_path: str, current_turn_only: bool = True) -> set[str]:
    """Return the skills invoked, by default only in the current turn.

    Checks direct Skill tool invocations and Agent subagent invocations that
    ask for a named skill to run (the parallel headless pattern).
    """
    skills: set[str] = set()
    if not transcript_path:
        return skills
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(entry, dict):
                    continue
                # Sidechain (subagent) entries never start a turn, but a skill
                # a subagent invoked still counts.
                if current_turn_only and not entry.get("isSidechain") and is_owner_prompt(entry):
                    skills = set()
                    continue
                for tool_use in _extract_tool_uses(entry):
                    skills |= _skills_from_tool_use(tool_use)
        return skills
    except (OSError, PermissionError):
        return skills


def build_violations(message: str, skills_invoked: set[str]) -> tuple[list[str], list[str]]:
    """Return (missing skills, order problems) for a detected package."""
    missing = []
    if needs_style_builder(message) and STYLE_SKILL not in skills_invoked:
        missing.append(STYLE_SKILL)
    if needs_lyric_transformer(message) and LYRIC_SKILL not in skills_invoked:
        missing.append(LYRIC_SKILL)
    return missing, check_package_order(message)


def main():
    # Parse args so `--help` works; the guard takes no positional args and
    # reads its real payload from stdin.
    build_parser().parse_args()
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    # Prevent infinite loops
    if input_data.get("stop_hook_active", False):
        sys.exit(0)

    message = input_data.get("last_assistant_message", "")
    if not message:
        sys.exit(0)

    # Only check if there's a Suno package in the output
    if not detect_suno_package(message):
        sys.exit(0)

    skills_invoked = check_skill_invocations(input_data.get("transcript_path", ""))
    missing, order_problems = build_violations(message, skills_invoked)

    reasons = []
    if missing:
        reasons.append(
            f"PIPELINE VIOLATION: this package was presented without invoking "
            f"the required skill(s) this turn: {', '.join(missing)}. "
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
        print(json.dumps({"decision": "block", "reason": " ".join(reasons)}))

    sys.exit(0)


if __name__ == "__main__":
    main()
