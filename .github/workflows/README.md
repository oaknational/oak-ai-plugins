# CI workflows

Every workflow here declares an explicit `permissions:` block, pins third-party
actions to a full commit SHA with the version in a trailing comment, and sets a
job timeout. Tools installed from npm are installed with lifecycle scripts
disabled, and the gitleaks archive is checked against its published checksum
before it runs.

| Workflow                           | Runs when                                           | What it does                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ---------------------------------- | --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`checks.yml`](checks.yml)         | Pull requests; pushes to `main`; manually           | `claude plugin validate --strict` on the Claude marketplace and plugin; checks the README, CHANGELOG and marketplace entries against the packages; checks the ChatGPT package's skills are exact copies of the Claude plugin's and the Microsoft package's are exact copies of the ChatGPT package's, and the rules the packages follow (`check_packages.py`); builds the ChatGPT upload ZIP; markdownlint and Prettier; gitleaks over the full history. |
| [`link-check.yml`](link-check.yml) | Pull requests; pushes to `main`; manually           | Checks every Markdown link that points inside the repository, anchors included, offline. The plugin's copied changelog is skipped.                                                                                                                                                                                                                                                                                                                       |
| [`pr-title.yml`](pr-title.yml)     | Pull requests opened, edited, reopened or pushed to | Checks the pull request title with commitlint. Pull requests are squash-merged, so the title becomes the commit on `main`.                                                                                                                                                                                                                                                                                                                               |
| [`release.yml`](release.yml)       | Manually, given a version; a dry run by default     | Checks the version against all three manifests and the latest CHANGELOG entry, runs the package checks, builds the ZIP OpenAI's plugin portal takes for the ChatGPT package (the manifest's name set to the live app's ID) and creates the release with the ZIP attached and the CHANGELOG entry as its notes. Releases are immutable, so the ZIP goes in as the release is created.                                                                     |
| [`drift.yml`](drift.yml)           | Mondays 07:30 UTC; manually                         | Validates the marketplace and the plugin with the latest Claude Code, so a spec change at Anthropic is noticed.                                                                                                                                                                                                                                                                                                                                          |

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
- `SonarCloud Code Analysis`

The ruleset also requires CodeQL results, an approving review from a code owner,
and every review thread resolved.
