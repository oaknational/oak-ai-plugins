# Oak AI plugins

[![Checks](https://github.com/oaknational/oak-ai-plugins/actions/workflows/checks.yml/badge.svg)](https://github.com/oaknational/oak-ai-plugins/actions/workflows/checks.yml)
![Status: experimental](https://img.shields.io/badge/status-experimental-orange)
[![Agent Skills](https://img.shields.io/badge/format-Agent%20Skills-blue)](https://agentskills.io/specification)
[![Licence](https://img.shields.io/badge/licence-MIT%20%2B%20Oak%20brand-informational)](LICENSE)

Oak National Academy's plugin for AI assistants: skills and workflows that ground an assistant in Oak's live curriculum data, Oak's curriculum principles and its accessibility guidance. Each host's package is published here in its own folder: the Claude plugin, and the ChatGPT package.

Each skill follows the [Agent Skills specification](https://agentskills.io/specification): a `SKILL.md` with YAML frontmatter, plus any supporting `references/` and `assets/`. The Claude plugin packages the skills with two slash-command workflows, the subagents behind them, and a connection to the Oak Curriculum MCP.

> [!IMPORTANT]
> **Experimental.** Output is AI-generated, not an official Oak resource, and has not been through Oak's editorial or quality-assurance process. Treat it as a starting point: check it against the current national curriculum and your own context, and have a teacher or subject expert sign it off before classroom or published use.

## Why these exist

Oak's approach to curriculum lives in its curriculum principles, in the units and lessons it publishes, and in the pupil misconceptions it has documented. These skills make that approach legible to an assistant, so a draft plan is checked against how Oak actually sequences the same units, a lesson anticipates the errors pupils really make, and a resource meets WCAG 2.2 AA, without a teacher having to explain Oak's approach each time.

## The skills

| Skill                                   | What it does                                                                                            | Use it when                                                                                                                                |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `find-misconceptions`                   | The pupil misconceptions Oak has documented for a topic, each with a teacher response.                  | Asked what pupils get wrong, what errors or misconceptions to anticipate, or for common mistakes for a topic or year group. Needs the MCP. |
| `audit-sequence`                        | Checks a draft plan's unit order and prior knowledge against how Oak sequences the same units.          | Asked to audit, sanity-check or sequence-check a long-term plan, scheme of work or unit order. Needs the MCP.                              |
| `oak-curriculum-principles`             | Oak's six curriculum principles, plus guiding principles for 15 subjects. Needs no connection.          | Planning a curriculum, scheme of work, unit or lesson, choosing the knowledge and vocabulary to teach, or auditing existing materials.     |
| `oak-curriculum-principles-mcp-enabled` | Checks a draft against Oak's live curriculum: threads, misconceptions, vocabulary and exemplar lessons. | Checking a curriculum, unit, lesson or resource against real Oak content, or finding an Oak exemplar. Needs the MCP.                       |
| `oak-accessibility`                     | Makes documents, decks, web pages, video and quizzes meet WCAG 2.2 AA, and audits existing ones.        | "Make this accessible", "is this WCAG 2.2 AA", or checking alt text, captions, contrast, structure or keyboard access.                     |

### How they fit together

- **Two workflows run as slash commands.** `find-misconceptions` and `audit-sequence` each hand the work to a subagent (`misconception-miner`, `sequencing-auditor`) and need the Oak Curriculum MCP.
- **The curriculum principles come in two layers.** `oak-curriculum-principles` holds the principles in full and works on its own. `oak-curriculum-principles-mcp-enabled` checks a draft against Oak's live data, and falls back to `oak-curriculum-principles` when the MCP isn't connected.
- **Accessibility applies to anything the plugin helps produce.** `oak-accessibility` is the WCAG 2.2 AA floor for documents, decks, web pages, video and quizzes.

## Repository layout

Each package lives at `<host>/<kind>/<package>/`, so another host, or another kind of package for the same host, gets a folder of its own. Apart from the repository's own files, the only things at the root are files a host requires there, such as its marketplace file.

```text
.claude-plugin/
  marketplace.json                  # Claude Code marketplace; points at claude/plugins/oak-national-academy
.agents/plugins/
  marketplace.json                  # ChatGPT and Codex marketplace; points at chatgpt/plugins/oak-national-academy
claude/
  plugins/
    oak-national-academy/           # the Claude plugin, copied from the ecosystem repository
      .claude-plugin/plugin.json    #   plugin manifest
      .mcp.json                     #   the Oak Curriculum MCP, installed with the plugin
      agents/                       #   the subagents the workflows hand work to
      skills/                       #   the three skills
      workflows/                    #   the two slash-command workflows
      assets/icon.png               #   the listing icon
      README.md                     #   the directory listing text
chatgpt/
  plugins/
    oak-national-academy/           # the ChatGPT package, copied from the ecosystem repository
      .codex-plugin/plugin.json     #   manifest, with the listing fields and review test cases
      .mcp.json                     #   the Oak Curriculum MCP
      skills/                       #   the five skills; each workflow merged into a skill
      assets/icon.png               #   the listing icon
      README.md                     #   how the package is derived from the Claude plugin
.github/
  pull_request_template.md
  workflows/
    checks.yml                      # plugin validation, sync fidelity, Markdown lint, Prettier, gitleaks
    link-check.yml                  # internal links and anchors
    pr-title.yml                    # the pull request title, which becomes the commit on main
    sync-plugin.yml                 # copies a version of both packages from the ecosystem and opens the publish PR
    chatgpt-zip.yml                 # builds the ChatGPT upload ZIP and attaches it to the release
    drift.yml                       # weekly: fails when the ecosystem is ahead of what's published, or the plugin no longer validates with the latest Claude Code
scripts/
  check_against_plugin.py           # checks this README, the CHANGELOG and the marketplace entries against the packages
  check_provenance.py               # checks each copy against the source commit in PROVENANCE.json
  sync_plugin.py                    # does the copy for sync-plugin.yml
  check_drift.py                    # the weekly version comparison for drift.yml
  build_chatgpt_zip.py              # builds the ChatGPT upload ZIP for chatgpt-zip.yml
PROVENANCE.json                     # where each published copy came from
.pre-commit-config.yaml             # the same checks, run locally before each commit
docs/
  public-release.md                 # how this repository was prepared for public release
CHANGELOG.md                        # what was published here, and when
CONTRIBUTING.md, SUPPORT.md, SECURITY.md, CODE_OF_CONDUCT.md
LICENSE, LICENCE-DATA.md, BRANDING.md, ATTRIBUTION.md
```

The `evals/` folders are left out of the copy. They are Oak's authoring tests and stay in the ecosystem repository.

## Using a skill

The skills follow the open [Agent Skills spec](https://agentskills.io/specification). Once the plugin is installed:

1. The assistant reads each skill's `description` to decide when it is relevant, and loads the body (and any `references/`) only when it is.
2. Trigger a skill by asking for the work its description covers. For example, "what do pupils get wrong about fractions?" surfaces `find-misconceptions`, "help me plan a Year 8 scheme of work" surfaces `oak-curriculum-principles`, and "make this worksheet accessible" surfaces `oak-accessibility`.
3. Or run a workflow directly as a slash command (see below).

Three skills need the **Oak Curriculum MCP** connected. See [The Oak Curriculum MCP](#the-oak-curriculum-mcp).

## Claude Code plugin

```text
# In Claude Code:
/plugin marketplace add oaknational/oak-ai-plugins
/plugin install oak-national-academy@oak-ai-plugins
```

Once installed you get:

| Command                                            | What it does                                                                                   |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `/find-misconceptions <topic> <year or key stage>` | The pupil misconceptions Oak has documented for a topic, each with a teacher response.         |
| `/audit-sequence <paste or reference the plan>`    | Checks a draft plan's unit order and prior knowledge against how Oak sequences the same units. |

Commands are namespaced when ambiguous, for example `/oak-national-academy:find-misconceptions`. The plugin bundles the Oak Curriculum MCP, so installing it connects live data in the same step: approve the `oak-national-academy` server when prompted and sign in on first use.

## ChatGPT package

The ChatGPT package carries the same five skills. ChatGPT has no workflows or subagents, so each of the two workflows and its subagent are merged into one skill of the same name. The package declares the Oak Curriculum MCP in its `.mcp.json`.

It is published to ChatGPT's plugin directory through OpenAI's plugin portal, which takes the package as a ZIP. The [ChatGPT upload ZIP workflow](.github/workflows/chatgpt-zip.yml) builds it for each release and attaches it to the release. The portal only accepts the live app's ID as the package name, so the ZIP's manifest carries the ID in place of `oak-national-academy`; every other file is the published copy unchanged. The demo video and the reviewer account are entered in the portal, not held here.

## The Oak Curriculum MCP

`find-misconceptions`, `audit-sequence` and `oak-curriculum-principles-mcp-enabled` use Oak's live curriculum data through the **Oak Curriculum MCP**, a [Model Context Protocol](https://modelcontextprotocol.io) server. The plugin connects it for you. To connect it without the plugin, add the server to your MCP client config:

```json
{
  "mcpServers": {
    "oak-national-academy": {
      "type": "http",
      "url": "https://mcp.thenational.academy/mcp"
    }
  }
}
```

- **Transport:** streamable HTTP. **Auth:** OAuth; sign in when prompted.
- **Claude Code:** `claude mcp add --transport http oak-national-academy https://mcp.thenational.academy/mcp`
- **Claude apps:** add it as a custom connector with the same URL.

The searches and lookups the assistant makes for you are sent to that server. See Oak's [privacy policy](https://www.thenational.academy/legal/privacy-policy).

The MCP sits on top of the [Oak Curriculum API](https://open-api.thenational.academy/docs), Oak's openly licensed curriculum data.

## Contributing

This repository publishes the plugins; it isn't where they are built. They are built in [oak-open-curriculum-ecosystem](https://github.com/oaknational/oak-open-curriculum-ecosystem), under `claude/plugins/oak-national-academy` and `chatgpt/plugins/oak-national-academy`, next to the Oak Curriculum MCP server they connect to. That repository is too large for Claude's plugin directory to read, so each release of the plugins is copied here. Each copy is made by the [sync workflow](.github/workflows/sync-plugin.yml), recorded in [PROVENANCE.json](PROVENANCE.json), and proven against its source by the Sync fidelity check on every pull request.

- **Feedback, bugs and curriculum corrections:** use the [AI plugin feedback form](https://survey.hsforms.com/2vy6BnIvzTASqx1DbH8CaJAbvumd). GitHub issues are turned off. See [SUPPORT.md](SUPPORT.md) for scope and response times.
- **Pull requests** are only accepted from Oak engineers. See [CONTRIBUTING.md](CONTRIBUTING.md). Pull requests here only carry copies from the ecosystem repository and changes to this repository's own files. They are squash-merged, so each title is written as a Conventional Commit with the ticket at the end when there is one, and becomes the commit on `main`.
- **Security vulnerabilities:** see [SECURITY.md](SECURITY.md), never the feedback form.
- Everyone is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

How the repository was prepared for public release, and why, is recorded in [docs/public-release.md](docs/public-release.md).

To run CI's checks locally before each commit, install [pre-commit](https://pre-commit.com) and the hooks once. The plugin validation hooks also need Claude Code installed.

```bash
pipx install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

## Licence

Different parts of this repository are licensed differently.

- **Code and repository structure** are released under the [MIT Licence](LICENSE).
- **Oak trademarks, logos and brand assets**, including the plugin's icon, are not MIT-licensed. See [BRANDING.md](BRANDING.md) and Oak's [brand guidelines](https://support.thenational.academy/using-the-oak-brand).
- **Curriculum principles** content is © Oak National Academy. See each skill's `references/sources.md` for sources and attribution.
- **Oak curriculum data**, reached through the Oak Curriculum MCP, is published under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) except where otherwise stated, and requires attribution to Oak National Academy. Some content may carry third-party rights that the OGL doesn't cover. See [LICENCE-DATA.md](LICENCE-DATA.md).

Each skill also states its own terms in its `SKILL.md` frontmatter. Where these differ, the more restrictive terms apply. Credits are in [ATTRIBUTION.md](ATTRIBUTION.md).
