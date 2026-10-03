#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Optional audio dependency checker for the audio-analysis scripts.

Audio analysis scripts are optional — the rest of the module works without
librosa and numpy. This module provides a check that exits gracefully with
structured JSON output if dependencies are missing.
"""

import json
import sys

def require_modules(modules, install_cmd, purpose="Audio analysis"):
    """Exit 2 with a structured JSON message if any import name in `modules` is missing.

    Used directly by the optional PyTorch-based scripts (beat-grid.py,
    vocal-placement.py), whose dependencies go beyond librosa/numpy.
    """
    import importlib.util

    missing = [m for m in modules if importlib.util.find_spec(m) is None]
    if missing:
        result = {
            "script": "audio-dependency-check",
            "status": "fail",
            "error": "missing_dependencies",
            "missing": missing,
            "install_command": install_cmd,
            "message": (
                f"{purpose} requires: {', '.join(missing)}.\n"
                "Run this script via `uv run` — uv reads the PEP 723 metadata and "
                f"provisions these automatically. Or install manually: {install_cmd}\n"
                "These are optional — the rest of the module works without them."
            ),
        }
        print(json.dumps(result, indent=2))
        sys.exit(2)


def require_audio_deps(extra=()):
    """Check for librosa and numpy (plus any `extra` import names, e.g. pyloudnorm).

    Exit with a helpful JSON message if any is missing.
    """
    required = ("librosa", "numpy", *extra)
    require_modules(required, "pip install " + " ".join(required))
