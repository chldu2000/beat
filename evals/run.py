"""Run eval tasks with fresh headless Claude Code agents, then grade them.

    uv run python -m evals.run --tasks t1,t5 --runs 3 --model sonnet
    uv run python -m evals.run --grade-only evals/results/<dir>     # re-grade existing runs
    uv run python -m evals.run --resume evals/results/<dir>         # finish runs stopped by usage limits

Each run gets a temp workspace outside this repo (so no CLAUDE.md or memory leaks in) holding
SPEC.md, the example song, an optional start file and a logging `beat` shim on PATH. The agent
runs in --safe-mode --restricted with the compose skill as its system-prompt addition; it may
run `beat` and use file tools inside the workspace only.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import yaml

from .describe import describe
from .grade import grade_run
from .report import write_report
from .score import load

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / ".claude" / "skills" / "compose" / "SKILL.md"
SONG = "song.beat.yaml"

FOOTER = f"""

Work in the current directory and write the song to {SONG}. Use `beat validate {SONG}` and
`beat events {SONG}` as often as you like (`beat` is on PATH; run it exactly like that); do not
render audio.

When you are done, write NOTES.md with three short lists:
1. What was hard or confusing about the Beat DSL or its tools.
2. Workarounds you used for things the DSL could not express directly.
3. Features or changes you wish existed.
"""


def load_task(task_id: str) -> dict:
    matches = sorted((REPO / "evals" / "tasks").glob(f"{task_id}*.yaml"))
    if len(matches) != 1:
        raise SystemExit(f"task '{task_id}' matches {len(matches)} files")
    return yaml.safe_load(matches[0].read_text())


def guide_text() -> str:
    text = SKILL.read_text()
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    return text.replace("(in this repo: `docs/SPEC.md`) ", "").strip()


def build_prompt(task: dict) -> str:
    prompt = task["prompt"]
    if "{description}" in prompt:
        _, ref, _ = load(REPO / task["reference"])
        prompt = prompt.replace("{description}", describe(ref))
    return prompt.rstrip() + FOOTER


def setup_workspace(task: dict) -> Path:
    ws = Path(tempfile.mkdtemp(prefix=f"beat-eval-{task['id']}-"))
    shutil.copyfile(REPO / "docs" / "SPEC.md", ws / "SPEC.md")
    (ws / "examples").mkdir()
    shutil.copyfile(REPO / "examples" / "demo.beat.yaml", ws / "examples" / "demo.beat.yaml")
    if task.get("start"):
        shutil.copyfile(REPO / task["start"], ws / SONG)
    bin_dir = ws / ".bin"
    bin_dir.mkdir()
    shim = bin_dir / "beat"
    shim.write_text(f"#!{sys.executable}\nimport sys\nsys.path.insert(0, {str(REPO)!r})\n"
                    f"from evals.shim import main\nsys.exit(main())\n")
    shim.chmod(0o755)
    return ws


def run_one(task: dict, run_dir: Path, model: str, budget: float, timeout: int) -> dict:
    ws = setup_workspace(task)
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt = build_prompt(task)
    (run_dir / "prompt.md").write_text(prompt)

    env = {**os.environ, "PATH": f"{ws / '.bin'}{os.pathsep}{os.environ['PATH']}",
           "BEAT_EVAL_LOG": str(ws / ".beatlog")}
    cmd = [
        "claude", "-p", prompt, "--model", model, "--safe-mode",
        # --restricted confines file tools to the workspace, so references in this repo stay unreadable.
        "--restricted", "--append-system-prompt", guide_text(),
        "--tools", "Bash,Read,Write,Edit,Glob,Grep",
        # Some agents call the shim by path; both spellings run the same logged CLI.
        "--allowedTools", "Bash(beat *)", "Bash(./.bin/beat *)", "Bash(.bin/beat *)", "Write", "Edit",
        "--permission-mode", "dontAsk", "--no-session-persistence",
        "--output-format", "stream-json", "--verbose", "--max-budget-usd", str(budget),
    ]
    started = time.time()
    with (run_dir / "transcript.jsonl").open("w") as out, (run_dir / "stderr.txt").open("w") as err:
        try:
            proc = subprocess.run(cmd, cwd=ws, env=env, stdout=out, stderr=err, timeout=timeout)
            status = f"exit {proc.returncode}"
        except subprocess.TimeoutExpired:
            status = "timeout"
    (run_dir / "status.txt").write_text(f"{status}\nwall_sec {time.time() - started:.0f}\nworkspace {ws}\n")

    for name in (SONG, "NOTES.md"):
        if (ws / name).exists():
            shutil.copyfile(ws / name, run_dir / name)
    if (ws / ".beatlog").exists():
        shutil.copytree(ws / ".beatlog", run_dir / "beatlog", dirs_exist_ok=True)
    shutil.rmtree(ws, ignore_errors=True)
    return grade_run(run_dir, task, REPO)


def _needs_run(run_dir: Path) -> bool:
    metrics = run_dir / "metrics.json"
    if not metrics.exists():
        return True
    if json.loads(metrics.read_text()).get("infra_failure"):
        shutil.rmtree(run_dir)
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="t1,t2,t3,t4,t5", help="comma-separated task id prefixes")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--jobs", type=int, default=3, help="runs in parallel")
    ap.add_argument("--budget", type=float, default=3.0, help="max USD per run")
    ap.add_argument("--timeout", type=int, default=1800, help="seconds per run")
    ap.add_argument("--label", default="", help="suffix for the results directory")
    ap.add_argument("--grade-only", type=Path, help="re-grade an existing results directory")
    ap.add_argument("--resume", type=Path, help="run missing or infra-failed runs of a results directory")
    args = ap.parse_args()

    if args.grade_only:
        out = args.grade_only
        for run_dir in sorted(p for p in out.glob("*/run-*") if p.is_dir()):
            grade_run(run_dir, load_task(run_dir.parent.name), REPO)
        write_report(out)
        print(f"report: {out / 'REPORT.md'}")
        return 0

    if args.resume:
        out = args.resume
        config = json.loads((out / "config.json").read_text())
        args.model, args.runs = config["model"], config["runs"]
        tasks = [load_task(t.strip()) for t in config["tasks"].split(",")]
    else:
        tasks = [load_task(t.strip()) for t in args.tasks.split(",")]
        stamp = datetime.now().strftime("%Y%m%d-%H%M")
        out = REPO / "evals" / "results" / f"{stamp}-{args.model}{'-' + args.label if args.label else ''}"
        out.mkdir(parents=True)
        (out / "config.json").write_text(json.dumps(vars(args), default=str, indent=2))

    jobs = [(t, out / t["id"] / f"run-{i + 1}") for t in tasks for i in range(args.runs)]
    jobs = [(t, d) for t, d in jobs if _needs_run(d)]
    print(f"{len(jobs)} runs -> {out}")
    stop = threading.Event()

    def job(task: dict, run_dir: Path) -> dict | None:
        if stop.is_set():
            return None
        m = run_one(task, run_dir, args.model, args.budget, args.timeout)
        if m.get("infra_failure"):
            stop.set()  # a usage limit will fail every later run too
        return m

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(job, t, d): d for t, d in jobs}
        for fut, d in futures.items():
            try:
                m = fut.result()
                if m is None:
                    print(f"{d.parent.name}/{d.name}: skipped (stopped after an infrastructure failure)")
                elif m.get("infra_failure"):
                    print(f"{d.parent.name}/{d.name}: INFRA FAILURE {m['infra_failure']}")
                else:
                    print(f"{d.parent.name}/{d.name}: valid={m['final_valid']} "
                          f"first_errors={m['first_check_errors']} cost=${m.get('cost_usd') or 0:.2f}")
            except Exception as e:
                print(f"{d.parent.name}/{d.name}: FAILED {type(e).__name__}: {e}")
    write_report(out)
    if stop.is_set():
        print(f"stopped early; continue later with: uv run python -m evals.run --resume {out}")
    print(f"report: {out / 'REPORT.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
