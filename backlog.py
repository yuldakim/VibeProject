#!/usr/bin/env python3
"""backlog.json 조회/수정/추가 CLI.

Usage:
  python backlog.py list [--status S] [--category C]
  python backlog.py show <id>
  python backlog.py add --title T --desc D [--category C] [--priority P]
                         [--depends-on T01,T02] [--minutes 30] [--id T19]
  python backlog.py update <id> [--status S] [--title T] [--desc D]
                         [--category C] [--priority P] [--depends-on T01,T02]
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
BACKLOG_PATH = ROOT / "backlog.json"

DOC_TEMPLATE = """# {id}. {title}

## 목표
{description}

## 작업 내용
-

## 완료 조건
- [ ]

## 참고
- 의존: {depends_on}
"""


def load():
    if not BACKLOG_PATH.exists():
        sys.exit(f"backlog.json not found at {BACKLOG_PATH}")
    return json.loads(BACKLOG_PATH.read_text(encoding="utf-8"))


def save(data):
    data["updated_at"] = today()
    BACKLOG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def today():
    return datetime.date.today().isoformat()


def find_task(data, task_id):
    for t in data["tasks"]:
        if t["id"] == task_id:
            return t
    return None


def next_id(data):
    nums = [
        int(m.group(1))
        for t in data["tasks"]
        if (m := re.fullmatch(r"T(\d+)", t["id"]))
    ]
    return f"T{(max(nums) + 1) if nums else 1:02d}"


def cmd_list(args, data):
    tasks = data["tasks"]
    if args.status:
        tasks = [t for t in tasks if t["status"] == args.status]
    if args.category:
        tasks = [t for t in tasks if t.get("category") == args.category]
    if not tasks:
        print("(no matching tasks)")
        return
    for t in tasks:
        deps = ",".join(t.get("depends_on", [])) or "-"
        print(
            f"{t['id']}  [{t['status']:<14}] {t['title']}  "
            f"(cat={t.get('category','-')} pri={t.get('priority','-')} deps={deps})"
        )


def cmd_show(args, data):
    t = find_task(data, args.id)
    if not t:
        sys.exit(f"task not found: {args.id}")
    print(json.dumps(t, ensure_ascii=False, indent=2))
    doc_path = ROOT / t.get("doc", "")
    if doc_path.exists():
        print(f"\n--- {t['doc']} ---")
        print(doc_path.read_text(encoding="utf-8"))
    else:
        print(f"\n(문서 없음: {t.get('doc')})")


def validate_status(data, status):
    if status not in data["statuses"]:
        allowed = ", ".join(data["statuses"])
        sys.exit(f"invalid status '{status}'. allowed: {allowed}")


def validate_deps(data, deps):
    ids = {t["id"] for t in data["tasks"]}
    unknown = [d for d in deps if d not in ids]
    if unknown:
        sys.exit(f"unknown depends_on ids: {', '.join(unknown)}")


def cmd_add(args, data):
    task_id = args.id or next_id(data)
    if find_task(data, task_id):
        sys.exit(f"id already exists: {task_id}")
    deps = [d.strip() for d in args.depends_on.split(",") if d.strip()] if args.depends_on else []
    validate_deps(data, deps)
    status = args.status or "todo"
    validate_status(data, status)
    doc_rel = f"tasks/{task_id}.md"

    task = {
        "id": task_id,
        "title": args.title,
        "description": args.desc,
        "status": status,
        "doc": doc_rel,
        "category": args.category or "misc",
        "priority": args.priority or "medium",
        "estimated_minutes": args.minutes,
        "depends_on": deps,
        "created_at": today(),
        "updated_at": today(),
    }
    data["tasks"].append(task)
    save(data)

    doc_path = ROOT / doc_rel
    if not doc_path.exists():
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(
            DOC_TEMPLATE.format(
                id=task_id,
                title=args.title,
                description=args.desc,
                depends_on=", ".join(deps) or "없음",
            ),
            encoding="utf-8",
        )
    print(f"added {task_id} -> {doc_rel}")


def cmd_update(args, data):
    t = find_task(data, args.id)
    if not t:
        sys.exit(f"task not found: {args.id}")

    if args.status:
        validate_status(data, args.status)
        t["status"] = args.status
    if args.title:
        t["title"] = args.title
    if args.desc:
        t["description"] = args.desc
    if args.category:
        t["category"] = args.category
    if args.priority:
        t["priority"] = args.priority
    if args.minutes is not None:
        t["estimated_minutes"] = args.minutes
    if args.depends_on is not None:
        deps = [d.strip() for d in args.depends_on.split(",") if d.strip()]
        validate_deps(data, deps)
        t["depends_on"] = deps

    if not any(
        [args.status, args.title, args.desc, args.category, args.priority,
         args.minutes is not None, args.depends_on is not None]
    ):
        sys.exit("nothing to update: pass at least one of --status/--title/--desc/--category/--priority/--minutes/--depends-on")

    t["updated_at"] = today()
    save(data)
    print(f"updated {t['id']}")


def build_parser():
    p = argparse.ArgumentParser(description="backlog.json CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("list", help="태스크 목록 조회")
    pl.add_argument("--status")
    pl.add_argument("--category")
    pl.set_defaults(func=cmd_list)

    ps = sub.add_parser("show", help="태스크 상세 + 연결 문서 조회")
    ps.add_argument("id")
    ps.set_defaults(func=cmd_show)

    pa = sub.add_parser("add", help="태스크 추가 (+ 상세 문서 스텁 생성)")
    pa.add_argument("--title", required=True)
    pa.add_argument("--desc", required=True)
    pa.add_argument("--category")
    pa.add_argument("--priority")
    pa.add_argument("--status")
    pa.add_argument("--depends-on", help="쉼표로 구분된 id 목록, 예: T01,T02")
    pa.add_argument("--minutes", type=int, default=30)
    pa.add_argument("--id", help="지정하지 않으면 자동 생성 (T## 형식)")
    pa.set_defaults(func=cmd_add)

    pu = sub.add_parser("update", help="태스크 필드 수정 (상태 변경 포함)")
    pu.add_argument("id")
    pu.add_argument("--status")
    pu.add_argument("--title")
    pu.add_argument("--desc")
    pu.add_argument("--category")
    pu.add_argument("--priority")
    pu.add_argument("--minutes", type=int)
    pu.add_argument("--depends-on", help="쉼표로 구분된 id 목록, 빈 문자열이면 초기화")
    pu.set_defaults(func=cmd_update)

    return p


def main():
    args = build_parser().parse_args()
    data = load()
    args.func(args, data)


if __name__ == "__main__":
    main()
