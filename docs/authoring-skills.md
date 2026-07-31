# Authoring skills

The long form of the skill contract. `CONTRIBUTING.md` is the checklist; this is the reasoning
behind it, with worked examples and the anti-patterns that actually occur.

If you would rather have an agent walk you through it, the catalog contains a skill for exactly
that: `skills/skill-authoring/`.

## The two contracts

**The format contract** is external and not ours to change: the Agent Skills open standard at
<https://agentskills.io/specification>. It defines the directory layout, the frontmatter fields,
and the loading model.

**The catalog contract** is ours: the tier model, the `fgdh.*` registry (`metadata-keys.md`), the
description policy, and the release semantics (`CONTRIBUTING.md`).

Most arguments about a skill turn out to be an argument about which contract is being appealed to.
A skill can satisfy the format contract and still be inadmissible here.

## The loading model, and why every limit follows from it

Agents load skills progressively:

1. **Metadata (~100 tokens):** `name` and `description` for *every* installed skill, at startup.
2. **Instructions (< 5000 tokens recommended):** the full `SKILL.md` body, once the skill is
   activated.
3. **Resources (on demand):** files under `references/`, `scripts/`, `assets/`.

Three consequences that explain otherwise arbitrary-looking rules:

- **The description carries the entire triggering decision.** It is the only text read before the
  decision is made. Nothing in the body can rescue a description that does not match how people
  ask.
- **Body length is a recurring cost.** Everything in the body is paid for on every activation;
  everything in `references/` is paid for only when needed. Hence: under 500 lines, and move detail
  out.
- **`fgdh.*` is invisible to the agent.** Tier, domain, owner and status exist for the catalog
  generator, for reviewers, and for `CODEOWNERS`. Any of them that must change what an agent
  *does* has to be mirrored into text the agent reads.

## The tier model

Classification has three outcomes. Only two are storable.

| Classification | May assume | Admitted here | Stored as `fgdh.tier` |
| --- | --- | --- | --- |
| `universal` | nothing; pure conventions, checklists, review procedures | yes | `universal` |
| `domain` | a toolchain is available; project layout is **discovered**, not assumed | yes | `domain` |
| `project` | specific files or paths exist | **no** — belongs in the consuming repository | never stored |

`fgdh.tier: "project"` is a validation error (`tier/rejected`), not a permitted state. The error
message says so, because the contributor's next move is to lift the skill to `domain` or move it to
their own repository — never to change the value.

**The lift is the work.** Replacing each hard-coded path with a discovery step plus an explicit
failure branch is what makes a skill survive installation into a repository nobody anticipated. A
skill that hard-codes a path classifies as `project` regardless of what its frontmatter claims; the
frontmatter is an assertion and review checks whether it is true.

> **Terminology.** "Tier" is the skill classification. The build-out **stages** in `roadmap.md` are
> a different axis and use a different word on purpose. Do not merge the two vocabularies.

### Worked example: a `universal` skill

`skills/skill-authoring/` in this repository. Its procedure is writing a Markdown file, so it
assumes no toolchain and no layout. Its `## Preconditions` still does real work: it detects whether
`scripts/build_index.py` is present and states what to do when it is not — apply the hand checklist
and *say so* rather than reporting the skill as done.

That last clause is the part people skip. A fallback that silently degrades is worse than no
fallback, because the caller cannot tell which of the two paths ran.

### Worked example: lifting a skill from `project` to `domain`

Before — inadmissible, because it can only work in one repository:

```markdown
## Procedure
1. Open `apps/frontend/src/environments/environment.prod.ts`.
2. Update the `fhirBaseUrl` constant.
```

After — `domain` tier, because the layout is discovered and failure is handled:

```markdown
## Preconditions
Locate the environment configuration: search for a file matching `environment*.ts` under a
`src/environments/` directory anywhere in the repository. If exactly one matches, use it. If
several match, list them and ask which is the production configuration. If none matches, stop
and report that this project does not use the Angular environment-file convention — do not
create one.

## Procedure
1. Read the configuration file located above.
2. Update the `fhirBaseUrl` constant.
```

The rewrite is longer, and that length is the skill's portability. Note what the failure branch
does *not* do: it does not invent the file. A skill that creates the context it expected to find
has stopped being a skill and become a scaffolder.

## The four mandatory sections

| Section | Purpose |
| --- | --- |
| `## Preconditions` | How the skill detects the context it needs, and what to do when detection fails. |
| `## Procedure` | The steps. Prefer commands with exit codes over judgement calls. |
| `## Verification` | How the agent confirms the result is correct. |
| `## Scope and delimitation` | What this skill deliberately does not cover, and which skill does. |

`## Verification` is the one most often written badly. "Check that it looks right" is not a
verification criterion; it is a way of moving the problem to whoever reads the output. State an
observable: an exit code, a diff that must be empty, a file that must exist, a count that must
match.

## Descriptions

The full policy, with a good and a poor example, is in
`skills/skill-authoring/references/description-policy.md`. The short version:

1. State what the skill does **and** the situations that should trigger it.
2. Use the vocabulary a user would type, not the vocabulary you would file it under.
3. End with a delimitation clause: `Do not use for X; see <other-skill>.`
4. Avoid trigger vocabulary that overlaps a neighbouring skill —
   `scripts/check_descriptions.py` checks this mechanically.
5. Write it in English, including the foreign-language terms a user would actually type.

**Under-triggering is the common failure mode**, and it is silent: no error, just an agent doing
the work badly by hand. Be explicit rather than coy.

## Language: three independent axes

| Axis | Rule |
| --- | --- |
| **Metadata** — `name`, `description`, every `fgdh.*` value | Always English. The description is the surface agents match against, and it must be comparable across the catalog. |
| **Instructions** — the body, `references/` | English by default; another language when the domain artifacts are. Declared in `fgdh.language`. |
| **Output** — what the skill produces | Stated explicitly in the first sentence of `## Procedure` whenever it is not English. |

None of the three follows from another. An English-bodied skill can legitimately require German
output; a German-bodied skill can require English output. A reviewer who cannot find the output
sentence rejects the skill.

Foreign-language trigger terms go *inside* the English description (`Kerndatensatz`,
`Implementierungsleitfaden`). Writing the whole description in German buys nothing and costs
comparability with every other entry.

## Status mirroring

| Status | Description | Body |
| --- | --- | --- |
| `stable` | no mention | no mention |
| `experimental` | **no mention** | caution banner first |
| `deprecated` | **mandatory redirect clause** | deprecation banner first |

`experimental` stays out of the description because a caution must not suppress triggering: the
skill *should* activate, and the agent should then be told to verify its output. That instruction
only has to survive until activation.

`deprecated` must reach the description because the redirect has to arrive *before* the activation
decision. A deprecated skill that still triggers normally will still be followed — the warning
arrives after the choice was made.

Exact required wording is in `CONTRIBUTING.md`; CI matches it as a substring.

## Anti-patterns

**Absolute paths and upward `..` traversal.** The rule that decides whether a skill still works
after installation, and it fails silently — the agent follows a pointer to nothing and improvises.
Everything the skill needs lives inside the skill directory, referenced one level deep.

**A bare Markdown link that does not resolve.** Every relative link in `SKILL.md` *and* in bundled
`references/` must point at a file that exists — the validator checks both, because a broken
reference inside `references/` fails just as silently and only surfaces after installation.

Illustrative link *syntax* is different from a link, and must be written as such: put it in
backticks or a fenced block. `` `[Text](StructureDefinition-mii-pr-x.html)` `` is documentation
about links; `[Text](StructureDefinition-mii-pr-x.html)` is a promise that the file is there. The
validator strips code spans and fenced blocks before extracting links, precisely so that a skill
can document link syntax without being punished for it.

**Assuming a file exists.** See the tier model. "Open `config/settings.yaml`" is a `project`-tier
instruction wearing a `domain`-tier hat.

**Vague descriptions.** "Helps with X" is not a capability and matches everything in the domain
equally badly.

**A body that is really reference material.** If it is a table, a mapping, or a long enumeration,
it belongs in `references/` — the body is paid for on every activation.

**A skill that is really a wiki page.** The entry test is whether the body can be written as steps
with a verification criterion. A glossary or a link collection is not a skill, however useful.

**Instructing the agent to fetch and execute remote content.** Forbidden outright. A skill is
untrusted code until reviewed, and this pattern makes review meaningless because the content
reviewed is not the content that runs.

**Promoting to `stable` without running the trigger prompts.** Mechanical validity does not imply
the skill will ever be loaded. See Gate 3 in `lifecycle.md`.

## Before you open the pull request

```bash
python scripts/build_index.py          # regenerate index and catalog
python scripts/build_index.py --check  # exit 0 = committed artefacts in sync
python scripts/check_descriptions.py   # trigger-collision report
agentskills validate skills/<name>     # specification conformance
```

Commit `skills/index.json` and `CATALOG.md` in the same pull request as the skill, and add the
skill's `CODEOWNERS` line. CI regenerates both and fails if the tree moves.
