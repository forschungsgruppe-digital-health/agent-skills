# Trigger prompts for `skill-authoring`

Mechanical validity does not imply the skill will ever be loaded. These prompts are the
evidence for Gate 3 of the catalog lifecycle — the empirical check required before this
skill may be promoted from `experimental` to `stable` — and the next annual re-validation
reuses them rather than inventing new ones.

**Status: not yet run.** This skill has not been exercised against an agent with the catalog
installed, which is why `fgdh.status` is `experimental`. Running these prompts, recording
which activated, and attaching the result to a pull request is what unblocks promotion.

## How to run them

1. Install the catalog into a throwaway project so the agent sees this skill's `name` and
   `description` at startup and nothing more.
2. Issue each prompt in a fresh session. A prompt issued after the skill has already been
   discussed proves nothing.
3. Record whether the skill activated, without prompting for it.
4. If a should-trigger prompt fails, **the description is the defect, not the user.** Widen
   it and re-run the whole set.
5. If a should-not-trigger prompt activates this skill, the delimitation clause is too weak
   or the neighbouring skill's description is too narrow. Fix both sides.

## Should trigger

1. "I want to add a new skill to the FGDH catalog for checking BPMN models — where do I
   start?"
2. "CI is failing on my skill with `tier/rejected`. It says project tier is never a valid
   stored value. What am I supposed to do about that?"
3. "My skill never seems to get picked up by the agent even though it's installed. Can you
   look at how it's described?"
4. "This SKILL.md is 700 lines. How should I split it?"
5. "How do I mark a skill as not-yet-verified so people know to double-check its output?"

Number 2 and number 3 are the important ones. Both are how the need actually presents — an
error string and a symptom — rather than how it would be filed, and a description written
only for "I want to author a skill" will miss both.

## Should not trigger

1. "Should we retire the `ig-translate` skill? Nobody has touched it in a year and the
   owner has left." — governance, answered by the catalog's `docs/lifecycle.md`. This skill
   covers writing the artefact, not deciding whether it should exist.
2. "Migrate this Implementation Guide onto the new MII KDS module template." — a domain
   task for the `mii-ig-migration` skill. If `skill-authoring` activates here, its
   description is matching on `template` and needs sharpening.

## Recording a run

Append a dated block to this file. Keep the prompts stable across runs; changing them makes
two re-validations incomparable, which defeats the purpose of storing them.

```markdown
### Run YYYY-MM-DD — <agent and version>

| # | Prompt | Expected | Observed |
| --- | --- | --- | --- |
| S1 | … | trigger | trigger |
| N1 | … | no trigger | no trigger |

Outcome: promoted / revised / unchanged. Notes: …
```
