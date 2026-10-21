# Oak National Academy — ChatGPT and Codex package

This directory is the ChatGPT/Codex packaging of the Claude plugin in `../../../claude/plugins/oak-national-academy/`.
It is a **checked-in copy**, not a build output. The Claude plugin is the source: a correction to
a shared skill lands there first and is re-copied here, never the other way round. Both carry the
same version; the changes per version are in `../../../claude/plugins/oak-national-academy/CHANGELOG.md`.

## Why a separate package

ChatGPT and Codex read a plugin's `skills/` directory and nothing else (observed 2026-09-07).
The Claude plugin keeps its two capabilities as agents in `agents/`, each reached through a
workflow that passes the user's input as `$ARGUMENTS`; ChatGPT has neither agents nor
workflows. So here:

- every skill present in both plugins is a byte-identical copy of the Claude one (`evals/`
  left out of the copy, and refused if it appears here); `scripts/check_skill_copies.py` (run in
  CI and pre-commit) discovers that set from the two trees rather than keeping a list, fails when a Claude skill has no copy
  here, and fails when a skill here has no Claude source unless it derives from a Claude
  workflow of the same name;
- `audit-sequence` and `find-misconceptions` each merge a Claude workflow and its agent into
  one self-contained skill. The agent's body is carried byte-identical from its first heading
  onward. The edits: the workflow's `$ARGUMENTS` line and its restatement of the method become
  one opening paragraph ("the plan or topic the user has shared; ask if missing"); the
  "Delegate to" line and the Claude-only frontmatter (`argument-hint`, `skills`, `model`) are
  dropped; the `skills:` dependency becomes one sentence appended to the agent's opening
  paragraph; the description is the Claude workflow's, word for word (both carry a do-not-use
  boundary naming the sibling skills); and `license`, `compatibility` and `metadata` are added
  to match the shared skills;
- `.mcp.json` declares the Oak MCP server, `https://mcp.thenational.academy/mcp`. It was left
  out until October because bundling a server badged a locally imported plugin "desktop only"
  (observed in the desktop app, 2026-09-07). OpenAI's portal now refuses skills-only packages
  (observed 2026-10-18), so the server is declared; whether a local import is still badged is
  unconfirmed (MCP-765);
- `interface.capabilities` is `[]`, the value the OpenAI sideload accepted on 2026-09-07.

The last two, the declared server and `capabilities: []`, and the agreement of the two
manifests are recomputed by `scripts/check_packages.py`: the manifest is checked against a
strict schema at every level, the package root is held to
exactly `.codex-plugin`, `.mcp.json`, `README.md`, `assets` and `skills`, so a companion file
cannot appear unnoticed, the review block holds exactly five positive and three negative test
cases and nothing else, and the root marketplace file must list exactly this package under the
manifest's name.

`check_skill_copies.py` fails the build when a shared copy drifts from its Claude source, and
`check_packages.py` fails it when a merged skill and its Claude agent stop matching from the
first heading onward.
The durable fix is a generator (MCP-342); until then the copies are honest because they are
checked.

Routing check (2026-09-09): the five descriptions were tested as an installed skill list
against eighteen teacher requests with known right answers, in twelve independent runs (Opus,
judging from the descriptions alone; current and proposed wording; the ChatGPT list and the
Claude list). Every run routed every request correctly. The descriptions therefore carry the
do-not-use boundaries and nothing more, and the two Claude workflow descriptions were made
identical to the merged skills' for consistency between the plugins, not as a routing fix.

Routing check (2026-09-16): oak-skills' own trigger-eval method — one fresh Opus judge per
query, shown the descriptions only — over the 27 upstream queries whose expected lead is a skill
shipped here, against both packages, four runs across three wordings. The two merged skills took
the narrow requests in every run, with or without a boundary sentence on
`oak-curriculum-principles-mcp-enabled`, and that sentence pulled general "review my unit"
requests onto the MCP-requiring skill. So the two merged skills carry do-not-use boundaries, and
the MCP-enabled skill's description is oak-skills' approved text, unchanged.

## Sideload for testing (desktop app)

These steps predate the bundled `.mcp.json`. Steps observed in the Codex desktop app, 2026-09-07, and re-verified in the ChatGPT desktop app
on 2026-09-09 with the package built from `00fa027eb` (marketplace added by path; all five skills
listed with their current descriptions; no desktop-only badge; `$find-misconceptions` resolved a
unit slug, called the misconception graph and quizzes, and attributed under OGL v3.0;
`$audit-sequence` with no plan asked for one).

1. `codex plugin marketplace add <repo root>` — the root `.agents/plugins/marketplace.json`
   lists this package.
2. Add the Oak MCP server in Codex: Plugins → Add → Add MCP server, Streamable HTTP,
   `https://mcp.thenational.academy/mcp`; sign in when prompted.
3. Quit the app from the system tray, reopen, Plugins → Personal → install.
4. Invoke a skill with `$` in the desktop app: `$find-misconceptions photosynthesis Year 9`.

Tool names arrived prefixed and with hyphens as underscores (`mcp__codex_apps__oak_<tool>`
via the connector, `mcp__<id>__<tool>` via a direct entry; observed 2026-09-07), so
the merged skills say to match by suffix treating `-` and `_` as the same.

## Submitting through the OpenAI plugin portal

The portal takes the whole package as one ZIP, with the manifest at the ZIP's root, and reads
the listing fields, skills, MCP configuration and review test cases from it (observed
2026-10-18). It replaced the portal's form steps. The portal's own review form takes what this
repository must not hold, because it is public: the demo video link and the reviewer test
account.

The portal also requires the package `name` to be the live app's ID,
`app-6aa0141317a08191a8e8f74fbabeeff1`, and rejects any other name; an update's version must
be above the published one (observed 2026-10-19). The name here stays `oak-national-academy`,
the name Codex and workspace installs show; the Release workflow sets the ID when it builds
the upload ZIP (MCP-767, MCP-773).

## Publishing

The package is submitted to OpenAI's Plugin Directory through the portal (MCP-107), from the
ZIP the Release workflow attaches to each release of oaknational/oak-ai-plugins.
