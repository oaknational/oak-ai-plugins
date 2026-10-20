"""Copy the plugins from their source repository into this one, consistently.

Given a checkout of the source repository, this script replaces every
published copy in PROVENANCE.json with its source directory (minus the
excluded paths), rewrites each publish's entry — a fresh copy is
verbatim, so any known_divergences are cleared — and, when the version
is new, inserts a stub entry at the top of the root CHANGELOG. The
packages are cut from the same source at the same version, so one sync
copies them all from one commit, and fails if their versions differ.

Run by the "Sync plugin from the ecosystem" workflow; runs locally too:

  python3 scripts/sync_plugin.py --source /path/to/ecosystem-checkout \\
      --commit <full sha> [--release v1.185.3]

After it runs, scripts/check_provenance.py should pass with no known
divergences, and scripts/check_against_plugin.py keeps the README,
CHANGELOG and marketplace entry honest.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LABELS = {
    "claude": "the Claude plugin",
    "chatgpt": "the ChatGPT package",
}


def copy_plugin(source_repo: Path, publish: dict) -> None:
    source = source_repo / publish["source_path"]
    if not source.is_dir():
        sys.exit(f"error: {source} is not a directory")
    copy = ROOT / publish["path"]
    if copy.exists():
        shutil.rmtree(copy)
    shutil.copytree(source, copy)
    for pattern in publish["excluded"]:
        for target in sorted(copy.rglob(pattern.rstrip("/"))):
            shutil.rmtree(target) if target.is_dir() else target.unlink()


def update_changelog(packages: str, version: str, commit: str, release: str | None) -> bool:
    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    latest = re.search(r"^## (\S+)", text, re.M)
    if latest and latest.group(1) == version:
        return False
    source = f"oak-open-curriculum-ecosystem at {commit[:9]}"
    if release:
        source += f" (release {release})"
    today = datetime.date.today().isoformat()
    entry = (
        f"## {version} — {today}\n\n"
        f"- Publishes {packages} {version}, copied from {source}, "
        f"without the `evals/` folders.\n"
    )
    text = text.replace("\n## ", f"\n{entry}\n## ", 1)
    changelog.write_text(text, encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="checkout of the source repository")
    parser.add_argument("--commit", required=True, help="full SHA the checkout is at")
    parser.add_argument("--release", help="source release the commit belongs to, e.g. v1.185.3")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        sys.exit("error: --commit must be a full 40-character SHA")

    provenance_file = ROOT / "PROVENANCE.json"
    provenance = json.loads(provenance_file.read_text(encoding="utf-8"))
    publishes = provenance["publishes"]
    source = Path(args.source).resolve()

    # Checked before anything is copied, so a refused sync leaves no trace.
    for p in publishes:
        if not (source / p["source_path"] / p["manifest"]).is_file():
            sys.exit(f"error: the source has no {p['source_path']}/{p['manifest']}")
    versions = {
        json.loads((source / p["source_path"] / p["manifest"]).read_text(encoding="utf-8"))[
            "version"
        ]
        for p in publishes
    }
    if len(versions) != 1:
        sys.exit(
            f"error: the source's packages carry different versions {sorted(versions)}; "
            "the root CHANGELOG has one heading per version"
        )
    version = versions.pop()

    for publish in publishes:
        copy_plugin(source, publish)
        publish["commit"] = args.commit
        # No --release means this commit has no known release: record null rather
        # than carrying the previous publish's release forward to a new commit.
        publish["release"] = args.release
        publish["plugin_version"] = version
        publish["known_divergences"] = []
        print(f"Copied {publish['source_path']} {version} at {args.commit[:9]}")
    provenance_file.write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    packages = " and ".join(LABELS[p["path"].split("/", 1)[0]] for p in publishes)
    added = update_changelog(packages, version, args.commit, args.release)
    print(f"PROVENANCE.json updated; version {version}")
    if not added:
        print(
            f"CHANGELOG.md already leads with {version} — "
            "extend that entry by hand if this publish needs recording."
        )


if __name__ == "__main__":
    main()
