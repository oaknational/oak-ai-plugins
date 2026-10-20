"""Check a release version and write its notes from the CHANGELOG.

A release must carry the version both manifests hold and the CHANGELOG's
latest entry names, so this script refuses any other version. The notes are
that CHANGELOG entry, followed by the install commands.

The notes go to standard output. Run by the "Release" workflow before it
builds the ChatGPT upload ZIP and creates the release; runs locally too:

  python3 scripts/release_notes.py --version 1.2.0 > notes.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = (
    "claude/plugins/oak-national-academy/.claude-plugin/plugin.json",
    "chatgpt/plugins/oak-national-academy/.codex-plugin/plugin.json",
)
INSTALL = """
## Install in Claude Code

```text
/plugin marketplace add oaknational/oak-ai-plugins
/plugin install oak-national-academy@oak-ai-plugins
```
"""


def latest_entry(changelog: str) -> tuple[str, str]:
    """The version and body of the CHANGELOG's first `## <version> — <date>` entry."""
    lines = changelog.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("## ")]
    if not starts:
        return "missing", ""
    first = starts[0]
    end = starts[1] if len(starts) > 1 else len(lines)
    return lines[first].split()[1], "\n".join(lines[first + 1:end]).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="version to release, without the v")
    args = parser.parse_args()

    problems = []
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        problems.append(f"{args.version} is not MAJOR.MINOR.PATCH")
    for manifest in MANIFESTS:
        found = json.loads((ROOT / manifest).read_text(encoding="utf-8")).get("version")
        if found != args.version:
            problems.append(f"{manifest} says {found}")
    version, body = latest_entry((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
    if version != args.version:
        problems.append(f"CHANGELOG.md's latest entry is {version}")
    if problems:
        for problem in problems:
            print(f"error: cannot release {args.version}: {problem}", file=sys.stderr)
        return 1

    print(body + "\n" + INSTALL, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
