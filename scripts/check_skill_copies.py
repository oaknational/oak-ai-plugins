"""Check the ChatGPT and Microsoft packages' skills are exact copies.

ChatGPT and Microsoft read only a package's own `skills/` folder, so both
packages carry their skills as checked-in copies. A copy is honest only while
it is checked, so this script recomputes the comparison on every run and
names each file that differs:

- every skill under the Claude plugin's `skills/` must have a copy under the
  ChatGPT package's `skills/`, byte for byte, file for file;
- a skill only the ChatGPT package has must derive from a Claude workflow of
  the same name (the merged skills; scripts/check_packages.py checks the
  derivation itself), otherwise it is a stale copy of a deleted skill;
- the Microsoft package's `skills/` must hold exactly the ChatGPT package's
  skills, merged ones included, byte for byte, file for file;
- nothing that must not ship reaches a copy: no `evals/` folder at any depth,
  and no symlink anywhere. Symlinks are reported, never followed.

A skill is a directory holding a regular `SKILL.md`. Which skills are shared
is discovered from the trees each run, never listed, so a new skill is
covered the moment it exists. An `evals/` folder is authoring tooling: it
is skipped in the Claude plugin's skills and is a finding in a copy. A
folder that cannot be read stops the check, so a partial scan never passes.

Ported from the oak-open-curriculum-ecosystem validator
validate-plugin-skill-copies. Exit 0 when the copies match; 1 when there are
findings; 2 when the check cannot run honestly (a root is missing or a
symlink, no skill is shared, or nothing was compared), so an empty or broken
scan is never a pass. Run by CI and by the pre-commit hook:

  python3 scripts/check_skill_copies.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = "claude/plugins/oak-national-academy/skills"
COPY = "chatgpt/plugins/oak-national-academy/skills"
MICROSOFT = "microsoft/plugins/oak-national-academy/skills"
WORKFLOWS = "claude/plugins/oak-national-academy/workflows"
NOT_SHIPPED = {"evals"}
MANIFEST = "SKILL.md"


def refuse(message: str) -> None:
    prefix = "::error::" if os.environ.get("GITHUB_ACTIONS") else "error: "
    print(f"{prefix}check_skill_copies: {message} — refusing to report clean.")
    sys.exit(2)


def require_real_directory(relative: str) -> Path:
    path = ROOT / relative
    if path.is_symlink() or not path.is_dir():
        refuse(f"{relative} is missing or is not a real directory")
    return path


def is_skill(path: Path) -> bool:
    manifest = path / MANIFEST
    return path.is_dir() and not path.is_symlink() and manifest.is_file() and not manifest.is_symlink()


def list_root(root: Path) -> tuple[list[str], list[str], list[str]]:
    """Skills, directories that are not skills, and symlinked entries directly under a root."""
    skills, invalid, symlinks = [], [], []
    for entry in sorted(root.iterdir(), key=lambda e: e.name):
        if entry.is_symlink():
            symlinks.append(entry.name)
        elif entry.is_dir():
            (skills if is_skill(entry) else invalid).append(entry.name)
    return skills, invalid, symlinks


def raise_error(error: OSError) -> None:
    raise error


def read_tree(skill_dir: Path, skip: set[str]) -> dict[str, bytes | None]:
    """Every entry under a skill, keyed by relative path: file bytes, or None for a symlink."""
    tree: dict[str, bytes | None] = {}
    for dirpath, dirnames, filenames in os.walk(skill_dir, onerror=raise_error):
        base = Path(dirpath)
        relative_dir = base.relative_to(skill_dir)
        kept = []
        for name in sorted(dirnames):
            path = base / name
            if path.is_symlink():
                tree[(relative_dir / name).as_posix()] = None
            elif name not in skip:
                kept.append(name)
        dirnames[:] = kept
        for name in sorted(filenames):
            path = base / name
            tree[(relative_dir / name).as_posix()] = None if path.is_symlink() else path.read_bytes()
    return tree


def not_shipped(relative: str) -> bool:
    """Whether any folder on the path is one that must not ship."""
    return any(part in NOT_SHIPPED for part in relative.split("/")[:-1])


def compare_skill(
    skill: str, source: Path, copy: Path,
    source_label: str = SOURCE, copy_label: str = COPY, skip: frozenset[str] = frozenset(NOT_SHIPPED),
) -> tuple[list[str], int]:
    """Compare one skill's files between a source and its copy; `skip` names source folders not shipped."""
    source_tree = read_tree(source / skill, set(skip))
    copy_tree = read_tree(copy / skill, set())
    findings, compared = [], 0
    for relative in sorted(set(source_tree) | set(copy_tree)):
        here, there = source_tree.get(relative, b""), copy_tree.get(relative, b"")
        if relative in copy_tree and not_shipped(relative):
            findings.append(f"not shipped: {copy_label}/{skill}/{relative}")
        elif not_shipped(relative):
            # Must not ship, so its absence from the copy is right; the source's
            # own check reports it if the source is itself a copy.
            continue
        elif here is None or there is None:
            side = copy_label if there is None else source_label
            findings.append(f"symlink: {side}/{skill}/{relative}")
        elif relative not in copy_tree:
            findings.append(f"missing in copy: {copy_label}/{skill}/{relative}")
        elif relative not in source_tree:
            findings.append(f"not in source: {copy_label}/{skill}/{relative}")
        else:
            compared += 1
            if here != there:
                findings.append(f"differs: {copy_label}/{skill}/{relative} from {source_label}/{skill}/{relative}")
    return findings, compared


def microsoft_findings(copy: Path, copy_skills: list[str]) -> tuple[list[str], int]:
    """The Microsoft package must hold exactly the ChatGPT package's skills, file for file."""
    microsoft = require_real_directory(MICROSOFT)
    skills, invalid, links = list_root(microsoft)
    findings = [f"symlink: {MICROSOFT}/{name}" for name in links]
    findings += [f"not a skill (no {MANIFEST}): {MICROSOFT}/{name}" for name in invalid]
    findings += [f"missing in copy: {MICROSOFT}/{s}" for s in copy_skills if s not in skills]
    findings += [f"not in the ChatGPT package: {MICROSOFT}/{s}" for s in skills if s not in copy_skills]
    shared = [s for s in copy_skills if s in skills]
    if not shared:
        refuse(f"no skill is present under both {COPY} and {MICROSOFT}")
    compared = 0
    for skill in shared:
        # The ChatGPT copy ships everything it holds, so nothing in it is skipped.
        found, count = compare_skill(skill, copy, microsoft, COPY, MICROSOFT, frozenset())
        findings += found
        compared += count
    return findings, compared


def copy_only_findings(skill: str, copy: Path) -> list[str]:
    """A merged skill has no source to compare, but it ships: walk it for symlinks and authoring content."""
    findings = []
    for relative, content in sorted(read_tree(copy / skill, set()).items()):
        if content is None:
            findings.append(f"symlink: {COPY}/{skill}/{relative}")
        elif not_shipped(relative):
            findings.append(f"not shipped: {COPY}/{skill}/{relative}")
    return findings


def main() -> int:
    source = require_real_directory(SOURCE)
    copy = require_real_directory(COPY)
    workflows = require_real_directory(WORKFLOWS)

    source_skills, source_invalid, source_links = list_root(source)
    copy_skills, copy_invalid, copy_links = list_root(copy)
    shared = [s for s in source_skills if s in copy_skills]
    if not shared:
        refuse(f"no skill is present under both {SOURCE} and {COPY}")

    findings = [f"symlink: {name}" for name in sorted(set(source_links) | set(copy_links))]
    findings += [f"not a skill (no {MANIFEST}): {SOURCE}/{name}" for name in source_invalid]
    findings += [
        f"missing in copy: {COPY}/{name}/{MANIFEST}" if name in source_skills
        else f"not shipped (not a skill): {COPY}/{name}"
        for name in copy_invalid
    ]
    findings += [f"missing in copy: {COPY}/{s}" for s in source_skills if s not in copy_skills]

    compared = 0
    for skill in shared:
        found, count = compare_skill(skill, source, copy)
        findings += found
        compared += count
    for skill in (s for s in copy_skills if s not in source_skills):
        if is_skill(workflows / skill):
            findings += copy_only_findings(skill, copy)
        elif skill not in source_invalid:
            findings.append(
                f"stale copy: {COPY}/{skill} has no Claude skill or workflow of that name"
            )
    microsoft_found, microsoft_compared = microsoft_findings(copy, copy_skills)
    findings += microsoft_found
    prefix = "::error::" if os.environ.get("GITHUB_ACTIONS") else "error: "
    for finding in findings:
        print(f"{prefix}{finding}")
    if findings:
        print(
            f"Re-copy each named file from {SOURCE} (into {COPY}) or from {COPY} (into {MICROSOFT}), "
            "or remove what must not ship."
        )
        return 1
    if compared == 0 or microsoft_compared == 0:
        refuse("compared no files")
    merged = [s for s in copy_skills if s not in source_skills]
    print(
        f"Skill copies: {len(shared)} shared skill(s), {compared} file(s) identical; "
        f"merged from workflows: {', '.join(merged) or 'none'}; "
        f"Microsoft package: {len(copy_skills)} skill(s), {microsoft_compared} file(s) identical to the ChatGPT package."
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OSError as error:
        # A broken scan must never read as an empty one, or as drift.
        refuse(f"could not read the skill trees ({error})")
