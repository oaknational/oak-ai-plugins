# Public release record

This document records the decisions taken when preparing `oaknational/oak-ai-plugins`
for public release against Oak's checklist for releasing public GitHub
repositories. It follows the record kept for `oaknational/oak-curriculum-api`
(`docs/public-release.md` there). It exists so a reviewer can tell "not relevant"
apart from "not done".

Last reviewed: **30 September 2026**.

## What this repository is

A published copy of Oak's AI plugins. The plugins are written and tested in
[oak-open-curriculum-ecosystem](https://github.com/oaknational/oak-open-curriculum-ecosystem)
and each release is copied here, so that Claude's plugin directory and Claude Code
users can read and install them. It holds Markdown, JSON, one image per plugin, CI
configuration and one small check script. It has no application code, no
dependencies and no build.

## Scope and triage

| Conditional item                                   | Applies | Decision                                                                                                                                                                                                                                              |
| -------------------------------------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CITATION.cff` and a DOI                           | No      | Not a research output, dataset or ontology.                                                                                                                                                                                                           |
| `.env.example`                                     | No      | Nothing reads environment variables.                                                                                                                                                                                                                  |
| Data provenance and licensing review               | Yes     | No datasets are committed. The skills set out Oak's own curriculum principles and WCAG-based guidance; curriculum data is fetched at runtime. See [Licensing](#licensing).                                                                            |
| Accessibility statement                            | No      | This repository publishes no website or interface. Accessibility guidance is itself one of the plugin's skills.                                                                                                                                       |
| Release artefacts and checksums                    | Yes     | Each release, from v1.2.0, carries the ChatGPT upload ZIP, built from the release commit by the Release workflow, which logs its sha256. Releases are immutable.                                                                                      |
| Published artefact validation and build provenance | Yes     | What is published is the plugin folder itself. CI validates it with `claude plugin validate --strict` on every pull request and push to `main`, and the Sync fidelity check proves each copy matches the source commit recorded in `PROVENANCE.json`. |
| SBOM archived per release                          | No      | No executables, packages or images are distributed.                                                                                                                                                                                                   |
| Named maintainer and stated support expectation    | Yes     | @oaknational/devs, first response within 5 working days. See [SUPPORT.md](../SUPPORT.md).                                                                                                                                                             |

## Secret scan

A full-history scan of every branch was run before publication:

```sh
gitleaks git --log-opts="--all" --redact .
```

**30 September 2026** — 18 commits scanned, **no findings**.

No environment, OS, credential or key files are tracked. **30 September 2026** —
no matches for:

```sh
git ls-files | grep -iE '(^|/)\.env($|\.)|\.DS_Store$|Thumbs\.db$|desktop\.ini$|__MACOSX/|\.pem$|\.key$|\.p12$|\.pfx$|\.jks$|\.keystore$|(^|/)id_(rsa|dsa|ecdsa|ed25519)(\.pub)?$|\.npmrc$|\.netrc$'
```

This checks file names only. The secret scan above and CI's gitleaks job check
file contents.

CI also runs gitleaks over the full history on every pull request and push to
`main`, and GitHub secret scanning with push protection is on.

## Licensing

The code and repository structure are licensed under the **MIT License**
([LICENSE](../LICENSE)). GitHub reports it as `MIT`:

```sh
gh api repos/oaknational/oak-ai-plugins --jq .license.spdx_id
```

Unlike the API repository, a single licence does not cover everything here:

- **Curriculum content** the plugins return comes from the Oak Open Curriculum
  API through the Oak Curriculum MCP, under the Open Government Licence v3.0
  except where otherwise stated. It is fetched at runtime, not committed. See
  [LICENCE-DATA.md](../LICENCE-DATA.md).
- **Oak's curriculum principles** in the skills are © Oak National Academy. Each
  skill states its own terms in its frontmatter.
- **Oak branding**, including the plugin's icon, is not MIT-licensed. See
  [BRANDING.md](../BRANDING.md).

Credits are in [ATTRIBUTION.md](../ATTRIBUTION.md), and the README states the
licence position so a reader never relies on the sidebar.

### Attribution

When using this work, please credit "Oak National Academy".

### Dependency licences

Not applicable. The repository has no package manifest and distributes no
dependencies. CI installs pinned tools to run its checks (Claude Code,
markdownlint-cli2, Prettier, gitleaks, commitlint, lychee); they run on the CI
runner and are never distributed.

## Data protection

The plugins send the searches and lookups an assistant makes to the Oak
Curriculum MCP at `https://mcp.thenational.academy/mcp`. This is stated in the
plugin's README, with a link to Oak's
[privacy policy](https://www.thenational.academy/legal/privacy-policy).

The correction and takedown route is the
[AI plugin feedback form](https://survey.hsforms.com/2vy6BnIvzTASqx1DbH8CaJAbvumd),
documented in [SUPPORT.md](../SUPPORT.md).

## Static analysis

CodeQL default setup analyses the workflow files (`actions`) and the check
script (`python`) with the extended query suite, on every push to `main` and on
pull requests. `main` requires CodeQL results before merging.

**30 September 2026** — zero findings in either language, zero open alerts.

## Repository settings applied

Verified through the API on **30 September 2026**:

| Setting                                         | Value                          | Why                                                                                                                                    |
| ----------------------------------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `default_workflow_permissions`                  | `read`                         | Every workflow declares the permissions its jobs need.                                                                                 |
| `can_approve_pull_request_reviews`              | `false`                        | Actions must not be able to approve pull requests.                                                                                     |
| `allowed_actions`                               | `all` — **pending** `selected` | To be GitHub-owned and verified creators plus `lycheeverse/lychee-action@*`. The API returned 502 on every attempt; set in the web UI. |
| `sha_pinning_required`                          | `true`                         | Tags are mutable. Every action is pinned to a full commit SHA with the version in a trailing comment.                                  |
| `secret_scanning`                               | `enabled`                      | Detection.                                                                                                                             |
| `secret_scanning_push_protection`               | `enabled`                      | Stops a secret being committed, rather than reporting it afterwards.                                                                   |
| `secret_scanning_non_provider_patterns`         | `enabled`                      | Catches generic credentials, not just recognised provider formats.                                                                     |
| `secret_scanning_validity_checks`               | `enabled`                      | Tells us whether a detected secret is still live.                                                                                      |
| `private_vulnerability_reporting`               | `enabled`                      | Researchers can report privately. See [SECURITY.md](../SECURITY.md).                                                                   |
| Dependabot alerts and security updates          | `enabled`                      | Dependabot also keeps the pinned actions current, weekly.                                                                              |
| CodeQL default setup                            | `actions`, `python`            | See [Static analysis](#static-analysis).                                                                                               |
| `has_issues`                                    | `false`                        | Feedback goes through the AI plugin feedback form. Stated in README, CONTRIBUTING and SUPPORT so readers are not left guessing.        |
| `has_wiki` / `has_projects` / `has_discussions` | `false`                        | Not used; the docs live in the repository.                                                                                             |
| `delete_branch_on_merge`                        | `true`                         | Tidiness.                                                                                                                              |
| Merge methods                                   | squash only                    | Each pull request becomes one commit on `main`, titled by the pull request title.                                                      |

Rulesets:

- **Protect default branch** (`main`): pull requests only, with one approval and
  a code-owner review; review threads resolved; the required checks listed in
  [.github/workflows/README.md](../.github/workflows/README.md); CodeQL results;
  Copilot review when a pull request opens; no deletion or force-push.
- **Protect release tags** (`v*`): no deletion or moving.

Confirm at any time with:

```sh
gh api repos/oaknational/oak-ai-plugins --jq .security_and_analysis
gh api repos/oaknational/oak-ai-plugins/actions/permissions
gh api repos/oaknational/oak-ai-plugins/actions/permissions/workflow
gh api repos/oaknational/oak-ai-plugins/rules/branches/main
```
