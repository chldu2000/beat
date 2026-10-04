from pathlib import Path

from evals.describe import describe
from evals.grade import categorize
from evals.score import compare, load

REFS = Path(__file__).parent.parent / "evals" / "refs"


def test_reference_matches_itself():
    for name in ("riff", "tricky"):
        _, song, _ = load(REFS / f"{name}.beat.yaml")
        assert compare(song, song)["f1"] == 1.0


def test_compare_detects_differences(tmp_path):
    text = (REFS / "riff.beat.yaml").read_text()
    changed = text.replace('"(A1:8)*8 | (A1:8)*6 G1:8 E1:8', '"(A1:8)*8 | (A1:8)*6 G1:4')
    path = tmp_path / "x.beat.yaml"
    path.write_text(changed)
    _, cand, _ = load(path)
    _, ref, _ = load(REFS / "riff.beat.yaml")
    result = compare(cand, ref)
    assert result["missing"] == ["bs bar 2 beat 4.5 E1"]
    assert result["wrong_length"] == ["bs bar 2 beat 4 G1: 1 beats (quarter) instead of 0.5 beats (eighth)"]
    assert result["per_part_f1"]["gt"] == 1.0


def test_broken_reference_is_broken():
    diags, _, _ = load(REFS / "riff_broken.beat.yaml")
    assert diags.has_errors


def test_describe_mentions_tricky_details():
    _, song, _ = load(REFS / "tricky.beat.yaml")
    text = describe(song)
    assert "beat 1+2/3: ride" in text
    assert "C2, 6 beats" in text
    assert "snare (flam)" in text
    assert "[dynamic f from here]" in text


def test_error_categories():
    assert categorize("[error] a > bs > bar 2: duration 3.5 beats, expected 4") == "bar_duration"
    assert categorize("[error] b > dr > bar 2: lane 'bd' has 17 steps in this bar, expected 16") == "grid_length"
    assert categorize("[error] a > gt > bar 1: unknown articulation '!palm' in 'A2!palm'") == "token"
    assert categorize("[error] YAML syntax error: ...") == "yaml"


def test_hits_and_beat_lengths_match_grid_and_ties(tmp_path):
    """The riff reference rewritten with `hits` and `:b` lengths compiles to the same notes."""
    text = (REFS / "riff.beat.yaml").read_text()
    text = text.replace("""    grid: |
      hh: x-x-x-x-x-x-x-x-
      sd: ----X-------X---
      bd: x-----x-x-------""", """    hits: |
      hh: every 0.5
      sd: 2!acc 4!acc
      bd: 1 2.5 3""")
    text = text.replace("F1:4. F1:8~ F1:2", "F1:4. F1:b2.5")
    path = tmp_path / "x.beat.yaml"
    path.write_text(text)
    diags, cand, _ = load(path)
    assert not diags.has_errors, diags.errors
    _, ref, _ = load(REFS / "riff.beat.yaml")
    assert compare(cand, ref)["f1"] == 1.0
    assert compare(cand, ref)["duration_acc"] == 1.0
