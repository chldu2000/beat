"""Stand-in for the `beat` command inside eval workspaces.

Runs the real CLI unchanged, then appends a record to $BEAT_EVAL_LOG/calls.jsonl with the
song's diagnostics at that moment and a snapshot of the file, so the grader can replay the
agent's validate-and-fix loop.
"""

import json
import os
import shutil
import sys
import time
from pathlib import Path

from beat.cli import main as cli_main

from .score import load

COMMANDS = {"validate", "events", "midi", "render"}


def main() -> int:
    argv = sys.argv[1:]
    try:
        code = cli_main(argv)
    except SystemExit as e:  # argparse usage errors
        code = e.code if isinstance(e.code, int) else 1
    sys.stdout.flush()

    log_dir = os.environ.get("BEAT_EVAL_LOG")
    if log_dir:
        _record(Path(log_dir), argv, code)
    return code


def _record(log_dir: Path, argv: list[str], code: int) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    calls = log_dir / "calls.jsonl"
    n = sum(1 for _ in calls.open()) if calls.exists() else 0
    entry: dict = {"n": n, "t": time.time(), "argv": argv, "exit": code}

    song = Path(argv[1]) if len(argv) > 1 and argv[0] in COMMANDS else None
    if song and song.is_file():
        snap = log_dir / f"snap-{n:03d}.yaml"
        shutil.copyfile(song, snap)
        diags, _, _ = load(song)
        entry.update(song=str(song), snapshot=snap.name,
                     errors=[str(d) for d in diags.errors], warnings=[str(d) for d in diags.warnings])
    with calls.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    sys.exit(main())
