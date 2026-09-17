#!/usr/bin/env python3
"""Write/Edit 후: 코드 줄수 한도(85% 경고 / 100% 재작업) + lint(ruff) + build(py_compile) 강제."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

MAX_LINES = 300  # ponytail: Streamlit MVP 스케일 기준. 모듈이 실제로 커지면 조정.
WARN_RATIO = 0.85


def main():
    data = json.load(sys.stdin)
    inp = data.get("tool_input", {}) or {}
    path_str = inp.get("file_path") or (data.get("tool_response") or {}).get("filePath")
    if not path_str or not path_str.endswith(".py"):
        return
    path = Path(path_str)
    if not path.exists():
        return

    blocking = []
    warnings = []

    lines = len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
    ratio = lines / MAX_LINES
    if ratio >= 1.0:
        blocking.append(
            f"{path.name}: {lines}줄로 최대 허용치 {MAX_LINES}줄을 초과했습니다 ({ratio*100:.0f}%). "
            "파일을 분리하거나 리팩토링한 뒤 다시 작업하세요."
        )
    elif ratio >= WARN_RATIO:
        warnings.append(
            f"{path.name}: {lines}/{MAX_LINES}줄 ({ratio*100:.0f}%) 사용 중입니다. "
            "계속 늘어나면 분리를 고려하세요."
        )

    compiled = subprocess.run(
        [sys.executable, "-m", "py_compile", str(path)], capture_output=True, text=True
    )
    if compiled.returncode != 0:
        blocking.append(f"{path.name} 빌드(컴파일) 실패:\n{compiled.stderr.strip()[:1000]}")

    ruff = shutil.which("ruff")
    if ruff:
        linted = subprocess.run([ruff, "check", str(path)], capture_output=True, text=True)
        if linted.returncode != 0:
            blocking.append(f"{path.name} lint 실패:\n{linted.stdout.strip()[:1000]}")

    if blocking:
        print(json.dumps({"decision": "block", "reason": "\n\n".join(blocking)}))
    elif warnings:
        print(json.dumps({"systemMessage": "\n".join(warnings)}))


if __name__ == "__main__":
    main()
