# Consuming skills from this catalog

Three integration paths, in increasing order of control and effort. All three are supported; pick
by how much you care about knowing exactly which version you are running.

| Path | One-sentence trade-off |
| --- | --- |
| [One-off `npx skills add`](#1-one-off-install) | Fastest way to try a skill, but nothing records what you installed or when. |
| [Pinned sync workflow](#2-pinned-sync-workflow) | Reproducible and reviewable, at the cost of one workflow file and a periodic pull request. |
| [Git submodule](#3-git-submodule) | Exact, auditable pinning with no tooling at all, at the cost of submodules being submodules. |

## Pin a ref. Do not track the default branch.

`main` is always releasable, but "releasable" is not "unchanged". A skill's procedure can move
under you between two runs of the same task, and the failure mode is an agent confidently doing
something slightly different from last week with nothing in your repository to explain why.

**How to pin depends on the tool, and the obvious syntax is a trap.**

| Form | Behaviour |
| --- | --- |
| `https://github.com/forschungsgruppe-digital-health/agent-skills/tree/<ref>` | **Pins.** `<ref>` may be a tag, branch or commit. |
| `forschungsgruppe-digital-health/agent-skills@<tag>` | **Does not pin.** In this CLI `@` introduces a *skill name*, not a version, and the install silently comes from the default branch. |

That second row was verified rather than assumed: installing from a tag whose commit contains no
skills at all reported "No skills found" for the tree-URL form and "Found 1 skill" for the `@`
form. If you take one thing from this page, take that one — it fails silently and looks like it
worked.

---

## 1. One-off install

List what is available, then install what you want:

```bash
npx skills add forschungsgruppe-digital-health/agent-skills --list

npx skills add https://github.com/forschungsgruppe-digital-health/agent-skills/tree/v0.1.0 \
  --skill skill-authoring \
  --agent claude-code codex \
  --yes
```

- `--list` / `-l` lists the skills in the repository without installing anything.
- `--skill` / `-s` selects skills by name; `'*'` means all.
- `--agent` / `-a` selects target agents; `'*'` means all.
- `--yes` / `-y` skips the confirmation prompts, which is what you want in CI.
- `--global` / `-g` installs at user level instead of into the project.
- `--copy` copies files instead of symlinking them from a canonical copy — use it where symlinks
  are not supported.

Installed skills are plain files. For Claude Code they land in `.claude/skills/` (or
`~/.claude/skills/` globally); for Codex, `.agents/skills/` (or `~/.codex/skills/`). Nothing is
hidden, and you can read exactly what an agent will read.

**Verify the round trip once**, especially the first time:

```bash
ls .claude/skills/skill-authoring/
head -20 .claude/skills/skill-authoring/SKILL.md   # frontmatter intact?
ls .claude/skills/skill-authoring/references/       # relative references still resolve?
```

The `references/` check is the one that matters. A skill whose relative references did not survive
installation fails silently: the agent reads `SKILL.md`, follows a pointer to a file that is not
there, and improvises.

## 2. Pinned sync workflow

For a repository that should track the catalog deliberately rather than accidentally. A scheduled
workflow reinstalls a pinned set of skills and opens a pull request when anything changed, so an
upgrade is a reviewable diff rather than a surprise.

The shape is small enough to write by hand: on `schedule` plus `workflow_dispatch`, run the
`npx skills add …/tree/<tag>` command from path 1 with `--yes`, then open a pull request if
`git status` is not clean. Three things belong in your own file rather than in a shared one — the
skill list, the pinned tag, and the target agent directories — because those are the decisions.

> A ready-made `templates/consumer/sync-skills.yml` is **not yet shipped** in this repository; it
> is a recorded follow-up rather than an omission. Until it lands, write the workflow yourself
> from the description above.

The point is not the automation — it is that the pinned tag lives in a file under review, and
moving it is a commit somebody approved.

You can also reuse the catalog's own validation, pinned to the same tag:

```yaml
jobs:
  validate-skills:
    uses: forschungsgruppe-digital-health/agent-skills/.github/workflows/validate-reusable.yml@v0.1.0
    with:
      skills-path: .claude/skills
      catalog-ref: v0.1.0
```

Pin `catalog-ref` to the tag you install from, so the rules that gate your repository are the rules
of the release you actually consume.

## 3. Git submodule

No tooling, maximum auditability. The submodule pointer is a commit SHA in your tree, so "which
version are we on" is answered by `git`.

```bash
git submodule add https://github.com/forschungsgruppe-digital-health/agent-skills.git vendor/agent-skills
git -C vendor/agent-skills checkout v0.1.0
git add vendor/agent-skills && git commit -m "chore: pin agent-skills to v0.1.0"
```

Point your agent at `vendor/agent-skills/skills/`, or symlink the individual skills you want into
the directory your agent reads. Upgrading is `git -C vendor/agent-skills checkout <newtag>` plus a
commit — visible in review, trivial to revert.

The cost is the usual submodule cost: fresh clones need `--recurse-submodules`, and people forget.

---

## Recovery

"Pin to a tag" only helps if you know what to do when a tag turns out to be bad.

### Go back to the previous tag

**The operation is a re-install, not a rollback.** Installed skills are plain files with no state
and no migrations, so the previous version simply overwrites the current one:

```bash
npx skills add https://github.com/forschungsgruppe-digital-health/agent-skills/tree/v0.1.0 \
  --skill skill-authoring --agent claude-code --yes
```

For a submodule, `git -C vendor/agent-skills checkout v0.1.0`. For the sync workflow, change the
pinned tag back and let the workflow run.

There is no uninstall step and nothing to clean up first. If a skill was *removed* between the two
tags, re-installing the older tag brings it back.

### Work out what actually changed

- **`CHANGELOG.md`** — generated by Release Please from the commit history. Each release names the
  skills added, the skills deprecated with their successors and earliest removal release, the
  skills removed, and any change to the `fgdh.*` registry or the index schema. A reader who sees
  only the changelog should be able to decide whether upgrading is safe.
- **`RETIRED.md`** — the tombstone list. If a skill is simply gone, this says when it was removed,
  why, and what replaced it. Retired names are never reused, so a name means one thing forever.
- **`CATALOG.md`** at each tag — the full state of the catalog at that release, generated from the
  skills themselves rather than maintained by hand.

### A skill that vanished without warning is a defect

Removal is a **two-release** process, and this is a promise rather than an aspiration:

1. Release *n* marks the skill `deprecated`, sets its successor, and adds a redirect clause to its
   description — so an agent that would have activated it is told where to go instead. The skill
   still works.
2. Release *n+m* removes the directory, no sooner than one release and thirty days later.

So if you upgrade and find a skill missing with no prior deprecation,
[open an issue](https://github.com/forschungsgruppe-digital-health/agent-skills/issues). That is a
process failure on our side, not expected behaviour, and it is worth reporting even if you have
already worked around it.

### If this repository stops being maintained

It keeps working. There is no server, no account, and no service to expire: a Git repository with a
generated index survives the end of any funding period, and every tag you have pinned stays exactly
as it was. The content is permissively licensed (Apache-2.0 for code, CC-BY-4.0 for documentation
and skill prose), so a fork may continue the catalog. Pinning tags is what makes that a
continuation rather than a migration.
