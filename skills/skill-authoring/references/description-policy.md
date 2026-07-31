# The description policy

The description is the only text an agent sees before deciding to load a skill. It
therefore carries the entire triggering decision, and nothing in the body can rescue a
description that does not match how people actually ask.

Treat it as the skill's interface, not its summary.

## What a description must do

1. **State what the skill does** — the capability, in one clause.
2. **State when to use it** — the concrete situations that should trigger it, using
   keywords a user would plausibly type. Not the situations as you would categorize them:
   the situations as they arrive.
3. **End with a delimitation clause** naming what the skill does *not* cover, and which
   neighbouring skill covers it: `Do not use for X; see <other-skill>.` Omit the clause only
   when no neighbouring skill exists yet, and add it in the pull request that adds one.
4. **Avoid trigger vocabulary that overlaps another skill** in the catalog.
   `scripts/check_descriptions.py` checks this mechanically.
5. **Be English**, while naming the foreign-language terms a user would actually type when
   the domain is not English-speaking.

## Be explicit about triggering

**Under-triggering is the common failure mode.** A skill that never activates is
indistinguishable from a skill that does not exist, and the failure is silent: no error, no
log line, just an agent doing the work badly by hand.

This is not hypothetical. The Skills-over-MCP working group reported that models frequently
ignored an available skill and reached for tools directly, sometimes failing several times
before eventually finding it; adding an explicit instruction to consult the skill first
helped, but adherence declined as the context grew
(<https://aaif.io/blog/skills-over-mcp>).

So err toward naming more trigger situations rather than fewer, and prefer the user's words
to yours. Being coy costs activations; being explicit costs a few characters of the 1024
available.

## Worked examples

### Poor

```yaml
description: Helps with implementation guides.
```

Everything is wrong with this in the same way: it says what the author was thinking about,
not what the user will be doing. "Helps with" is not a capability. "Implementation guides"
matches every request in the domain and none of them well. There is no trigger situation,
no vocabulary a user would type, and no delimitation — so it competes with every
neighbouring skill for every request.

### Good

```yaml
description: Migrates a FHIR Implementation Guide project onto the MII KDS module template —
  rewrites sushi-config.yaml, the IG template reference and the page structure, then verifies
  the build. Use this skill when moving an existing IG to the module template, when a build
  fails after a template bump, or when the user mentions Kerndatensatz, KDS-Modul,
  Implementierungsleitfaden, sushi-config, ig.ini or the IG Publisher. Do not use for
  authoring new profiles or for translating page content; see fhir-profiling and ig-translate.
```

What makes it work:

- **A capability, then its parts.** "Migrates … onto the MII KDS module template" is one
  clause; the three concrete artefacts it touches follow.
- **Three distinct trigger situations**, one of which ("a build fails after a template
  bump") is how the need usually *presents* rather than how it would be filed.
- **The user's vocabulary, including German terms**, inside an English description. A user
  types `Kerndatensatz`, not "core data set". Translating the description into German would
  buy nothing and would cost comparability with every other entry in the catalog.
- **A delimitation clause** naming two real neighbours, so the overlap between them is
  resolved in the descriptions rather than by chance.

## Mechanical overlap checking

```bash
python scripts/check_descriptions.py
python scripts/check_descriptions.py --warn 0.30 --fail 0.55
python scripts/check_descriptions.py --stopword fhir --stopword kerndatensatz
```

It tokenizes `name` + `description`, drops stopwords and tokens shorter than three
characters, and computes pairwise Jaccard similarity. It reports every pair at or above
`--warn` with the shared tokens listed, and exits 1 at or above `--fail`.

Two things to hold onto:

- **It is a deterministic heuristic, not a semantic judgement.** It finds descriptions that
  reuse each other's vocabulary. It cannot see that two differently worded skills answer the
  same question, and it will flag two genuinely distinct skills that happen to share jargon.
  A finding is a prompt to look, not a verdict.
- **The fix is usually both descriptions, not one.** If two skills compete, sharpen each to
  name the situations it is *for* and add a delimitation clause pointing at the other. If
  that turns out to be impossible, the honest answer is that they are one skill.

Domain jargon that legitimately appears everywhere in your catalog (`fhir`, `skill`,
`repository`) inflates every pair equally. Add those to a stopword file rather than raising
the threshold — raising the threshold hides real collisions too.

## Status and the description

Only one status ever reaches the description.

- `stable` — no mention.
- `experimental` — **no mention.** The caution goes in the body. Suppressing activation is
  precisely the wrong outcome: the skill should trigger, and the agent should then be told
  to verify its output.
- `deprecated` — **mandatory.** Append `Deprecated as of <version>; use <successor>
  instead.` The redirect has to reach the agent *before* it decides to activate, and the
  description is the only text that does.

See [the frontmatter contract](frontmatter-contract.md) for the exact required wording.

## Editorial or substantive?

A description edit is **editorial** only if it does not change the set of situations that
trigger the skill. If it changes the trigger surface, it is **substantive** — a `feat:`
commit and a MINOR release — because that is what consumers actually experience.

Rewording "Use when handling PDFs" to "Use when working with PDF documents" is editorial.
Adding "or when the user mentions forms" is substantive: a request that previously went
elsewhere now lands here.
