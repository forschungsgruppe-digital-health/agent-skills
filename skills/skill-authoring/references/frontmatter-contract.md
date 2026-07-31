# The frontmatter contract

Two contracts apply to every `SKILL.md`, and most confusion comes from conflating them.

The **format contract** is external and not ours to change: it is the Agent Skills open
standard at <https://agentskills.io/specification>. The **catalog contract** is ours: the
`fgdh.*` registry, the tier model, and the description policy.

A skill that satisfies only the format contract is a valid skill but not an admissible
catalog entry. A skill that satisfies only the catalog contract is not a skill at all.

## Format contract — fields defined by the standard

| Field | Required | Constraint |
| --- | --- | --- |
| `name` | yes | 1–64 characters; lowercase `a-z`, `0-9` and hyphens only; must not start or end with a hyphen; must not contain consecutive hyphens; **must equal the parent directory name** |
| `description` | yes | 1–1024 characters; states *what* the skill does **and** *when* to use it |
| `license` | no | a license name, or a reference to a bundled license file |
| `compatibility` | no | 1–500 characters; environment requirements only. Most skills omit it |
| `metadata` | no | a map of string keys to string values; keys should be namespaced to avoid collisions |
| `allowed-tools` | no | space-separated pre-approved tools. Experimental; support varies between agents |

No other top-level field is defined, and the catalog's validator rejects unknown ones —
that check exists to catch `descriptions:` and `licence:`, which YAML would otherwise
accept in silence.

### Structural rules from the standard

- Keep `SKILL.md` under 500 lines and the body under roughly 5000 tokens.
- Move detail into `references/`.
- Reference files by **relative paths from the skill root**, kept one level deep.
- Never use an absolute path and never traverse upward with `..`.

These follow from how agents load skills: `name` and `description` at startup for every
skill (~100 tokens each), the full body only once the skill is activated, and files under
`references/`, `scripts/` and `assets/` only when actually needed. Anything in the body is
paid for on every activation; anything in `references/` is paid for only when used.

## Catalog contract — the `fgdh.*` registry

All values are strings. Quote anything YAML would coerce, and always quote a handle:
`@` is a reserved YAML indicator.

| Key | Required | Values |
| --- | --- | --- |
| `fgdh.tier` | yes | `universal` or `domain`. **Never `project`** — see below |
| `fgdh.domain` | yes | free-form lowercase hyphenated slug, e.g. `repo-conventions` |
| `fgdh.owner` | yes | GitHub handle or team, quoted, starting with `@` |
| `fgdh.language` | no | BCP 47 tag for the **instruction language of the body**, e.g. `en`, `de`. Default `en` |
| `fgdh.status` | no | `stable`, `experimental` or `deprecated`. Default `stable` |
| `fgdh.replaced-by` | no | the successor skill's name, or the literal `none`. **Required** when the status is `deprecated` |

Adding a key to this registry is a contract change: register it in the catalog's
`docs/metadata-keys.md` first, then teach the validator about it. An unregistered `fgdh.*`
key is a validation error, not a private extension.

## Why `project` is not a storable value

Tier classification has three outcomes; only two of them describe a skill that belongs in
this catalog.

| Classification | May assume | Admitted |
| --- | --- | --- |
| `universal` | nothing — conventions, checklists, review procedures | yes |
| `domain` | a toolchain is available; project layout is **discovered**, not assumed | yes |
| `project` | specific files at specific paths | **no** — it belongs in the consuming repository |

So `fgdh.tier: "project"` is a validation error rather than a permitted state, and the
correct response to that error is never to change the value. It is either to lift the skill
to `domain` — replace each hard-coded path with a discovery step and an explicit failure
branch — or to move it to the repository it actually belongs to.

A skill that hard-codes a path or requires a specific file to exist classifies as `project`
regardless of what its frontmatter claims. The frontmatter is an assertion; review checks
whether it is true.

## Status: three values, three different treatments

An agent sees only `name` and `description` before deciding whether to activate a skill,
and the body only afterwards. Everything under `fgdh.*` is invisible to it. That is not a
defect — tier, domain and owner exist for the catalog generator, for reviewers and for
`CODEOWNERS`, and they should stay out of the agent's context. But it means any status that
must change what an agent *does* has to be mirrored into text the agent actually reads.

Mirroring all three would be wrong. They need different treatments:

| Status | Description | Body | Why |
| --- | --- | --- | --- |
| `stable` | no mention | no mention | "This skill is stable" matches nothing a user would type and consumes the trigger surface. |
| `experimental` | **no mention** | caution banner as the first element | Caution must not suppress triggering. The skill *should* activate; the agent should then be told to verify its output. That instruction only has to survive until activation, so the body is enough. |
| `deprecated` | **mandatory redirect clause** | deprecation banner as the first element | The only case where the description must carry it. Suppressing activation and redirecting to the successor can only happen *before* the body loads — a deprecated skill that still triggers normally will still be followed, because the warning arrives after the decision. |

### Required wording

CI matches these as substrings, so they are fixed rather than suggested.

Experimental body, first element after the H1:

```markdown
> **Experimental.** This skill has not been verified against a real task since its last change. Verify its output before relying on it.
```

Deprecated body, first element after the H1:

```markdown
> **Deprecated.** <reason> Use <successor> instead. Removal may occur no earlier than <release>.
```

Deprecated description, appended:

```text
Deprecated as of <version>; use <successor> instead.
```

or, when `fgdh.replaced-by` is `none`:

```text
Deprecated as of <version>; no successor.
```

The validator enforces the coupling in **both** directions: a `deprecated` skill whose
description lacks the redirect fails, and a `stable` skill whose description still
announces a deprecation fails. Without the second half the two drift apart at exactly the
release where it matters — the one where a skill is deprecated but its description is not
touched.

Promotion from `experimental` to `stable` removes the banner in the same change that flips
the field. Leaving it in place is the mirror image of the deprecation failure, and the
validator reports it as `mirror/stale-experimental`.

## The three language axes

They are independent, and treating any two as one produces skills that are correct and
useless.

| Axis | Rule |
| --- | --- |
| **Metadata** — `name`, `description`, every `fgdh.*` value | **Always English.** No exceptions. The description is the surface agents match against, and it must be comparable across the whole catalog; a mixed-language description space makes the overlap check meaningless and makes triggering depend on which language the user happened to type. |
| **Instructions** — the body, `references/`, comments in `scripts/` | English by default. May be another language when the domain artifacts are in that language. Declared in `fgdh.language`. An agent following a procedure about German-language governance documents needs the German terms of art, not translations of them. |
| **Output** — what the skill tells the agent to produce | **Stated explicitly in the body**, never left implicit. This is the axis that silently goes wrong: an English-bodied skill can legitimately require German output, and a German-bodied skill can require English output. Neither follows from the other. |

Put foreign-language trigger vocabulary *inside* the English description. A skill about
German implementation guides keeps an English description but names the German terms a user
would actually type (`Kerndatensatz`, `Implementierungsleitfaden`). That preserves one
comparable description space *and* matches real requests. Writing the whole description in
German buys nothing and costs comparability.

When the required output language is not English, the first sentence of `## Procedure` says
so. A reviewer who cannot find that sentence rejects the skill.

## Licensing inside a skill folder

The repository splits Apache-2.0 for code and CC-BY-4.0 for documentation, and a single
skill folder contains both.

- `license:` covers `SKILL.md`, `references/` and `assets/`.
- Anything under `scripts/` is Apache-2.0.
- A skill needing different terms declares them in its own bundled license file and points
  `license:` at that file.

Imported material carries a `## Provenance` section naming the source repository, the path,
and the commit SHA it was derived from, plus the original license.
