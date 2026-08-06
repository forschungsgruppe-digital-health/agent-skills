# Migration report — {MODULE} → MII KDS module template

<!-- TEMPLATE for migration-log/migration-report.md (SKILL.md step 8). Copy, then replace every
     {curly} value. A section that would be empty says "none" — never delete it: an absent
     section is indistinguishable from a forgotten one. Keep the L0 box under 8 lines.
     The three QUEUES are the point of this report: every reviewer action lands in exactly
     one of them, each row names a concrete next step and who takes it. A report that only
     narrates what happened has failed its job. -->

## L0 — Read this first (for everyone)

This module was moved from {source platform, e.g. Simplifier} onto the MII KDS module template.
**State:** {complete through build | stopped at {step} because {reason}}.
**Build:** sushi {n} errors · qa {errors}/{warnings}/{broken links} · preview: {URL | none}.
**Verification (spec §11):** `verify-migration.py` exit **{0 | 1 | 3}** — {n} IDENTISCH · {n}
DIVERGIERT · {n} NICHT PRÜFBAR. Exit 3 means *incomplete*, not passed.
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

**Narrative source (spec §5.1d):** {the repository's own pages | the authenticated project download
| the guide harvest | none — escalated}. For a harvest, take the numbers from
`migration-log/guide-harvest.tsv`, not from memory: **{n} discovered, {n} harvested, {n} skipped**
({n} narrative, {n} artefact-view), guide version `{version}`. Every skipped page is a row below
with its reason. **A template page whose content is still the template's starter text is a GAP, not
a migrated page** — say so here rather than letting the build's green tick imply otherwise.

**The machine-readable form of this table is `migration-log/page-map.tsv`** (`source_page` →
`target_page` or `RETIRED` + reason), which spec §11.2's C3 check reads: a page in neither is
reported MISSING. Keep the two consistent — the ledger is the one that is checked.

| Source page | Target page | Anything lost? |
|---|---|---|
| {page} | {page or "— retired: {reason}"} | {none \| description} |
| {harvested page, skipped} | — | **not harvested: {reason from the manifest}** |

**Template pages without source content (kept as stubs — gaps, not errors):** {list | none}.
**Source files retained for Gate-D retirement (listed, not removed):** {list}.

## Identity (what makes this module *this* module — verified unchanged)

| Field | Value | Same as source? |
|---|---|---|
| id / packageId / canonical / version / status / licence / publisher / dependencies | {…} | {yes \| DIVERGES → D{n}} |

### Where each value came from (generated — do not retype)

<!-- `bash "$ML" claims --markdown` (spec §2.1.4) prints this from
     migration-log/identity-claims.tsv: one row per field PER SOURCE, with the tier letter, and
     contradictions flagged. A field carrying two distinct values is a ① decision, never a pick
     made here. Tiers: C sushi-config · P published package · J package.json · I generated IG ·
     R source repository · H rendered guide (human-read) · T template default · G goFSH (never
     identity). Recovered is not applied: nothing in the repository was rewritten from these. -->

| Field | Tier | Source | Value | Contradiction |
|---|---|---|---|---|
| {field} | {P} | {package/package.json} | {value} | {— \| YES — Gate A} |

**Still unrecovered after every tier (a human supplies these):** {list, e.g. publisher | none}.
**Parent packages missing snapshots (spec §5.1b.5):** {package@version — n of m SDs carry none,
rebuilt as `{id}#{version}-snapshots`, SUSHI {before} → {after} errors | none}; **how the rebuild
reaches CI:** {CI prebuild step | vendored | internal registry | not repinned, profiles stay
blocked} → D{n}.

## Verification (generated — paste `migration-log/verification.md`, do not retype)

<!-- The four layers plus the run log as a second oracle (spec §11). This block is GENERATED by
     scripts/verify-migration.py; §10.6's rule applies to it as much as to the protocol section.
     Three verdicts, and the third is the point: NICHT PRÜFBAR is not a pass, so every such row
     owes queue ① a human action and a gate. Every DIVERGIERT row is queued too — ① when it is a
     decision, ③ when it is a build/QA finding. A verification section with no `11 verify-migration`
     line behind it in run.log is claiming something that did not happen. -->

**Exit status:** {0 = clean | 1 = at least one DIVERGIERT | 3 = incomplete: a check could not be
mechanised}. **Inputs:** target · source `{path | — not supplied, which is itself a finding}` ·
rendered `{output | — not built}` · log.

| Layer | Check | IDENTISCH | DIVERGIERT | NICHT PRÜFBAR |
|---|---|---|---|---|
| conservation | C1 present · C2 **reachable** · C3 pages · C4 text runs | {n} | {n} | {n} |
| fidelity | F1 identity · F2 pins · F3 licence · F4 FSH residue | {n} | {n} | {n} |
| provenance | P1 rendered template · P2 vendored ref · P3 publisher · P4 guide pin | {n} | {n} | {n} |
| rendering | R1 views · R2 header · R3 language parity · R4 example links · R5 titles | {n} | {n} | {n} |
| run log (2nd oracle) | L0 exists · L1 unactioned WARN · L2 silent step · L3 contradiction · L4 cross-checks | {n} | {n} | {n} |

**DIVERGIERT — each row, its evidence and its queue:** {paste the generated table | none}.
**NICHT PRÜFBAR — not a pass; who does what, at which gate:** {paste the generated table | none}.

## Auto-fix (spec §12 — only if the loop ran)

<!-- From migration-log/autofix.tsv. If the loop did not run, say "not run" — an absent table is
     indistinguishable from a forgotten one. Every row is individually revertible from the snapshot
     beside it in migration-log/autofix/iter<N>/<finding>/before.tar. -->

**Loop:** {not run | {n} iterations of at most 3, stopped by {clean | no fixable findings |
no-progress | the ceiling}}. **Allowlist offered:** {classes} — everything else was excluded by
construction (identity, narrative, a source defect, a judgement call).

| # | Finding | Class | What changed | Why it is auto-fixable | Cleared? |
|---|---|---|---|---|---|
| {1} | `{id}` | {class} | {files} | {mechanical · reversible · confirmed by check {X}} | {yes \| REVERTED → ①} |

**Reverted or refused fixes are findings, not footnotes:** each one is a ① row below. A fix whose
finding did not clear was undone deliberately — a half-fix is an unexplained change attached to an
unsolved problem.

## Protocol (what was executed — for auditors; keep last)

<!-- GENERATED FROM `migration-log/run.log` (spec §10.6). Do NOT write this from recollection:
     every claim here traces to a log line, and where the two disagree the log is right. A claim
     with no line behind it is a defect — re-run the step, do not add the sentence.
     Structure: the log grouped by step, in step order, each group with its acceptance verdict.
     Tool versions, pins and the goFSH `-d` set are read out of the `cmd=` tokens, never restated
     from memory. Every WARN and ERROR in the log must also appear in one of the queues above —
     a WARN that reaches nobody is the failure mode this section exists to prevent. -->

| Step | What ran (`cmd=` from the log) | Measured outcome | Raw log | WARN/ERROR → queue | Acceptance |
|---|---|---|---|---|---|
| {5.1b.2} | `{the actual command line}` | {counts, exit code} | `migration-log/{action}.log` | {n} → {①②③ \| none} | met \| met-as-qualified (spec §5.1b.4) \| NOT met |

**Log:** `migration-log/run.log` — {n} lines, {n} WARN, {n} ERROR, {n} runs, all accounted for above.
Take those numbers from the log itself, not from memory: `wc -l`,
`grep -c '  WARN   ' migration-log/run.log`, `grep -c '  ERROR  ' migration-log/run.log`,
`grep -c '  run-boundary  ' migration-log/run.log`. More than one run means the block was repeated;
report the LAST run's numbers and say the earlier ones exist.
**Silent-partial-success WARNs:** {list | none}
(`grep -F 'silent-partial-success:' migration-log/run.log`).
**Other WARN classes, each with its queue:** `anticipated-nonzero-exit:` (the shape-B `sushi-after`
escalation → ①, one entry per residual error), `exit-status-truncated:` / `exit-status-disagrees:`
(believe the printed error count, not the status), `stale-raw-log:`, `count-above-expected:`,
`identity-contradiction:` (→ ①, one row per contradicting field, §2.1.4),
`not-in-a-package-manifest:` / `not-recoverable-from-a-repository:` / `license-text-unrecognized:`
(→ ①, the fields a human still supplies), `client-rendered-page:` (→ ②, read **that** page by hand —
it is the PROJECT page; the `/guide/` space is server-rendered, is discovered by §5.1c and is
harvested by §5.1d),
`unpinned-guide-version:` / `page-unreachable:` / `content-region-absent:` /
`project-download-unavailable:` (→ ②, the narrative harvest's own gaps — one entry per skipped page),
`generated-view-lossy:` (→ ③, a rendered artefact view the IG Publisher regenerates anyway),
`parent-without-snapshots:` / `generator-refused:` / `snapshot-implausible:` (→ ①, §5.1b.5),
`verification-divergence:` (→ ① or ③, one entry per DIVERGIERT row, §11) / `not-mechanisable:`
(→ ①, one entry per NICHT PRÜFBAR row — the class that must never be read as a pass),
`autofix-reverted:` / `autofix-refused:` / `autofix-no-progress:` / `autofix-ceiling:` (→ ①, §12 —
what the loop declined to leave behind).
**Deviations from the skill or the template, with justification:** {list | none}.

## Mini-glossary (novices start here)

- **canonical** — the module's permanent identifying URL; changing it breaks everyone who uses it.
- **qa.txt / qa.html** — the IG Publisher's validation report; errors block a release, warnings
  need judgement, "broken links" are unresolved references in the rendered site.
- **Gate A–D** — the four human sign-offs: identity (A) → narrative (B) → language (C) →
  release governance (D). The agent never passes a gate itself.
- **TODO:REVIEW** — an in-tree marker meaning "a human must look here"; queue ② lists them all.
- **Logical model / profile** — the dataset described abstractly vs. its concrete FHIR shape.
- **Run log** — `migration-log/run.log`, the timestamped record of every step, the command it ran
  and what that command measurably produced. The Protocol section above is generated from it, so
  the report cannot claim something the run did not do.
- **The two oracles** — the run log records what each step *intended and measured*; the target tree
  records the *outcome*. The verification phase reads both, because a class of defect exists only in
  the gap between them (the log says 20 converted, the tree holds 19).
- **IDENTISCH / DIVERGIERT / NICHT PRÜFBAR** — the three verification verdicts: matches · differs,
  named · could not be checked. The third is **not** a pass; it is a job for a named human.
