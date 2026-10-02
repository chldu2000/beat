"""Command-line interface: validate / events / midi / render (spec section 13)."""

import argparse
import json
import sys
from pathlib import Path

from .compile import Compiled, compile_song
from .diagnostics import Diagnostics
from .pitch import pitch_name
from .song import Song, load_song


def _load(path: str, sections: str | None = None) -> tuple[Diagnostics, Song | None, Compiled | None]:
    diags = Diagnostics()
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as e:
        diags.error("", f"cannot read {path}: {e}")
        return diags, None, None
    song = load_song(text, diags)
    if song is None:
        return diags, None, None
    form = None
    if sections:
        wanted = [s.strip() for s in sections.split(",") if s.strip()]
        for s in wanted:
            if s not in song.sections:
                diags.error("--sections", f"unknown section '{s}'")
        form = [s for s in song.form if s in wanted]
        if not form:
            diags.error("--sections", "none of the selected sections appear in the form")
            return diags, song, None
    return diags, song, compile_song(song, diags, form)


def _summary(compiled: Compiled | None) -> dict:
    if compiled is None:
        return {}
    return {"bars": compiled.total_bars, "duration_sec": round(compiled.duration_sec, 2),
            "events": len(compiled.events), "form": compiled.form}


def _print_diags(diags: Diagnostics) -> None:
    for d in diags.errors + diags.warnings:
        print(d, file=sys.stderr)


def _report(diags: Diagnostics, compiled: Compiled | None, as_json: bool) -> int:
    ok = not diags.has_errors
    if as_json:
        print(json.dumps({"ok": ok, "errors": [d.to_dict() for d in diags.errors],
                          "warnings": [d.to_dict() for d in diags.warnings],
                          "summary": _summary(compiled)}, ensure_ascii=False, indent=2))
    else:
        _print_diags(diags)
        s = _summary(compiled)
        status = "OK" if ok else f"FAILED ({len(diags.errors)} error(s))"
        detail = f": {s['bars']} bars, {s['duration_sec']}s, {s['events']} events" if s and ok else ""
        print(f"{status}{detail}, {len(diags.warnings)} warning(s)")
    return 0 if ok else 1


def cmd_validate(args) -> int:
    diags, _, compiled = _load(args.song)
    return _report(diags, compiled, args.json)


def cmd_events(args) -> int:
    diags, song, compiled = _load(args.song, args.sections)
    if diags.has_errors or compiled is None:
        return _report(diags, compiled, args.json)
    if args.json:
        print(json.dumps(compiled.to_dict(), ensure_ascii=False, indent=1))
        return 0
    _print_diags(diags)
    print(f"{'time':>8} {'dur':>6}  {'part':<6} {'note':<5} {'vel':>5}  where / arts")
    for e in compiled.events:
        if args.parts and e.part not in args.parts.split(","):
            continue
        note = e.lane or pitch_name(e.pitch)
        s = e.src
        arts = " ".join("!" + k if v is True else f"!{k}={v}" for k, v in e.arts.items())
        print(f"{e.time:8.3f} {e.dur:6.3f}  {e.part:<6} {note:<5} {e.velocity:5.2f}  "
              f"{s['section']}#{s['instance']} bar {s['bar']} beat {s['beat']:g} {arts}")
    return 0


def cmd_midi(args) -> int:
    from .midi import export_midi

    diags, _, compiled = _load(args.song, args.sections)
    if diags.has_errors or compiled is None:
        return _report(diags, compiled, False)
    _print_diags(diags)
    export_midi(compiled, args.output)
    print(f"wrote {args.output}")
    return 0


def cmd_render(args) -> int:
    from .render import SR, render, write_wav

    diags, song, compiled = _load(args.song, args.sections)
    parts = [p.strip() for p in args.parts.split(",")] if args.parts else None
    if song and parts:
        for p in parts:
            if p not in song.instruments:
                diags.error("--parts", f"unknown part '{p}'")
    if diags.has_errors or compiled is None:
        return _report(diags, compiled, False)
    _print_diags(diags)
    audio = render(compiled, parts)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    write_wav(args.output, audio)
    print(f"wrote {args.output} ({len(audio) / SR:.1f}s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="beat", description="Beat song toolchain (spec v0.1)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="check a song for errors and warnings")
    p.add_argument("song")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("events", help="print the compiled event list")
    p.add_argument("song")
    p.add_argument("--json", action="store_true")
    p.add_argument("--parts", help="comma-separated part ids")
    p.add_argument("--sections", help="comma-separated section ids")
    p.set_defaults(func=cmd_events)

    p = sub.add_parser("midi", help="export a MIDI file")
    p.add_argument("song")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--sections", help="comma-separated section ids")
    p.set_defaults(func=cmd_midi)

    p = sub.add_parser("render", help="render to a WAV file")
    p.add_argument("song")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--parts", help="comma-separated part ids (solo)")
    p.add_argument("--sections", help="comma-separated section ids")
    p.set_defaults(func=cmd_render)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
