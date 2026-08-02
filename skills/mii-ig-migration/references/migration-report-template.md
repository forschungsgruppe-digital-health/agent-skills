# Migration report — {MODULE} → MII KDS module template

<!-- TEMPLATE for .ai-log/migration-report.md (SKILL.md step 8). Copy, then replace every
     {curly} value. A section that would be empty says "none" — never delete it: an absent
     section is indistinguishable from a forgotten one. Keep the L0 box under 8 lines.
     The three QUEUES are the point of this report: every reviewer action lands in exactly
     one of them, each row names a concrete next step and who takes it. A report that only
     narrates what happened has failed its job. -->

## L0 — Read this first (for everyone)

This module was moved from {source platform, e.g. Simplifier} onto the MII KDS module template.
**State:** {complete through build | stopped at {step} because {reason}}.
**Build:** sushi {n} errors · qa {errors}/{warnings}/{broken links} · preview: {URL | none}.
**Your job as reviewer:** work the three queues below in order — ① decide, ② review, ③ triage.
Nothing is published until Gate D (a human merge decision); everything here is reversible.

## ① Decision queue (Gate A — someone must choose)

<!-- One row per open decision. "Default applied" = what the migration did in the meantime;
     it is a placeholder, not a recommendation. Consequences in one clause each. -->

| # | Decision | Options (with consequence) | Default applied | Decide at |
|---|---|---|---|---|
| D1 | canonical | keep `{source}` (consumers keep resolving) \| adopt template pattern (breaks every consumer) | kept source | Gate A |
| D2 | licence | keep `{source}` \| adopt template `{value}` (relicenses published content) | kept source | Gate A |
| D3 | {…} | | | |

## ② Review queue (Gates B/C — someone must check)

<!-- Group the in-tree TODO:REVIEW markers into reviewable units; never paste the raw grep.
     Typical groups: machine-translated pages (C), section-mapping homes (B), replaced live
     tables (B), image/link substitutions (B), governance dates (D). -->

| Where | What to check | Suggested action | Gate |
|---|---|---|---|
| `input/pagecontent/{page}.md` | machine translation vs the German original | correct wording, remove the marker | C |
| {…} | | | |

## ③ QA triage (what the build says, and whose problem it is)

<!-- Provenance requires PROOF: "pre-existing" means you built the unmigrated source and saw
     the same finding; "environment" names the missing prerequisite. Anything you cannot
     prove is "unclassified" and stays in the queue. -->

| Finding (shortened) | Count | Provenance (proof) | Next action |
|---|---|---|---|
| {qa error text} | {n} | pre-existing (baseline build) \| migration-induced \| environment: {what} \| unclassified | {fix \| accept \| escalate to maintainers} |

## Content map (where every source page went)

<!-- "Anything lost?" is the honest column: name RENDERING losses (e.g. a live query table
     that became a static pointer) even when the underlying data survives in the resources. -->

| Source page | Target page | Anything lost? |
|---|---|---|
| {page} | {page or "— retired: {reason}"} | {none \| description} |

**Template pages without source content (kept as stubs — gaps, not errors):** {list | none}.
**Source files retained for Gate-D retirement (listed, not removed):** {list}.

## Identity (what makes this module *this* module — verified unchanged)

| Field | Value | Same as source? |
|---|---|---|
| id / packageId / canonical / version / status / licence / publisher / dependencies | {…} | {yes \| DIVERGES → D{n}} |

## Protocol (what was executed — for auditors; keep last)

{step-by-step run log: tool versions and pins, preconditions results, per-step outcomes,
deviations from the skill or template with their justification}

## Mini-glossary (novices start here)

- **canonical** — the module's permanent identifying URL; changing it breaks everyone who uses it.
- **qa.txt / qa.html** — the IG Publisher's validation report; errors block a release, warnings
  need judgement, "broken links" are unresolved references in the rendered site.
- **Gate A–D** — the four human sign-offs: identity (A) → narrative (B) → language (C) →
  release governance (D). The agent never passes a gate itself.
- **TODO:REVIEW** — an in-tree marker meaning "a human must look here"; queue ② lists them all.
- **Logical model / profile** — the dataset described abstractly vs. its concrete FHIR shape.
