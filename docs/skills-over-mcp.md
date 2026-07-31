# Skills over MCP, and why this catalog is static

`skills/index.json` is shaped the way it is because of a proposal that has not been accepted yet.
This page explains what that proposal is, what is actually decided, and why the catalog
deliberately stops short of implementing any of it.

## What the proposal is

**SEP-2640, "Skills Extension"**, extension identifier `io.modelcontextprotocol/skills`, developed
in a working group under the Model Context Protocol project:
<https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2640>

**It is an active proposal, not a ratified standard.** As of 2026-07-31 the pull request is open
and unmerged against `main`, last updated 2026-07-27. Nothing in it is binding on anyone, and it
can still change shape or be rejected. Check the state before relying on any of this — the
scheduled watch in `.github/workflows/spec-watch.yml` exists precisely so that a change here
produces a tracking issue rather than a surprise.

Background:

- Working group charter: <https://modelcontextprotocol.io/community/skills-over-mcp/charter>
- Meeting notes:
  <https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/categories/meeting-notes-skills-over-mcp-wg>
- Plain-language summary of the proposal and its open questions:
  <https://aaif.io/blog/skills-over-mcp>

## How it works

The approach reuses the existing **Resources** primitive
(<https://modelcontextprotocol.io/specification/2025-11-25/server/resources>) rather than inventing
a new one. A server exposes skills under a `skill://` URI scheme, plus an optional well-known
catalog resource, `skill://index.json`, so a host can read lightweight metadata for every skill
instead of fetching every `SKILL.md` to find out what exists.

The skill *format* is untouched. It remains owned by the Agent Skills specification at
<https://agentskills.io/specification>. Skills over MCP is a transport and discovery question, not
a format question — which is why a static catalog and a future server can share one source of
truth without either being a translation of the other.

### `skill://index.json` is a resource URI, not a file path

Say this out loud because it reads like a path and is not one. There is no directory named
`skill:` in this repository and there never will be. The file at `skills/index.json` is the
**source** from which such a resource *would* be served if someone built a server; the `skill://`
strings inside it are identifiers, not locations.

Every entry in the generated index therefore carries both:

```json
{
  "url": "skill://skill-authoring/SKILL.md",
  "path": "skills/skill-authoring/SKILL.md"
}
```

`path` is what tooling needs today. `url` is what the extension would use. Emitting the second one
now costs nothing and means the file can back a server later without restructuring.

Note also that the `frontmatter` object in the index carries only `name` and `description` — a
faithful subset of what the open standard defines — while the organization's `fgdh.*` keys sit in a
sibling `metadata` object. That separation is deliberate: it keeps `frontmatter` standard-shaped, so
a consumer of the index never has to know which fields are ours.

## What is not settled

Stated as open, because they are:

- **Client support for Resources is uneven.** Tools are universally supported by MCP clients;
  Resources are not. A server that exposes skills only as resources may be talking to nobody.
- **Models often ignore available skills.** Early experiments in the working group found models
  reaching for tools directly instead of reading a relevant skill, sometimes failing repeatedly
  before finding it. An explicit server instruction to consult skills first helped measurably, but
  adherence declined as the context grew. Discovery is not use.
- **Trust is unresolved.** Whether a host should automatically trust skills delivered by a server,
  and whether a user should be shown a skill's origin, has no answer yet.
- **Precedence is unspecified.** If a server provides a skill with the same name as a locally
  defined one, nothing says which wins. Until something does, this catalog encodes precedence in
  the skill body itself — that is what the `## Scope and delimitation` section of every skill is
  for.

## Why this repository stays static

A Git repository with a generated index has **no runtime to maintain**. That is the whole argument,
and it is a sustainability argument rather than a technical one.

- It survives the end of any funding period. Nobody has to keep paying for anything, renew a
  certificate, or notice that a container stopped.
- Every tag a consumer pinned stays exactly as it was, forever, whether or not anyone is still
  maintaining the catalog.
- It works with any skills-compatible agent today, without waiting for a proposal to be ratified
  or for clients to implement it.
- And it can back a server later **without restructuring**, because the index is already the shape
  the extension proposes.

The alternative — building a server now — would mean operating a service to serve files that Git
already serves, in a format that is not final, to clients that mostly cannot consume it yet.

`docs/roadmap.md` records what Stage 2 (a local MCP server started as a package) and Stage 3 (a
remote server) would look like, what would trigger building them, and what each would cost. Both
are deferred, and a roadmap item implemented without a recorded trigger is scope creep.

## Prior art worth reading first

Microsoft's Agent Framework already implements MCP-hosted skill discovery in .NET, including
`skill://index.json` discovery and both `skill-md` and archive distribution modes:
<https://devblogs.microsoft.com/agent-framework/discover-agent-skills-from-mcp-servers-in-net/>

The archive mode is the interesting part for anyone who eventually builds Stage 2 here: a server
that hands back text serves instruction-only skills perfectly well, but a skill that bundles
executables under `scripts/` needs those files on a filesystem to run.
