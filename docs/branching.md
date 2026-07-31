# Branching: trunk-based development

This repository practises [trunk-based development](https://trunkbaseddevelopment.com/).
There is exactly one long-lived branch, and the configuration below exists so that the
platform enforces that rather than merely suggesting it. A policy GitHub does not enforce
is a suggestion.

## The policy

### One trunk

`main` is the only long-lived branch. There is no `develop`, no `release/*`, no `hotfix/*`.
Releases are cut from the trunk as tags by
[Release Please](https://github.com/googleapis/release-please); see `CONTRIBUTING.md`.

If you believe this repository needs a second long-lived branch, open an issue and argue for
it. Do not create one — the catalog's generated artefacts (`skills/index.json`, `CATALOG.md`)
are byte-compared against the skills they were derived from, and two divergent lines of that
comparison is precisely the failure mode this avoids.

### Short-lived branches only

One task, one branch, one author, merged within two days. The working rule from the practice
is that a branch lasting longer than a couple of days has stopped being a short-lived branch
and become a feature branch, which is the thing trunk-based development exists to avoid
(<https://trunkbaseddevelopment.com/short-lived-feature-branches/>).

Branch naming is `<type>/<short-slug>`, where `<type>` is the
[Conventional Commit](https://www.conventionalcommits.org/) type of the intended change:

```text
feat/add-fhir-profiling-skill
fix/description-overlap-threshold
docs/clarify-tier-model
ci/pin-release-please-sha
```

### The trunk is always releasable

Every commit on `main` passes validation, and the generated index and catalog are always in
sync with the skills they describe. That is what `scripts/build_index.py --check` enforces in
CI: it regenerates the artefacts and fails if the working tree changes.

### Incomplete work is merged, not parked

A skill that is not finished is merged with `fgdh.status: "experimental"`, the matching body
banner, and `TODO(owner):` markers. Together those are this repository's equivalent of a
feature flag — the metadata field marks it for humans and for the catalog generator, and the
banner is the part that actually reaches an agent, because an agent never sees `fgdh.*`.

Never keep an unfinished skill on a branch instead. A branch is invisible to everyone but its
author; an experimental skill on the trunk is visible, reviewable, and mechanically tracked in
the health metrics (`docs/lifecycle.md`).

### Two documented exceptions

These branches are bot-maintained and legitimately outlive two days. Nobody should "clean them
up", and the stale-branch guard excludes them:

1. **`release-please--branches--main`** — Release Please maintains one continuously updated
   release pull request between releases. It is not a divergent feature branch; it is a
   proposal that is rewritten on every push to the trunk.
2. **Dependabot and Renovate branches** (`dependabot/**`, `renovate/**`) — bot-maintained and
   short-lived by construction; they disappear when their pull request is merged or closed.

## Repository settings

| Setting | Value | Why |
| --- | --- | --- |
| Default branch | `main` | The trunk. |
| Allow merge commits | **off** | Merge commits are incompatible with the linear-history rule. |
| Allow rebase merging | off | One incoming commit per pull request keeps the changelog readable. |
| Allow squash merging | **on** | Required: a linear-history rule needs squash or rebase merging enabled ([GitHub docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)). |
| Default squash commit title | pull request **title** (`PR_TITLE`) | Because merges are squash merges, the pull request title becomes the trunk commit message, and that is the Conventional Commit that Release Please parses. |
| Default squash commit message | pull request **body** (`PR_BODY`) | Keeps the reasoning with the commit rather than only in the web UI. |
| Automatically delete head branches | **on** | Mechanically prevents branch accumulation. |
| Allow auto-merge | on | Lets a passing pull request land without waiting for someone to click. |

The consequence worth internalizing: **the pull request title is the commit message.** An
invalid title silently breaks release automation, which is why CI lints it (below).

The merge-method restriction is enforced **twice**, on purpose: squash is the only method enabled
at the repository level, *and* the ruleset pins `allowed_merge_methods: ["squash"]`. Either alone
would do the job today; together they mean that re-enabling merge commits in repository settings
does not quietly re-open them on the trunk.

An audit found the ruleset had originally been created *without* that parameter, so GitHub had
defaulted it to all three methods. It was left out because the parameter could not be verified
against the documentation at the time, and this repository does not write configuration keys it has
not confirmed. GitHub's own API response later confirmed it, so it is now pinned in both places.

## The ruleset on `main`

The configuration is committed at [`.github/rulesets/main.json`](../.github/rulesets/main.json)
so it is reviewable in a pull request and restorable if someone changes it in the UI. This uses
a **ruleset** rather than a legacy branch protection rule: GitHub documents rulesets as the
successor, and rulesets can be layered, whereas with branch protection rules only one rule
applies at a time
(<https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches>).

Rules enabled:

- **Restrict deletions** (`deletion`) — the trunk cannot be deleted.
- **Block force pushes** (`non_fast_forward`) — history on the trunk is append-only.
- **Require a pull request before merging** (`pull_request`) — with conversation resolution
  required; see the review model below.
- **Require linear history** (`required_linear_history`) — no merge commits reach the trunk.
- **Require status checks to pass** (`required_status_checks`) — the `validate` and `pr-title`
  jobs of `.github/workflows/validate.yml`, each bound to `integration_id: 15368` (the GitHub
  Actions app) so a check of the same name reported by a different app cannot satisfy the rule.
  `strict_required_status_checks_policy` is on: a branch must be up to date with `main` before
  it can merge. That is what makes "integrate frequently" enforceable rather than aspirational,
  and it is the reason a branch left open for a week becomes work rather than a click.

  These were added *after* the workflow had reported once and its job names were known.
  Requiring a check that has never run blocks every merge, including the one that would create
  the check — so the ordering here is a constraint, not a preference. If you add a job and
  require it in the same change, you will lock the repository.

### Applying or restoring it

```bash
# Create the ruleset from the committed configuration.
gh api --method POST repos/forschungsgruppe-digital-health/agent-skills/rulesets \
  --input .github/rulesets/main.json

# Inspect what is actually configured (the authority is GitHub, not this file).
gh api repos/forschungsgruppe-digital-health/agent-skills/rulesets --jq '.[] | "\(.id) \(.name) \(.enforcement)"'
gh api repos/forschungsgruppe-digital-health/agent-skills/rulesets/<id>

# Update an existing ruleset in place after editing the file.
gh api --method PUT repos/forschungsgruppe-digital-health/agent-skills/rulesets/<id> \
  --input .github/rulesets/main.json
```

The same JSON can be imported through the web UI under **Settings → Rules → Rulesets → New
ruleset → Import a ruleset**.

The ruleset currently in force has id `20117709`. That id is not stable across a
delete-and-recreate, so resolve it with the listing command above rather than trusting this
line if the two disagree.

Keep the file and the live ruleset in sync by hand. Nothing verifies this automatically, so
treat a change made in the UI as incomplete until it is mirrored here.

## Review model — Option 2 is in force

§6.17 of the scaffold specification presents three review models and requires the choice to be
recorded rather than assumed. **This repository uses Option 2: zero required approvals,
enforced status checks and required conversation resolution.**

- `required_approving_review_count: 0`
- `required_review_thread_resolution: true`
- Status checks gate the merge (added with the validation workflow).

The reasoning, stated plainly so it can be revisited rather than rediscovered: requiring an
approving review is standard practice, but with a single maintainer it blocks every merge —
including the Release Please pull request — and the usual workaround of granting that
maintainer bypass permission removes exactly the protection the rule was meant to provide. The
mechanical gates still block the merge; the review becomes social rather than enforced.

**Revisit this when a second maintainer joins.** At that point Option 1 (require one approval)
becomes correct at no cost, and this section should be updated in the same pull request that
adds them to `CODEOWNERS`.

No actor holds bypass permission on the ruleset (`bypass_actors` is empty), including the
maintainer. That is deliberate: with zero required approvals there is nothing left to bypass
except the status checks, and bypassing those is never the right answer.

## Guard rails in CI

| Guard | Where | Blocking |
| --- | --- | --- |
| Pull request title lints as a Conventional Commit | `.github/workflows/validate.yml` | yes |
| Catalog validation (`build_index.py --check`, description overlap, spec conformance) | `.github/workflows/validate.yml` | yes |
| Stale branch report — branches with no commit in three days, excluding the bot exceptions | `.github/workflows/stale-branches.yml` | no |

The stale-branch workflow reports and does not act: it has no `contents: write` permission and
never deletes anything. Deleting someone's branch automatically is hostile, but letting branches
age silently is how trunk-based development quietly turns into GitFlow, so the middle path is a
single tracking issue updated in place.
