#!/usr/bin/env python3
"""List and resolve installed QCC leaf Skills without loading their full bodies."""

import argparse
import json
from pathlib import Path
import re
import sys


LEAF_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-qcc$")


def installed_root(supplied: str | None) -> Path:
    root = Path(supplied).expanduser() if supplied is not None else Path.home() / ".claude/skills"
    if not root.is_absolute() or not root.is_dir():
        raise ValueError(f"installed QCC skills root missing or not absolute: {root}")
    return root


def description(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"QCC Skill has no YAML frontmatter: {path}")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(f"QCC Skill frontmatter is unclosed: {path}") from exc
    header = lines[1:end]
    for index, line in enumerate(header):
        if not line.startswith("description:"):
            continue
        value = line.partition(":")[2].strip()
        if value in (">", ">-", "|", "|-"):
            parts = []
            for continuation in header[index + 1 :]:
                if continuation and not continuation[0].isspace():
                    break
                if continuation.strip():
                    parts.append(continuation.strip())
            value = " ".join(parts)
        if not value:
            raise ValueError(f"QCC Skill description is empty: {path}")
        return value[:240]
    raise ValueError(f"QCC Skill description missing: {path}")


def leaves(root: Path) -> list[dict[str, str]]:
    entries = []
    for directory in sorted(root.iterdir(), key=lambda path: path.name):
        if not LEAF_NAME.fullmatch(directory.name) or not directory.is_dir():
            continue
        entry = directory / "SKILL.md"
        if not entry.is_file():
            raise ValueError(f"installed QCC leaf missing SKILL.md: {entry}")
        entries.append({"name": directory.name, "description": description(entry)})
    if not entries:
        raise ValueError(f"no installed QCC leaf Skills found under {root}")
    return entries


def resolve(root: Path, name: str) -> Path:
    if not LEAF_NAME.fullmatch(name):
        raise ValueError(f"invalid QCC Skill directory name: {name}")
    entry = root / name / "SKILL.md"
    if not entry.is_file():
        raise ValueError(f"QCC Skill is not installed: {entry}")
    description(entry)
    return entry.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="absolute installed skills directory")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    selected = sub.add_parser("resolve")
    selected.add_argument("name")
    args = parser.parse_args()
    try:
        root = installed_root(args.root)
        if args.command == "list":
            print(json.dumps(leaves(root), ensure_ascii=False, indent=2))
        else:
            print(resolve(root, args.name))
    except (OSError, ValueError) as exc:
        print(f"qcc-router: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
