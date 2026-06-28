#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Optional audio dependency checker for librosa/numpy scripts.

Audio analysis scripts are optional — the rest of the module works without
librosa and numpy. This module provides a check that exits gracefully with
structured JSON output if dependencies are missing.
"""

import json
import sys

_INSTALL_CMD = "pip install librosa numpy"


def require_audio_deps():
    """Check for librosa and numpy. Exit with helpful JSON message if missing."""
    missing = []
    try:
        import librosa  # noqa: F401
    except ImportError:
        missing.append("librosa")
    try:
        import numpy  # noqa: F401
    except ImportError:
        missing.append("numpy")

    if missing:
        result = {
            "script": "audio-dependency-check",
            "status": "fail",
            "error": "missing_dependencies",
            "missing": missing,
            "install_command": _INSTALL_CMD,
            "message": (
                f"Audio analysis requires: {', '.join(missing)}.\n"
                "Run this script via `uv run` — uv reads the PEP 723 metadata and "
                f"provisions these automatically. Or install manually: {_INSTALL_CMD}\n"
                "These are optional — the rest of the module works without them."
            ),
        }
        print(json.dumps(result, indent=2))
        sys.exit(2)
