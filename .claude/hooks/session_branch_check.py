#!/usr/bin/env python3
"""세션 시작 시 현재 git 브랜치 안내. main이면 dev로 전환하라고 경고."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    result = subprocess.run(
        ["git", "branch", "--show-current"], cwd=ROOT, capture_output=True, text=True
    )
    branch = result.stdout.strip()

    if not branch:
        message = "현재 git 브랜치를 확인할 수 없습니다 (detached HEAD이거나 git 저장소가 아님)."
    elif branch == "main":
        message = (
            f"현재 브랜치: main\n"
            "⚠️ main 브랜치에서 바로 작업 중입니다. "
            "`git checkout dev` (또는 없다면 `git checkout -b dev`)로 전환한 뒤 작업하세요."
        )
    else:
        message = f"현재 브랜치: {branch}"

    print(json.dumps({"systemMessage": message}))


if __name__ == "__main__":
    main()
