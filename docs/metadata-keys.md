# The `fgdh.*` metadata registry

This file is the **normative registry** for the organization-specific metadata keys. CI error
messages point here, so it has to answer the question a contributor actually has when they arrive:
what is this key, what may it contain, and why does it exist at all.

The Agent Skills specification defines `metadata` as an arbitrary map of string keys to string
values and recommends namespacing the keys to avoid collisions with what other tools might
interpret ([specification](https://agentskills.io/specification)). `fgdh` is that namespace. It is
short and owned by the group rather than reverse-DNS, because reverse-DNS is only meaningful for a
domain the organization actually controls. If this catalog is ever published to the MCP Registry,
the verified namespace there would be `io.github.forschungsgruppe-digital-health`; that is a
different identifier for a different purpose and does not change these keys.

**All values are strings.** Quote anything YAML would coerce — `"1.0"` is a string, `1.0` is a
float — and always quote a handle, because `@` is a reserved YAML indicator.

## The registry

| Key | Type | Required | Allowed values | Default | Stability |
| --- | --- | --- | --- | --- | --- |
| `fgdh.tier` | string | yes | `universal`, `domain` | — | stable |
| `fgdh.domain` | string | yes | lowercase hyphenated slug, `^[a-z0-9]+(-[a-z0-9]+)*$` | — | stable |
| `fgdh.owner` | string | yes | GitHub handle or team, starting with `@` | — | stable |
| `fgdh.language` | string | no | BCP 47 tag, e.g. `en`, `de`, `en-GB` | `en` | stable |
| `fgdh.status` | string | no | `stable`, `experimental`, `deprecated` | `stable` | stable |
| `fgdh.replaced-by` | string | no | a skill `name`, or the literal `none` | — | stable |

An `fgdh.*` key that is not in this table is a validation error (`metadata/unknown`), not a
private extension. Keys outside the `fgdh.` namespace are left alone: the specification's own
example uses generic `author` and `version`, and this catalog does not police them.

---

### `fgdh.tier`

**Why it exists.** It records whether a skill can be installed into a repository nobody
anticipated. That is the single property that decides whether the catalog is portable or is
really a collection of one team's local scripts.

| Value | May assume |
| --- | --- |
| `universal` | nothing — conventions, checklists, review procedures |
| `domain` | a toolchain is available; project layout is **discovered**, not assumed |

**`project` is not a value.** Classification has three outcomes and the third one means the skill
belongs in the consuming repository. A `SKILL.md` carrying `fgdh.tier: "project"` fails validation
with `tier/rejected`, and the correct response to that error is never to change the value: either
lift the skill to `domain` by replacing each hard-coded path with a discovery step plus an
explicit failure branch, or move it to the repository it belongs to.

A `domain` skill must contain a `## Preconditions` section describing how it detects its context
and what the agent should do when detection fails. A skill that hard-codes a path or requires a
specific file to exist classifies as `project` regardless of what its frontmatter claims — the
frontmatter is an assertion, and review checks whether it is true.

> **Terminology.** This "tier" is the skill classification and nothing else. The build-out
> **stages** in `roadmap.md` (Stage 1 static, Stage 2 local MCP server, Stage 3 remote server) are
> a different axis and deliberately use a different word. Do not mix the two vocabularies.

### `fgdh.domain`

**Why it exists.** It groups the catalog for humans — `CATALOG.md` sorts by domain then name —
and gives the Stage 2 ranking a cheap facet to filter on. It is deliberately free-form: an
enumerated list would need a contract change every time someone works in a new area, which is
exactly the friction that makes people skip the field.

Keep slugs coarse. `fhir-ig` is useful; `fhir-ig-sushi-config-migration` is a skill name wearing a
domain's clothes.

### `fgdh.owner`

**Why it exists.** A skill without a reachable owner cannot be re-validated, and a skill nobody
knows still works is retired rather than left to be trusted at the moment it is loaded
(`lifecycle.md` §3.1).

The value must resolve to an existing GitHub user or team. `scripts/check_owners.py` verifies this
weekly and reports `resolved`, `not-found` or `unverifiable`. An unresolved owner starts a 30-day
reassignment window before the retirement trigger fires, because a handle can fail to resolve for
reasons other than departure.

The same handle belongs in `CODEOWNERS` on the skill's directory, added in the pull request that
adds the skill. The two are not linked automatically; keeping them in step is a review item.

**This check does not run on pull requests, on purpose.** It needs a network call, and a
contributor's merge must not be blocked by an unrelated owner having left the organization, nor by
GitHub's rate limits.

### `fgdh.language`

**Why it exists.** It records the **instruction language of the body** — nothing else. Some skills
operate on artifacts that are not English (German specifications, German-language deliverables),
and forcing those skills into English produces instructions that are correct and useless: an agent
following a procedure about German governance documents needs the German terms of art, not
translations of them.

Three axes are easy to conflate and must not be:

| Axis | Rule |
| --- | --- |
| **Metadata** — `name`, `description`, every `fgdh.*` value | Always English, no exceptions. The description is the surface agents match against; a mixed-language description space makes the overlap check meaningless and makes triggering depend on which language the user happened to type. |
| **Instructions** — the body, `references/` | English by default; another language when the artifacts are. Declared here. |
| **Output** — what the skill tells the agent to produce | Stated explicitly in the body's `## Procedure`, never left implicit. It does not follow from either of the other two. |

Put foreign-language trigger vocabulary *inside* the English description. That preserves one
comparable description space and still matches real requests.

### `fgdh.status`

**Why it exists.** It drives the health metrics and the promotion gate — and, critically, it is
the field whose value must be **mirrored into text an agent can read**, because an agent sees only
`name` and `description` before deciding to activate a skill and never sees `fgdh.*` at all.

| Value | Description | Body |
| --- | --- | --- |
| `stable` | no mention | no mention |
| `experimental` | **no mention** | caution banner first |
| `deprecated` | **mandatory redirect clause** | deprecation banner first |

Mirroring all three would be wrong. `experimental` stays out of the description because caution
must not suppress triggering — the skill *should* activate, and the agent should then be told to
verify its output, which only has to survive until activation. `deprecated` must reach the
description because redirecting to a successor can only happen *before* the body loads.

`build_index.py` enforces the coupling in both directions, including the case that actually
happens: a skill deprecated in metadata whose description was not touched.

The exact required wording is in `CONTRIBUTING.md` and in
`skills/skill-authoring/references/frontmatter-contract.md`. CI matches it as a substring, so it
is fixed rather than suggested.

### `fgdh.replaced-by`

**Why it exists.** It names the successor so the deprecation redirect can be checked mechanically
rather than trusted. Required when `fgdh.status` is `deprecated`; set it to the successor's `name`
or to the literal `none`.

When it is a name, the description must contain `use <that name> instead.`. When it is `none`, the
description must contain `no successor.`. Those are the two forms the validator accepts.

---

## Changing this registry

The `fgdh.*` registry is part of the catalog's public surface, alongside the set of skill names
and the `index.json` schema. So:

- **Adding an optional key** is a MINOR release (`feat:`). Register it here first, then teach
  `build_index.py` about it, then use it.
- **Removing a key, or narrowing its allowed values**, is a MAJOR release (`feat!:`). A consumer
  pinned to the previous tag breaks on upgrade.
- **Making an optional key required** is also MAJOR: every existing skill becomes invalid.

Nothing enforces "register it here first" mechanically. It is a review item, and it is the reason
`build_index.py` rejects unregistered `fgdh.*` keys instead of ignoring them — an unregistered key
in a merged skill is a registry that has already drifted.
