#!/usr/bin/env python3
"""backlog.json 직접 조회/수정 차단 -> backlog.py CLI 사용 유도."""
import json
import re
import sys

BACKLOG_NAME = "backlog.json"

READ_CMD_RE = re.compile(
    r"\b(cat|type|more|less|Get-Content|gc)\b[^|;&\n]*\bbacklog\.json\b",
    re.IGNORECASE,
)

MESSAGE = (
    "backlog.json은 직접 조회/수정할 수 없습니다. "
    "다음 CLI를 사용하세요: "
    "python backlog.py list [--status S] | show <id> | "
    "add --title T --desc D | update <id> --status S"
)


def deny():
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": MESSAGE,
        }
    }))
    sys.exit(0)


def main():
    data = json.load(sys.stdin)
    tool = data.get("tool_name")
    inp = data.get("tool_input", {}) or {}

    if tool in ("Read", "Edit", "Write"):
        path = (inp.get("file_path") or "").replace("\\", "/").rstrip("/")
        if path.endswith(BACKLOG_NAME):
            deny()
    elif tool == "Bash":
        cmd = inp.get("command", "") or ""
        if "backlog.py" in cmd:
            return
        if READ_CMD_RE.search(cmd):
            deny()


if __name__ == "__main__":
    main()
