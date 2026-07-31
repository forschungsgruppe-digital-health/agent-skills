# Catalog Lifecycle: Intake, Maintenance, Retirement, and Quality Assurance

This document defines how a skill enters the catalog, how it is kept correct, how it is retired,
and how quality is assured. It is normative: the review checklists here are the ones a reviewer is
expected to apply, and the automated gates are the ones CI enforces.

Every claim about an external specification or tool below carries a source link. Where no source
exists, the statement is marked as a local policy decision rather than an external requirement.

---

## 0. Scope, roles, and the two contracts

The catalog has two distinct contracts, and most disputes come from conflating them.

**The format contract** is external and not ours to change. A skill is a directory containing a
`SKILL.md` with YAML frontmatter and Markdown instructions, optionally accompanied by `scripts/`,
`references/`, and `assets/`
([specification](https://agentskills.io/specification)). Required frontmatter is `name` and
`description`; `license`, `compatibility`, `metadata`, and the experimental `allowed-tools` are
optional. `name` is limited to 64 characters of lowercase letters, digits and hyphens, must not
start or end with a hyphen, must not contain consecutive hyphens, and must equal the parent
directory name. `description` is limited to 1024 characters and should state both what the skill
does and when to use it.

**The catalog contract** is ours: the tier model, the `fgdh.*` metadata registry, the
description policy, and the release semantics. It is versioned with
[SemVer](https://semver.org/) and released from
[Conventional Commits](https://www.conventionalcommits.org/) by
[Release Please](https://github.com/googleapis/release-please).

| Role | Responsibility |
| --- | --- |
| **Skill owner** | Correctness of one skill's content. Named in `fgdh.owner` and in `CODEOWNERS`. Answers review questions, performs the annual re-validation, decides on deprecation. |
| **Catalog maintainer** | The catalog contract: tier decisions, metadata registry, CI gates, releases. Does not need domain expertise in every skill. |
| **Contributor** | Anyone proposing a skill or a change. May become the owner. |

A skill without a reachable owner is not maintainable. That is why ownerless skills are retired
(§3.1), not merely flagged.

---

## 1. Intake (*Aufnahme*)

### 1.1 Entry criteria — the four questions

A proposal is accepted into the pipeline only if all four are answered affirmatively. These are
local policy, chosen to keep a multi-domain catalog navigable.

1. **Is it procedural knowledge, not reference material?** Skills package repeatable procedures.
   A glossary, a link collection, or a specification excerpt belongs in a wiki. The test: can the
   body be written as steps with a verification criterion?
2. **Is it tier `universal` or `domain`?** A skill that requires specific files at specific paths
   is tier `project` and belongs in the consuming repository, not here. See §1.3.
3. **Does it have a named owner willing to be listed?** No owner, no intake.
4. **Is its trigger vocabulary distinguishable from every existing skill?** If two skills would
   compete for the same request, either merge them or sharpen both descriptions. This is checked
   mechanically (§4.1) but decided by a human.

### 1.2 The intake pipeline

```
proposal issue → tier assessment → authoring → mechanical gates → review → merge → release
    (§1.2.1)        (§1.3)          (§1.4)        (§4.1)         (§4.2)         (§5)
```

#### 1.2.1 Proposal

Open an issue from the `new-skill` template. It records: the procedure to be captured, the
trigger situations in the requester's own words, the proposed tier, the intended owner, and the
neighbouring skills it might collide with. The proposal is a design review, not a formality —
rejecting at this stage costs one issue comment; rejecting after authoring costs a person-day.

#### 1.2.2 Authoring

Copy `templates/SKILL.md.template`. The template's sections are mandatory, in this order:

| Section | Purpose |
| --- | --- |
| `## Preconditions` | How the skill detects the context it needs, and what to do when detection fails. |
| `## Procedure` | The steps. Prefer commands with exit codes over judgement calls. |
| `## Verification` | How the agent confirms the result is correct. |
| `## Scope and delimitation` | What this skill deliberately does not cover, and which skill does. |

Structural rules that follow from the specification: keep `SKILL.md` under 500 lines and the body
under roughly 5000 tokens, move detail into `references/`, reference files by relative paths from
the skill root, and keep those references one level deep
([specification](https://agentskills.io/specification)). Absolute paths and `../` traversal are
consequently forbidden; CI enforces this.

**Language.** Metadata — `name`, `description`, and every `fgdh.*` value — is always
English, because the description is the surface agents match against and it must stay
comparable across the catalog. The body may be another language when the artifacts the skill
operates on are in that language; declare it in `fgdh.language`. Foreign-language trigger
terms belong *inside* the English description. If the required output language is not English,
the first sentence of `## Procedure` says so.

The three-stage loading model is the reason these limits matter: agents load only `name` and
`description` at startup, the full body on activation, and bundled resources on demand
([specification](https://agentskills.io/specification)). Anything in the body is paid for on every
activation; anything in `references/` is paid for only when actually needed.

### 1.3 Tier assessment — the gate that keeps the catalog portable

Classification has three outcomes, but only two of them are storable values. `project` is a
verdict that the skill belongs elsewhere; it is never written into `fgdh.tier`, and a
`SKILL.md` carrying that value fails validation.

| Classification | May assume | Belongs in the catalog | Stored as `fgdh.tier` |
| --- | --- | --- | --- |
| `universal` | nothing; conventions, checklists, review procedures | yes | `universal` |
| `domain` | a toolchain exists; project layout is **discovered**, not assumed | yes | `domain` |
| `project` | specific files at specific paths | **no** | never — the skill is not committed here |

The assessment is a written decision recorded in the pull request, not a checkbox. A skill that
was drafted as `project` tier can often be lifted to `domain` by replacing hard-coded paths with a
discovery step plus an explicit failure branch — that rewrite is the work, and it is what makes
the skill survive being installed into a repository nobody anticipated.

### 1.4 Definition of Done

- All mechanical gates green (§4.1).
- Review checklist signed off (§4.2).
- `fgdh.status` set to `experimental` for a newly authored or newly reworked skill; promotion
  to `stable` requires at least one recorded successful use (§2.3).
- Provenance recorded if the skill was imported from elsewhere: source repository, path, and the
  commit SHA it was derived from, plus the original license.
- Generated artefacts (`skills/index.json`, `CATALOG.md`) regenerated and committed in the same
  pull request.

---

## 2. Maintenance (*Pflege*)

### 2.1 Change classes

The release semantics (§5) depend on classifying the change correctly. The public surface is the
set of skill names, the frontmatter contract, the `fgdh.*` registry, and the `index.json`
schema — **not** the prose inside a skill.

| Class | Examples | Commit type | Effect |
| --- | --- | --- | --- |
| Editorial | typos, clearer wording, formatting | `fix:` / `docs:` | PATCH |
| Substantive | procedure changed, step added, reference file added | `feat:` | MINOR |
| Contract | skill added, metadata key added | `feat:` | MINOR |
| Breaking | skill removed or renamed, metadata key removed or narrowed, index schema changed incompatibly, preconditions widened so previously working invocations fail | `feat!:` / `BREAKING CHANGE:` | MAJOR |

A description edit is editorial **only** if it does not change the set of situations that trigger
the skill. If it changes the trigger surface, it is substantive — because that is what consumers
actually experience.

### 2.2 Scheduled maintenance

| Cadence | Activity | Owner |
| --- | --- | --- |
| Per pull request | Mechanical gates (§4.1) and review (§4.2) | Reviewer |
| Weekly, automated | Spec and dependency watch (§6), plus the owner resolution check | Catalog maintainer triages |
| Quarterly | Overlap report review: inspect the highest-similarity pairs from `check_descriptions.py` even when below the failure threshold | Catalog maintainer |
| Annually | **Re-validation** of every skill (§2.3) | Skill owner |
| On upstream change | Impact assessment triggered by a watch finding (§6.4) | Catalog maintainer |

### 2.3 Annual re-validation

Each skill is re-validated once a year by its owner. The re-validation is a short written record
in the pull request or issue, answering four questions:

1. Have the external anchors changed? (repository URLs, tool names, commands, version pins)
2. Has the procedure been used at least once since the last re-validation, and did it work?
3. Is the description still distinguishable from the skills added since?
4. Is the owner still the right owner?

Outcomes: `stable` confirmed, promoted from `experimental` to `stable`, revised, or entered into
retirement (§3). Promotion to `stable` also removes the experimental banner from the body;
leaving it in place after promotion is the mirror-image of the deprecation failure above. A skill that cannot be re-validated because nobody knows whether it still works
is by definition unmaintained — retire it rather than leaving it to be trusted at the moment it
is loaded.

### 2.4 Handling an upstream specification change

When the watch (§6) reports a change:

1. Read the upstream diff and classify: does it affect the **format contract**, the **tooling**,
   or neither?
2. If it affects the format contract, run the reference validator against every skill before
   changing anything, so the blast radius is measured rather than estimated.
3. Open one issue per affected skill, referencing the upstream change.
4. Update `docs/watchlist.yaml` with the new observed state so the watch stops reporting the same
   change.

---

## 3. Retirement (*Ausmusterung*)

### 3.1 Retirement triggers

Any one of these starts the retirement process:

- The procedure the skill describes no longer exists, or its target system was decommissioned.
- Annual re-validation failed and no owner is willing to revise it.
- The skill has no reachable owner. The weekly owner check (`scripts/check_owners.py`) reports
  handles that no longer resolve; an unresolved owner starts a 30-day reassignment window
  before this trigger fires, because a handle can fail to resolve for reasons other than
  departure.
- It has been superseded by another skill (merge or replacement).
- Review found that it is tier `project` and was admitted in error.

### 3.2 The two-release rule

Consumers pin by skill **name**. A silent removal is an unannounced break, so removal is always a
two-step process across two releases:

**Release *n* — deprecate (MINOR).**

- Set `fgdh.status: "deprecated"`.
- Set `fgdh.replaced-by` to the successor's name, or to `none` if there is none.
- **Add the redirect clause to the `description`** — `Deprecated as of <version>; use
  <successor> instead.` This is the load-bearing step, not the metadata field. An agent sees
  only the description before deciding to activate a skill, so a deprecation recorded only in
  metadata is invisible: the skill keeps triggering and keeps being followed. CI enforces the
  coupling; do not rely on remembering it.
- Prepend a deprecation banner to the body stating the reason, the successor, and the earliest
  release in which removal may occur.
- Do **not** change the `name`, and do not delete the folder.

**Release *n+m* — remove (MAJOR).**

- Delete the directory.
- Record the removal in the changelog under a breaking-change heading.
- Add the name to a `RETIRED.md` tombstone list with the reason and the successor, so that a
  consumer encountering a missing skill can discover what happened without reading Git history.

Local policy: the minimum deprecation period is **one release and thirty days**, whichever is
longer. Shortening it requires a recorded decision naming the consumers who were contacted.

### 3.3 Renaming is not renaming

A rename is a removal plus an addition. Add the new name, deprecate the old one, remove the old
one later. Renaming a directory in place breaks every pinned consumer while looking like a
cosmetic change in the diff — which is exactly why it must be handled as a breaking change.

### 3.4 What is never deleted

The tombstone entry in `RETIRED.md`, and the Git history. The point of a catalog is that a name
means one thing forever; reusing a retired name for a different skill is forbidden.

---

## 4. Quality assurance

Three gates, in increasing cost and decreasing automation. A change passes all three.

### 4.1 Gate 1 — mechanical (CI, blocking)

| Check | Tool | What it catches |
| --- | --- | --- |
| Specification conformance | [`skills-ref validate`](https://github.com/agentskills/agentskills/tree/main/skills-ref) — the reference validator, which checks frontmatter validity and naming conventions ([spec](https://agentskills.io/specification)) | Invalid frontmatter, illegal names |
| Catalog contract | `scripts/build_index.py --check` | Missing or invalid `fgdh.*` keys, name/directory mismatch, index drift |
| Trigger collision | `scripts/check_descriptions.py` | Descriptions competing for the same requests |
| Path portability | `grep` for absolute paths and `../` | Skills that only work in the repository they were written in |
| Body size | line count per `SKILL.md` | Bodies that will crowd the context on every activation |

Owner resolution is deliberately **not** in this table. It requires a network call and would
make merge results depend on API availability and rate limits, so it runs weekly and reports
instead of blocking (§6).

These are deterministic: pass or fail comes from an exit code, never from a judgement. That
property is what makes the gate trustworthy when the contributor is an agent rather than a person.

### 4.2 Gate 2 — human review (blocking)

The reviewer checks what a script cannot:

- **Tier decision** is correct and written down.
- **Preconditions** genuinely detect rather than assume, and the failure branch is explicit.
- **Verification section** states an observable criterion, not "check that it looks right".
- **Delimitation** names the neighbouring skills accurately.
- **Description** describes the situations a real user would be in, using their vocabulary —
  in English, but including the foreign-language terms they would actually type.
- **Language declaration** present and correct if the body is not English, and the output
  language stated where it is not English.
- **Status is mirrored where an agent can see it**: a deprecated skill carries the redirect in
  its description, an experimental one carries the caution banner in its body and *no* warning
  in its description. A status recorded only in metadata changes nothing an agent does.
- **Scripts** — if `scripts/` is present, read every line. See §4.4.
- **Provenance and license** present for imported material.

### 4.3 Gate 3 — empirical (required for promotion to `stable`)

Mechanical validity does not imply the skill will ever be loaded. The Skills-over-MCP working
group reported that models frequently ignored available skills and used tools directly, sometimes
failing before eventually finding the skill; adding an instruction to consult the skill first
helped, but adherence declined as context grew
([AAIF](https://aaif.io/blog/skills-over-mcp)). Triggering is therefore something to test, not
assume.

Minimum empirical check before promoting `experimental` → `stable`:

1. Write three to five realistic task prompts that *should* trigger the skill, phrased as a user
   would phrase them — not as the description is phrased.
2. Write two prompts that should **not** trigger it, ideally ones aimed at a neighbouring skill.
3. Run them against an agent with the catalog installed. Record which triggered.
4. Record the results in the pull request. If a should-trigger prompt fails, the description is
   the defect, not the user.

Store the prompts alongside the skill in `references/triggers.md` so the next re-validation
re-uses them.

### 4.4 Security review of bundled content

Skills carry instructions and, optionally, executable code, so a skill is untrusted code until
reviewed. Published guidance is to use skills only from trusted sources and to audit all bundled
files before use, since a malicious skill can direct an agent to act in ways that do not match its
stated purpose ([Ylang Labs summary of the specification's guidance](https://ylanglabs.com/blogs/agent-skills)).
Ecosystem scans of public skills have reported substantial rates of prompt-injection and other
findings — figures published by commercial vendors rather than peer-reviewed, so treat the
magnitude as indicative and the direction as sound
([ecosystem report](https://agentman.ai/blog/agent-skills-ecosystem-report-2026)).

Practical consequences for this catalog, as local policy:

- Every `scripts/` file is read line by line in review. No exceptions for "it's just a wrapper".
- No skill instructs an agent to fetch and execute remote content.
- No skill embeds credentials, tokens, or internal hostnames.
- Imported skills (from another repository or a public marketplace) are reviewed as third-party
  code, regardless of source reputation, and the review is recorded in the pull request.

### 4.5 Health metrics

Track these per release; they are cheap to compute from `skills/index.json` and Git:

| Metric | Signal when it degrades |
| --- | --- |
| Skills per tier | Growth in `domain` relative to `universal` means the catalog is specializing |
| Skills by status | A rising `experimental` share means Gate 3 is being skipped |
| Highest description similarity pair | Approaching the failure threshold means the namespace is crowding |
| Median age since last re-validation | The single best predictor of stale content |
| Skills without a recorded use in 12 months | Retirement candidates |

---

## 5. Release and communication

Releases are produced by Release Please from Conventional Commits. Consumers pin to tags, so the
changelog is the primary communication channel: a consumer who reads only the changelog must be
able to tell whether upgrading is safe.

Because installed skills are plain files, a consumer's recovery path is a re-install from the
previous tag rather than an in-place rollback. State that in `docs/consuming-skills.md` and
keep the changelog precise enough to support the decision: a reader must be able to tell
whether a skill changed, was deprecated, or disappeared.

Required in each release's notes:

- Skills added, with tier and one-line purpose.
- Skills deprecated, with successor and earliest removal release.
- Skills removed (breaking), with the tombstone reference.
- Any change to the `fgdh.*` registry or the index schema.

---

## 6. Watching the specification and the toolchain

The question this answers: *is there a Dependabot-equivalent for specifications?* Partly. Three
mechanisms cover three different kinds of upstream, and only the first is fully off-the-shelf.

### 6.1 What Dependabot can and cannot do

Dependabot raises pull requests for dependencies declared in **a manifest or lock file of a
supported package manager**
([GitHub Docs](https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories)).
That covers this repository's *tooling* and nothing else:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule: { interval: "weekly" }
  - package-ecosystem: "pip"
    directory: "/"
    schedule: { interval: "weekly" }
```

This keeps the Actions in `validate.yml`, `release.yml`, and `pages.yml` current, and `PyYAML`
and the validator current if the validator is installed from a package index. It cannot watch a
specification document, because a specification is not a declared dependency.

### 6.2 Renovate for versioned upstreams without a manifest

Renovate's custom manager reads version strings out of **arbitrary files** using named capture
groups, and pairs them with a datasource such as `github-tags` or `github-releases`
([Renovate docs](https://docs.renovatebot.com/modules/manager/regex/)). This turns "which version
of the spec are we written against?" into a tracked dependency.

Record the tracked versions in one file, `docs/watchlist.yaml`, with inline Renovate annotations:

```yaml
# renovate: datasource=github-tags depName=agentskills/agentskills
agent_skills_spec: "v1.2.3"

# renovate: datasource=github-releases depName=googleapis/release-please
release_please: "v17.0.0"
```

Renovate then opens a pull request when upstream tags a new version, and the pull request itself
is the prompt to reassess. Note the naming history: the feature was formerly configured as
`regexManagers` and is now `customManagers` with `customType: "regex"` — older examples on the web
use the old key.

For upstreams that publish versions over HTTP but have no Git releases, Renovate's **custom
datasource** requests version data from a generic HTTP(S) endpoint and reshapes it with JSONata
transforms ([Renovate docs](https://docs.renovatebot.com/modules/datasource/custom/)).

### 6.3 A scheduled watch workflow for unversioned upstreams

Neither tool helps with an upstream that has no version at all — a living specification page, an
open proposal, a working group's meeting notes. For those, a small scheduled workflow is the
honest answer.

**`docs/watchlist.yaml`** carries one entry per watched source:

```yaml
watches:
  - id: agent-skills-spec
    url: https://agentskills.io/llms.txt
    kind: text
    why: "Format contract. A change here can invalidate frontmatter rules."
    owner: "@catalog-maintainer"
    last_seen_sha256: "…"

  - id: sep-2640-skills-extension
    url: https://api.github.com/repos/modelcontextprotocol/modelcontextprotocol/pulls/2640
    kind: json
    watch_fields: [state, merged, updated_at]
    why: "Skills over MCP. Merge would make skill://index.json normative."
    owner: "@catalog-maintainer"
    last_seen_sha256: "…"

  - id: agentskills-repo-commits
    url: https://api.github.com/repos/agentskills/agentskills/commits?per_page=1
    kind: json
    watch_fields: [sha]
    why: "Spec repository activity, including changes without a release."
    owner: "@catalog-maintainer"
    last_seen_sha256: "…"
```

**`scripts/watch_specs.py`**, run weekly by `.github/workflows/spec-watch.yml`:

1. Fetch each `url`.
2. Normalize: for `kind: json`, select only `watch_fields` and serialize canonically; for
   `kind: text`, strip trailing whitespace and normalize line endings.
3. Hash the normalized content and compare with `last_seen_sha256`.
4. On difference, open or update a single tracking issue per watch id, containing the diff excerpt,
   the `why` field, and a checklist: *assess impact → open per-skill issues → update watchlist*.
5. Never auto-update `last_seen_sha256` in the repository. Acknowledging a change is a human act;
   automatic acknowledgement would silently close the loop the watch exists to open.

Design notes learned the hard way, stated so they are not rediscovered:

- **Prefer machine-readable endpoints to HTML pages.** HTML changes constantly for reasons
  unrelated to content, and a watch that cries wolf gets muted. `agentskills.io` publishes a
  documentation index at `llms.txt` intended as a discovery mechanism, which is far more stable
  than the rendered page.
- **Watch state, not prose, for proposals.** For an open pull request, the `state`, `merged`, and
  `updated_at` fields answer the question that matters; the diff does not.
- **One issue per watch, updated in place**, not one issue per run. Otherwise the noise becomes
  the reason the watch is disabled.

### 6.4 Triage: what a watch finding obliges

A finding is not a change request. It obliges an **impact assessment** within one week, recorded
as a comment on the tracking issue and classified as: *no impact*, *documentation only*,
*skills affected* (with the list), or *contract change* (requiring a MAJOR release). Only the last
two produce work.

---

## 7. Summary of cadences

| When | What | Who | Blocking |
| --- | --- | --- | --- |
| Per pull request | Gates 1 and 2 | CI, reviewer | yes |
| Before `stable` | Gate 3, trigger testing | Skill owner | yes |
| Weekly | Dependabot, Renovate, spec watch | Automated; maintainer triages | no |
| Within one week of a watch finding | Impact assessment | Catalog maintainer | no |
| Quarterly | Overlap report review | Catalog maintainer | no |
| Annually | Re-validation of every skill | Skill owner | leads to retirement if skipped |
| Release *n* / *n+m* | Deprecate / remove | Catalog maintainer | yes |

---

## Sources

- Agent Skills specification: <https://agentskills.io/specification>
- Specification repository and reference validator: <https://github.com/agentskills/agentskills>,
  <https://github.com/agentskills/agentskills/tree/main/skills-ref>
- Skills over MCP, proposal and open questions: <https://aaif.io/blog/skills-over-mcp>,
  <https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2640>
- Dependabot supported ecosystems:
  <https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories>
- Renovate custom manager (regex): <https://docs.renovatebot.com/modules/manager/regex/>
- Renovate custom datasource: <https://docs.renovatebot.com/modules/datasource/custom/>
- Release Please: <https://github.com/googleapis/release-please>
- Conventional Commits: <https://www.conventionalcommits.org/>
- Semantic Versioning: <https://semver.org/>
- Skill security guidance and ecosystem scan figures (vendor-published, not peer-reviewed):
  <https://ylanglabs.com/blogs/agent-skills>, <https://agentman.ai/blog/agent-skills-ecosystem-report-2026>
