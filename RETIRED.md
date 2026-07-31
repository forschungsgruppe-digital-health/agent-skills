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

Nothing has been retired yet. That is a fact about this catalog, not a missing file — an empty
tombstone list is meaningful, while an absent one tells you nothing.

| Skill | Removed in | Reason | Successor |
| --- | --- | --- | --- |
| — | — | — | — |

<!--
When retiring a skill, replace the placeholder row (or add a row) in the form:

| `old-skill-name` | v2.0.0 | The target system was decommissioned. | `new-skill-name`, or "none" |

Record the version in which the directory was DELETED, not the one in which it was deprecated.
-->
