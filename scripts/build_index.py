#!/usr/bin/env python3
"""Validate every skill and generate `skills/index.json` and `CATALOG.md`.

This is the catalog's Gate 1: pass or fail comes from an exit code, never from a
judgement. That property is what makes the gate trustworthy when the contributor
is an agent rather than a person.

Two properties are load-bearing and must survive any change to this file:

*   **Deterministic.** Running it twice produces byte-identical output. No
    timestamps, no hostnames, no absolute paths, no iteration over an unordered
    set. `--check` regenerates into memory and compares bytes, so any
    nondeterminism turns a clean tree into a spurious CI failure.
*   **Offline.** This script makes no network calls, on purpose. Owner
    resolution needs the GitHub API and therefore lives in
    `scripts/check_owners.py`, which runs weekly and reports rather than
    blocking. A merge must not depend on GitHub's availability or rate limits.

The `version` field of the index is **not** computed here. Release Please owns
it. This script reads the existing value and writes it back unchanged, which is
what keeps the drift test honest: regeneration reproduces the file byte for byte
including a version the builder never derived.

Usage:
    python scripts/build_index.py            # write outputs
    python scripts/build_index.py --check    # write nothing; exit 1 on drift
    python scripts/build_index.py --json     # violation report as JSON on stderr

    # Validate skills that live somewhere else -- a consuming repository with
    # the catalog installed into .claude/skills/, for example. Generation and
    # the drift check are catalog-specific and meaningless there, so this mode
    # validates and writes nothing.
    python scripts/build_index.py --skills-dir .claude/skills --validate-only

Exit codes:
    0  clean
    1  validation failure or drift
    2  internal error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.frontmatter import FrontmatterError, load  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
SKILLS_REL = "skills"
INDEX_PATH = SKILLS_DIR / "index.json"
CATALOG_PATH = REPO_ROOT / "CATALOG.md"


def configure(skills_dir: Path) -> None:
    """Point the builder at a different skills directory.

    Used by `--skills-dir` so the reusable validation workflow can check a
    consuming repository's installed skills. The generated-artefact paths follow
    the skills directory, but `--validate-only` is the only sensible mode there:
    a consumer has no committed index to drift against.
    """
    global SKILLS_DIR, SKILLS_REL, INDEX_PATH, CATALOG_PATH
    SKILLS_REL = skills_dir.as_posix().rstrip("/")
    SKILLS_DIR = skills_dir.resolve()
    INDEX_PATH = SKILLS_DIR / "index.json"
    CATALOG_PATH = SKILLS_DIR.parent / "CATALOG.md"

GENERATOR = "scripts/build_index.py"
SCHEMA_VERSION = "1"
FALLBACK_VERSION = "0.0.0"

PREFIX = "fgdh"

# --- The format contract (agentskills.io). Not ours to change. ----------------

SPEC_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
REQUIRED_SPEC_FIELDS = {"name", "description"}
NAME_MAX = 64
DESCRIPTION_MAX = 1024
COMPATIBILITY_MAX = 500
BODY_MAX_LINES = 500

# --- The catalog contract (ours). Documented in docs/metadata-keys.md. --------

TIER_KEY = f"{PREFIX}.tier"
DOMAIN_KEY = f"{PREFIX}.domain"
OWNER_KEY = f"{PREFIX}.owner"
LANGUAGE_KEY = f"{PREFIX}.language"
STATUS_KEY = f"{PREFIX}.status"
REPLACED_BY_KEY = f"{PREFIX}.replaced-by"

REQUIRED_META = (TIER_KEY, DOMAIN_KEY, OWNER_KEY)
KNOWN_META = (TIER_KEY, DOMAIN_KEY, OWNER_KEY, LANGUAGE_KEY, STATUS_KEY, REPLACED_BY_KEY)

# `project` is a classification outcome, never a stored value: such a skill
# belongs in the consuming repository. See docs/authoring-skills.md.
TIERS = ("universal", "domain")
REJECTED_TIER = "project"
STATUSES = ("stable", "experimental", "deprecated")
DEFAULT_STATUS = "stable"
DEFAULT_LANGUAGE = "en"

# --- Status mirroring (the fixed wording CI matches as a substring) -----------
#
# An agent sees only `name` and `description` before deciding to activate a
# skill, and the body only afterwards. Everything under `fgdh.*` is invisible to
# it. So any status that must change what an agent DOES has to be mirrored into
# text the agent actually reads -- and the mirror has to be enforced here, or it
# drifts from the field it mirrors at exactly the release where it matters.

EXPERIMENTAL_BANNER = (
    "**Experimental.** This skill has not been verified against a real task "
    "since its last change. Verify its output before relying on it."
)
DEPRECATED_BANNER_PREFIX = "**Deprecated.**"
DEPRECATED_DESCRIPTION_MARKER = "Deprecated as of "
DEPRECATED_NO_SUCCESSOR = "no successor."

NAME_CHARSET = re.compile(r"^[a-z0-9-]+$")
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# BCP 47, restricted to the shapes a skill body plausibly needs: `de`, `en-GB`,
# `zh-Hant`, `de-DE`. Anything more exotic is likelier a typo than a real tag.
LANGUAGE_TAG = re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$")
MD_LINK = re.compile(r"\]\(([^)\s]+)")
URI_SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:")
# Code spans and fenced blocks must be stripped before extracting links.
# Documentation about link syntax legitimately contains link syntax -- a skill
# that explains `[Text](Type-id.html)` is describing an example, not linking to a
# file. Without this, the portability check would force authors to avoid writing
# about links, which is the opposite of useful.
FENCED_BLOCK = re.compile(r"^```.*?^```", re.M | re.S)
CODE_SPAN = re.compile(r"`+[^`\n]*`+")


@dataclass
class Violation:
    path: str
    rule: str
    message: str

    def render(self) -> str:
        return f"{self.path}: [{self.rule}] {self.message}"


@dataclass
class Skill:
    name: str
    directory: str
    path: str
    frontmatter: dict
    metadata: dict = field(default_factory=dict)

    @property
    def description(self) -> str:
        return str(self.frontmatter.get("description", ""))

    @property
    def tier(self) -> str:
        return self.metadata.get(TIER_KEY, "")

    @property
    def domain(self) -> str:
        return self.metadata.get(DOMAIN_KEY, "")

    @property
    def owner(self) -> str:
        return self.metadata.get(OWNER_KEY, "")

    @property
    def status(self) -> str:
        return self.metadata.get(STATUS_KEY, DEFAULT_STATUS)


def leading_banner(body: str) -> str:
    """Return the first blockquote block of the body, ignoring a leading H1.

    Returns an empty string when the body does not open with a blockquote. This
    is the deterministic stand-in for "the body begins with the banner".
    """
    lines = body.split("\n")
    index = 0

    def skip_blank(i: int) -> int:
        while i < len(lines) and not lines[i].strip():
            i += 1
        return i

    index = skip_blank(index)
    if index < len(lines) and lines[index].startswith("# "):
        index = skip_blank(index + 1)

    if index >= len(lines) or not lines[index].lstrip().startswith(">"):
        return ""

    collected = []
    while index < len(lines) and lines[index].lstrip().startswith(">"):
        collected.append(lines[index].lstrip()[1:].strip())
        index += 1
    return " ".join(part for part in collected if part).strip()


def check_name(skill_dir: Path, frontmatter: dict, out: list[Violation]) -> None:
    rel = f"{SKILLS_REL}/{skill_dir.name}/SKILL.md"
    name = frontmatter.get("name")

    if name is None:
        out.append(Violation(rel, "name/required", "`name` is required"))
        return
    if not isinstance(name, str):
        out.append(Violation(rel, "name/type", f"`name` must be a string, got {type(name).__name__}"))
        return
    if not 1 <= len(name) <= NAME_MAX:
        out.append(
            Violation(rel, "name/length", f"`name` must be 1-{NAME_MAX} characters, got {len(name)}")
        )
    if not NAME_CHARSET.match(name):
        out.append(
            Violation(
                rel,
                "name/charset",
                f"`name` may only contain lowercase a-z, 0-9 and hyphens; got {name!r}",
            )
        )
    if name.startswith("-") or name.endswith("-"):
        out.append(Violation(rel, "name/hyphen", "`name` must not start or end with a hyphen"))
    if "--" in name:
        out.append(Violation(rel, "name/hyphen", "`name` must not contain consecutive hyphens"))
    if name != skill_dir.name:
        out.append(
            Violation(
                rel,
                "name/directory",
                f"`name` is {name!r} but the parent directory is {skill_dir.name!r}; "
                "the specification requires them to be equal. Rename the directory, "
                "not the field, unless you intend a rename (which is a breaking change: "
                "see the two-release rule in docs/lifecycle.md).",
            )
        )


def check_spec_fields(rel: str, frontmatter: dict, out: list[Violation]) -> None:
    unknown = sorted(set(frontmatter) - SPEC_FIELDS)
    if unknown:
        out.append(
            Violation(
                rel,
                "frontmatter/unknown",
                f"unknown top-level frontmatter field(s) {unknown}; the specification defines "
                f"only {sorted(SPEC_FIELDS)}. Organization metadata belongs under `metadata:` "
                "with the `fgdh.` prefix -- see docs/metadata-keys.md.",
            )
        )
    for required in sorted(REQUIRED_SPEC_FIELDS):
        if required not in frontmatter:
            out.append(Violation(rel, f"{required}/required", f"`{required}` is required"))

    description = frontmatter.get("description")
    if description is not None:
        if not isinstance(description, str):
            out.append(
                Violation(
                    rel,
                    "description/type",
                    f"`description` must be a string, got {type(description).__name__}",
                )
            )
        elif not 1 <= len(description) <= DESCRIPTION_MAX:
            out.append(
                Violation(
                    rel,
                    "description/length",
                    f"`description` must be 1-{DESCRIPTION_MAX} characters, got {len(description)}",
                )
            )

    compatibility = frontmatter.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str):
            out.append(Violation(rel, "compatibility/type", "`compatibility` must be a string"))
        elif not 1 <= len(compatibility) <= COMPATIBILITY_MAX:
            out.append(
                Violation(
                    rel,
                    "compatibility/length",
                    f"`compatibility` must be 1-{COMPATIBILITY_MAX} characters, "
                    f"got {len(compatibility)}",
                )
            )

    for optional in ("license", "allowed-tools"):
        value = frontmatter.get(optional)
        if value is not None and not isinstance(value, str):
            out.append(Violation(rel, f"{optional}/type", f"`{optional}` must be a string"))


def check_metadata(rel: str, frontmatter: dict, out: list[Violation]) -> dict:
    raw = frontmatter.get("metadata")
    if raw is None:
        out.append(
            Violation(
                rel,
                "metadata/required",
                f"`metadata` is required by the catalog contract and must carry "
                f"{list(REQUIRED_META)} -- see docs/metadata-keys.md",
            )
        )
        return {}
    if not isinstance(raw, dict):
        out.append(Violation(rel, "metadata/type", "`metadata` must be a mapping"))
        return {}

    metadata: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            out.append(Violation(rel, "metadata/key", f"metadata key {key!r} must be a string"))
            continue
        if not isinstance(value, str):
            out.append(
                Violation(
                    rel,
                    "metadata/value",
                    f"metadata value for {key!r} must be a string, got "
                    f"{type(value).__name__}. Quote values YAML would coerce, "
                    'e.g. version: "1.0" and "@handle".',
                )
            )
            continue
        metadata[key] = value

    stray = sorted(k for k in metadata if k.startswith(f"{PREFIX}.") and k not in KNOWN_META)
    if stray:
        out.append(
            Violation(
                rel,
                "metadata/unknown",
                f"unknown {PREFIX}.* key(s) {stray}; the registry is {list(KNOWN_META)} "
                "-- see docs/metadata-keys.md. Adding a key is a contract change and needs "
                "a registry entry first.",
            )
        )

    for key in REQUIRED_META:
        if key not in metadata:
            out.append(Violation(rel, "metadata/required", f"`{key}` is required"))

    tier = metadata.get(TIER_KEY)
    if tier == REJECTED_TIER:
        out.append(
            Violation(
                rel,
                "tier/rejected",
                f"`{TIER_KEY}: \"{REJECTED_TIER}\"` is never a valid stored value. Tier "
                "classification has three outcomes but only two are admissible here: a "
                "skill that requires specific files at specific paths belongs in the "
                "consuming repository, not in this catalog. Your next move is to lift it "
                "to `domain` by replacing hard-coded paths with a discovery step and an "
                "explicit failure branch, or to move it out. Do not simply change the "
                "value. See docs/authoring-skills.md (tier model) and docs/lifecycle.md "
                "section 1.3.",
            )
        )
    elif tier is not None and tier not in TIERS:
        out.append(
            Violation(rel, "tier/enum", f"`{TIER_KEY}` must be one of {list(TIERS)}, got {tier!r}")
        )

    domain = metadata.get(DOMAIN_KEY)
    if domain is not None and not SLUG.match(domain):
        out.append(
            Violation(
                rel,
                "domain/slug",
                f"`{DOMAIN_KEY}` must be a lowercase hyphenated slug, got {domain!r}",
            )
        )

    owner = metadata.get(OWNER_KEY)
    if owner is not None and not owner.startswith("@"):
        out.append(
            Violation(
                rel,
                "owner/format",
                f"`{OWNER_KEY}` must be a GitHub handle or team starting with '@', got "
                f"{owner!r}. Quote it -- '@' is a reserved YAML indicator.",
            )
        )

    language = metadata.get(LANGUAGE_KEY)
    if language is not None and not LANGUAGE_TAG.match(language):
        out.append(
            Violation(
                rel,
                "language/tag",
                f"`{LANGUAGE_KEY}` must be a BCP 47 tag such as 'en' or 'de', got {language!r}",
            )
        )

    status = metadata.get(STATUS_KEY, DEFAULT_STATUS)
    if status not in STATUSES:
        out.append(
            Violation(rel, "status/enum", f"`{STATUS_KEY}` must be one of {list(STATUSES)}, got {status!r}")
        )
    if status == "deprecated" and REPLACED_BY_KEY not in metadata:
        out.append(
            Violation(
                rel,
                "status/replaced-by",
                f"`{REPLACED_BY_KEY}` is required when the status is 'deprecated'; set it to "
                "the successor's name or to the literal 'none'",
            )
        )

    return metadata


def check_status_mirroring(rel: str, frontmatter: dict, metadata: dict, body: str,
                           out: list[Violation]) -> None:
    """Enforce the coupling between `fgdh.status`, the description and the body.

    See docs/authoring-skills.md. In short: `stable` is mentioned nowhere,
    `experimental` is a body banner only (a caution must not suppress
    triggering), and `deprecated` MUST reach the description, because
    redirecting to a successor can only happen before the body loads.
    """
    status = metadata.get(STATUS_KEY, DEFAULT_STATUS)
    if status not in STATUSES:
        return  # already reported as an enum violation; do not pile on

    description = frontmatter.get("description")
    description = description if isinstance(description, str) else ""
    banner = leading_banner(body)
    lowered = description.lower()

    if status == "deprecated":
        replaced_by = metadata.get(REPLACED_BY_KEY, "")
        if DEPRECATED_DESCRIPTION_MARKER not in description:
            out.append(
                Violation(
                    rel,
                    "mirror/deprecated-description",
                    "a deprecated skill must carry its redirect in the DESCRIPTION: append "
                    f'"{DEPRECATED_DESCRIPTION_MARKER}<version>; use <successor> instead." '
                    f'(or "{DEPRECATED_DESCRIPTION_MARKER}<version>; {DEPRECATED_NO_SUCCESSOR}"). '
                    "The metadata field alone is invisible to an agent, which sees only the "
                    "description before deciding to activate the skill -- so a deprecation "
                    "recorded only in metadata keeps triggering and keeps being followed. "
                    "See docs/authoring-skills.md, status mirroring.",
                )
            )
        elif replaced_by == "none":
            if DEPRECATED_NO_SUCCESSOR not in description:
                out.append(
                    Violation(
                        rel,
                        "mirror/deprecated-description",
                        f'`{REPLACED_BY_KEY}` is "none", so the description must end with '
                        f'"{DEPRECATED_DESCRIPTION_MARKER}<version>; {DEPRECATED_NO_SUCCESSOR}"',
                    )
                )
        elif replaced_by and f"use {replaced_by} instead." not in description:
            out.append(
                Violation(
                    rel,
                    "mirror/deprecated-description",
                    f'`{REPLACED_BY_KEY}` is "{replaced_by}", so the description must contain '
                    f'"use {replaced_by} instead."',
                )
            )

        if not banner.startswith(DEPRECATED_BANNER_PREFIX):
            out.append(
                Violation(
                    rel,
                    "mirror/deprecated-banner",
                    f"the body of a deprecated skill must open with a blockquote starting "
                    f'"> {DEPRECATED_BANNER_PREFIX}" and stating the reason, the successor, and '
                    "the earliest release in which removal may occur",
                )
            )

    if status == "experimental":
        if banner != EXPERIMENTAL_BANNER:
            out.append(
                Violation(
                    rel,
                    "mirror/experimental-banner",
                    "the body of an experimental skill must open with exactly this "
                    f'blockquote: "> {EXPERIMENTAL_BANNER}"',
                )
            )
        if "experimental" in lowered:
            out.append(
                Violation(
                    rel,
                    "mirror/experimental-description",
                    "the description of an experimental skill must NOT mention that it is "
                    "experimental. Caution must not suppress triggering: the skill should "
                    "activate, and the agent should then be told to verify its output. That "
                    "instruction only has to survive until activation, so it belongs in the "
                    "body, and the description stays a clean matching surface.",
                )
            )

    if status != "deprecated" and "deprecated" in lowered:
        out.append(
            Violation(
                rel,
                "mirror/stale-deprecation",
                f"the status is '{status}' but the description still announces a deprecation. "
                "These drift apart at exactly the release where it matters; fix one of the two.",
            )
        )

    if status != "experimental" and banner == EXPERIMENTAL_BANNER:
        out.append(
            Violation(
                rel,
                "mirror/stale-experimental",
                f"the status is '{status}' but the body still opens with the experimental "
                "banner. Promotion to 'stable' removes the banner in the same change.",
            )
        )
    if status != "deprecated" and banner.startswith(DEPRECATED_BANNER_PREFIX):
        out.append(
            Violation(
                rel,
                "mirror/stale-deprecation",
                f"the status is '{status}' but the body still opens with a deprecation banner",
            )
        )


def strip_code(text: str) -> str:
    """Remove fenced blocks and inline code spans, preserving line count.

    Line count is preserved so that a future line-numbered diagnostic still
    points at the right line.
    """
    def blank(match: re.Match) -> str:
        return "\n" * match.group(0).count("\n")

    return CODE_SPAN.sub("", FENCED_BLOCK.sub(blank, text))


def check_portability(skill_dir: Path, rel: str, text: str, out: list[Violation]) -> None:
    """Reject references that only work in the repository they were written in."""
    for target in MD_LINK.findall(strip_code(text)):
        if target.startswith("#") or URI_SCHEME.match(target):
            continue
        clean = target.split("#", 1)[0].strip()
        if not clean:
            continue
        if clean.startswith("/"):
            out.append(
                Violation(
                    rel,
                    "path/absolute",
                    f"reference {target!r} is an absolute path. Skills are installed into "
                    "repositories nobody anticipated; use a path relative to the skill root.",
                )
            )
            continue
        if ".." in Path(clean).parts:
            out.append(
                Violation(
                    rel,
                    "path/traversal",
                    f"reference {target!r} escapes the skill root with '..'. Everything a "
                    "skill needs must live inside the skill directory, or it breaks on "
                    "installation -- silently.",
                )
            )
            continue
        parts = Path(clean).parts
        if len(parts) > 2:
            out.append(
                Violation(
                    rel,
                    "path/depth",
                    f"reference {target!r} is more than one level deep; the specification asks "
                    "for references one level deep from SKILL.md",
                )
            )
        if not (skill_dir / clean).exists():
            out.append(
                Violation(
                    rel,
                    "path/missing",
                    f"reference {target!r} does not exist in the skill directory",
                )
            )


def collect(out: list[Violation]) -> list[Skill]:
    skills: list[Skill] = []
    if not SKILLS_DIR.is_dir():
        return skills

    for skill_dir in sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        rel = f"{SKILLS_REL}/{skill_dir.name}/SKILL.md"
        if not skill_md.is_file():
            out.append(
                Violation(
                    f"{SKILLS_REL}/{skill_dir.name}/",
                    "skill/missing-skill-md",
                    "a directory under skills/ must contain a SKILL.md",
                )
            )
            continue

        try:
            frontmatter, body = load(skill_md)
        except FrontmatterError as exc:
            out.append(Violation(rel, "frontmatter/parse", exc.message))
            continue

        raw = skill_md.read_text(encoding="utf-8")
        line_count = len(raw.split("\n"))
        if line_count >= BODY_MAX_LINES:
            out.append(
                Violation(
                    rel,
                    "body/length",
                    f"SKILL.md is {line_count} lines; keep it under {BODY_MAX_LINES}. The body "
                    "is paid for on every activation, whereas references/ is paid for only "
                    "when actually needed -- move detail there.",
                )
            )

        check_name(skill_dir, frontmatter, out)
        check_spec_fields(rel, frontmatter, out)
        metadata = check_metadata(rel, frontmatter, out)
        check_status_mirroring(rel, frontmatter, metadata, body, out)
        check_portability(skill_dir, rel, body, out)

        # Bundled Markdown is checked too. A broken reference inside references/
        # fails exactly as silently as one in SKILL.md -- the agent follows a
        # pointer to nothing and improvises -- and it is the failure mode that
        # only shows up after installation, where nobody is looking.
        for bundled in sorted(skill_dir.rglob("*.md")):
            if bundled.name == "SKILL.md" and bundled.parent == skill_dir:
                continue
            bundled_rel = f"{SKILLS_REL}/{skill_dir.name}/{bundled.relative_to(skill_dir).as_posix()}"
            try:
                check_portability(bundled.parent, bundled_rel, bundled.read_text(encoding="utf-8"), out)
            except (OSError, UnicodeDecodeError) as exc:
                out.append(Violation(bundled_rel, "bundled/unreadable", f"cannot read: {exc}"))

        name = frontmatter.get("name")
        skills.append(
            Skill(
                name=name if isinstance(name, str) else skill_dir.name,
                directory=skill_dir.name,
                path=f"{SKILLS_REL}/{skill_dir.name}/SKILL.md",
                frontmatter=frontmatter,
                metadata=metadata,
            )
        )

    seen: dict[str, str] = {}
    for skill in skills:
        if skill.name in seen:
            out.append(
                Violation(
                    skill.path,
                    "name/duplicate",
                    f"`name` {skill.name!r} is already used by {seen[skill.name]}",
                )
            )
        else:
            seen[skill.name] = skill.path

    return sorted(skills, key=lambda s: s.name)


def read_version() -> str:
    """Read the release version out of the existing index, or fall back.

    Release Please owns this value (see .github/release-please-config.json). It
    is deliberately not derived from Git tags, the manifest, or the environment:
    any of those would reintroduce the nondeterminism that `--check` exists to
    detect.
    """
    if not INDEX_PATH.is_file():
        return FALLBACK_VERSION
    try:
        existing = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return FALLBACK_VERSION
    version = existing.get("version")
    return version if isinstance(version, str) and version else FALLBACK_VERSION


def render_index(skills: list[Skill]) -> str:
    document = {
        "schemaVersion": SCHEMA_VERSION,
        "version": read_version(),
        "generator": GENERATOR,
        "skills": [
            {
                # The `skill://` scheme is the identifier the proposed MCP
                # skills extension would use. Nothing serves it yet; emitting it
                # now costs nothing and means the file can back a server later
                # without restructuring. See docs/skills-over-mcp.md.
                "url": f"skill://{skill.name}/SKILL.md",
                "path": skill.path,
                # A faithful subset of the open standard. Organization metadata
                # sits in the sibling object so this one stays standard-shaped.
                "frontmatter": {
                    "name": skill.name,
                    "description": skill.description,
                },
                "metadata": {
                    key: skill.metadata[key] for key in KNOWN_META if key in skill.metadata
                },
            }
            for skill in skills
        ],
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def render_catalog(skills: list[Skill]) -> str:
    lines = [
        "<!-- GENERATED FILE -- do not edit by hand. -->",
        "<!-- Regenerate with: python scripts/build_index.py -->",
        "",
        "# Catalog",
        "",
        "Every skill in this repository, generated from the frontmatter of each `SKILL.md`.",
        "CI regenerates this file and fails if it changes, so what you read here is provably",
        "what the skills declare.",
        "",
        "The machine-readable equivalent is [`skills/index.json`](skills/index.json).",
        "",
    ]

    if not skills:
        lines += [
            "The catalog is currently empty. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to",
            "add the first skill.",
            "",
        ]
        return "\n".join(lines)

    lines += [
        "| Skill | Tier | Domain | Owner | Status | Description |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for skill in sorted(skills, key=lambda s: (s.domain, s.name)):
        lines.append(
            "| [`{name}`]({path}) | {tier} | {domain} | {owner} | {status} | {description} |".format(
                name=skill.name,
                path=skill.path,
                tier=escape_cell(skill.tier),
                domain=escape_cell(skill.domain),
                owner=escape_cell(skill.owner),
                status=escape_cell(skill.status),
                description=escape_cell(skill.description),
            )
        )
    lines.append("")
    return "\n".join(lines)


def run(check: bool, as_json: bool, validate_only: bool = False) -> int:
    violations: list[Violation] = []
    skills = collect(violations)

    if violations:
        if as_json:
            json.dump(
                {"ok": False, "violations": [v.__dict__ for v in violations]},
                sys.stderr,
                indent=2,
                ensure_ascii=False,
            )
            sys.stderr.write("\n")
        else:
            print(f"{len(violations)} validation error(s):", file=sys.stderr)
            for violation in violations:
                print(f"  {violation.render()}", file=sys.stderr)
        return 1

    if validate_only:
        if as_json:
            json.dump({"ok": True, "skills": len(skills), "written": False}, sys.stderr, indent=2)
            sys.stderr.write("\n")
        else:
            print(f"valid: {len(skills)} skill(s) in {SKILLS_REL}/ (nothing generated)")
        return 0

    index_text = render_index(skills)
    catalog_text = render_catalog(skills)

    if check:
        drifted = []
        for path, expected in ((INDEX_PATH, index_text), (CATALOG_PATH, catalog_text)):
            actual = path.read_text(encoding="utf-8") if path.is_file() else None
            if actual != expected:
                try:
                    drifted.append(path.relative_to(REPO_ROOT).as_posix())
                except ValueError:
                    # --skills-dir pointed outside the repository; report the path as given.
                    drifted.append(path.as_posix())
        if drifted:
            if as_json:
                json.dump({"ok": False, "drift": drifted}, sys.stderr, indent=2)
                sys.stderr.write("\n")
            else:
                print(
                    "generated artefacts are out of sync with the skills they describe: "
                    + ", ".join(drifted),
                    file=sys.stderr,
                )
                print("run `python scripts/build_index.py` and commit the result", file=sys.stderr)
            return 1
        if as_json:
            json.dump({"ok": True, "skills": len(skills)}, sys.stderr, indent=2)
            sys.stderr.write("\n")
        else:
            print(f"clean: {len(skills)} skill(s), generated artefacts in sync")
        return 0

    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(index_text, encoding="utf-8")
    CATALOG_PATH.write_text(catalog_text, encoding="utf-8")
    if as_json:
        json.dump({"ok": True, "skills": len(skills), "written": True}, sys.stderr, indent=2)
        sys.stderr.write("\n")
    else:
        print(f"wrote skills/index.json and CATALOG.md ({len(skills)} skill(s))")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the skills and generate skills/index.json and CATALOG.md.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit 1 if the generated artefacts would change",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="emit a machine-readable report on stderr",
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=None,
        help="validate the skills in this directory instead of ./skills (implies --validate-only "
        "unless --check is given); used by the reusable workflow for consuming repositories",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="validate and write nothing; skip generation and the drift check entirely",
    )
    args = parser.parse_args(argv)

    validate_only = args.validate_only
    if args.skills_dir is not None:
        if not args.skills_dir.is_dir():
            print(f"--skills-dir: {args.skills_dir} is not a directory", file=sys.stderr)
            return 2
        configure(args.skills_dir)
        if not args.check:
            validate_only = True

    if args.check and validate_only:
        print("--check and --validate-only are mutually exclusive", file=sys.stderr)
        return 2

    try:
        return run(check=args.check, as_json=args.as_json, validate_only=validate_only)
    except Exception as exc:  # noqa: BLE001 - exit code 2 means "the tool broke"
        print(f"internal error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
