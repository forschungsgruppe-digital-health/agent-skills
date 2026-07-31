# Roadmap — Stage 2 and Stage 3

**Nothing on this page is implemented in this repository, and nothing on it is a dependency of
what is.** This repository is Stage 1: a Git repository with a generated index, and no runtime.
Everything below is a deliberately deferred option, recorded so that the trade-offs are available
when someone considers building it — not a plan, not a commitment, and not a description of
anything that exists today. Writing code from this page is a scope violation until the decision
in §12.5 has been recorded.

The section numbering is kept from the scaffold specification so that references to "§12.2" keep
resolving.

## 12.0 Why the stages exist

| Stage | What it is | Runtime to maintain | Reach |
| --- | --- | --- | --- |
| **1 (built)** | Git repository, generated `skills/index.json`, installation via CLI or sync workflow | none | any skills-compatible agent |
| **2** | Local MCP server started as a package (`npx`/`uvx`), reading the same index | none (runs on the user's machine) | additionally: MCP clients that do not implement the skills standard |
| **3** | Remote Streamable HTTP MCP server | a service someone must operate | additionally: clients that cannot spawn local processes; non-developer users |

The decisive asymmetry: Stage 1 keeps working with no owner. Stage 3 stops working the day nobody
pays the hosting bill. Cross that threshold only when a concrete client forces it, and record
which client it was.

## 12.1 Reference material (verify before relying on any of it)

All links were valid in July 2026. The MCP skills work is an **active proposal**, so re-check
status before building. Where a link contradicts this document, the link wins.

**Agent Skills standard**

- Specification: <https://agentskills.io/specification>
- Spec repository (Apache-2.0 code, CC-BY-4.0 docs): <https://github.com/agentskills/agentskills>
- Reference validator `skills-ref`: <https://github.com/agentskills/agentskills/tree/main/skills-ref>
- Client showcase (which tools support skills): <https://agentskills.io/clients>
- Documentation index for agents: <https://agentskills.io/llms.txt>
- Example skills: <https://github.com/anthropics/skills>

**Release tooling (already in use, listed here for completeness)**

- Release Please manifest releaser: <https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md>
- Customizing releases: <https://github.com/googleapis/release-please/blob/main/docs/customizing.md>
- Config schema: <https://github.com/googleapis/release-please/blob/main/schemas/config.json>
- GitHub Action: <https://github.com/googleapis/release-please-action>
- Conventional Commits: <https://www.conventionalcommits.org/>
- Semantic Versioning: <https://semver.org/>

**Skills over MCP (proposal)**

- SEP-2640, extension identifier `io.modelcontextprotocol/skills`:
  <https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2640>
- Working group charter: <https://modelcontextprotocol.io/community/skills-over-mcp/charter>
- Working group meeting notes:
  <https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/categories/meeting-notes-skills-over-mcp-wg>
- Plain-language summary of the proposal and its open questions:
  <https://aaif.io/blog/skills-over-mcp>
- MCP Resources primitive (the primitive the proposal builds on):
  <https://modelcontextprotocol.io/specification/2025-11-25/server/resources>

**Building and publishing MCP servers**

- Building servers with the help of skills, including transport selection and scaffolds:
  <https://modelcontextprotocol.io/docs/develop/build-with-agent-skills>
- Reference server implementations: <https://github.com/modelcontextprotocol/servers>
- Community registry (namespace verification, `mcp-publisher` CLI):
  <https://github.com/modelcontextprotocol/registry>
- How registry namespaces and trust work: <https://modelcontextprotocol.io/registry/about>

**Existing implementations worth reading before writing anything**

- Microsoft Agent Framework, MCP-hosted skills in .NET (`skill://index.json` discovery,
  `skill-md` and archive distribution modes):
  <https://devblogs.microsoft.com/agent-framework/discover-agent-skills-from-mcp-servers-in-net/>
- Agent Framework skills documentation: <https://learn.microsoft.com/en-us/agent-framework/agents/skills>

**Distribution and governance on the consuming side**

- Skills package manager / marketplace: <https://skills.sh>
- GitHub MCP Registry (discovery only; GitHub does not host or generate servers):
  <https://github.com/mcp>
- Configuring an organization or enterprise MCP registry:
  <https://docs.github.com/en/enterprise-cloud@latest/copilot/how-tos/administer-copilot/manage-mcp-usage/configure-mcp-registry>
- Claude Code plugin marketplaces (relevant only for the optional adapter in §12.4):
  <https://code.claude.com/docs/en/plugin-marketplaces>

## 12.2 Stage 2 — local MCP server as a package

**Trigger to build:** an MCP client in use that does not implement the Agent Skills standard, or
a wish to query the catalog without installing skills first.

**Shape.** A small server, distributed on npm or PyPI, started by the client as a subprocess
(`npx <pkg>` / `uvx <pkg>`) over stdio. It reads `skills/index.json` — from a local clone, from a
pinned release tag, or from the Pages URL — and serves the catalog. No hosting, no credentials,
no shared state.

**Interface: implement both, in this order.**

1. *Tools* — `list_skills(domain?, tier?)`, `search_skills(query)`, `get_skill(name)`,
   `get_skill_resource(name, path)`. Tools are universally supported by MCP clients today. This
   is the layer that will actually get used.
2. *Resources per SEP-2640* — expose each skill file under `skill://<name>/<path>` and the
   catalog as the well-known `skill://index.json`. Forward-looking; client support for the
   Resources primitive is still uneven, which is the proposal's own main open question.

Both layers read the same generated index. Neither becomes a second source of truth.

**Three findings from the working group that should shape the implementation:**

- Models frequently ignore an available skill and reach for tools directly. Adding a server
  instruction that tells the agent to read the relevant skill first measurably helped, but
  adherence declines as the context grows. Budget for this; do not assume discovery equals use.
- Trust is unresolved: whether a host should automatically trust skills delivered by a server,
  and whether users should see a skill's origin, is still open.
- Precedence between a server-provided skill and a locally defined one of the same name is
  unspecified. Until it is, encode precedence in the skill body itself — this is what the
  "Scope and delimitation" section of the template is for.

**Ranking.** Keyword matching (BM25 or simpler) over `name`, `description`, and
`fgdh.domain`. At catalog sizes below a few hundred skills, embeddings add operational
burden without changing outcomes, and the model makes the final selection anyway.

**Publishing.** The community registry verifies namespace ownership against the GitHub account or
domain, so the organization's namespace would be `io.github.forschungsgruppe-digital-health` — an
identifier actually owned rather than merely asserted. Publish with the `mcp-publisher` CLI from
the registry repository.

**Scripts caveat.** Skills that bundle executables under `scripts/` need those files on a
filesystem to run. A server that only hands back text serves instruction-only skills well;
anything executable needs an install step on the client side, or an archive distribution mode of
the kind the Microsoft implementation provides.

## 12.3 Stage 3 — remote Streamable HTTP server

**Trigger to build:** clients that cannot start local processes (web chat, non-developer users),
or a requirement for central usage telemetry and access control. Nothing else justifies it.

**Shape.** The same server as Stage 2 behind Streamable HTTP. Remote HTTP is the standard
recommendation for anything wrapping a remote source, since it removes installation friction and
one deployment serves everyone; published scaffolds cover Cloudflare Workers and portable
Express/FastMCP setups. If data residency matters, build a container in CI, publish to GHCR, and
run it on institutional infrastructure instead.

**Auth.** A public read-only catalog needs none. Introduce OAuth only if private skills are
added — at which point the catalog is no longer a public artifact and the sustainability argument
in §12.0 has to be re-made.

**Governance hooks that only exist at this stage.** An organization or enterprise MCP registry can
allowlist which servers Copilot may reach, and the equivalent for Claude Code is the strict
known-marketplaces setting in managed settings. Both are per-vendor; there is no neutral
equivalent, and that gap is the honest reason not to promise vendor neutrality above Stage 1.

**Exit condition.** Write down, at build time, what happens to the service at the end of the
funding period. If the answer is "it goes away", consumers must still be pinned to Git tags so
that its disappearance is an inconvenience rather than a breakage.

## 12.4 Optional side track — Claude Code plugin marketplace adapter

Independent of Stages 2 and 3, and cheap: generate `.claude-plugin/marketplace.json` from the same
index so Claude Code users can install through the native mechanism. Points to get right:

- Version resolution is `plugin.json` → marketplace entry → commit SHA. Set the version in
  **one** place only; a version present in `plugin.json` silently wins, and an unbumped value
  means users keep a cached copy.
- Omitting the version entirely makes every commit a new version — often the right choice for an
  internal catalog.
- The plugin `name` is the stable identifier. Renaming or removing without an append-only
  `renames` map produces `plugin-not-found` for existing users.
- Plugins are copied into a cache on install, so relative references outside the plugin root
  break; symlinks are the documented way to share content across plugin boundaries.
- Some names are reserved and re-checked on every load; verify the current list before choosing.
- `claude plugin validate .` is the vendor-specific gate, complementary to `skills-ref validate`.

Treat this as a generated adapter over `skills/index.json`. If it ever needs hand-editing, the
generator is wrong.

## 12.5 Decision record

When any of these is built, add an ADR under `docs/adr/` recording: the client or requirement
that forced the step, what was rejected, and the exit condition. A roadmap item implemented
without a recorded trigger is scope creep.
