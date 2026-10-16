"""Musical descriptors of songs, how alike a set of songs is, and a few floor checks.

    uv run python -m evals.music examples/*.beat.yaml
    uv run python -m evals.music --group pilot='evals/results/*pilot/t3*/run-*/song.beat.yaml' \
                                 --group voicing='evals/results/*voicing*/t3*/run-*/song.beat.yaml'

Nothing here is a score of how good a song is. The descriptors and similarities measure whether
songs written under the same guidance converge on one template (compare a group's similarity
before and after a guidance change); the floor checks report only clear defects (muddy low
voicings, minor-9th clashes with the bass, a lead under the rhythm guitars, a part that never
changes), each with a location.
"""

import argparse
import glob
import json
import re
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from statistics import mean

from beat.compile import Compiled, Event
from beat.pitch import _pitch_class, chord_tones, pitch_name
from beat.views import fmt_pos

from .score import load, score_events

STRING_TECHNIQUES = ("vib", "bend", "sl", "fall", "h", "p", "harm", "release")
# The lowest note at which an interval still sounds clear (common orchestration rule of thumb).
LOW_INTERVAL_LIMIT = {1: 52, 2: 51, 3: 48, 4: 46}  # m2 E3, M2 Eb3, m3 C3, M3 Bb2
DEGREES = {0: "R", 3: "3", 4: "3", 7: "5", 10: "7", 11: "7", 2: "9", 1: "b9", 5: "4", 6: "#4", 9: "6", 8: "b6"}


# --- loading ------------------------------------------------------------------

def _tonic(song) -> tuple[int | None, str]:
    m = re.match(r"\s*([A-G][#b]?)\s*(minor|min|m\b)?", str(song.meta.get("key", "")), re.I)
    if not m:
        return None, "?"
    return _pitch_class(m.group(1)), "minor" if m.group(2) else "major"


def _chord_at(compiled: Compiled) -> dict[int, list]:
    """global bar -> the section's chord spans for that bar (or [])."""
    out = {}
    for ins in compiled.instances:
        for i in range(ins.section.bars):
            out[ins.global_bar + i] = ins.section.chords[i] if ins.section.chords else []
    return out


def _chord_of(ev: Event, chords: dict[int, list]):
    span = None
    for c in chords.get(ev.src["global_bar"], []):
        if c.onset <= ev.pos_in_bar:
            span = c
    if span is None or span.pcs is None:
        return None
    return chord_tones(span.symbol)


def _lead_part(compiled: Compiled, events: list[Event]) -> str | None:
    insts = compiled.song.instruments
    leads = [p for p, i in insts.items() if i.tone == "lead"]
    if leads:
        return leads[0]
    best, best_pitch = None, -1.0
    for pid, inst in insts.items():
        if inst.type in ("drums", "bass"):
            continue
        evs = [e for e in events if e.part == pid]
        onsets = Counter(e.beat for e in evs)
        if not evs or len(evs) / len(onsets) > 1.2:  # mostly chords: an accompaniment part
            continue
        p = mean(e.pitch for e in evs)
        if p > best_pitch:
            best, best_pitch = pid, p
    return best


def _where(compiled: Compiled, ev: Event) -> str:
    return f"{ev.src['section']} > {ev.part} > bar {ev.src['bar']}, beat {fmt_pos(ev.pos_in_bar + 1)}"


def _sec(compiled: Compiled, ev: Event) -> float:
    return compiled.beat_to_sec(float(ev.beat + ev.beats)) - compiled.beat_to_sec(float(ev.beat))


# --- descriptors ----------------------------------------------------------------

def _hist(counter: Counter, keys) -> dict:
    total = sum(counter.values()) or 1
    return {k: round(counter[k] / total, 3) for k in keys}


def describe(path: Path) -> dict | None:
    diags, song, compiled = load(path)
    if compiled is None or diags.errors:
        return None
    events = score_events(song)
    tonic, mode = _tonic(song)
    ref = tonic if tonic is not None else 0
    chords = _chord_at(compiled)
    bar_beats = song.bar_beats

    # Form shape: sections lettered by first appearance.
    letters: dict[str, str] = {}
    form = "".join(letters.setdefault(s, chr(ord("A") + len(letters))) for s in compiled.form)

    # Harmony: the chord sequence over the whole form, relative to the tonic, repeats collapsed.
    prog = []
    for bar in sorted(chords):
        for c in chords[bar]:
            t = chord_tones(c.symbol) if c.pcs is not None else None
            label = "NC" if t is None else f"{(t[0] - ref) % 12}:{'-'.join(map(str, t[1]))}"
            if not prog or prog[-1] != label:
                prog.append(label)
    trigrams = sorted({"|".join(prog[i:i + 3]) for i in range(len(prog) - 2)})

    # Drums: the kick and snare pattern of each bar.
    drum_bars: dict[int, list] = defaultdict(list)
    for e in events:
        if e.lane in ("bd", "sd"):
            drum_bars[e.src["global_bar"]].append((e.lane, str(e.pos_in_bar)))
    drum_patterns = Counter(tuple(sorted(v)) for v in drum_bars.values())

    d = {
        "path": str(path), "title": song.meta.get("title"), "tempo": song.tempo,
        "key": f"{pitch_name(60 + ref)[:-1]} {mode}" if tonic is not None else "?",
        "bars": compiled.total_bars, "seconds": round(compiled.duration_sec, 1), "form": form,
        "parts": sorted(f"{i.type}{'/' + i.tone if i.tone else ''}" for i in song.instruments.values()),
        "chord_trigrams": trigrams, "distinct_chords": len(set(prog)),
        "drum_patterns": [list(map(list, p)) for p in drum_patterns],
        "drum_top_share": round(drum_patterns.most_common(1)[0][1] / sum(drum_patterns.values()), 3)
        if drum_patterns else None,
    }

    lead = _lead_part(compiled, events)
    d["lead"] = lead
    if lead:
        d.update(_describe_lead(compiled, [e for e in events if e.part == lead], chords, ref, bar_beats))
    return d


def _describe_lead(compiled: Compiled, evs: list[Event], chords, ref: int, bar_beats: Fraction) -> dict:
    evs = sorted(evs, key=lambda e: (e.beat, -e.pitch))
    line = [e for i, e in enumerate(evs) if i == 0 or e.beat != evs[i - 1].beat]  # top note of each onset

    intervals = Counter()
    for a, b in zip(line, line[1:]):
        step = abs(b.pitch - a.pitch)
        intervals["repeat" if step == 0 else "step" if step <= 2 else "third" if step <= 4
                  else "leap" if step <= 7 else "wide"] += 1

    lengths = Counter()
    for e in line:
        s = _sec(compiled, e)
        lengths["<0.25s" if s < 0.25 else "<0.5s" if s < 0.5 else "<1s" if s < 1 else ">=1s"] += 1

    strong = {Fraction(0), bar_beats / 2} if bar_beats.denominator == 1 and bar_beats % 2 == 0 else {Fraction(0)}
    degrees = Counter()
    for e in line:
        if e.pos_in_bar in strong:
            t = _chord_of(e, chords)
            if t:
                degrees[DEGREES[(e.pitch - t[0]) % 12]] += 1

    rhythms = defaultdict(list)
    for e in line:
        rhythms[e.src["global_bar"]].append(f"{e.pos_in_bar}/{e.beats}")
    rhythm_seq = [tuple(rhythms[b]) for b in sorted(rhythms)]
    longest = run = 1
    for a, b in zip(rhythm_seq, rhythm_seq[1:]):
        run = run + 1 if a == b else 1
        longest = max(longest, run)

    played, end = 0.0, Fraction(-1)  # sounding time; overlapping notes count once
    for e in line:
        start, stop = max(e.beat, end), e.beat + e.beats
        if stop > start:
            played += float(stop - start)
            end = stop
    # Bars the lead sounds in, including bars a held note reaches without a new onset.
    span_bars = len({int(b) for e in line
                     for b in range(int(e.beat // bar_beats), int((e.beat + e.beats) // bar_beats) + 1)
                     if b * bar_beats < e.beat + e.beats})
    techniques = Counter(a for e in line for a in STRING_TECHNIQUES
                         if a in e.arts or any(a in t for t in e.arts.get("tied", [])))
    return {
        "lead_notes": len(line),
        "lead_range": f"{pitch_name(min(e.pitch for e in line))}-{pitch_name(max(e.pitch for e in line))}",
        "lead_intervals": _hist(intervals, ("repeat", "step", "third", "leap", "wide")),
        "lead_lengths": _hist(lengths, ("<0.25s", "<0.5s", "<1s", ">=1s")),
        "lead_strong_degrees": _hist(degrees, ("R", "3", "5", "7", "9", "4", "6", "b9", "#4", "b6")),
        "lead_pcs": _hist(Counter((e.pitch - ref) % 12 for e in line), range(12)),
        "lead_rest_share": round(1 - played / (span_bars * float(bar_beats)), 3) if span_bars else None,
        "lead_technique_rate": round(sum(1 for e in line if any(
            a in e.arts or any(a in t for t in e.arts.get("tied", [])) for a in STRING_TECHNIQUES)) / len(line), 3),
        "lead_techniques": dict(techniques.most_common()),
        "lead_bar_rhythms": sorted({"|".join(r) for r in rhythm_seq}),
        "lead_longest_same_rhythm": longest,
    }


# --- similarity ----------------------------------------------------------------

def _jaccard(a, b) -> float | None:
    a, b = set(map(str, a)), set(map(str, b))
    return len(a & b) / len(a | b) if a or b else None


def _overlap(a: dict, b: dict) -> float:
    return sum(min(a[k], b.get(k, 0)) for k in a)


def _edit_sim(a: str, b: str) -> float:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return 1 - prev[-1] / max(len(a), len(b), 1)


DIMENSIONS = {
    "tempo": lambda a, b: max(0.0, 1 - abs(a["tempo"] - b["tempo"]) / 40),
    "form": lambda a, b: _edit_sim(a["form"], b["form"]),
    "harmony": lambda a, b: _jaccard(a["chord_trigrams"], b["chord_trigrams"]),
    "drums": lambda a, b: _jaccard(a["drum_patterns"], b["drum_patterns"]),
    "lead_intervals": lambda a, b: _overlap(a["lead_intervals"], b["lead_intervals"]),
    "lead_lengths": lambda a, b: _overlap(a["lead_lengths"], b["lead_lengths"]),
    "lead_degrees": lambda a, b: _overlap(a["lead_strong_degrees"], b["lead_strong_degrees"]),
    "lead_pitches": lambda a, b: _overlap(a["lead_pcs"], b["lead_pcs"]),
    "lead_rhythms": lambda a, b: _jaccard(a["lead_bar_rhythms"], b["lead_bar_rhythms"]),
}


def similarity(songs: list[dict]) -> dict[str, float | None]:
    """Mean pairwise similarity (0 = nothing shared, 1 = identical) per dimension."""
    out = {}
    for name, fn in DIMENSIONS.items():
        vals = []
        for a, b in combinations(songs, 2):
            try:
                v = fn(a, b)
            except KeyError:  # a song without a lead
                continue
            if v is not None:
                vals.append(v)
        out[name] = round(mean(vals), 3) if vals else None
    return out


# --- floor checks ----------------------------------------------------------------

def floors(path: Path) -> list[str]:
    diags, song, compiled = load(path)
    if compiled is None or diags.errors:
        return []
    events = score_events(song)
    insts = song.instruments
    found: list[str] = []

    # Muddy low voicings: a close interval inside one part's chord below its low-interval limit.
    for pid, inst in insts.items():
        if not inst.pitched:
            continue
        groups = defaultdict(list)
        for e in events:
            if e.part == pid:
                groups[e.beat].append(e)
        reported = set()
        for group in groups.values():
            ps = sorted({e.pitch for e in group})
            for lo, hi in zip(ps, ps[1:]):
                limit = LOW_INTERVAL_LIMIT.get(hi - lo)
                key = (group[0].src["section"], lo, hi)
                if limit and lo < limit and key not in reported:
                    reported.add(key)
                    found.append(f"{_where(compiled, group[0])}: {pitch_name(lo)} and {pitch_name(hi)} "
                                 f"together sound muddy that low; voice the chord higher or drop a note")

    # A held melody note a minor 9th above the bass note sounding under it.
    lead = _lead_part(compiled, events)
    bass = [e for e in events if insts[e.part].type == "bass"]
    if lead:
        reported = set()
        for e in (e for e in events if e.part == lead):
            for b in bass:
                start, end = max(e.beat, b.beat), min(e.beat + e.beats, b.beat + b.beats)
                if end <= start or (e.pitch - b.pitch) % 12 != 1:
                    continue
                overlap = compiled.beat_to_sec(float(end)) - compiled.beat_to_sec(float(start))
                key = (e.src["section"], e.src["bar"], e.pitch)
                if overlap >= 0.4 and key not in reported:
                    reported.add(key)
                    found.append(f"{_where(compiled, e)}: {pitch_name(e.pitch)} clashes with the bass "
                                 f"{pitch_name(b.pitch)} a minor 9th below for {overlap:.1f} s; "
                                 f"change one of the two notes or shorten the overlap")

    # A lead mostly under the rhythm guitars' top notes in a section.
    if lead:
        rhythm = [e for e in events if e.part != lead and insts[e.part].type in ("guitar", "organ", "piano")]
        by_section = defaultdict(lambda: [0, 0])
        for e in (e for e in events if e.part == lead):
            tops = [r.pitch for r in rhythm if r.beat <= e.beat < r.beat + r.beats]
            if tops:
                counts = by_section[(e.src["section"], e.src["instance"])]
                counts[0] += 1
                counts[1] += e.pitch < max(tops)
        for (sec, inst_no), (n, under) in by_section.items():
            if n >= 8 and under / n > 0.5:
                found.append(f"{sec} (#{inst_no}) > {lead}: {under} of {n} lead notes sit under the top note "
                             f"of the rhythm parts; move the lead up an octave or voice the rhythm lower")

    # A part that plays the very same bar everywhere.
    for pid in insts:
        bars = defaultdict(list)
        for e in events:
            if e.part == pid:
                bars[e.src["global_bar"]].append((str(e.pos_in_bar), e.lane or e.pitch, str(e.beats)))
        contents = {tuple(sorted(v)) for v in bars.values()}
        if len(bars) >= 16 and len(contents) == 1:
            found.append(f"{pid}: plays the same bar in all {len(bars)} bars it plays; "
                         f"vary it between sections (fills, accents, a different groove in the chorus)")
    return found


# --- report ----------------------------------------------------------------------

def _paths(patterns: list[str]) -> list[Path]:
    out = []
    for p in patterns:
        matched = sorted(glob.glob(p, recursive=True))
        out += [Path(m) for m in matched] if matched else [Path(p)]
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="songs (one group named 'songs')")
    ap.add_argument("--group", action="append", default=[], metavar="NAME=GLOB",
                    help="a named group of songs; repeat to compare groups")
    ap.add_argument("--json", action="store_true", help="print all descriptors as JSON")
    args = ap.parse_args(argv)

    groups: dict[str, list[Path]] = {}
    if args.files:
        groups["songs"] = _paths(args.files)
    for g in args.group:
        name, _, pattern = g.partition("=")
        groups.setdefault(name, []).extend(_paths([pattern]))
    if not groups:
        ap.error("give song files or --group NAME=GLOB")

    result = {}
    for name, paths in groups.items():
        songs, skipped = [], []
        for p in paths:
            d = describe(p)
            (songs.append(d) if d else skipped.append(str(p)))
        for d in songs:
            d["floors"] = floors(Path(d["path"]))
        result[name] = {"songs": songs, "skipped": skipped, "similarity": similarity(songs)}

    if args.json:
        json.dump(result, sys.stdout, indent=1, default=str)
        return
    _print(result)


def _print(result: dict) -> None:
    dims = list(DIMENSIONS)
    print("## Similarity within each group (mean pairwise, 0-1; higher = more alike)\n")
    print("| group | songs | " + " | ".join(dims) + " |")
    print("|---|---|" + "---|" * len(dims))
    for name, g in result.items():
        sim = g["similarity"]
        cells = ["—" if sim[k] is None else f"{sim[k]:.2f}" for k in dims]
        print(f"| {name} | {len(g['songs'])} | " + " | ".join(cells) + " |")

    for name, g in result.items():
        print(f"\n## {name}\n")
        print("| song | key | tempo | bars | form | lead range | held >=1s | strong-beat degrees | "
              "technique rate | rest share | longest same rhythm | floors |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for d in g["songs"]:
            cells = [d["title"] or Path(d["path"]).name, d["key"], f"{d['tempo']:g}", d["bars"], d["form"]]
            if "lead_lengths" in d:
                deg = sorted(d["lead_strong_degrees"].items(), key=lambda kv: -kv[1])
                cells += [d["lead_range"], f"{d['lead_lengths']['>=1s']:.0%}",
                          ", ".join(f"{k} {v:.0%}" for k, v in deg[:3] if v) or "—",
                          f"{d['lead_technique_rate']:.0%}", f"{d['lead_rest_share']:.0%}",
                          d["lead_longest_same_rhythm"]]
            else:
                cells += ["—"] * 6
            print("| " + " | ".join(map(str, cells + [len(d["floors"])])) + " |")
        for d in g["songs"]:
            if d["floors"]:
                print(f"\n**{d['title'] or d['path']}** (`{d['path']}`)")
                for f in d["floors"][:8]:
                    print(f"- {f}")
                if len(d["floors"]) > 8:
                    print(f"- … {len(d['floors']) - 8} more")
        if g["skipped"]:
            print("\nSkipped (errors): " + ", ".join(g["skipped"]))


if __name__ == "__main__":
    main()
