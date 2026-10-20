# CI workflows

Every workflow here declares an explicit `permissions:` block, pins third-party
actions to a full commit SHA with the version in a trailing comment, and sets a
job timeout. Tools installed from npm are installed with lifecycle scripts
disabled, and the gitleaks archive is checked against its published checksum
before it runs.

| Workflow                             | Runs when                                           | What it does                                                                                                                                                                                                                                                                                                                                    |
| ------------------------------------ | --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`checks.yml`](checks.yml)           | Pull requests; pushes to `main`; manually           | `claude plugin validate --strict` on the Claude marketplace and plugin; checks the README, CHANGELOG and marketplace entries against the packages; builds the ChatGPT upload ZIP; **Sync fidelity**, which checks each copy against the source commit recorded in `PROVENANCE.json`; markdownlint and Prettier; gitleaks over the full history. |
| [`link-check.yml`](link-check.yml)   | Pull requests; pushes to `main`; manually           | Checks every Markdown link that points inside the repository, anchors included, offline. The plugin's copied changelog is skipped.                                                                                                                                                                                                              |
| [`pr-title.yml`](pr-title.yml)       | Pull requests opened, edited, reopened or pushed to | Checks the pull request title with commitlint. Pull requests are squash-merged, so the title becomes the commit on `main`.                                                                                                                                                                                                                      |
| [`sync-plugin.yml`](sync-plugin.yml) | Manually, given an ecosystem ref and release        | Copies the Claude plugin and the ChatGPT package from oak-open-curriculum-ecosystem at that ref, updates `PROVENANCE.json` and `CHANGELOG.md`, and opens the publish pull request. It can't open pull requests yet: Actions isn't allowed to here, and the Oak Semantic Release Bot's token is still to be set up.                              |
| [`chatgpt-zip.yml`](chatgpt-zip.yml) | Releases published; manually, given a release tag   | Builds the ZIP OpenAI's plugin portal takes for the ChatGPT package, with the manifest's name set to the live app's ID, and attaches it to the release.                                                                                                                                                                                         |
| [`drift.yml`](drift.yml)             | Mondays 07:30 UTC; manually                         | Fails when the ecosystem's version of either package is ahead of the one published here, so a release that hasn't been synced is noticed. Also validates the marketplace and the plugin with the latest Claude Code, so a spec change at Anthropic is noticed too.                                                                              |

**SonarCloud** analyses every pull request (automatic analysis, no workflow
file). GitHub also runs **CodeQL** (default setup, not a workflow file here) on the
workflow files and the scripts, and **Dependabot** checks the pinned
actions weekly.

The same lint, format, secret and plugin checks run locally through the
pre-commit hooks in [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml).

## Required status checks

The branch ruleset on `main` requires these checks by name. **If you rename a
job, update the ruleset in the same change.** Otherwise the ruleset keeps
waiting for the old name, which never reports again, and every pull request
stays blocked until the ruleset is updated:

- `Plugin validation`
- `Markdown lint + Prettier`
- `Secret scan (gitleaks)`
- `Link check`
- `PR title`
- `Sync fidelity`
- `SonarCloud Code Analysis`

The ruleset also requires CodeQL results, an approving review from a code owner,
and every review thread resolved.
