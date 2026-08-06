# One instance is not the class

A skill turns measurements into normative text. This page is the rule that governs that step, in
both of its directions, and the operational test that enforces it.

**The rule.** A measurement licenses a claim about the artefact it was taken on. Encoding it as
normative for a *class* of artefacts is a separate act, and it needs its own evidence.

| Direction | The mistake | How it fails |
| --- | --- | --- |
| **Negative** — "X cannot be done" | measured on one artefact, stated about the platform, the format or the tool | the capability is removed from the skill; a claim of impossibility is never re-checked, so the loss is permanent until somebody stumbles over the counter-example |
| **Positive** — "X has shape S" / "X is done this way" | measured on one instance, encoded as the shape every instance has | the skill produces plausible output on the instance it was measured on and silently wrong output everywhere else |

Only the first half of this used to be written down here. The second half is the one that has cost
this catalog more, and it is the harder of the two to notice: a false negative at least *stops*,
while a false positive keeps running and looks green.

## Why the first sample is the one that misleads you

Samples are not drawn at random. The first instance to hand is the reference module, the flagship
guide, the example in the documentation — the best-maintained, most regular member of its class, and
therefore the member *least* likely to exhibit a variant.

In all three defects below the single sample happened to be the benign one. That is not bad luck; it
is the normal case, and it is why the fix is not "measure twice" but "measure the instance most
likely to differ".

## The three defects this rule is made of

All three are from `mii-ig-migration`, all three were shipped, and all three were found by an
operator rather than by review.

| # | The claim | Sample it rested on | What a second instance showed |
| --- | --- | --- | --- |
| **a** | how IG page titles localize | first a constant in the publisher's source with **no build at all** (`TRANSLATION_SUPPLEMENT_RESOURCE_TYPES`), read as "page titles cannot be localized"; then **one** build, of one guide, on one publisher version (2.2.11) | a second build outside our own — the HL7 `multi-lang-test-ig` on publisher **2.0.13**, with `/fr/` deliberately declared in `i18n-lang` but left out of `translation-sources` as a controlled negative. The impossibility was simply false, and the mechanism is now stated bullet by bullet with its own basis each ("observed on our build" / "read from the source, not proven" / "corroborated outside it") |
| **b** | "Simplifier is client-rendered, so nothing is extractable" | the Simplifier **project** page — HTTP 200, ~56 KB, 52 script markers, no identity metadata in the DOM. A real measurement, and still true of that URL | the **guide** pages are server-rendered and hand their whole narrative to `curl`. The generalisation had cost the skill a working discovery procedure, and the skill told its readers to give up on the rendering |
| **c** | the guide-key attribute shape `data-url="/guide/<key>"` | the Consent project's guide listing, where **every** key happens to be bare, so an extractor anchored on the closing quote read 3 of 3 | preview and archived guides carry `data-url="/guide/<key>?version=current"`. Measured across all 23 MII modules: consent 3 of 3, **mikrobiologie 2 of 3, person 0 of 3** — keys dropped silently, at exit 0 |

Note what **b** and **c** have in common: both were measured on the same reference module, on the
same day, by the same person, and one is the negative direction while the other is the positive.
The direction is not the diagnosis. The sample size is.

## The operational test

Before encoding a shape or a capability as normative:

1. **Name the class the claim is about.** "Simplifier", "every MII module", "the IG Publisher" —
   write it down. A claim whose class is left implicit is generalised by the reader, not by you.
2. **Measure it on more than one instance.** One instance is a hypothesis. Two is a rule only if the
   second was chosen to break the first.
3. **Choose the second instance to be the one most likely to differ**, not the next one to hand:
   - a different member of the class, never another page of the same artefact;
   - the irregular one — the oldest, the newest, the largest, the one with the odd history, the one
     nobody maintains;
   - where the class is enumerable and small, **all of it**. Twenty-three modules is a `for` loop,
     and it is what turned defect **c** from "works" into "drops 1 of 3 keys on two modules".
   - best of all, a **controlled negative**: an instance where the mechanism is expected *not* to
     work. If it works there too, the mechanism is not the one you think it is. Defect **a**'s repair
     is trustworthy because `/fr/` was misconfigured on purpose and duly failed to localize.
4. **Record the sample with the claim** — which instances, which versions, which date, which
   numbers. A claim carrying its own sample can be re-scoped later; one that does not has to be
   re-derived from scratch.
5. **When only one instance is available, say so and bound the claim to it.** Write it about that
   artefact, mark the generalisation as unverified, and leave it as a review item. Never widen it
   silently because widening reads better.

## Writing it down

- **Bound each statement to its own evidence, and never lend one statement's evidence to another.**
  The pattern that survived review is a bulleted mechanism where every bullet names its own basis:
  *observed on our build* / *read from the source, not proven by a build* / *not observed, do not
  claim*.
- **Record which URL returned what**, not the conclusion you drew from it. `repo-identity.sh` now
  reports `client-rendered-page:` **scoped to the URL it probed**, rather than reporting a property
  of the platform.
- **An exit code is not evidence of completeness; the counts are.** Defect **c** exited 0 on every
  one of the 23 modules. What exposed it was comparing extracted keys against keys present.
- A claim that turns out to be wrong is **retired in the text, with its date and its measurement**,
  not quietly deleted — otherwise the next author re-derives it from the same single sample.

## Checklist

- [ ] the class the claim is about is named in the claim
- [ ] the claim was measured on **more than one** instance, or is explicitly bounded to the one
- [ ] the second instance was chosen as the one most likely to differ, and that choice is stated
- [ ] a controlled negative was tried where one exists
- [ ] each statement names its own basis; none borrows a neighbour's
- [ ] the sample — instances, versions, date, numbers — is recorded next to the claim
- [ ] a negative claim names the exact artefact and URL it was measured on
- [ ] completeness is claimed from counts, never from an exit code
