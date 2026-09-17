#!/usr/bin/env python3
"""backlog.json 변경 감지 -> 자동 커밋. 상태가 done으로 바뀌면 전체 변경 커밋 + push."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKLOG = ROOT / "backlog.json"

TRAILER = "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"


def run(*args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


def newly_done_ids():
    if not BACKLOG.exists():
        return []
    try:
        current = json.loads(BACKLOG.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    show = run("git", "show", "HEAD:backlog.json")
    try:
        prior = json.loads(show.stdout) if show.returncode == 0 else {"tasks": []}
    except json.JSONDecodeError:
        prior = {"tasks": []}

    prior_status = {t["id"]: t.get("status") for t in prior.get("tasks", [])}
    return [
        t["id"] for t in current.get("tasks", [])
        if t.get("status") == "done" and prior_status.get(t["id"]) != "done"
    ]


def main():
    status = run("git", "status", "--porcelain", "--", "backlog.json")
    if not status.stdout.strip():
        return

    done_ids = newly_done_ids()

    if done_ids:
        run("git", "add", "-A")
        msg = f"backlog: complete {', '.join(done_ids)} - sync all work\n\n{TRAILER}"
    else:
        run("git", "add", "backlog.json", "tasks")
        msg = f"backlog: update via CLI\n\n{TRAILER}"

    commit = run("git", "commit", "-m", msg)
    if commit.returncode != 0:
        return

    if done_ids:
        push = run("git", "push")
        note = f"backlog: {', '.join(done_ids)} 완료 -> 커밋"
        note += " + push 완료" if push.returncode == 0 else f" (push 실패: {push.stderr.strip()[:200]})"
    else:
        note = "backlog.json 변경 감지 -> 자동 커밋 완료"

    print(json.dumps({"systemMessage": note}))


if __name__ == "__main__":
    main()
