#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["beat-this>=1.1", "torch>=2.1", "librosa>=1.0", "numpy>=2.1"]
# ///
"""Neural beat and downbeat tracking (Beat This!) — the command-line entry point.

The implementation is the shared `beat_grid` helper (scripts/_shared/beat_grid.py),
which the librosa scripts in this skill and the playlist sequencer also run as its
own `uv run` process. Usage, flags and exit codes are documented there and in
references/audio-analysis-scripts.md.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "_shared"))
from beat_grid import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
