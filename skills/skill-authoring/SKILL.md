---
name: skill-authoring
description: Writes a new Agent Skill for the FGDH catalog, or brings an existing one up to
  the catalog contract. Use this skill when adding a skill, filling in a SKILL.md, choosing
  between the universal and domain tier, writing or sharpening a description so it triggers
  reliably, setting the fgdh.tier / fgdh.domain / fgdh.owner / fgdh.language / fgdh.status
  metadata keys, splitting an over-long body into references, or fixing a validation error
  such as tier/rejected, name/directory, path/absolute or one of the mirror/ rules. Do not
  use for deciding whether a skill should exist at all, for retiring one, or for release
  mechanics; those are governance questions answered by the catalog's lifecycle document.
license: CC-BY-4.0
metadata:
  fgdh.tier: "universal"
  fgdh.domain: "skill-catalog"
  fgdh.owner: "@msusky"
  fgdh.language: "en"
  fgdh.status: "experimental"
---

# Authoring a skill for the FGDH catalog

> **Experimental.** This skill has not been verified against a real task since its last change. Verify its output before relying on it.

## Preconditions

This skill is pure convention. It needs no toolchain and makes no assumption about where
it is running, so it works whether you are authoring inside the catalog repository or
drafting a skill somewhere else.

Detect which of the two you are in, because it changes only the verification step:

- **Inside the catalog repository** — `scripts/build_index.py` exists at the repository
  root. The mechanical gate is available; use it, and treat its exit code as the answer.
- **Anywhere else** — no `scripts/build_index.py`. The checklist in *Verification* below
  is then the whole gate, and the skill is not finished until it has been opened as a pull
  request against the catalog and passed CI there. Say so explicitly rather than reporting
  the skill as done.

Do not attempt to install or fetch the validator when it is absent. Fall back to the
checklist and state that you did.

## Procedure

1. **Decide the tier before writing anything.** Classification has three outcomes and only
   two of them may be stored:

   | Classification | May assume | Stored as `fgdh.tier` |
   | --- | --- | --- |
   | `universal` | nothing — conventions, checklists, review procedures | `universal` |
   | `domain` | a toolchain exists; project layout is **discovered**, not assumed | `domain` |
   | `project` | specific files at specific paths | **never** — the skill belongs in the consuming repository |

   A skill drafted as `project` can usually be lifted to `domain` by replacing each
   hard-coded path with a discovery step plus an explicit failure branch. **That rewrite is
   the work.** It is what makes the skill survive installation into a repository nobody
   anticipated. If it genuinely cannot be lifted, stop and say so — do not change the value
   to get past the validator.

2. **Copy the template.** `templates/SKILL.md.template` in the catalog repository. The
   directory name and the `name:` field must be identical; the specification requires it.
   Replace every `<angle-bracket>` placeholder and delete the instructional comment.

3. **Write the description last, and write it as the triggering decision it is.** An agent
   sees only `name` and `description` before deciding whether to load the skill. The body
   arrives after that decision, so nothing in the body can rescue a description that does
   not match how people actually ask.

   Read [the description policy](references/description-policy.md) before writing it. The short form: say what the
   skill does *and* the situations that should trigger it, use the vocabulary a user would
   type rather than the vocabulary you would choose, and end with a delimitation clause
   naming the neighbouring skill (`Do not use for X; see <other-skill>.`).

   Under-triggering is the common failure mode. Be explicit rather than coy.

4. **Fill the four mandatory sections in order:** `## Preconditions`, `## Procedure`,
   `## Verification`, `## Scope and delimitation`. Prefer a command with an exit code over
   a judgement call at every step where one is possible.

4a. **Measure on more than one instance before writing anything down as normative.** A skill
    turns measurements into rules, and a measurement licenses a claim about the artefact it
    was taken on — nothing more. That cuts **both** ways: "X cannot be done here" must not
    become "X cannot be done", and "X has this shape here" must not become the shape every
    instance has. The positive direction is the dangerous one, because a false negative stops
    while a false shape keeps running and looks green.

    So: name the class the claim is about, measure a **second** instance chosen as the one
    most likely to differ (the irregular one, a controlled negative, or the whole set where it
    is small), and record the sample — instances, versions, date, numbers — beside the claim.
    Where only one instance is available, bound the claim to it and say the generalisation is
    unverified. The rule, the three shipped defects it is made of, and the checklist are in
    [the measurement rule](references/measurement-rule.md).

5. **Set the metadata.** `fgdh.tier`, `fgdh.domain` and `fgdh.owner` are required;
   `fgdh.language` and `fgdh.status` default to `en` and `stable`. All values are strings —
   quote anything YAML would coerce, and quote `"@handle"` because `@` is a reserved YAML
   indicator. The full registry with allowed values is in
   [the frontmatter contract](references/frontmatter-contract.md).

6. **Set `fgdh.status: "experimental"` and open the body with the banner.** A newly
   authored skill has not been exercised against a real task. The field alone is invisible
   to an agent, so the caution has to be mirrored where the agent will read it:

   ```markdown
   > **Experimental.** This skill has not been verified against a real task since its last change. Verify its output before relying on it.
   ```

   Put **no** warning in the description. Caution must not suppress triggering: the skill
   *should* activate, and the agent should then be told to verify its output. That
   instruction only has to survive until activation, so the body is the right place and the
   description stays a clean matching surface.

   Deprecation is the opposite case and the one exception — see
   [the frontmatter contract](references/frontmatter-contract.md).

7. **Keep `SKILL.md` under 500 lines and the body under roughly 5000 tokens.** The body is
   paid for on every activation; `references/` is paid for only when actually needed. Move
   tables, mappings and long procedures into `references/`, one level deep, referenced by a
   path relative to the skill root.

8. **Never write an absolute path, and never traverse upward with `..`.** Not in a link, not in a command.
   Everything the skill needs lives inside the skill directory. This is the rule that
   decides whether the skill still works after installation, and it fails silently when
   broken.

9. **Declare the language axes.** Metadata is always English. The body may be another
   language when the artifacts the skill operates on are — declare that in
   `fgdh.language`, and put the foreign-language terms a user would actually type inside
   the English description instead of translating the description. If the required *output*
   language is not English, say so in the first sentence of `## Procedure`; it does not
   follow from either of the other two axes.

10. **Write the trigger prompts.** Three to five realistic prompts that should activate the
    skill, phrased as a user would phrase them rather than as the description is phrased,
    plus two that should activate a neighbouring skill instead. Store them in
    [references/triggers.md](references/triggers.md). They are the evidence required to promote the skill from
    `experimental` to `stable`, and the next annual re-validation reuses them.

## Verification

Inside the catalog repository, in this order. The first two are the gate; the rest is what
a reviewer will check anyway, so checking it yourself is cheaper.

```bash
python scripts/build_index.py          # regenerates the index and the catalog
python scripts/build_index.py --check  # exit 0 means the committed artefacts are in sync
python scripts/check_descriptions.py   # trigger-collision report
```

`build_index.py` reports **all** violations at once, each naming the file and the rule.
Rule names are stable and greppable: `tier/rejected`, `name/directory`, `path/absolute`,
`path/traversal`, `path/depth`, `path/missing`, `mirror/experimental-banner`,
`mirror/deprecated-description`, `mirror/stale-experimental`. Fix the cause, not the check.

Commit `skills/index.json` and `CATALOG.md` in the same change as the skill. CI regenerates
both and fails if the working tree moves, so a skill whose generated artefacts were not
refreshed will not merge.

Outside the catalog repository, or if the validator is unavailable, confirm by hand:

- [ ] directory name equals `name`; lowercase, digits and single hyphens only, ≤ 64 chars
- [ ] description is 1–1024 characters, states what *and* when, ends with a delimitation clause
- [ ] `fgdh.tier` is `universal` or `domain` — never `project`
- [ ] `fgdh.domain` and `fgdh.owner` are set; `fgdh.owner` is quoted and starts with `@`
- [ ] status is `experimental` and the body opens with the banner; the description does not mention it
- [ ] all four mandatory sections are present, in order
- [ ] every normative claim about a class of artefacts was measured on more than one instance,
      or is explicitly bounded to the single one it was measured on; the sample is recorded
      beside the claim — see [the measurement rule](references/measurement-rule.md)
- [ ] `SKILL.md` is under 500 lines
- [ ] no absolute path, no upward `..` traversal, every relative reference exists and is one level deep
- [ ] bundled scripts are *referenced* relatively but *invoked* through a resolved `$SKILL_DIR`
- [ ] if `allowed-tools` is declared, every command the body instructs running — bundled scripts
      included — is covered by a grant (a bash script needs `Bash(bash:*)` + a `bash …`
      invocation, not `Bash(python3:*)`); see [the frontmatter contract](references/frontmatter-contract.md)
- [ ] `references/triggers.md` exists

## Scope and delimitation

This skill covers **writing the artefact**: the frontmatter contract, the tier decision,
the description, the body structure, and the mechanical checks that gate it.

It deliberately does not cover:

- **Whether a skill should exist**, who owns it, how it is reviewed, when it is
  re-validated, and how it is deprecated and removed. That is governance, and the catalog's
  `docs/lifecycle.md` is the normative answer.
- **Release mechanics** — which change is a MAJOR, MINOR or PATCH, and how a release is
  cut. See the catalog's `CONTRIBUTING.md`.
- **Any domain content.** This skill tells you how to shape a skill, never what to put in
  one. If you do not have source material for a domain, the correct output is a stub with
  `TODO(owner):` markers, not plausible-sounding instructions.

If a skill of the same name is provided both by this catalog and locally, the local one
wins: precedence between server-provided and locally-defined skills is unspecified
upstream, so it is stated here rather than left to the host.
