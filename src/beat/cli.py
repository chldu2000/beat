"""Command-line interface: validate / events / midi / render / voicing (spec section 13)."""

import argparse
import json
import sys
from pathlib import Path

from .compile import Compiled, compile_song
from .diagnostics import Diagnostics, did_you_mean
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
                diags.error("--sections", f"unknown section '{s}'{did_you_mean(s, song.sections)}")
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
    from .views import by_bar, parse_bar_range, select, table

    diags, song, compiled = _load(args.song, args.sections)
    parts = [p.strip() for p in args.parts.split(",")] if args.parts else None
    bars = None
    if args.bars:
        try:
            bars = parse_bar_range(args.bars)
        except ValueError as e:
            diags.error("--bars", str(e))
    if song and parts:
        for p in parts:
            if p not in song.instruments:
                diags.error("--parts", f"unknown part '{p}'{did_you_mean(p, song.instruments)}")
    if diags.has_errors or compiled is None:
        return _report(diags, compiled, args.json)
    events = select(compiled.events, parts, bars)
    if args.json:
        out = compiled.to_dict()
        out["events"] = [e.to_dict() for e in events]
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    _print_diags(diags)
    print(by_bar(compiled, events) if args.by_bar else table(compiled, events))
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
    from .diagnostics import Diagnostic
    from .render import SR, mixdown, write_wav

    diags, song, compiled = _load(args.song, args.sections)
    parts = [p.strip() for p in args.parts.split(",")] if args.parts else None
    if song and parts:
        for p in parts:
            if p not in song.instruments:
                diags.error("--parts", f"unknown part '{p}'{did_you_mean(p, song.instruments)}")
    if diags.has_errors or compiled is None:
        return _report(diags, compiled, False)
    _print_diags(diags)
    audio, report = mixdown(compiled, parts, mix=args.mix == "on")
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    write_wav(args.output, audio)
    print(f"wrote {args.output} ({len(audio) / SR:.1f}s)")
    if report:
        print("\n".join(report.lines()))
        for where, msg in report.warnings:
            print(Diagnostic("warning", where, msg), file=sys.stderr)
    return 0


def cmd_voicing(args) -> int:
    from .pitch import parse_pitch, pitch_name
    from .song import DEFAULT_FRETS, DEFAULT_TUNING, FIXED_RANGE
    from .voicing import voicings

    fretted = args.instrument in DEFAULT_TUNING
    try:
        if args.tuning and not fretted:
            raise ValueError(f"--tuning only applies to guitar and bass, not {args.instrument}")
        names = args.tuning.split(",") if args.tuning else DEFAULT_TUNING.get(args.instrument, [])
        tuning = tuple(parse_pitch(n.strip()) for n in names)
        low = parse_pitch(args.low)
        found = voicings(args.chord, args.style, tuning=tuning, frets=DEFAULT_FRETS.get(args.instrument, 0),
                         low=low, limit=args.max)
    except ValueError as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1
    if not fretted:
        lo, hi = FIXED_RANGE[args.instrument]
        found = [v for v in found if lo <= v.pitches[0] and v.pitches[-1] <= hi]

    if args.json:
        print(json.dumps([{"notes": v.notes, "shape": v.shape or None} for v in found], indent=1))
        return 0 if found else 1
    on = f"{args.instrument} ({' '.join(pitch_name(t) for t in tuning)})" if fretted else \
        f"{args.instrument}, from {args.low} up"
    if not found:
        print(f"no playable {args.style} voicing of {args.chord} on {on}")
        return 1
    print(f"{args.chord} {args.style} voicings on {on}, easiest first:")
    for v in found:
        print(f"  {v.shape:<18} {v.notes}" if fretted else f"  {v.notes}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="beat", description="Beat song toolchain (spec v0.1)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="check a song for errors and warnings")
    p.add_argument("song")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("events", help="print the compiled notes")
    p.add_argument("song")
    p.add_argument("--json", action="store_true")
    p.add_argument("--parts", help="comma-separated part ids")
    p.add_argument("--sections", help="comma-separated section ids (renders only these, in form order)")
    p.add_argument("--bars", help="global bar number or range, e.g. 5 or 5-8")
    p.add_argument("--by-bar", action="store_true",
                   help="compact view: one line per part per bar, beat:note/length")
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
    p.add_argument("--mix", choices=["on", "off"], default="on",
                   help="off: only gain_db and pan, peak-normalized (the v0.1 mix, for comparison)")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("voicing", help="list playable voicings of a chord to paste into notes")
    p.add_argument("chord", help="chord symbol, e.g. Am, G/B, C7")
    p.add_argument("style", nargs="?", choices=["full", "power"], default="full",
                   help="full: every chord tone (default); power: root, fifth, octave")
    p.add_argument("--for", dest="instrument", choices=["guitar", "bass", "organ", "piano"], default="guitar")
    p.add_argument("--tuning", help="guitar/bass strings low to high, e.g. D2,A2,D3,G3,B3,E4")
    p.add_argument("--low", default="C3", help="organ/piano: lowest note of the voicing (default C3)")
    p.add_argument("--max", type=int, default=6, help="how many voicings to list (default 6)")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_voicing)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
