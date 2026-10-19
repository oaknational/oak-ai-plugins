"""Prove each published plugin is a faithful copy of its recorded source.

PROVENANCE.json records, for every plugin copy this repository publishes,
the source repository, the commit the copy was taken from, the paths left
out of the copy and any known, explained divergences. This script checks
that every plugin the marketplace publishes has a provenance entry, clones
each entry's source at its recorded commit (sparse and blobless, so it is
quick) and compares the trees file by file. Any differing, missing or
extra file that is not excluded or recorded as a known divergence fails
the check, as does a plugin manifest whose version differs from the
recorded one.

The comparison walks both trees in Python rather than parsing `git diff`
output: --no-index reports one-sided files as /dev/null and C-quotes
unusual names, both of which are easy to mishandle silently.

Run by CI (the "Sync fidelity" job); needs network access. Run it locally
the same way: python3 scripts/check_provenance.py
"""

from __future__ import annotations

import filecmp
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(args: list[str], cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def clone_source(publish: dict, workdir: Path) -> Path:
    """Sparse-clone the source repository at the recorded commit and return
    the path of the source plugin directory."""
    repo = workdir / "source"
    run(
        [
            "git",
            "clone",
            "--filter=blob:none",
            "--no-checkout",
            publish["source_repo"],
            str(repo),
        ],
        cwd=workdir,
    )
    run(["git", "sparse-checkout", "set", publish["source_path"]], cwd=repo)
    run(["git", "checkout", "--quiet", publish["commit"]], cwd=repo)
    return repo / publish["source_path"]


def tree_files(base: Path, excluded_names: set[str]) -> set[str]:
    """Every file under base as a relative POSIX path, pruning any directory
    or file whose name is excluded — at any depth, matching how the sync
    strips exclusions from the copy."""
    files = set()
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in excluded_names]
        for name in filenames:
            if name not in excluded_names:
                path = Path(dirpath, name).relative_to(base)
                files.add(path.as_posix())
    return files


def differing_files(source: Path, copy: Path, excluded: list[str]) -> list[str]:
    """Files that differ between the source tree and the copy, as paths
    relative to the copy: changed content, missing from the copy, or
    present only in the copy."""
    excluded_names = {p.rstrip("/") for p in excluded}
    source_files = tree_files(source, excluded_names)
    copy_files = tree_files(copy, excluded_names)
    differing = source_files ^ copy_files
    for name in source_files & copy_files:
        if not filecmp.cmp(source / name, copy / name, shallow=False):
            differing.add(name)
    return sorted(differing)


def published_paths() -> set[str]:
    """The plugin copies this repository actually publishes, from the
    marketplace files — the set PROVENANCE.json must cover. Claude's lists
    each source as a path; the ChatGPT/Codex one as {"source", "path"}."""
    claude = json.loads(
        (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    chatgpt = json.loads(
        (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
    )
    sources = [p["source"] for p in claude["plugins"]]
    sources += [p["source"]["path"] for p in chatgpt["plugins"]]
    return {s.removeprefix("./") for s in sources}


def check_publish(publish: dict) -> list[str]:
    problems = []
    copy = ROOT / publish["path"]
    if not copy.is_dir():
        return [f"{publish['path']}: recorded in PROVENANCE.json but not in the repository"]
    if not re.fullmatch(r"[0-9a-f]{40}", publish["commit"]):
        problems.append(f"{publish['path']}: commit must be a full 40-character SHA")
        return problems

    manifest = json.loads((copy / publish["manifest"]).read_text(encoding="utf-8"))
    if manifest["version"] != publish["plugin_version"]:
        problems.append(
            f"{publish['path']}: {publish['manifest']} says {manifest['version']}, "
            f"PROVENANCE.json says {publish['plugin_version']}"
        )

    # Not a TemporaryDirectory context: git can still be writing maintenance
    # files when the check finishes, and a cleanup failure must not fail it.
    tmp = tempfile.mkdtemp()
    try:
        source = clone_source(publish, Path(tmp))
        differing = differing_files(source, copy, publish["excluded"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    allowed = {d["file"] for d in publish.get("known_divergences", [])}
    for name in differing:
        if name not in allowed:
            problems.append(
                f"{publish['path']}/{name}: differs from "
                f"{publish['source_path']} at {publish['commit'][:9]} and is not "
                "a recorded divergence — re-run the sync, or record why it differs"
            )
    for name in sorted(allowed - set(differing)):
        print(
            f"note: {publish['path']}/{name} no longer differs from the source; "
            "its known_divergences entry can be removed"
        )
    return problems


def main() -> int:
    provenance = json.loads((ROOT / "PROVENANCE.json").read_text(encoding="utf-8"))
    problems = []

    recorded = {p["path"] for p in provenance["publishes"]}
    for path in sorted(published_paths() - recorded):
        problems.append(
            f"{path}: published by a marketplace but has no PROVENANCE.json entry"
        )

    for publish in provenance["publishes"]:
        problems.extend(check_publish(publish))

    prefix = "::error::" if os.environ.get("GITHUB_ACTIONS") else "error: "
    for problem in problems:
        print(f"{prefix}{problem}")
    if not problems:
        print(
            f"Sync fidelity: {len(provenance['publishes'])} publish(es) "
            "match their recorded sources."
        )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
