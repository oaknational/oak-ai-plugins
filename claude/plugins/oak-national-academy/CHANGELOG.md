# Changelog

Versions are the plugin manifest version. The Claude Code plugin and the
ChatGPT/Codex package share one version. Each entry is dated when it is
written. Up to 1.1.0 the plugins were built in oak-open-curriculum-ecosystem;
from 1.1.1 they are built in oaknational/oak-ai-plugins.

## 1.1.1 — 2026-10-21

- Both manifests' `license` field links to this repository's LICENSE,
  LICENCE-DATA.md and BRANDING.md, in place of oak-open-curriculum-ecosystem's.
- The ChatGPT/Codex package README names the checks that hold it here,
  `scripts/check_skill_copies.py` and `scripts/check_packages.py`, in place of
  the ecosystem's.
- The ChatGPT/Codex package's release notes: "Maintenance update. No changes to
  the skills or what the plugin does."
- No changes to the skills.

## 1.1.0 — 2026-10-19

- The ChatGPT/Codex package declares the Oak MCP server in `.mcp.json`. OpenAI's
  plugin portal no longer accepts skills-only packages.
- The ChatGPT/Codex package carries the fields OpenAI's ZIP upload checks: the
  subtitle, long description, category, support link and default prompts from
  the approved ChatGPT listing, the Oak icon, the review test cases and release
  notes.
- The ChatGPT/Codex package names oaknational/oak-ai-plugins as its repository.
- Version 1.1.0 is above the approved ChatGPT listing's 1.0.0, which the portal
  requires of an update. The Claude plugin changes only its version.

## 0.1.6 — 2026-10-01

- The Claude plugin README says who the plugin is for and the DfE standards it
  is designed in line with, warns against entering pupil data, and links
  Anthropic's privacy policy alongside Oak's.

## 0.1.5 — 2026-09-30

- The Claude plugin gains support, documentation and terms of service links
  for its directory listing.
- New listing text: a one-line description, and a README that describes Oak
  and what the plugin draws on.
- The Claude plugin names oaknational/oak-ai-plugins as its repository: the
  public copy the directory lists, rather than oak-open-curriculum-ecosystem.

## 0.1.4 — 2026-09-30 (repo release v1.185.4)

- The Claude plugin and the ChatGPT/Codex package are renamed from
  `oak-open-curriculum` to `oak-national-academy`, to match the display name.
  The full form of a command is now `/oak-national-academy:<skill>`. Claude
  Code moves existing installs to the new name.
- The MCP server is now named `oak-national-academy`. It is the same server at
  the same address, but Claude identifies it by the plugin and server names, so
  it asks you to sign in again and to approve each tool again the first time it
  is used.

## 0.1.3 — 2026-09-28 (repo release v1.185.3)

- Claude plugin: adds an icon, a privacy policy link and a README, which the
  Claude plugin directory asks for.
- oak-curriculum-principles: the hexagon diagram's path is a Markdown link,
  not code, so the directory does not hold the plugin for a reviewer.

## 0.1.2 — 2026-09-17 (repo release v1.182.0)

- Adds the ChatGPT/Codex package: the same skills, with the two workflows
  packaged as skills.
- oak-accessibility: transcripts recommended, not required, at WCAG AA.
- MCP-enabled skill and agents: tool names may arrive with underscores in
  place of hyphens.
- oak-curriculum-principles: three passages matched to oak-skills' approved
  wording.
- find-misconceptions: keeps the order the tool returns.

## 0.1.1 — 2026-09-07

- audit-sequence: checks same-year order now the tool serves it; reads
  prior-knowledge statements as what a unit assumes, not a dependency graph.

## 0.1.0 — 2026-08-07

- First release: three skills, two workflows, two agents, and the Oak
  Curriculum MCP binding.
