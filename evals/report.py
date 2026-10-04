"""Aggregate metrics.json files of a results directory into REPORT.md."""

import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


def _avg(values) -> str:
    values = [v for v in values if v is not None]
    return f"{mean(values):.2f}" if values else "—"


def _rate(flags) -> str:
    flags = list(flags)
    return f"{sum(flags)}/{len(flags)}" if flags else "—"


def write_report(out: Path) -> None:
    runs = defaultdict(list)
    skipped: list[str] = []
    for f in sorted(out.glob("*/run-*/metrics.json")):
        m = json.loads(f.read_text())
        if m.get("infra_failure"):
            skipped.append(f"{m['task']}/{m['run']}: {m['infra_failure']}")
            continue
        runs[m["task"]].append(m)

    lines = [f"# Eval report: {out.name}", ""]
    config = out / "config.json"
    if config.exists():
        c = json.loads(config.read_text())
        lines += [f"model `{c.get('model')}`, {c.get('runs')} run(s) per task", ""]

    if skipped:
        lines += [f"**{len(skipped)} run(s) excluded (infrastructure failures, e.g. usage limits):**", ""]
        lines += [f"- {s}" for s in skipped] + [""]

    lines += [
        "| task | final valid | first check clean | checks to green | F1 | dur acc | arts acc | dyn acc "
        "| task checks | chars/bar | cost $ | turns |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for task, ms in runs.items():
        cmp = [m.get("compare") or {} for m in ms]
        checks = [f"{m['checks_passed']}/{m['checks_total']}" for m in ms if "checks_total" in m]
        lines.append(" | ".join([
            f"| {task}", _rate(m["final_valid"] for m in ms),
            _rate(m["first_check_errors"] == 0 for m in ms if m["first_check_errors"] is not None),
            _avg(m["checks_to_green"] for m in ms),
            _avg(c.get("f1") for c in cmp), _avg(c.get("duration_acc") for c in cmp),
            _avg(c.get("arts_acc") for c in cmp), _avg(c.get("dynamic_acc") for c in cmp),
            ", ".join(checks) or "—", _avg(m.get("chars_per_bar") for m in ms),
            _avg(m.get("cost_usd") for m in ms), _avg(m.get("turns") for m in ms) + " |",
        ]))

    lines += ["", "## Error categories (distinct errors seen during the session, summed over runs)", "",
              "| task | " + " | ".join(["first check", "whole session"]) + " |", "|---|---|---|"]
    total_first, total_all = Counter(), Counter()
    for task, ms in runs.items():
        first = sum((Counter(m["error_categories_first"]) for m in ms), Counter())
        allc = sum((Counter(m["error_categories_all"]) for m in ms), Counter())
        total_first += first
        total_all += allc
        fmt = lambda c: ", ".join(f"{k} {v}" for k, v in c.most_common()) or "—"
        lines.append(f"| {task} | {fmt(first)} | {fmt(allc)} |")
    lines.append(f"| **all** | {', '.join(f'{k} {v}' for k, v in total_first.most_common()) or '—'} "
                 f"| {', '.join(f'{k} {v}' for k, v in total_all.most_common()) or '—'} |")

    lines += ["", "## Per run", ""]
    for task, ms in runs.items():
        lines.append(f"### {task}")
        for m in ms:
            c = m.get("compare") or {}
            failed = [k for k, v in (m.get("checks") or {}).items() if not v]
            lines.append(f"- **{m['run']}**: valid={m['final_valid']}, error trace {m['error_trace']}, "
                         f"F1={c.get('f1', '—')}, cost=${m.get('cost_usd') or 0:.2f}"
                         + (f", failed checks: {failed}" if failed else "")
                         + (f", final errors: {m['final_errors'][:3]}" if m.get("final_errors") else "")
                         + (f", denied: {m['denied'][:3]}" if m.get("denied") else ""))
            for key in ("missing", "extra", "wrong_length"):
                if c.get(key):
                    lines.append(f"  - {key}: {'; '.join(c[key][:6])}")
        lines.append("")

    lines += ["## Agent notes", ""]
    for task, ms in runs.items():
        for m in ms:
            if m.get("notes"):
                lines += [f"### {task} / {m['run']}", "", m["notes"].strip(), ""]

    (out / "REPORT.md").write_text("\n".join(lines) + "\n")
