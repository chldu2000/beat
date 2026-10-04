"""Grade one finished run directory into metrics.json."""

import json
import re
from collections import Counter
from pathlib import Path

from .score import compare, load
from .taskchecks import run_checks

SONG = "song.beat.yaml"

# Ordered: the first matching pattern names the category.
ERROR_CATEGORIES = [
    ("yaml", r"YAML syntax error|YAML read it|must be a string"),
    ("bar_duration", r"duration .* beats, expected"),
    ("bar_count", r"bars written, expected|bars of chords, expected"),
    ("grid_length", r"steps( in this bar)?, expected"),
    ("token", r"cannot parse|invalid duration|unknown articulation|unknown dynamic|invalid pitch|"
              r"unbalanced|needs a value|invalid chord|invalid length|cannot parse hit|unknown hit mark|"
              r"outside the bar|listed twice|separated by '\|'"),
    ("range", r"outside the .* range"),
    ("playability", r"not playable|drummer needs"),
    ("tie", r"tie from"),
    ("structure", r"unknown (part|pattern|section)|extends|exactly one of|must be a|needs a type|"
                  r"invalid bar range|is a pitched instrument|drums use"),
    ("performance", r"edit|performance|swing"),
]


def categorize(message: str) -> str:
    for name, pattern in ERROR_CATEGORIES:
        if re.search(pattern, message):
            return name
    return "other"


def _transcript_stats(path: Path) -> dict:
    """Tool usage from a stream-json transcript, including calls the permission rules denied."""
    stats: dict = {"tool_calls": Counter(), "other_bash": [], "denied": []}
    if not path.exists():
        return stats
    uses: dict[str, tuple[str, dict]] = {}
    for line in path.read_text().splitlines():
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = msg.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        blocks = content if isinstance(content, list) else []
        if msg.get("type") == "assistant":
            for block in blocks:
                if block.get("type") == "tool_use":
                    stats["tool_calls"][block["name"]] += 1
                    uses[block["id"]] = (block["name"], block.get("input") or {})
                    cmd = (block.get("input") or {}).get("command", "")
                    if block["name"] == "Bash" and not cmd.strip().startswith(("beat ", "./.bin/beat ", ".bin/beat ")):
                        stats["other_bash"].append(cmd)
        elif msg.get("type") == "user":
            for block in blocks:
                if block.get("type") != "tool_result" or not block.get("is_error"):
                    continue
                text = block.get("content")
                text = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
                if re.search(r"permission|denied|not allowed", text, re.I):
                    name, inp = uses.get(block.get("tool_use_id"), ("?", {}))
                    stats["denied"].append(f"{name}: {inp.get('command') or inp.get('file_path') or ''}"[:200])
        elif msg.get("type") == "result":
            usage = msg.get("usage") or {}
            stats.update(cost_usd=msg.get("total_cost_usd"), turns=msg.get("num_turns"),
                         duration_sec=round((msg.get("duration_ms") or 0) / 1000),
                         result_error=msg.get("is_error"), subtype=msg.get("subtype"),
                         output_tokens=usage.get("output_tokens"))
            # Rate or session limits say nothing about the DSL: such runs are excluded from the report.
            limited = msg.get("is_error") and "limit" in str(msg.get("result", "")).lower()
            if msg.get("api_error_status") == 429 or limited:
                stats["infra_failure"] = str(msg.get("result"))[:200]
    return stats


def grade_run(run_dir: Path, task: dict, repo: Path) -> dict:
    m: dict = {"task": task["id"], "run": run_dir.name}

    calls = []
    log = run_dir / "beatlog" / "calls.jsonl"
    if log.exists():
        calls = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
    checked = [c for c in calls if "errors" in c]
    m["beat_calls"] = len(calls)
    m["validate_calls"] = sum(1 for c in calls if c["argv"][:1] == ["validate"])
    m["events_calls"] = sum(1 for c in calls if c["argv"][:1] == ["events"])
    m["first_check_errors"] = len(checked[0]["errors"]) if checked else None
    m["checks_to_green"] = next((i + 1 for i, c in enumerate(checked) if not c["errors"]), None)
    m["error_trace"] = [len(c["errors"]) for c in checked]

    # Distinct (category, message) pairs over the whole session; first check separately.
    seen = {e for c in checked for e in c["errors"]}
    m["error_categories_all"] = dict(Counter(categorize(e) for e in seen))
    m["error_categories_first"] = dict(Counter(categorize(e) for e in (checked[0]["errors"] if checked else [])))
    m["error_examples"] = sorted(seen)[:30]

    song_path = run_dir / SONG
    m["final_exists"] = song_path.exists()
    m["final_valid"] = False
    if song_path.exists():
        diags, song, compiled = load(song_path)
        m["final_valid"] = not diags.has_errors and compiled is not None
        m["final_errors"] = [str(d) for d in diags.errors]
        m["final_warnings"] = len(diags.warnings)
        text = song_path.read_text()
        m["file_chars"] = len(text)
        if compiled is not None:
            m["bars"] = compiled.total_bars
            m["chars_per_bar"] = round(len(text) / max(1, compiled.total_bars))
        if m["final_valid"]:
            if task.get("reference"):
                _, ref, _ = load(repo / task["reference"])
                m["compare"] = compare(song, ref)
            if task.get("checks"):
                start = repo / task["start"] if task.get("start") else None
                m["checks"] = run_checks(task["checks"], song, compiled, start)
                m["checks_passed"] = sum(m["checks"].values())
                m["checks_total"] = len(m["checks"])

    stats = _transcript_stats(run_dir / "transcript.jsonl")
    m["tool_calls"] = dict(stats.pop("tool_calls"))
    m.update(stats)
    m["notes"] = (run_dir / "NOTES.md").read_text() if (run_dir / "NOTES.md").exists() else None

    (run_dir / "metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=2))
    return m
