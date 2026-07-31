<!--
The pull request TITLE becomes the commit message on main, because merges are
squash merges. It must be a Conventional Commit; CI checks it.
-->

## What and why

<!-- One paragraph. What changes, and what problem it solves. -->

## Change classification

Pick one. It determines the release, so it is not a formality — see the
MAJOR/MINOR/PATCH table in `CONTRIBUTING.md`.

- [ ] **Editorial** — typos, wording, formatting. No change to what any skill does. → `fix:` / `docs:` → PATCH
- [ ] **Substantive** — a procedure changed, a step added, a reference file added. → `feat:` → MINOR
- [ ] **Contract** — a skill added, a metadata key added, a skill marked deprecated. → `feat:` → MINOR
- [ ] **Breaking** — a skill removed or renamed, a metadata key removed or its values narrowed, an incompatible index-schema change, preconditions widened so previously working invocations fail. → `feat!:` / `BREAKING CHANGE:` → MAJOR

A description edit is editorial **only** if it does not change the set of
situations that trigger the skill. If the trigger surface moved, it is
substantive — that is what consumers actually experience.

## Tier decision

<!-- Required when this pull request adds or reworks a skill. A written
     decision, not a checkbox: say why, in one or two sentences. Delete this
     section if no skill changed. -->

Tier: `universal` / `domain` — because …

## Review checklist

From `docs/lifecycle.md` section 4.2. The reviewer checks what a script cannot.

- [ ] **Tier decision** is correct and written down above.
- [ ] **Preconditions** genuinely detect rather than assume, and the failure branch is explicit.
- [ ] **Verification** states an observable criterion — an exit code or a diff, not "check that it looks right".
- [ ] **Delimitation** names the neighbouring skills accurately.
- [ ] **Description** describes the situations a real user would be in, in their vocabulary — English, including the foreign-language terms they would actually type.
- [ ] **Language** — `fgdh.language` present and correct if the body is not English; the required output language stated in the first sentence of `## Procedure` where it is not English.
- [ ] **Status is mirrored where an agent can see it** — a deprecated skill carries the redirect in its description; an experimental one carries the caution banner in its body and *no* warning in its description. A status recorded only in metadata changes nothing an agent does.
- [ ] **Scripts** — if `scripts/` is present, every line was read. A skill is untrusted code until reviewed; no exceptions for "it's just a wrapper".
- [ ] **Provenance and license** present for imported material, naming the source repository, path and commit SHA.
- [ ] **Generated artefacts** (`skills/index.json`, `CATALOG.md`) regenerated and committed in this pull request.

## Verification run

<!-- Paste the commands and their output. "CI is green" is not the same claim. -->

```text
python scripts/build_index.py --check
python scripts/check_descriptions.py
```
