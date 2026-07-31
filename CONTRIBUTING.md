# Contributing

This is the checklist. The reasoning behind it is in
[docs/authoring-skills.md](docs/authoring-skills.md), the governance in
[docs/lifecycle.md](docs/lifecycle.md), and the branching model in
[docs/branching.md](docs/branching.md).

## Adding a skill

1. **Open a proposal issue** from the `new-skill` template. It is a design review, not a
   formality: rejecting at this stage costs one issue comment, rejecting after authoring costs a
   person-day. It records the procedure, the trigger situations in your own words, the proposed
   tier, the intended owner, and the neighbouring skills it might collide with.
2. **Branch.** `<type>/<short-slug>`, one task, merged within two days.
3. **Copy** `templates/SKILL.md.template` to `skills/<your-skill-name>/`. The directory name and
   the `name:` field must be identical.
4. **Fill in the four mandatory sections** — `## Preconditions`, `## Procedure`,
   `## Verification`, `## Scope and delimitation` — and replace every `<angle-bracket>`
   placeholder.
5. **Set the metadata** (below) with `fgdh.status: "experimental"` and the matching body banner.
6. **Add trigger prompts** at `references/triggers.md`: three to five that should activate the
   skill, two that should activate a neighbour instead.
7. **Add the `CODEOWNERS` line** for the skill directory, matching `fgdh.owner`.
8. **Regenerate and commit** the artefacts:

   ```bash
   python scripts/build_index.py
   python scripts/build_index.py --check
   python scripts/check_descriptions.py
   agentskills validate skills/<your-skill-name>
   ```

9. **Open a pull request.** The template carries the review checklist. Paste the command output —
   "CI is green" is a different claim from "I ran it".

## The frontmatter contract

### Fields defined by the open standard

| Field | Required | Constraint |
| --- | --- | --- |
| `name` | yes | 1–64 chars; lowercase `a-z`, `0-9`, hyphens; no leading/trailing hyphen; no consecutive hyphens; **must equal the parent directory name** |
| `description` | yes | 1–1024 chars; states what the skill does **and** when to use it |
| `license` | no | a license name or a reference to a bundled license file |
| `compatibility` | no | ≤ 500 chars; environment requirements only. Most skills omit it |
| `metadata` | no | map of string keys to string values |
| `allowed-tools` | no | space-separated pre-approved tools. Experimental; support varies |

No other top-level field is defined, and CI rejects unknown ones — that check exists to catch
`descriptions:` and `licence:`, which YAML accepts in silence.

Structural rules: `SKILL.md` under 500 lines, body under roughly 5000 tokens, detail in
`references/`, references one level deep by a path relative to the skill root, **no absolute paths
and no upward `..` traversal**.

### The `fgdh.*` keys

All values are strings. Quote anything YAML would coerce, and always quote a handle — `@` is a
reserved YAML indicator. The normative registry, with rationale per key, is
[docs/metadata-keys.md](docs/metadata-keys.md).

| Key | Required | Allowed values | Default |
| --- | --- | --- | --- |
| `fgdh.tier` | yes | `universal`, `domain` — **never `project`** | — |
| `fgdh.domain` | yes | lowercase hyphenated slug | — |
| `fgdh.owner` | yes | GitHub handle or team, quoted, starting with `@` | — |
| `fgdh.language` | no | BCP 47 tag for the body's instruction language | `en` |
| `fgdh.status` | no | `stable`, `experimental`, `deprecated` | `stable` |
| `fgdh.replaced-by` | no | successor's `name`, or the literal `none`. Required when deprecated | — |

An unregistered `fgdh.*` key is a validation error, not a private extension. Adding a key means
registering it in `docs/metadata-keys.md` first.

## Descriptions

The description is the only text an agent sees before deciding to load a skill, so it carries the
entire triggering decision.

- State what the skill does **and** the situations that should trigger it, in the vocabulary a
  user would type.
- End with a delimitation clause: `Do not use for X; see <other-skill>.`
- Avoid vocabulary that overlaps a neighbouring skill.
- **Under-triggering is the common failure mode.** Be explicit rather than coy.

**Poor:**

```yaml
description: Helps with implementation guides.
```

Not a capability, no trigger situation, no user vocabulary, no delimitation — it competes with
every neighbouring skill for every request and wins none of them clearly.

**Good:**

```yaml
description: Migrates a FHIR Implementation Guide project onto the MII KDS module template —
  rewrites sushi-config.yaml, the IG template reference and the page structure, then verifies the
  build. Use this skill when moving an existing IG to the module template, when a build fails
  after a template bump, or when the user mentions Kerndatensatz, KDS-Modul,
  Implementierungsleitfaden, sushi-config, ig.ini or the IG Publisher. Do not use for authoring
  new profiles or for translating page content; see fhir-profiling and ig-translate.
```

One capability clause, three trigger situations (one phrased as the *symptom* rather than the
intention), the user's real vocabulary including the German terms, and a delimitation clause
naming two neighbours.

## Language

Three axes, independent of each other:

| Axis | Rule |
| --- | --- |
| **Metadata** — `name`, `description`, every `fgdh.*` value | **Always English.** The description is the surface agents match against and must stay comparable across the catalog. |
| **Instructions** — the body, `references/` | English by default; another language when the domain artifacts are. Declare it in `fgdh.language`. |
| **Output** — what the skill produces | **State it in the first sentence of `## Procedure`** whenever it is not English. |

Foreign-language trigger terms go *inside* the English description (`Kerndatensatz`,
`Implementierungsleitfaden`). Translating the whole description buys nothing and costs
comparability.

## Status mirroring — the exact wording CI matches

An agent sees only `name` and `description` before deciding to activate a skill, and never sees
`fgdh.*`. So a status that must change what an agent does has to be mirrored into text it reads.
The three statuses need three different treatments; mirroring all of them would be wrong.

| Status | Description | Body |
| --- | --- | --- |
| `stable` | no mention | no mention |
| `experimental` | **no mention** | caution banner first |
| `deprecated` | **mandatory redirect clause** | deprecation banner first |

CI matches these as substrings, so they are fixed rather than suggested:

Experimental body, first element after the H1:

```markdown
> **Experimental.** This skill has not been verified against a real task since its last change. Verify its output before relying on it.
```

Deprecated body, first element after the H1:

```markdown
> **Deprecated.** <reason> Use <successor> instead. Removal may occur no earlier than <release>.
```

Deprecated description, appended — one of:

```text
Deprecated as of <version>; use <successor> instead.
Deprecated as of <version>; no successor.
```

The coupling is enforced in **both** directions: a `deprecated` skill whose description lacks the
redirect fails, and a `stable` skill whose description still announces a deprecation fails.
Promotion to `stable` removes the experimental banner in the same change.

## Review checklist

Applied by the reviewer; also in the pull request template.

- [ ] Tier correct, and the decision written down.
- [ ] Preconditions genuinely detect rather than assume; the failure branch is explicit.
- [ ] Verification states an observable criterion, not "check that it looks right".
- [ ] Delimitation clause present and naming real neighbours.
- [ ] No absolute paths, no upward `..`, references one level deep and existing.
- [ ] `SKILL.md` under 500 lines.
- [ ] Owner set, and the matching `CODEOWNERS` line added.
- [ ] Status mirrored where an agent can see it.
- [ ] `scripts/` read line by line if present — a skill is untrusted code until reviewed.
- [ ] Provenance and license present for imported material.
- [ ] Generated artefacts regenerated and committed.

## Versioning

The repository uses [SemVer](https://semver.org/), released by
[Release Please](https://github.com/googleapis/release-please) from
[Conventional Commits](https://www.conventionalcommits.org/).

SemVer was defined for APIs, so the catalog needs an explicit reading. **The public surface is: the
set of skill names, the frontmatter contract, the `fgdh.*` key registry, and the
`skills/index.json` schema.** Skill *prose* is not part of the public surface; the contract around
it is.

| Bump | Meaning here | Commit form |
| --- | --- | --- |
| **MAJOR** | A consumer pinned to the previous tag breaks on upgrade: a skill name removed or renamed without a deprecation period; an `fgdh.*` key removed or its allowed values narrowed; an incompatible change to the `index.json` schema; a skill's required preconditions widened so previously working invocations now fail. | `feat!:` or a `BREAKING CHANGE:` footer |
| **MINOR** | New capability, backwards compatible: a skill added; a new optional metadata key; a substantive change to a skill's procedure that keeps its contract; a skill marked `deprecated` while still present. | `feat:` |
| **PATCH** | No change in capability: wording, typos, clarifications, description tuning that does not change the skill's scope, refreshed generated files, CI fixes. | `fix:`, `docs:`, `chore:`, `ci:` |

Two rules follow:

1. **Deletion is a two-release process.** Release *n* marks the skill `fgdh.status: "deprecated"`
   with `fgdh.replaced-by` set — a MINOR. Release *n+m* removes the folder — a MAJOR. Never both
   at once: consumers pin by name, and a silent removal is an unannounced break.
2. **A renamed skill is a new skill.** Add the new name, deprecate the old one, remove it later.
   Renaming in place is a MAJOR even if the content is identical.

### The one exception: before the first external consumer

The two-release rule exists to protect consumers who pinned a name. Before the first external
consumer exists there is nobody to protect, and serving a deprecation period costs a release and
adds a redirect nobody will read.

So a name **may** be changed in place, without a deprecation release, when **all** of these hold:

- the catalog is still below `1.0.0`;
- the name has never appeared in a release that anyone installed — verify it, do not assume it
  (`gh api repos/<org>/<repo> --jq '.forks_count'`, the clone traffic endpoint, and a code search
  across the organization);
- the old name is **tombstoned in `RETIRED.md`** anyway, because a name means one thing forever
  regardless of how briefly it existed;
- the change is committed as `feat!:` so the changelog records it as breaking, and the pull request
  states the verification above.

Outside those conditions, follow the two-release rule. And note what the exception does *not* buy:
it removes the waiting period, not the tombstone and not the breaking-change marker. If you cannot
demonstrate that nobody installed the name, you do not have this exception.

While the catalog is below `1.0.0`, breaking changes bump MINOR rather than MAJOR by SemVer
convention. Cut `1.0.0` deliberately: it should follow the first external consumer, not a feeling
of completeness. Record that decision in an ADR.

### Cutting a release

Release Please keeps a pull request titled `chore: release <version>` up to date between releases.
Merging it tags the release, publishes the GitHub Release, and updates `CHANGELOG.md`,
`version.txt`, `$.version` in `skills/index.json`, and the pinned tag in `README.md`.

**The release pull request needs its workflow run approved before it can merge.** This is the one
manual step in the process, and it is not a defect:

1. Open the release pull request. Its `validate` and `pr-title` runs sit at **`action_required`** —
   GitHub holds workflow runs on pull requests from the `github-actions` bot until someone approves
   them.
2. Approve the run — the **"Approve and run"** button on the pull request's checks, or:

   ```bash
   gh api -X POST repos/forschungsgruppe-digital-health/agent-skills/actions/runs/<run-id>/approve
   ```

3. The checks then run normally, and the pull request merges like any other.

Observed rather than assumed: this was hit on the first release, `v0.1.0`. Do not respond to it by
granting the ruleset a bypass actor — a human approving each release is a feature at this scale,
and it costs one click a release.

### Two further traps

- **The default `GITHUB_TOKEN` does not trigger other workflows.** A release created with it will
  not set off a publishing or Pages workflow listening for a tag push. If that is ever needed, use
  a separate token or `workflow_dispatch`. Do not rely on the default and discover this after the
  first release.
- **`bump-minor-pre-major` does not govern the *first* release.** It controls how commits bump an
  existing pre-1.0 version. With no prior release tag, Release Please uses its own default initial
  version — which is `1.0.0`, not `0.1.0`, and the manifest entry alone does not override it. That
  is what `"initial-version": "0.1.0"` in `.github/release-please-config.json` is for. It has
  already done its job; the note is here so nobody removes it as redundant.

## Commits and branching

- One long-lived branch: `main`. No `develop`, no `release/*`. Short-lived branches only, merged
  within two days.
- Merges are **squash** merges, so **the pull request title becomes the commit message on `main`**
  and is what Release Please parses. CI lints it.
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`, `style`,
  `revert`.
- Incomplete work is merged as `experimental` with a `TODO(owner):` marker, never parked on a
  branch.

Full detail, including the two bot-branch exceptions and the review model in force, is in
[docs/branching.md](docs/branching.md).

## Deprecating a skill

Set `fgdh.status: "deprecated"`, set `fgdh.replaced-by`, **and add the redirect clause to the
description in the same commit.** The field alone changes nothing an agent can see — it sees only
the description before deciding to activate, so a deprecation recorded only in metadata keeps
triggering and keeps being followed.

Never delete a folder without a deprecation release. The minimum period is one release and thirty
days, whichever is longer. When the folder finally goes, add the name to
[RETIRED.md](RETIRED.md); retired names are never reused.
