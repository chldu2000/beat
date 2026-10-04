"""Task-specific requirements on the final song (`checks:` in a task file)."""

from pathlib import Path

from beat.compile import Compiled
from beat.song import Song

from .score import load, score_events, section_events


def run_checks(checks: dict, song: Song, compiled: Compiled, start: Path | None) -> dict[str, bool]:
    results: dict[str, bool] = {}
    events = score_events(song)

    for name, arg in checks.items():
        if name == "bars":
            results[f"bars in {arg}"] = arg[0] <= compiled.total_bars <= arg[1]
        elif name == "tempo":
            results[f"tempo in {arg}"] = arg[0] <= song.tempo <= arg[1]
        elif name == "parts_play":
            for pid in arg:
                results[f"{pid} plays"] = any(e.part == pid for e in events)
        elif name == "min_sections":
            results[f">= {arg} distinct sections"] = len(set(song.form)) >= arg
        elif name == "repeated_section":
            # A variant made with `extends` counts as the same section coming back.
            roots = [song.sections[sid].extends or sid for sid in song.form]
            results["a section repeats"] = len(set(roots)) < len(roots)
        elif name == "form":
            results[f"form == {arg}"] = song.form == arg
        elif name == "section_bars":
            for sid, bars in arg.items():
                results[f"{sid} has {bars} bars"] = sid in song.sections and song.sections[sid].bars == bars
        elif name == "section_parts":
            for sid, spec in arg.items():
                playing = {e.part for e in events if e.src["section"] == sid}
                for pid in spec.get("play", []):
                    results[f"{pid} plays in {sid}"] = pid in playing
                for pid in spec.get("silent", []):
                    results[f"{pid} silent in {sid}"] = pid not in playing
        elif name == "unchanged_sections":
            _, start_song, _ = load(start)
            before = section_events(start_song, arg)
            after = section_events(song, arg)
            for sid in arg:
                results[f"{sid} unchanged"] = before.get(sid) == after.get(sid)
        elif name == "perf":
            value = song.performance
            for key in arg["path"].split("."):
                value = value.get(key) if isinstance(value, dict) else None
            results[f"performance.{arg['path']} == {arg['equals']}"] = value == arg["equals"]
        else:
            raise ValueError(f"unknown check '{name}'")
    return results
