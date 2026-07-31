# Retired skills

The tombstone list. Every skill ever removed from this catalog is recorded here, permanently.

**Why this file exists.** Consumers pin by skill *name*. When a name disappears, the question
"was it renamed, was it merged into something else, or did it just break?" has to be answerable
without reading Git history — and it has to stay answerable years later, by someone who was not
here. A missing entry in a changelog is invisible; a missing skill with a tombstone is a lookup.

**Names are never reused.** The point of a catalog is that a name means one thing forever. A
retired name is retired: pointing it at a different skill later would silently give every pinned
consumer something they did not ask for, in the one place where they were being careful.

**Removal is a two-release process** (`lifecycle.md` §3.2). A skill is first marked `deprecated`
with a successor and a redirect clause in its description — that is a MINOR release, and the skill
still works. It is removed no sooner than one release and thirty days later, and that removal is a
MAJOR release. A skill that vanished without a prior deprecation is a defect worth reporting, not
expected behaviour.

## Tombstones

Both entries below were **renamed, not withdrawn**, under the narrow pre-first-consumer exception in
`CONTRIBUTING.md` — they existed only in `v0.4.0` and nothing had installed them. They are
tombstoned anyway, because the rule that a name means one thing forever does not depend on whether a
deprecation period was served.

| Skill | Removed in | Reason | Successor |
| --- | --- | --- | --- |
| `fhir-ig-analyze` | v0.5.0 | Renamed for a consistent naming scheme: nominal action form. | `fhir-ig-analysis` |
| `fhir-ig-translate` | v0.5.0 | Renamed for a consistent naming scheme, and the skill was generalised from one language pair to any, which is what earns its `fhir-` prefix. | `fhir-ig-translation` |

<!--
When retiring a skill, replace the placeholder row (or add a row) in the form:

| `old-skill-name` | v2.0.0 | The target system was decommissioned. | `new-skill-name`, or "none" |

Record the version in which the directory was DELETED, not the one in which it was deprecated.
-->
