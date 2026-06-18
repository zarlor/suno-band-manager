#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest>=7.0"]
# ///
"""Tests for pipeline-guard.py"""

import sys
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

spec = spec_from_file_location(
    "pipeline_guard",
    Path(__file__).parent.parent / "pipeline-guard.py",
)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


def test_detect_suno_package_positive():
    assert mod.detect_suno_package("## Your Suno Package\n...")
    assert mod.detect_suno_package("### Copy-Ready: Style Prompt v5")
    assert mod.detect_suno_package("## Copy-Ready Lyrics\n[Verse]")


def test_detect_suno_package_negative():
    assert not mod.detect_suno_package("Just a normal chat about music.")
    assert not mod.detect_suno_package("Let's talk about the band direction.")


def test_extract_tool_uses_nested_message_shape():
    entry = {
        "message": {
            "content": [
                {"type": "tool_use", "name": "Skill", "input": {"skill": "x"}},
                {"type": "text", "text": "ignore me"},
            ]
        }
    }
    uses = mod._extract_tool_uses(entry)
    assert len(uses) == 1
    assert uses[0]["name"] == "Skill"


def test_extract_tool_uses_flattened_legacy_shape():
    entry = {"tool_name": "Skill", "tool_input": {"skill": "y"}}
    uses = mod._extract_tool_uses(entry)
    assert uses and uses[0]["name"] == "Skill"
    assert uses[0]["input"]["skill"] == "y"


def _write_transcript(tmp_path, lines):
    p = tmp_path / "transcript.jsonl"
    p.write_text("\n".join(lines), encoding="utf-8")
    return str(p)


def test_check_skill_invocations_detects_skill_tool(tmp_path):
    import json
    line = json.dumps({
        "message": {"content": [
            {"type": "tool_use", "name": "Skill",
             "input": {"skill": "suno-style-prompt-builder"}}
        ]}
    })
    skills = mod.check_skill_invocations(_write_transcript(tmp_path, [line]))
    assert "suno-style-prompt-builder" in skills


def test_check_skill_invocations_detects_agent_subagent(tmp_path):
    import json
    line = json.dumps({
        "message": {"content": [
            {"type": "tool_use", "name": "Agent",
             "input": {"prompt": "run suno-lyric-transformer headless ..."}}
        ]}
    })
    skills = mod.check_skill_invocations(_write_transcript(tmp_path, [line]))
    assert "suno-lyric-transformer" in skills


def test_check_skill_invocations_missing_path_returns_empty():
    assert mod.check_skill_invocations("") == set()


def test_main_blocks_when_pipeline_skipped(tmp_path, monkeypatch, capsys):
    import io
    import json
    payload = {
        "last_assistant_message": "## Your Suno Package\nStyle, lyrics, settings.",
        "transcript_path": "",  # no skills invoked
        "stop_hook_active": False,
    }
    monkeypatch.setattr(sys, "argv", ["pipeline-guard.py"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code == 0  # hooks never crash the turn
    decision = json.loads(capsys.readouterr().out)
    assert decision["decision"] == "block"
    assert "suno-style-prompt-builder" in decision["reason"]


def test_main_silent_when_no_package(tmp_path, monkeypatch, capsys):
    import io
    import json
    payload = {
        "last_assistant_message": "Just chatting, no package here.",
        "transcript_path": "",
        "stop_hook_active": False,
    }
    monkeypatch.setattr(sys, "argv", ["pipeline-guard.py"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == ""
