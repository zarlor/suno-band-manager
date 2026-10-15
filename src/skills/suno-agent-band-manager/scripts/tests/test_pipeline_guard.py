#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Tests for pipeline-guard.py: package structure, structural skill evidence,
turn scoping, fail-open on unreadable transcripts, and the Dominion hook."""

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
spec = spec_from_file_location("pipeline_guard", SCRIPTS / "pipeline-guard.py")
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import TempDirMixin  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures: synthetic transcript entries
# ---------------------------------------------------------------------------


def _write(path: Path, entries: list) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e) for e in entries), encoding="utf-8")
    return str(path)


def transcript(tmp_path, entries, name="session"):
    return _write(tmp_path / f"{name}.jsonl", entries)


def user(text, **extra):
    return {"type": "user", "message": {"role": "user", "content": text}, **extra}


def tool_use(name, tool_input, use_id="toolu_x", **extra):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": use_id, "name": name, "input": tool_input}]}, **extra}


def skill(name, use_id="toolu_skill", **extra):
    return tool_use("Skill", {"skill": name}, use_id, **extra)


def agent(prompt, use_id="toolu_agent", **inp):
    return tool_use("Agent", {"description": "run it", "prompt": prompt, **inp}, use_id)


def agent_result(use_id, text, agent_id=None):
    entry = {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": use_id, "content": [{"type": "text", "text": text}]}]}}
    if agent_id:
        entry["toolUseResult"] = {"agentId": agent_id, "status": "completed"}
    return entry


def notification(use_id, task_id, result):
    return user(
        f"<task-notification>\n<task-id>{task_id}</task-id>\n<tool-use-id>{use_id}</tool-use-id>\n"
        f"<status>completed</status>\n<result>{result}</result>\n</task-notification>",
        origin={"kind": "task-notification"}, promptSource="system",
    )


def subagent_file(tmp_path, agent_id, entries, name="session", meta=None):
    folder = tmp_path / name / "subagents"
    _write(folder / f"agent-{agent_id}.jsonl", entries)
    if meta is not None:
        (folder / f"agent-{agent_id}.meta.json").write_text(json.dumps(meta), encoding="utf-8")


STYLE_RETURN = {
    "status": "complete", "mode": "build", "style_prompt": "warm folk, brushed drums",
    "style_prompt_chars": 24, "exclusion_prompt": "autotune", "validation": {"status": "pass"},
}
LYRIC_RETURN = {
    "status": "complete", "transformed_lyrics": "[Verse 1]\nThe porch light",
    "transformation_summary": {"section_count": 1}, "spacing_check": {"status": "pass"},
}


def fenced(obj):
    return "Done.\n```json\n" + json.dumps(obj, indent=2) + "\n```\n"


class GuardTestCase(TempDirMixin, unittest.TestCase):
    """Shared plumbing: a temp dir, env patching, running main(), and the
    Dominion project."""

    def setenv(self, key, value):
        patcher = patch.dict(os.environ, {key: value})
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_main(self, payload, argv=("pipeline-guard.py",)):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", list(argv)), \
                patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
                redirect_stdout(out), redirect_stderr(err):
            with self.assertRaises(SystemExit) as exc:
                mod.main()
        self.assertEqual(exc.exception.code, 0)  # hooks never crash the turn
        return SimpleNamespace(out=out.getvalue(), err=err.getvalue())

    def make_project(self):
        root = self.tmp_path / "proj"
        sanctum = root.joinpath(*mod.SANCTUM_REL)
        sanctum.mkdir(parents=True)
        (sanctum / "CREED.md").write_text(CREED, encoding="utf-8")
        self.setenv("CLAUDE_PROJECT_DIR", str(root))
        awake = _write(self.tmp_path / "awake.jsonl", [
            user(f"<command-message>{mod.AGENT_SKILL}</command-message>\n<command-name>/{mod.AGENT_SKILL}</command-name>")])
        asleep = _write(self.tmp_path / "asleep.jsonl", [user("fix the tests")])
        return root, sanctum, awake, asleep

    def project_with_shard(self):
        root = self.tmp_path / "proj"
        (root / "_bmad").mkdir(parents=True)
        (root / "docs").mkdir()
        (root / "docs" / "mac-preferences-packages.md").write_text("# package rules\n")
        self.setenv("CLAUDE_PROJECT_DIR", str(root))
        return root


# ---------------------------------------------------------------------------
# Package structure (#6)
# ---------------------------------------------------------------------------

AUTO_LYRICS_PACKAGE = (
    "## Your Suno Package\n\n"
    "### Lyrics\nLyrics: Auto-generated by Suno — set Lyrics Mode to Auto\n\n"
    "### Style Prompt (v6)\n120/1000 characters\n\n```\nwarm folk, brushed drums\n```\n\n"
    "### Exclude Styles\n```\nautotune\n```\n\n"
    "### Settings\n- Model: v6\n\n"
    "### Song Title\n```\nPorch Light\n```\n\n"
    "### Save to\nPaper Lanterns\n\n"
    "### Wild Card Variant — The Unexpected Take\n```\n1960s coffeehouse folk\n```\n"
)

TAGGED_PACKAGE = AUTO_LYRICS_PACKAGE.replace(
    "Lyrics: Auto-generated by Suno — set Lyrics Mode to Auto",
    "```\n[Verse 1]\nThe porch light flickers on\n\n[Chorus]\nCome back home\n```",
)

INSTRUMENTAL_PACKAGE = AUTO_LYRICS_PACKAGE.replace(
    "Lyrics: Auto-generated by Suno — set Lyrics Mode to Auto",
    "Lyrics: Instrumental (no vocals)\n[Intro]\n[Build]",
)

# refine-song Step 4: only what changed, under the package's own headings.
LYRICS_ONLY_REFINEMENT = (
    "## Paper Lanterns Refinement Update\n\n### What Changed\n- added a bridge\n\n"
    "### Lyrics\n```\n[Verse 1]\nThe porch light\n\n[Bridge]\nSomething new\n```\n"
)
STYLE_ONLY_REFINEMENT = (
    "## Paper Lanterns Refinement Update\n\n### What Changed\n- rawer vocal\n\n"
    "### Style Prompt (v6)\n```\nraw folk vocal, brushed drums\n```\n"
)


class PackageStructureTests(GuardTestCase):
    def test_detects_full_package_and_refinement_updates(self):
        self.assertTrue(mod.detect_suno_package(AUTO_LYRICS_PACKAGE))
        self.assertTrue(mod.detect_suno_package(TAGGED_PACKAGE))
        self.assertTrue(mod.detect_suno_package(LYRICS_ONLY_REFINEMENT))
        self.assertTrue(mod.detect_suno_package(STYLE_ONLY_REFINEMENT))
        self.assertTrue(mod.detect_suno_package("## Copy-Ready Lyrics\n[Verse]\nline"))

    def test_chat_about_prompts_is_not_a_package(self):
        self.assertFalse(mod.detect_suno_package("Just a normal chat about music."))
        self.assertFalse(mod.detect_suno_package("### Style prompt thoughts\nMaybe rawer next time."))
        self.assertFalse(mod.detect_suno_package("Next I'll paste into Suno the usual way."))
        self.assertFalse(mod.detect_suno_package("### Lyrics\nWe could add a bridge, no tags yet."))

    def test_lyrics_only_refinement_needs_only_the_transformer(self):
        self.assertFalse(mod.needs_style_builder(LYRICS_ONLY_REFINEMENT))
        self.assertTrue(mod.needs_lyric_transformer(LYRICS_ONLY_REFINEMENT))
        missing, order = mod.build_violations(LYRICS_ONLY_REFINEMENT, {mod.LYRIC_SKILL})
        self.assertEqual(missing, [])
        self.assertEqual(order, [])
        missing, _ = mod.build_violations(LYRICS_ONLY_REFINEMENT, set())
        self.assertEqual(missing, [mod.LYRIC_SKILL])

    def test_style_only_refinement_needs_only_the_builder(self):
        missing, _ = mod.build_violations(STYLE_ONLY_REFINEMENT, set())
        self.assertEqual(missing, [mod.STYLE_SKILL])

    def test_auto_lyrics_package_needs_no_lyric_transformer(self):
        self.assertFalse(mod.needs_lyric_transformer(AUTO_LYRICS_PACKAGE))
        missing, order = mod.build_violations(AUTO_LYRICS_PACKAGE, {mod.STYLE_SKILL})
        self.assertEqual(missing, [])
        self.assertEqual(order, [])

    def test_instrumental_package_needs_no_lyric_transformer(self):
        self.assertFalse(mod.needs_lyric_transformer(INSTRUMENTAL_PACKAGE))

    def test_tagged_lyrics_need_lyric_transformer(self):
        self.assertTrue(mod.needs_lyric_transformer(TAGGED_PACKAGE))
        missing, _ = mod.build_violations(TAGGED_PACKAGE, {mod.STYLE_SKILL})
        self.assertEqual(missing, [mod.LYRIC_SKILL])

    def test_headingless_package_still_needs_style_builder(self):
        self.assertTrue(mod.needs_style_builder("Here you go: warm folk, brushed drums"))

    def test_unknown_evidence_reports_no_missing_skill(self):
        missing, _ = mod.build_violations(TAGGED_PACKAGE, None)
        self.assertEqual(missing, [])


# ---------------------------------------------------------------------------
# Package order
# ---------------------------------------------------------------------------


class PackageOrderTests(GuardTestCase):
    def test_package_in_create_screen_order_passes(self):
        self.assertEqual(mod.check_package_order(AUTO_LYRICS_PACKAGE), [])
        self.assertEqual(mod.package_sections(AUTO_LYRICS_PACKAGE), [
            "Lyrics", "Style Prompt", "Exclude Styles", "Settings", "Title", "Save to", "Wild Card",
        ])

    def test_title_first_is_flagged(self):
        msg = "## Your Suno Package\n### Song Title\nX\n### Lyrics\n...\n### Style Prompt\n..."
        self.assertIn("Lyrics should come before Title", mod.check_package_order(msg))

    def test_style_before_lyrics_is_flagged(self):
        msg = "## Your Suno Package\n### Style Prompt (v6)\n...\n### Lyrics\n..."
        self.assertEqual(mod.check_package_order(msg), ["Lyrics should come before Style Prompt"])

    def test_wild_card_style_prompt_heading_is_the_wild_card(self):
        msg = "### Lyrics\n..\n### Style Prompt\n..\n### Wild Card Style Prompt\n..\n"
        self.assertEqual(mod.package_sections(msg), ["Lyrics", "Style Prompt", "Wild Card"])

    def test_voice_and_persona_come_first(self):
        self.assertEqual(mod.check_package_order("### Persona\nX\n### Lyrics\n..\n### Style Prompt\n.."), [])
        self.assertEqual(mod.check_package_order("### Lyrics\n..\n### Voice\nX\n"), ["Voice should come before Lyrics"])


# ---------------------------------------------------------------------------
# Structural evidence (#1)
# ---------------------------------------------------------------------------


class StructuralEvidenceTests(GuardTestCase):
    def test_skill_tool_in_main_transcript_counts(self):
        path = transcript(self.tmp_path, [user("make a song"), skill(mod.STYLE_SKILL)])
        self.assertEqual(mod.check_skill_invocations(path), {mod.STYLE_SKILL})

    def test_agent_prompt_wording_never_counts(self):
        """'invoke', 'run', 'headless' and the skill name in a prompt are not evidence."""
        for prompt in (
            f"Invoke {mod.LYRIC_SKILL} in headless mode with this poem",
            f"Run {mod.STYLE_SKILL} --headless via the Skill tool",
            f"Summarize what {mod.STYLE_SKILL} returned last week",
        ):
            path = transcript(self.tmp_path, [user("go"), agent(prompt), agent_result("toolu_agent", "Here is the prompt: warm folk")])
            self.assertEqual(mod.check_skill_invocations(path), set(), prompt)

    def test_headless_named_but_subagent_hand_built_does_not_count(self):
        path = transcript(self.tmp_path, [
            user("go"),
            agent(f"Invoke {mod.STYLE_SKILL} headless", "toolu_a"),
            agent_result("toolu_a", "Style prompt: warm folk, brushed drums", agent_id="a1"),
        ])
        subagent_file(self.tmp_path, "a1", [
            tool_use("Bash", {"command": "echo 'warm folk' > /tmp/x"}, isSidechain=True, agentId="a1"),
        ])
        skills, unread = mod.gather_evidence(path)
        self.assertEqual(skills, set())
        self.assertEqual(unread, [])

    def test_skill_tool_in_subagent_transcript_counts(self):
        path = transcript(self.tmp_path, [
            user("go"), agent("build the style", "toolu_a"),
            agent_result("toolu_a", "Async agent launched", agent_id="a1"),
        ])
        subagent_file(self.tmp_path, "a1", [skill(mod.STYLE_SKILL, isSidechain=True, agentId="a1")])
        self.assertEqual(mod.check_skill_invocations(path), {mod.STYLE_SKILL})

    def test_subagent_reading_skill_md_or_running_its_scripts_counts(self):
        path = transcript(self.tmp_path, [
            user("go"),
            agent("style", "toolu_a"), agent_result("toolu_a", "launched", agent_id="a1"),
            agent("lyrics", "toolu_b"), agent_result("toolu_b", "launched", agent_id="a2"),
        ])
        subagent_file(self.tmp_path, "a1", [tool_use(
            "Read", {"file_path": f"/repo/.claude/skills/{mod.STYLE_SKILL}/SKILL.md"}, isSidechain=True)])
        subagent_file(self.tmp_path, "a2", [tool_use(
            "Bash", {"command": f"cd /repo/.claude/skills/{mod.LYRIC_SKILL} && uv run scripts/spacing-check.py x"},
            isSidechain=True)])
        self.assertEqual(mod.check_skill_invocations(path), {mod.STYLE_SKILL, mod.LYRIC_SKILL})

    def test_subagent_found_by_meta_tool_use_id(self):
        path = transcript(self.tmp_path, [user("go"), agent("style", "toolu_a")])
        subagent_file(self.tmp_path, "zz9", [skill(mod.STYLE_SKILL, isSidechain=True)],
                      meta={"toolUseId": "toolu_a", "description": "style"})
        self.assertEqual(mod.check_skill_invocations(path), {mod.STYLE_SKILL})

    def test_return_shape_in_sync_agent_result_counts(self):
        path = transcript(self.tmp_path, [
            user("go"),
            agent("style", "toolu_a"), agent_result("toolu_a", fenced(STYLE_RETURN)),
            agent("lyrics", "toolu_b"), agent_result("toolu_b", json.dumps(LYRIC_RETURN)),
        ])
        skills, unread = mod.gather_evidence(path)
        self.assertEqual(skills, {mod.STYLE_SKILL, mod.LYRIC_SKILL})
        self.assertEqual(unread, [])

    def test_return_shape_in_task_notification_counts_even_from_an_earlier_turn_launch(self):
        path = transcript(self.tmp_path, [
            user("go"),
            agent("lyrics", "toolu_b"), agent_result("toolu_b", "Async agent launched", agent_id="a2"),
            user("still there?"),
            notification("toolu_b", "a2", fenced(LYRIC_RETURN)),
        ])
        self.assertEqual(mod.check_skill_invocations(path), {mod.LYRIC_SKILL})

    def test_blocked_return_does_not_count(self):
        blocked = {"status": "blocked", "style_prompt": "", "exclusion_prompt": None, "missing": ["genre_mood"]}
        path = transcript(self.tmp_path, [user("go"), agent("style", "toolu_a"),
                                     agent_result("toolu_a", fenced(blocked), agent_id="a1")])
        subagent_file(self.tmp_path, "a1", [])
        self.assertEqual(mod.check_skill_invocations(path), set())

    def test_sendmessage_to_teammate_counts_only_work_after_the_message(self):
        entries = [
            user("first build", timestamp="2026-10-01T10:00:00Z"),
            agent("style", "toolu_a", name="grey-style"),
            user("now make it rawer", timestamp="2026-10-01T11:00:00Z"),
            tool_use("SendMessage", {"to": "grey-style", "message": "rawer"}, "toolu_s",
                     timestamp="2026-10-01T11:00:05Z"),
        ]
        path = transcript(self.tmp_path, entries)
        before = tool_use("Read", {"file_path": f"/r/{mod.STYLE_SKILL}/SKILL.md"}, isSidechain=True,
                          timestamp="2026-10-01T10:00:10Z")
        subagent_file(self.tmp_path, "agrey-style-1", [before], meta={"name": "grey-style"})
        self.assertEqual(mod.check_skill_invocations(path), set())
        after = tool_use("Bash", {"command": f"uv run /r/{mod.STYLE_SKILL}/scripts/validate-prompt.py --stdin"},
                         isSidechain=True, timestamp="2026-10-01T11:01:00Z")
        subagent_file(self.tmp_path, "agrey-style-1", [before, after], meta={"name": "grey-style"})
        self.assertEqual(mod.check_skill_invocations(path), {mod.STYLE_SKILL})

    def test_inline_sidechain_entries_count(self):
        path = transcript(self.tmp_path, [
            user("go"), agent("lyrics", "toolu_b"),
            tool_use("Read", {"file_path": f"/r/{mod.LYRIC_SKILL}/SKILL.md"}, isSidechain=True),
            user("subagent prompt text", isSidechain=True),
        ])
        self.assertIn(mod.LYRIC_SKILL, mod.check_skill_invocations(path))


# ---------------------------------------------------------------------------
# Turn scoping
# ---------------------------------------------------------------------------


class TurnScopingTests(GuardTestCase):
    def test_earlier_turn_invocation_does_not_count(self):
        path = transcript(self.tmp_path, [user("make me a song"), skill(mod.STYLE_SKILL), user("now another one")])
        self.assertEqual(mod.check_skill_invocations(path), set())

    def test_non_prompts_do_not_reset_turn(self):
        path = transcript(self.tmp_path, [
            user("make me a song"),
            skill(mod.STYLE_SKILL),
            agent_result("toolu_skill", "Launching skill"),
            {"type": "user", "isMeta": True, "message": {"content": [
                {"type": "text", "text": "Base directory for this skill: ..."}]}},
            user("<task-notification>agent finished</task-notification>",
                 origin={"kind": "task-notification"}, promptSource="system"),
            user("Another Claude session sent a message:\n<teammate-message teammate_id=\"x\">{}</teammate-message>"),
            user("Stop hook feedback: PIPELINE VIOLATION ..."),
            skill(mod.LYRIC_SKILL, "toolu_skill2"),
        ])
        self.assertEqual(mod.check_skill_invocations(path), {mod.STYLE_SKILL, mod.LYRIC_SKILL})


# ---------------------------------------------------------------------------
# Unreadable transcripts fail open (#22)
# ---------------------------------------------------------------------------


def stop_payload(message, path):
    return {"last_assistant_message": message, "transcript_path": path, "stop_hook_active": False}


class UnreadableTranscriptTests(GuardTestCase):
    def test_missing_transcript_raises_distinct_state(self):
        with self.assertRaises(mod.TranscriptUnavailable):
            mod.gather_evidence("")
        with self.assertRaises(mod.TranscriptUnavailable):
            mod.gather_evidence(str(self.tmp_path / "nope.jsonl"))

    def test_main_fails_open_without_a_transcript(self):
        for path in ("", "/nonexistent/session.jsonl"):
            with self.subTest(path=path):
                out = self.run_main(stop_payload(TAGGED_PACKAGE, path))
                self.assertEqual(out.out.strip(), "")
                self.assertIn("can't tell", out.err)

    def test_main_still_reports_order_without_a_transcript(self):
        msg = "## Your Suno Package\n### Style Prompt (v6)\n```\nx\n```\n### Lyrics\nAuto-generated by Suno\n"
        out = self.run_main(stop_payload(msg, ""))
        decision = json.loads(out.out)
        self.assertIn("PACKAGE ORDER", decision["reason"])
        self.assertNotIn("PIPELINE VIOLATION", decision["reason"])

    def test_main_fails_open_when_a_subagent_transcript_is_missing(self):
        path = transcript(self.tmp_path, [user("go"), skill(mod.STYLE_SKILL),
                                     agent("lyrics", "toolu_b"), agent_result("toolu_b", "launched", agent_id="gone")])
        out = self.run_main(stop_payload(TAGGED_PACKAGE, path))
        self.assertEqual(out.out.strip(), "")
        self.assertIn("unreadable", out.err)


# ---------------------------------------------------------------------------
# Stop hook end to end
# ---------------------------------------------------------------------------


class StopHookEndToEndTests(GuardTestCase):
    def test_main_blocks_when_pipeline_skipped(self):
        path = transcript(self.tmp_path, [user("make a song")])
        out = self.run_main(stop_payload(TAGGED_PACKAGE, path))
        decision = json.loads(out.out)
        self.assertEqual(decision["decision"], "block")
        self.assertIn(mod.STYLE_SKILL, decision["reason"])
        self.assertIn(mod.LYRIC_SKILL, decision["reason"])

    def test_main_blocks_lyrics_only_refinement_without_transformer(self):
        path = transcript(self.tmp_path, [user("add a bridge"), agent(f"invoke {mod.LYRIC_SKILL} headless", "toolu_b"),
                                     agent_result("toolu_b", "Here are the new lyrics", agent_id="a2")])
        subagent_file(self.tmp_path, "a2", [])
        decision = json.loads(self.run_main(stop_payload(LYRICS_ONLY_REFINEMENT, path)).out)
        self.assertEqual(decision["decision"], "block")
        self.assertIn(mod.LYRIC_SKILL, decision["reason"])
        self.assertNotIn(mod.STYLE_SKILL, decision["reason"])

    def test_main_silent_when_no_package(self):
        out = self.run_main(stop_payload("Just chatting, no package here.", ""))
        self.assertEqual(out.out.strip(), "")
        self.assertEqual(out.err.strip(), "")

    def test_main_passes_auto_lyrics_package_with_style_builder_this_turn(self):
        path = transcript(self.tmp_path, [user("surprise me"), skill(mod.STYLE_SKILL)])
        self.assertEqual(self.run_main(stop_payload(AUTO_LYRICS_PACKAGE, path)).out.strip(), "")

    def test_main_passes_parallel_headless_agents_returning_contract_json(self):
        path = transcript(self.tmp_path, [
            user("make a song"),
            agent("style", "toolu_a"), agent("lyrics", "toolu_b"),
            agent_result("toolu_a", fenced(STYLE_RETURN)), agent_result("toolu_b", fenced(LYRIC_RETURN)),
        ])
        self.assertEqual(self.run_main(stop_payload(TAGGED_PACKAGE, path)).out.strip(), "")

    def test_main_blocks_out_of_order_package(self):
        path = transcript(self.tmp_path, [user("go"), skill(mod.STYLE_SKILL)])
        msg = "## Your Suno Package\n### Style Prompt (v6)\n```\nx\n```\n### Lyrics\nAuto-generated by Suno\n"
        decision = json.loads(self.run_main(stop_payload(msg, path)).out)
        self.assertIn("PACKAGE ORDER", decision["reason"])
        self.assertNotIn("PIPELINE VIOLATION", decision["reason"])

    def test_stop_hook_active_is_silent(self):
        payload = {**stop_payload(TAGGED_PACKAGE, ""), "stop_hook_active": True}
        self.assertEqual(self.run_main(payload).out.strip(), "")


# ---------------------------------------------------------------------------
# Unchanged re-show of earlier pipeline output
# ---------------------------------------------------------------------------

STYLE_TEXT = "warm folk, brushed drums, close-miked tenor"
EXCLUDE_TEXT = "autotune, trap hats"
LYRICS_TEXT = "[Verse 1]\nThe porch light flickers on\n\n[Chorus]\nCome back home"


def package(style=STYLE_TEXT, exclude=EXCLUDE_TEXT, lyrics=LYRICS_TEXT):
    return (
        "## Your Suno Package\n\n"
        f"### Lyrics\n```\n{lyrics}\n```\n\n"
        f"### Style Prompt (v6)\n{len(style)}/1000 characters\n\n```\n{style}\n```\n\n"
        f"### Exclude Styles\n```\n{exclude}\n```\n\n"
        "### Settings\n- Model: v6\n"
    )


def assistant_text(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def earlier_turn_with_returns():
    """Turn 1: both skills return through Agents, Mac presents the package."""
    style_ret = {**STYLE_RETURN, "style_prompt": STYLE_TEXT, "exclusion_prompt": EXCLUDE_TEXT}
    lyric_ret = {**LYRIC_RETURN, "transformed_lyrics": LYRICS_TEXT}
    return [
        user("make the porch song"),
        agent("style", "toolu_a"), agent("lyrics", "toolu_b"),
        agent_result("toolu_a", fenced(style_ret)), agent_result("toolu_b", fenced(lyric_ret)),
        assistant_text(package()),
    ]


class UnchangedReshowTests(GuardTestCase):
    def test_unchanged_reshow_in_a_later_turn_passes(self):
        # Extra whitespace in the re-show still matches.
        reshow = package(style="warm folk,  brushed drums,\nclose-miked tenor")
        path = transcript(self.tmp_path, earlier_turn_with_returns() + [user("show me the package again")])
        self.assertEqual(self.run_main(stop_payload(reshow, path)).out.strip(), "")

    def test_unchanged_reshow_of_presented_text_after_skill_tool_run_passes(self):
        """No JSON return: the earlier turn's presented sections count because the
        skills ran (Skill tool) in that turn."""
        path = transcript(self.tmp_path, [
            user("make it"), skill(mod.STYLE_SKILL), skill(mod.LYRIC_SKILL, "toolu_s2"),
            assistant_text(package()),
            user("harpsichord was fine, show it again"),
        ])
        self.assertEqual(self.run_main(stop_payload(package(), path)).out.strip(), "")

    def test_one_edited_word_in_the_style_prompt_blocks(self):
        edited = package(style=STYLE_TEXT.replace("warm", "cold"))
        path = transcript(self.tmp_path, earlier_turn_with_returns() + [user("make it colder")])
        decision = json.loads(self.run_main(stop_payload(edited, path)).out)
        self.assertEqual(decision["decision"], "block")
        self.assertIn(mod.STYLE_SKILL, decision["reason"])
        self.assertNotIn(mod.LYRIC_SKILL, decision["reason"])
        self.assertIn("Style Prompt", decision["reason"])

    def test_lyrics_edited_by_hand_block(self):
        edited = package(lyrics=LYRICS_TEXT.replace("[Chorus]", "[Chorus]\nOne new line"))
        path = transcript(self.tmp_path, earlier_turn_with_returns() + [user("add a line to the chorus")])
        decision = json.loads(self.run_main(stop_payload(edited, path)).out)
        self.assertEqual(decision["decision"], "block")
        self.assertIn(mod.LYRIC_SKILL, decision["reason"])
        self.assertNotIn(mod.STYLE_SKILL, decision["reason"])

    def test_presented_text_from_a_turn_without_the_skill_is_not_approved(self):
        """A hand-built package shown earlier doesn't become approved by being shown."""
        path = transcript(self.tmp_path, [
            user("make it"), assistant_text(package()), user("show it again"),
        ])
        decision = json.loads(self.run_main(stop_payload(package(), path)).out)
        self.assertIn(mod.STYLE_SKILL, decision["reason"])
        self.assertIn(mod.LYRIC_SKILL, decision["reason"])

    def test_only_tagged_blocks_under_a_lyrics_heading_are_lyrics(self):
        msg = f"## Take 2: the Lyrics-box test\n```\n{LYRICS_TEXT}\n```\n\nNotes:\n```\nnot lyrics at all\n```\n"
        approved = {mod.LYRIC_SKILL: {mod.normalize(LYRICS_TEXT)}, mod.STYLE_SKILL: set()}
        self.assertEqual(mod.changed_sections(msg, mod.LYRIC_SKILL, approved), [])

    def test_changed_sections_reports_only_the_edited_section(self):
        approved = {mod.STYLE_SKILL: {mod.normalize(STYLE_TEXT), mod.normalize(EXCLUDE_TEXT)}, mod.LYRIC_SKILL: set()}
        msg = package(exclude="autotune")
        self.assertEqual(mod.changed_sections(msg, mod.STYLE_SKILL, approved), ["Exclude Styles"])
        self.assertIsNone(mod.changed_sections("## Your Suno Package\nno sections", mod.STYLE_SKILL, approved))


# ---------------------------------------------------------------------------
# Dominion hook (#26)
# ---------------------------------------------------------------------------

CREED = """# Creed

## Dominion (Access Boundaries)

### Read Access
- `{project-root}/docs/` — owner docs

### Write Access
- `{project-root}/_bmad/memory/suno-agent-band-manager/` — own memory
- `docs/wip-*.md` — fragments

### Deny Zones
- `src/` — module source

## Next
"""


def write_payload(target, transcript_path, tool="Write"):
    return {"tool_name": tool, "tool_input": {"file_path": str(target)}, "transcript_path": transcript_path}


class DominionHookTests(GuardTestCase):
    def test_dominion_asks_on_a_deny_zone_write_while_mac_is_awake(self):
        root, _, awake, _ = self.make_project()
        decision = mod.run_dominion_hook(write_payload(root / "src" / "x.py", awake, "Edit"))
        out = decision["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "ask")
        self.assertIn("Deny Zone", out["permissionDecisionReason"])

    def test_dominion_asks_on_a_path_outside_write_access(self):
        root, _, awake, _ = self.make_project()
        decision = mod.run_dominion_hook(write_payload("docs/voice-context-sam.md", awake))
        self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "ask")
        self.assertIn("Write Access", decision["hookSpecificOutput"]["permissionDecisionReason"])

    def test_dominion_allows_listed_paths_and_the_sanctum(self):
        root, sanctum, awake, _ = self.make_project()
        self.assertIsNone(mod.run_dominion_hook(write_payload(root / "docs" / "wip-song.md", awake)))
        self.assertIsNone(mod.run_dominion_hook(write_payload(sanctum / "memory" / "work" / "current.md", awake)))

    def test_dominion_skill_tool_activation_counts_as_awake(self):
        root, _, _, _ = self.make_project()
        via_skill = _write(self.tmp_path / "skill.jsonl", [user("talk to Mac"), skill(mod.AGENT_SKILL)])
        self.assertIsNotNone(mod.run_dominion_hook(write_payload(root / "src" / "x.py", via_skill)))

    def test_dominion_silent_when_mac_is_not_awake(self):
        root, _, _, asleep = self.make_project()
        self.assertIsNone(mod.run_dominion_hook(write_payload(root / "src" / "x.py", asleep)))

    def test_dominion_ignores_other_tools(self):
        root, _, awake, _ = self.make_project()
        self.assertIsNone(mod.run_dominion_hook({"tool_name": "Read", "tool_input": {"file_path": str(root / "src/x")},
                                      "transcript_path": awake}))

    def test_dominion_fails_open_without_sanctum(self):
        root, sanctum, awake, _ = self.make_project()
        (sanctum / "CREED.md").unlink()
        with redirect_stderr(io.StringIO()) as err:
            self.assertIsNone(mod.run_dominion_hook(write_payload(root / "src" / "x.py", awake)))
        self.assertIn("CREED.md", err.getvalue())

    def test_dominion_fails_open_without_validate_path(self):
        root, _, awake, _ = self.make_project()
        empty = self.tmp_path / "no-scripts"
        empty.mkdir()
        with redirect_stderr(io.StringIO()) as err:
            self.assertIsNone(mod.run_dominion_hook(write_payload(root / "src" / "x.py", awake), script_dir=empty))
        self.assertIn("validate-path.py", err.getvalue())

    def test_dominion_fails_open_without_transcript(self):
        root, _, _, _ = self.make_project()
        with redirect_stderr(io.StringIO()) as err:
            self.assertIsNone(mod.run_dominion_hook(write_payload(root / "src" / "x.py", "")))
        self.assertIn("can't tell", err.getvalue())

    def test_dominion_main_prints_decision(self):
        root, _, awake, _ = self.make_project()
        out = self.run_main(write_payload(root / "src" / "x.py", awake),
                       argv=("pipeline-guard.py", "--dominion"))
        self.assertEqual(json.loads(out.out)["hookSpecificOutput"]["permissionDecision"], "ask")


# --- the packages shard of the owner's preferences must be read before a package ---


class PackagesShardTests(GuardTestCase):
    def test_package_without_reading_the_packages_shard_blocks(self):
        self.project_with_shard()
        path = transcript(self.tmp_path, [user("make the song"), skill(mod.STYLE_SKILL), skill(mod.LYRIC_SKILL, use_id="toolu_l")])
        decision = mod.run_stop_hook({"last_assistant_message": TAGGED_PACKAGE, "transcript_path": path})
        self.assertTrue(decision)
        self.assertIn("PREFERENCES NOT LOADED", decision["reason"])
        self.assertNotIn("PIPELINE VIOLATION", decision["reason"])

    def test_package_after_reading_the_shard_in_any_turn_passes(self):
        root = self.project_with_shard()
        path = transcript(self.tmp_path, [
            user("wake up"),
            tool_use("Read", {"file_path": str(root / "docs" / "mac-preferences-packages.md")}, use_id="toolu_r"),
            user("make the song"), skill(mod.STYLE_SKILL), skill(mod.LYRIC_SKILL, use_id="toolu_l"),
        ])
        self.assertIsNone(mod.run_stop_hook({"last_assistant_message": TAGGED_PACKAGE, "transcript_path": path}))

    def test_no_shard_in_the_project_means_no_preferences_check(self):
        root = self.tmp_path / "proj"
        (root / "_bmad").mkdir(parents=True)
        self.setenv("CLAUDE_PROJECT_DIR", str(root))
        path = transcript(self.tmp_path, [user("make the song"), skill(mod.STYLE_SKILL), skill(mod.LYRIC_SKILL, use_id="toolu_l")])
        self.assertIsNone(mod.run_stop_hook({"last_assistant_message": TAGGED_PACKAGE, "transcript_path": path}))


if __name__ == "__main__":
    unittest.main()
