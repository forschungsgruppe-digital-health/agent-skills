#!/usr/bin/env python3
"""page-structure-advice.py - the MEASUREMENT behind the spec 9d/9e routing decision.

WHAT IT IS FOR
--------------
Spec 9d/9e asks the migration to route every source page to one of four
destinations BEFORE any target text is written:

  1  input/intro-notes/<Type>-<id>-intro.md   (content about ONE artefact)
  2  an h3/h4 section on an artefact index page that already exists in the menu
  3  merge into an agreed page that already owns the concern
  4  its own page  -> 4a HUB or merged prose, 4b menu entry or pages:-nested

Left to judgement, that choice drifts from page to page. This script turns it
into arithmetic: it measures the SOURCE page tree, the TARGET page sizes and
the TARGET menu budget, and then prints, per source page, the branch the
measurements support and the number that forced it.

IT PROPOSES AND NEVER EDITS.
It opens the source repository and the target repository read-only and writes
exactly one file, the report named by --out (stdout when --out is omitted).
It refuses to write inside either repository. Nothing in it applies a decision;
a human (or the skill, at step 5) does that.

USAGE
-----
  python3 page-structure-advice.py --source <source-repo> \
                                  [--target <migrated-repo>] \
                                  [--out <file.md>]

  --source  the ORIGINAL module repository. The page tree comes from the FIRST
            of three inputs that yields pages:
              (a) the `pages:` block of sushi-config.yaml
              (b) the AUTHORITATIVE Simplifier guide tree under
                  implementation-guides/ (spec 5.1a), walked from its toc.yaml
              (c) a flat count of input/pagecontent/*.md
            fsh-generated/resources or input/fsh give the artefact index used
            by branch 1.
  --target  the MIGRATED repository (input/includes/menu.xml for the menu
            budget, input/pagecontent/*.md for the size gate, input/intro-notes
            for artefact-anchor evidence).  Omit it before the target exists:
            the source half of the report still works, and every
            budget-dependent decision is reported as "unknown (no --target)"
            instead of being guessed.
  --guide-tree
            HUMAN OVERRIDE of the authoritative-guide-tree choice: the
            directory name under implementation-guides/. Without it the script
            picks per spec 5.1a and reports every tree, the choice and the
            reason.

Python 3 standard library only.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import sys
from collections import Counter, OrderedDict

SCRIPT_VERSION = "1.1.0"

# --------------------------------------------------------------------------
# Contract limits (spec 9e).  Changing these changes the advice, so they are
# named once, here, and printed in the report.
# --------------------------------------------------------------------------
LIMIT_MENU_TOTAL = 33          # total clickable menu entries
LIMIT_DROPDOWN_CHILDREN = 10   # children of any one dropdown
LIMIT_TOP_LEVEL = 8            # top-level menu entries
LIMIT_MENU_DEPTH = 2           # the template supports ONE sub-menu level
GATE_WORDS = 2500              # size gate: more than this many words
GATE_MERGED_SOURCES = 4        # size gate: more than this many merged sources
HUB_CHILDREN = 3               # 4a: this many children or more -> hub

# Artefact types, most-anchoring first.  A source page that names an instrument
# usually maps onto several artefacts (the questionnaire, its profile, its
# score definitions, its value sets); the anchor is the one the intro note
# hangs off.
TYPE_PRIORITY = [
    "Questionnaire",
    "StructureDefinition",
    "ObservationDefinition",
    "ValueSet",
    "CodeSystem",
    "CapabilityStatement",
    "OperationDefinition",
    "SearchParameter",
    "ConceptMap",
]
# Instance-ish types are examples, never the anchor of a narrative page.
EXAMPLE_TYPES = {
    "Bundle", "Observation", "QuestionnaireResponse", "Patient",
    "Practitioner", "PractitionerRole", "Encounter", "Organization",
    "Condition", "Procedure", "Medication", "MedicationAdministration",
    "MedicationStatement", "MedicationRequest", "Consent", "Specimen",
    "DiagnosticReport", "ServiceRequest", "ImplementationGuide",
}

# Which artefact index page hosts a branch-2 family overview, per artefact
# type.  Only used when the page actually exists in the target's agreed menu;
# otherwise the report says so instead of inventing a host.
TYPE_INDEX_PAGE = {
    "StructureDefinition": "profiles",
    "Questionnaire": "profiles",
    "ObservationDefinition": "profiles",
    "ValueSet": "value-sets",
    "CodeSystem": "code-systems",
    "CapabilityStatement": "capability-statements",
    "SearchParameter": "search-parameters",
    "OperationDefinition": "artifacts",
    "ConceptMap": "artifacts",
}

# Fallback list of pages the TF-KDS menu agrees on, used only when --target is
# absent.  With --target the agreed set is READ from the target instead.
FALLBACK_AGREED_PAGES = [
    "index", "changes", "downloads", "uml-diagrams", "logical-models",
    "security-and-privacy", "translationinfo", "version-history",
    "artifacts", "profiles", "extensions", "examples",
]


# ==========================================================================
# small helpers
# ==========================================================================

def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


def compact(name):
    """'eq-5d-5l' -> 'eq5d5l'.  Lowercase, alphanumerics only."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def tokens(name):
    """'bdi-ii' -> ['bdi', 'ii'].  Split on every non-alphanumeric run."""
    return [t for t in re.split(r"[^a-z0-9]+", name.lower()) if t]


def strip_html_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def strip_code_fences(text):
    """Drop fenced blocks - used for HEADING detection only, so that a '#'
    inside a shell example is not counted as a heading."""
    out = []
    in_fence = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


# ==========================================================================
# word count
# ==========================================================================
# Definition, stated so the number is reproducible and arguable:
#   words = whitespace-separated tokens of the page after
#     (a) removing HTML comments          - they are not rendered
#     (b) removing table separator rows    - '|---|:--:|' renders as a rule
#     (c) removing leading blockquote '>'  - markup, not a word
#     (d) turning '|' into a space         - cell separators, not words
#     (e) removing '*', '_' and '`'        - emphasis/code markup, not words
# Everything else counts: headings, list items, table cells and fenced code
# all cost the reader scrolling, and the size gate measures exactly that.

_TABLE_SEPARATOR = re.compile(r"^\s*\|?[\s:\-\|]+\|?\s*$")


def count_words(text):
    text = strip_html_comments(text)
    kept = [ln for ln in text.split("\n")
            if not ("|" in ln and _TABLE_SEPARATOR.match(ln))]
    text = "\n".join(kept)
    text = re.sub(r"^\s*>\s?", "", text, flags=re.M)
    text = text.replace("|", " ")
    text = re.sub(r"[*_`]", "", text)
    return len(text.split())


# ==========================================================================
# headings and anchors
# ==========================================================================

_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")


def anchor_slug(title):
    """Approximate the publisher's anchor: lowercase, punctuation dropped,
    spaces to hyphens."""
    slug = title.strip().lower()
    slug = re.sub(r"[`*_\[\]\(\)]", "", slug)
    slug = re.sub(r"[^a-z0-9\s\-]", "", slug)
    slug = re.sub(r"\s+", "-", slug).strip("-")
    return slug


def analyse_headings(text):
    body = strip_code_fences(strip_html_comments(text))
    heads = []
    for line in body.split("\n"):
        match = _HEADING.match(line)
        if match:
            heads.append((len(match.group(1)), match.group(2).strip()))
    by_level = Counter(level for level, _ in heads)
    titles = Counter(title for _, title in heads)       # case-SENSITIVE
    repeated = OrderedDict()
    for _, title in heads:
        if titles[title] > 1 and title not in repeated:
            repeated[title] = titles[title]
    collisions = []
    seen = Counter()
    for _, title in heads:
        base = anchor_slug(title)
        seen[base] += 1
        if seen[base] > 1:
            collisions.append("%s-%d" % (base, seen[base]))
    return {
        "headings": heads,
        "by_level": by_level,
        "repeated": repeated,
        "collisions": collisions,
    }


_SOURCE_MARKER = re.compile(r"<!--\s*source:\s*([^\s>]+)", re.I)


def merged_sources(text):
    """Distinct `<!-- source: X.md -->` section markers - the migration's own
    record of how many SOURCE PAGES were merged into this page.

    Only values naming a page file count. The page-header form
    `<!-- Source: <template-repo> input/pagecontent/<page>.md ... -->` names the
    template the page was derived from, not a merged module page, and its first
    token is a repository name; requiring a `.md` value drops it without a
    case-sensitivity trick."""
    found = []
    for value in _SOURCE_MARKER.findall(text):
        value = value.strip().rstrip("-").strip()
        if not value.lower().endswith(".md"):
            continue
        if value not in found:
            found.append(value)
    return found


# ==========================================================================
# SOURCE: the sushi-config.yaml `pages:` tree
# ==========================================================================

_PAGE_KEY = re.compile(r"^(\s*)([A-Za-z0-9][A-Za-z0-9._\- ]*\.(?:md|xml|html)):\s*(?:#.*)?$")


class PageNode(object):
    def __init__(self, filename, level, parent, slug=None):
        # `filename` is what a human types to find the page: the bare file name
        # for a `pages:` entry, the guide-root-relative PATH for a Simplifier
        # guide page (a guide ships dozens of `Index.page.md`, so the bare name
        # would not identify one).  `slug` is the matching key - always the base
        # name without its extension.
        self.filename = filename
        self.slug = slug if slug is not None else re.sub(r"\.(md|xml|html)$", "", filename)
        self.level = level
        self.parent = parent
        self.children = []
        self.title = ""
        self.words = 0
        # filled in later
        self.branch = ""
        self.destination = ""
        self.measurement = ""
        self.anchor = None
        self.anchor_candidates = 0
        self.anchor_how = ""
        self.is_family = False
        self.notes = []


def parse_pages_block(config_text):
    """Indentation-based, line-oriented parse of the `pages:` block.

    Returns (roots, all_nodes, found).  `found` is False when the config has no
    `pages:` block at all - the caller then falls back to counting files and
    says the tree is flat/unknown rather than inventing one.
    """
    lines = config_text.split("\n")
    start = None
    for index, line in enumerate(lines):
        if re.match(r"^pages:\s*(?:#.*)?$", line):
            start = index + 1
            break
    if start is None:
        return [], [], False

    entries = []            # (indent, filename, line_number)
    titles = {}             # line_number of the page it belongs to -> title
    last_page_line = None
    for index in range(start, len(lines)):
        line = lines[index]
        if not line.strip():
            continue
        if re.match(r"^\S", line):          # dedented to column 0 -> block over
            break
        match = _PAGE_KEY.match(line)
        if match:
            entries.append((len(match.group(1)), match.group(2), index + 1))
            last_page_line = index + 1
            continue
        title_match = re.match(r"^\s*title:\s*(.+?)\s*$", line)
        if title_match and last_page_line is not None:
            titles.setdefault(last_page_line, title_match.group(1).strip().strip('"\''))

    if not entries:
        return [], [], False

    indents = sorted({indent for indent, _, _ in entries})
    level_of = {indent: position + 1 for position, indent in enumerate(indents)}

    roots = []
    all_nodes = []
    stack = []              # (level, node)
    for indent, filename, line_number in entries:
        level = level_of[indent]
        while stack and stack[-1][0] >= level:
            stack.pop()
        parent = stack[-1][1] if stack else None
        node = PageNode(filename, level, parent)
        node.title = titles.get(line_number, "")
        if parent is None:
            roots.append(node)
        else:
            parent.children.append(node)
        stack.append((level, node))
        all_nodes.append(node)
    return roots, all_nodes, True


# ==========================================================================
# SOURCE: the Simplifier guide trees under implementation-guides/
# ==========================================================================
# The normal MII shape: the narrative does NOT live in input/pagecontent, it
# lives in one or more Simplifier guide trees, and input/pagecontent holds a
# single stub.  Measured on kerndatensatzmodul-onkologie v2026.0.3: three trees
# (2025.x-DE, 2025.x-EN, 2026.x-DE) and ONE file in input/pagecontent.
#
# Structure of a tree, verified:
#   <tree>/guide.yaml        title:, description:, version:, style-*
#   <tree>/toc.yaml          a list of {name:, filename:} entries
#   a `filename` ending in `.page.md` is a PAGE;
#   any other `filename` is a SUB-DIRECTORY holding its own toc.yaml.  Recurse.
#
# Parsed line by line with the standard library, like the rest of this script.

GUIDE_DIR_NAME = "implementation-guides"
PAGE_SUFFIX = ".page.md"
INDEX_PAGE = "index" + PAGE_SUFFIX          # compared case-insensitively

_TOC_ITEM_START = re.compile(r"^\s*-\s*(.*)$")
_TOC_FIELD = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_\-]*)\s*:\s*(.*)$")
_VERSION_TOKEN = re.compile(r"v?(\d+(?:\.[0-9xX]+)*)")
_LANG_SUFFIX = re.compile(r"[-_ ]([A-Za-z]{2})$")
_LANG_TAG = re.compile(r"^\s*\[([A-Za-z]{2})\]")


def _unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        inner = value[1:-1]
        return inner.replace("''", "'") if value[0] == "'" else inner
    return value


def parse_toc_file(path):
    """Return the toc.yaml entries as [(name, filename), ...] in document order.

    Line-oriented: a `- ` starts an entry, `name:`/`filename:` fill it, and both
    values may be quoted (measured: the Onkologie 2026 tree quotes them in
    `Organspezifische-Module/toc.yaml` and nowhere else)."""
    entries = []
    current = None
    for raw in read_text(path).split("\n"):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        start = _TOC_ITEM_START.match(raw)
        if start:
            if current and current.get("filename"):
                entries.append(current)
            current = {}
            rest = start.group(1)
            field = _TOC_FIELD.match(rest) if rest else None
            if field:
                current[field.group(1).lower()] = _unquote(field.group(2))
            continue
        field = _TOC_FIELD.match(raw)
        if field and current is not None:
            key = field.group(1).lower()
            current.setdefault(key, _unquote(field.group(2)))
    if current and current.get("filename"):
        entries.append(current)
    return [(entry.get("name", ""), entry["filename"]) for entry in entries]


def parse_guide_yaml(path):
    """`title:`, `description:`, `version:` from a guide.yaml - flat, top level."""
    fields = {}
    for raw in read_text(path).split("\n"):
        if raw.startswith((" ", "\t")) or not raw.strip():
            continue
        field = _TOC_FIELD.match(raw)
        if field:
            fields.setdefault(field.group(1).lower(), _unquote(field.group(2)))
    return fields


def version_from_name(name):
    """The longest version-looking substring of a directory name.
    'ImplementationGuide-2026.x-DE' -> '2026.x'; 'MII-PRO-v2026-DE' -> '2026';
    'Common' -> ''."""
    best = ""
    for match in _VERSION_TOKEN.finditer(name):
        if len(match.group(1)) > len(best):
            best = match.group(1)
    return best


def version_key(text):
    """Sort key for a dotted version. Numeric parts compare numerically; an
    'x' placeholder ('2026.x') sorts BELOW any explicit number in the same
    position, so an explicit 2026.0.3 outranks a bare 2026.x. Stated because it
    decides which tree is authoritative."""
    if not text:
        return ()
    parts = []
    for part in re.split(r"[.\-_]", text):
        parts.append((1, int(part)) if part.isdigit() else (0, 0))
    return tuple(parts)


def language_of(dir_name, fields):
    """Two-letter language of a guide tree, uppercased.  The description tag
    (`'[DE] Modul ...'`) is authoritative; the directory-name suffix is the
    fallback; a tree with neither (a shared-asset tree like `Common`) has none."""
    tag = _LANG_TAG.match(fields.get("description", "") or "")
    if tag:
        return tag.group(1).upper()
    suffix = _LANG_SUFFIX.search(dir_name)
    if suffix:
        return suffix.group(1).upper()
    return ""


def source_language(config_text):
    """The module's own narrative language from sushi-config `language:`
    ('de-DE' -> 'DE'). Empty when the config does not state one."""
    match = re.search(r"^language:\s*(.+?)\s*$", config_text, re.M)
    if not match:
        return ""
    value = _unquote(match.group(1))
    return value.split("-")[0].upper() if value else ""


def _dir_has_pages(path):
    for _dirpath, _dirnames, filenames in os.walk(path):
        if any(name.endswith(PAGE_SUFFIX) for name in filenames):
            return True
    return False


def discover_guide_trees(source_root):
    """Every directory under implementation-guides/, with its metadata and its
    on-disk page count.  Nothing is filtered away here: the report lists them
    all, including the ones that are not guide trees at all (spec 5.1a #4)."""
    guide_root = os.path.join(source_root, GUIDE_DIR_NAME)
    if not os.path.isdir(guide_root):
        return []
    trees = []
    for name in sorted(os.listdir(guide_root)):
        path = os.path.join(guide_root, name)
        if not os.path.isdir(path):
            continue
        fields = parse_guide_yaml(os.path.join(path, "guide.yaml"))
        page_files = 0
        for _dirpath, _dirnames, filenames in os.walk(path):
            page_files += sum(1 for f in filenames if f.endswith(PAGE_SUFFIX))
        trees.append({
            "name": name,
            "path": path,
            "title": fields.get("title", ""),
            "description": fields.get("description", ""),
            "version_yaml": fields.get("version", ""),
            "version_name": version_from_name(name),
            "language": language_of(name, fields),
            "has_guide_yaml": os.path.isfile(os.path.join(path, "guide.yaml")),
            "has_toc": os.path.isfile(os.path.join(path, "toc.yaml")),
            "page_files": page_files,
            "disposition": "",
        })
    return trees


def choose_guide_tree(trees, module_language, override):
    """Spec 5.1a #1: the AUTHORITATIVE tree is the highest-version guide in the
    module's own narrative language.

    Returns (chosen, reason, notes).  It never chooses silently: the caller
    prints every tree, the choice, the reason and the override switch."""
    notes = []
    usable = [t for t in trees if t["page_files"] > 0]
    if not usable:
        return None, "no directory under %s/ contains a *%s file" % (
            GUIDE_DIR_NAME, PAGE_SUFFIX), notes

    if override:
        wanted = override.strip().strip("/")
        for tree in usable:
            if tree["name"].lower() == wanted.lower():
                return tree, ("HUMAN OVERRIDE: --guide-tree %s (the spec 5.1a "
                              "ranking below was not applied)" % tree["name"]), notes
        notes.append("--guide-tree %s does not name a guide tree that holds pages; "
                     "falling back to the spec 5.1a ranking." % override)

    versioned = [t for t in usable if t["version_name"]]
    if not versioned:
        notes.append("no directory name under %s/ carries a version substring; "
                     "ranked by name instead." % GUIDE_DIR_NAME)
        versioned = usable

    same_language = [t for t in versioned
                     if module_language and t["language"] == module_language]
    if same_language:
        pool, why = same_language, ("highest version among the trees in the module's own "
                                    "narrative language %s (sushi-config `language:`)"
                                    % module_language)
    else:
        pool = versioned
        if module_language:
            why = ("highest version overall - NO tree matches the module's narrative "
                   "language %s, so the language criterion of spec 5.1a #1 could not be "
                   "applied" % module_language)
            notes.append("the module's narrative language (%s) matches none of the guide "
                         "trees; confirm the choice by hand." % module_language)
        else:
            why = ("highest version overall - sushi-config states no `language:`, so the "
                   "language criterion of spec 5.1a #1 could not be applied")
            notes.append("sushi-config states no `language:`; the narrative language could "
                         "not be determined, so only the version decided.")

    chosen = max(pool, key=lambda t: (version_key(t["version_name"]),
                                      version_key(t["version_yaml"]),
                                      t["name"]))
    reason = "%s: %s (directory version %s, guide.yaml version %s)" % (
        why, chosen["name"], chosen["version_name"] or "-", chosen["version_yaml"] or "-")
    return chosen, reason, notes


def label_dispositions(trees, chosen):
    """Spec 5.1a's four dispositions, recorded for EVERY tree."""
    for tree in trees:
        if chosen is not None and tree is chosen:
            tree["disposition"] = "**AUTHORITATIVE** - steps 5.4/5.5 operate on this tree"
        elif tree["page_files"] == 0 and not tree["has_guide_yaml"]:
            tree["disposition"] = ("unrecognized directory - needs a retain/retire "
                                   "proposal (5.1a #4)")
        elif not tree["version_name"] and not tree["language"]:
            tree["disposition"] = "shared assets - retain unchanged (5.1a #3)"
        elif (chosen is not None and tree["language"] and chosen["language"]
                and tree["language"] != chosen["language"]):
            text = ("parallel-language tree - harvest seed for the translation skill, "
                    "not a machine translation (5.1a #2)")
            if version_key(tree["version_name"]) < version_key(chosen["version_name"]):
                text += ("; **STALE** (%s vs %s) - every harvested page needs a per-page "
                         "`TODO:REVIEW` naming both versions"
                         % (tree["version_name"] or "-", chosen["version_name"] or "-"))
            tree["disposition"] = text
        else:
            tree["disposition"] = ("historical version tree - retain unchanged, Gate-D "
                                   "retirement set (5.1a #3)")


class GuideWalk(object):
    """Walks one guide tree's toc.yaml hierarchy into the SAME PageNode tree
    `parse_pages_block` builds, so the depth histogram and the whole routing
    pass work unchanged.

    Two modelling decisions the shape forces, both stated in the report:

    * A sub-directory is a LEVEL, not a page.  Every page inside one directory
      therefore shares one level - which is how Simplifier renders a folder's
      contents - and the levels are shifted so the shallowest page sits at
      level 1 (a guide root whose toc holds nothing but one folder entry adds
      no page level).
    * Routing still needs a page PARENT, so a directory is represented by its
      `Index.page.md` (the folder's landing page); the directory's other pages
      and the representatives of its sub-directories become that page's
      children.  A parent may therefore sit at the same level as its children.
    """

    def __init__(self, root):
        self.root = root
        self.roots = []
        self.nodes = []
        self.dirs_without_toc = []      # rel dir -> hierarchy from directory nesting
        self.dirs_unreached = []        # rel dir -> holds pages, no toc.yaml links to it
        self.dangling = []              # (rel toc, filename, why)
        self.unreferenced = []          # (rel page, why)
        self.seen_pages = set()
        self.seen_dirs = set()
        self.dir_info = {}              # realpath(dir) -> (level, representative)

    # -- helpers ----------------------------------------------------------
    def rel(self, path):
        return os.path.relpath(path, self.root).replace(os.sep, "/")

    def listing(self, directory):
        try:
            return sorted(os.listdir(directory))
        except OSError:
            return []

    def make_node(self, directory, filename, level, title):
        path = os.path.join(directory, filename)
        node = PageNode(self.rel(path), level, None, slug=filename[:-len(PAGE_SUFFIX)])
        node.title = title
        node.words = count_words(read_text(path))
        self.seen_pages.add(os.path.realpath(path))
        return node

    def synthesise(self, directory):
        """No toc.yaml: fall back to directory nesting - pages first, then the
        sub-directories that actually hold pages."""
        entries = [("", name) for name in self.listing(directory)
                   if name.endswith(PAGE_SUFFIX)]
        for name in self.listing(directory):
            path = os.path.join(directory, name)
            if (os.path.isdir(path) and not name.startswith(".")
                    and _dir_has_pages(path)):
                entries.append(("", name))
        return entries

    # -- the walk ---------------------------------------------------------
    def visit(self, directory, level, inherited_parent):
        real = os.path.realpath(directory)
        if real in self.seen_dirs:
            return
        self.seen_dirs.add(real)

        toc_path = os.path.join(directory, "toc.yaml")
        has_toc = os.path.isfile(toc_path)
        if has_toc:
            entries = parse_toc_file(toc_path)
        else:
            entries = self.synthesise(directory)
            self.dirs_without_toc.append(self.rel(directory))

        pages = []
        subdirs = []
        listed = set()
        for title, filename in entries:
            path = os.path.join(directory, filename)
            if filename.endswith(PAGE_SUFFIX):
                listed.add(filename)
                if not os.path.isfile(path):
                    self.dangling.append((self.rel(toc_path), filename,
                                          "page file does not exist"))
                    continue
                pages.append(self.make_node(directory, filename, level, title))
            else:
                if not os.path.isdir(path):
                    self.dangling.append((self.rel(toc_path), filename,
                                          "sub-directory does not exist"))
                    continue
                subdirs.append(path)

        # Pages on disk that this directory's toc.yaml never mentions.  They are
        # real pages, so they join the tree - flagged, never dropped silently.
        if has_toc:
            for filename in self.listing(directory):
                if not filename.endswith(PAGE_SUFFIX) or filename in listed:
                    continue
                node = self.make_node(directory, filename, level, "")
                node.notes.append("on disk but not listed in %s" % self.rel(toc_path))
                self.unreferenced.append((node.filename,
                                          "not listed in %s" % self.rel(toc_path)))
                pages.append(node)

        representative = None
        for node in pages:
            if os.path.basename(node.filename).lower() == INDEX_PAGE:
                representative = node
                break
        if representative is None and pages:
            representative = pages[0]

        for node in pages:
            node.parent = inherited_parent if node is representative else representative
            if node.parent is None:
                self.roots.append(node)
            else:
                node.parent.children.append(node)
            self.nodes.append(node)

        next_parent = representative if representative is not None else inherited_parent
        self.dir_info[real] = (level, next_parent)
        for path in subdirs:
            self.visit(path, level + 1, next_parent)

    def sweep_unvisited(self):
        """Pages under a directory no toc.yaml ever reaches.  Placed by
        directory nesting, relative to the nearest directory the walk did
        reach, and reported."""
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            extra = sorted(f for f in filenames
                           if f.endswith(PAGE_SUFFIX)
                           and os.path.realpath(os.path.join(dirpath, f)) not in self.seen_pages)
            if not extra:
                continue
            level, parent, steps = 1, None, 0
            probe = os.path.realpath(dirpath)
            while probe and probe.startswith(os.path.realpath(self.root)):
                if probe in self.dir_info:
                    level, parent = self.dir_info[probe]
                    level += steps
                    break
                parent_dir = os.path.dirname(probe)
                if parent_dir == probe:
                    break
                probe, steps = parent_dir, steps + 1
            self.dirs_unreached.append(self.rel(dirpath))
            for filename in extra:
                node = self.make_node(dirpath, filename, level, "")
                node.notes.append("directory is reached by no toc.yaml - placed by "
                                  "directory nesting")
                node.parent = parent
                if parent is None:
                    self.roots.append(node)
                else:
                    parent.children.append(node)
                self.nodes.append(node)
                self.unreferenced.append((node.filename,
                                          "in a directory no toc.yaml reaches"))

    def normalise_levels(self):
        if not self.nodes:
            return 0
        shift = min(node.level for node in self.nodes) - 1
        if shift:
            for node in self.nodes:
                node.level -= shift
        return shift


def walk_guide_tree(tree_path):
    """Returns (roots, nodes, walk).  `walk` carries everything the report has
    to disclose: directories with no toc.yaml, dangling toc references, and
    pages no toc.yaml mentions."""
    walk = GuideWalk(tree_path)
    walk.visit(tree_path, 1, None)
    walk.sweep_unvisited()
    walk.normalise_levels()
    return walk.roots, walk.nodes, walk


# ==========================================================================
# artefact index (branch-1 evidence)
# ==========================================================================

_FSH_DECL = re.compile(r"^(Profile|Extension|Instance|ValueSet|CodeSystem|Logical|Resource|Mapping):\s*(\S+)")
_FSH_ID = re.compile(r"^Id:\s*(\S+)")
_FSH_INSTANCEOF = re.compile(r"^InstanceOf:\s*(\S+)")


def collect_artefacts(source_root, target_root):
    """(type, id) pairs from fsh-generated filenames, the FSH sources, and the
    target's intro notes.  Nothing is invented: every entry comes from a file
    that exists."""
    artefacts = OrderedDict()          # id -> {"type":..., "intro": bool}

    generated = os.path.join(source_root, "fsh-generated", "resources")
    if os.path.isdir(generated):
        for name in sorted(os.listdir(generated)):
            if not name.endswith(".json"):
                continue
            stem = name[:-5]
            if "-" not in stem:
                continue
            rtype, rid = stem.split("-", 1)
            artefacts.setdefault(rid, {"type": rtype, "intro": False})

    if not artefacts:
        fsh_root = os.path.join(source_root, "input", "fsh")
        for dirpath, _dirnames, filenames in os.walk(fsh_root):
            for name in sorted(filenames):
                if not name.endswith(".fsh"):
                    continue
                current_type = None
                current_name = None
                for line in read_text(os.path.join(dirpath, name)).split("\n"):
                    decl = _FSH_DECL.match(line)
                    if decl:
                        keyword, value = decl.group(1), decl.group(2)
                        current_type = {
                            "Profile": "StructureDefinition",
                            "Extension": "StructureDefinition",
                            "Logical": "StructureDefinition",
                            "Resource": "StructureDefinition",
                            "ValueSet": "ValueSet",
                            "CodeSystem": "CodeSystem",
                            "Instance": None,
                            "Mapping": None,
                        }.get(keyword)
                        current_name = value
                        if current_type and current_name:
                            artefacts.setdefault(current_name, {"type": current_type, "intro": False})
                        continue
                    instance_of = _FSH_INSTANCEOF.match(line)
                    if instance_of and current_name:
                        current_type = instance_of.group(1)
                        artefacts.setdefault(current_name, {"type": current_type, "intro": False})
                        continue
                    ident = _FSH_ID.match(line)
                    if ident and current_type:
                        artefacts.setdefault(ident.group(1), {"type": current_type, "intro": False})

    if target_root:
        intro_dir = os.path.join(target_root, "input", "intro-notes")
        if os.path.isdir(intro_dir):
            for name in sorted(os.listdir(intro_dir)):
                match = re.match(r"^([A-Za-z]+)-(.+)-intro\.md$", name)
                if not match:
                    continue
                rtype, rid = match.group(1), match.group(2)
                entry = artefacts.setdefault(rid, {"type": rtype, "intro": False})
                entry["intro"] = True
    return artefacts


def build_token_frequency(artefacts):
    frequency = Counter()
    for rid in artefacts:
        for token in set(tokens(rid)):
            frequency[token] += 1
    return frequency


def match_artefact(page_slug, artefacts, frequency):
    """Return (best, candidate_count, how).  `how` is 'compact' when the page
    name appears verbatim inside an artefact id, 'tokens' when a majority of
    the page's distinctive name tokens do, and '' when nothing matched."""
    total = max(1, len(artefacts))
    page_compact = compact(page_slug)
    distinctive = [t for t in tokens(page_slug)
                   if len(t) >= 3 and frequency.get(t, 0) < 0.5 * total]

    candidates = []
    for rid, meta in artefacts.items():
        rtype = meta["type"]
        if rtype in EXAMPLE_TYPES or "-exa-" in rid:
            continue
        strong = len(page_compact) >= 4 and page_compact in compact(rid)
        ratio = 0.0
        if distinctive:
            id_tokens = set(tokens(rid))
            hit = sum(1 for t in distinctive if t in id_tokens)
            ratio = hit / float(len(distinctive))
        if not strong and ratio < 0.5:
            continue
        priority = TYPE_PRIORITY.index(rtype) if rtype in TYPE_PRIORITY else len(TYPE_PRIORITY)
        candidates.append((
            0 if meta["intro"] else 1,
            0 if strong else 1,
            -ratio,
            priority,
            len(rid),
            rid,
            rtype,
            "compact" if strong else "tokens",
        ))
    if not candidates:
        return None, 0, ""
    candidates.sort()
    best = candidates[0]
    return {"id": best[5], "type": best[6], "intro": artefacts[best[5]]["intro"]}, len(candidates), best[7]


# ==========================================================================
# TARGET: menu budget
# ==========================================================================

def parse_menu(menu_path):
    text = strip_html_comments(read_text(menu_path))
    if not text.strip():
        return None

    open_ul = [m.start() for m in re.finditer(r"<\s*ul\b", text, re.I)]
    close_ul = [m.start() for m in re.finditer(r"<\s*/\s*ul\s*>", text, re.I)]

    def depth_at(position):
        return (sum(1 for p in open_ul if p < position)
                - sum(1 for p in close_ul if p < position))

    anchors = []
    for match in re.finditer(r"<a\b([^>]*)>(.*?)</a>", text, re.S | re.I):
        attrs, inner = match.group(1), match.group(2)
        label = re.sub(r"<[^>]*>", "", inner)
        label = re.sub(r"\s+", " ", label).strip()
        href = ""
        href_match = re.search(r'href\s*=\s*"([^"]*)"', attrs)
        if href_match:
            href = href_match.group(1)
        toggle = "dropdown-toggle" in attrs
        anchors.append({
            "label": label,
            "href": href,
            "toggle": toggle,
            "depth": depth_at(match.start()),
        })
    if not anchors:
        return None

    top_level = [a for a in anchors if a["depth"] <= 1]
    clickable = [a for a in anchors if not a["toggle"]]
    max_depth = max(a["depth"] for a in anchors)

    dropdowns = OrderedDict()
    current = None
    for anchor in anchors:
        if anchor["depth"] <= 1:
            current = anchor["label"] if anchor["toggle"] else None
            if current:
                dropdowns.setdefault(current, [])
        elif current:
            dropdowns[current].append(anchor)

    return {
        "anchors": anchors,
        "clickable": clickable,
        "top_level": top_level,
        "max_depth": max_depth,
        "dropdowns": dropdowns,
    }


class MenuBudget(object):
    """The running budget while branch-4 pages are proposed for the menu."""

    def __init__(self, menu):
        self.known = menu is not None
        self.total = len(menu["clickable"]) if menu else 0
        self.top_level = len(menu["top_level"]) if menu else 0
        self.depth = menu["max_depth"] if menu else 0
        self.dropdowns = OrderedDict(
            (name, len(children)) for name, children in menu["dropdowns"].items()
        ) if menu else OrderedDict()

    def freest_dropdown(self):
        if not self.dropdowns:
            return None, 0
        name = min(self.dropdowns, key=lambda k: self.dropdowns[k])
        return name, LIMIT_DROPDOWN_CHILDREN - self.dropdowns[name]

    def can_add_top_level(self, extra_children):
        """A new top-level entry costs 1 clickable; if it has children it
        becomes a dropdown, and this template's convention repeats the parent
        as its own first child, so that costs 1 more plus one per child."""
        cost = 1 + (1 + extra_children if extra_children else 0)
        if self.total + cost > LIMIT_MENU_TOTAL:
            return False, "total %d + %d > %d" % (self.total, cost, LIMIT_MENU_TOTAL)
        if self.top_level + 1 > LIMIT_TOP_LEVEL:
            return False, "top level %d + 1 > %d" % (self.top_level, LIMIT_TOP_LEVEL)
        if extra_children and 1 + extra_children > LIMIT_DROPDOWN_CHILDREN:
            return False, "dropdown children %d > %d" % (1 + extra_children, LIMIT_DROPDOWN_CHILDREN)
        if extra_children and LIMIT_MENU_DEPTH < 2:
            return False, "children would need depth 2 > %d" % LIMIT_MENU_DEPTH
        return True, "total %d->%d, top level %d->%d" % (
            self.total, self.total + cost, self.top_level, self.top_level + 1)

    def add_top_level(self, extra_children):
        cost = 1 + (1 + extra_children if extra_children else 0)
        self.total += cost
        self.top_level += 1
        if extra_children:
            self.depth = max(self.depth, 2)
        return cost

    def headroom_text(self):
        name, free = self.freest_dropdown()
        return "total %d free, top level %d free, freest dropdown %s (%d free)" % (
            LIMIT_MENU_TOTAL - self.total,
            LIMIT_TOP_LEVEL - self.top_level,
            name if name else "-", free)


# ==========================================================================
# TARGET: page measurements
# ==========================================================================

def measure_target_pages(target_root):
    page_dir = os.path.join(target_root, "input", "pagecontent")
    if not os.path.isdir(page_dir):
        return OrderedDict()
    pages = OrderedDict()
    for name in sorted(os.listdir(page_dir)):
        if not name.endswith(".md"):
            continue
        text = read_text(os.path.join(page_dir, name))
        heads = analyse_headings(text)
        sources = merged_sources(text)
        words = count_words(text)
        reasons = []
        if words > GATE_WORDS:
            reasons.append("%d words > %d" % (words, GATE_WORDS))
        if len(sources) > GATE_MERGED_SOURCES:
            reasons.append("%d merged sources > %d" % (len(sources), GATE_MERGED_SOURCES))
        if heads["repeated"]:
            reasons.append("%d repeated heading title(s)" % len(heads["repeated"]))
        pages[name[:-3]] = {
            "file": name,
            "words": words,
            "by_level": heads["by_level"],
            "repeated": heads["repeated"],
            "collisions": heads["collisions"],
            "sources": sources,
            "gate_reasons": reasons,
        }
    return pages


# ==========================================================================
# routing
# ==========================================================================

def agreed_pages(target_root, menu, target_pages):
    """The agreed page set, READ from the target: every local page the menu
    links to, plus every file in input/pagecontent.  Titles are kept so a
    source page can match a link-only menu entry by its label (the way
    "Datasets and Descriptions" points at logical-models.html)."""
    by_slug = OrderedDict()
    by_title = OrderedDict()
    if target_pages:
        for slug in target_pages:
            by_slug[slug] = slug
    if menu:
        for anchor in menu["clickable"]:
            href = anchor["href"]
            if not href or "://" in href or href.startswith("#"):
                continue
            slug = re.sub(r"\.html?$", "", href.split("/")[-1])
            if not slug:
                continue
            by_slug.setdefault(slug, slug)
            label = anchor["label"]
            label = re.sub(r"\s*\((optional|opt\.)\)\s*$", "", label, flags=re.I).strip()
            if label:
                by_title.setdefault(compact(label), slug)
    if not by_slug and not target_root:
        for slug in FALLBACK_AGREED_PAGES:
            by_slug[slug] = slug
    # Case-insensitive aliases.  Target page files are lower case; Simplifier
    # guide pages are CamelCase (`Index.page.md`, `Downloads.page.md`), so
    # without the alias the exact-name match never fires on a guide tree.  For a
    # `pages:` source, whose names are already lower case, this adds nothing.
    for slug in list(by_slug):
        by_slug.setdefault(slug.lower(), by_slug[slug])
    return by_slug, by_title


def route(nodes, artefacts, frequency, agreed_slug, agreed_title,
          target_pages, budget, folder_landing_pages=False):
    """Fill node.branch / .destination / .measurement for every source page.

    Evaluation order (the branch NUMBER reported is always the spec's):
      0  an EXACT agreed-page name or menu-label match decides rule 3 first -
         a page the humans already agreed on is a stronger signal than a
         name-similarity match against an artefact id;
      1  artefact anchor  -> rule 1;
      2  family overview  -> rule 2;
      3  fuzzy agreed-page match -> rule 3;
      4  everything else  -> rule 4 (+ 4a presentation, 4b visibility).

    `folder_landing_pages` is set for a Simplifier guide tree, where every
    folder ships an `Index.page.md`.  Only the one at level 1 is the guide's
    index; the deeper ones are FOLDER landing pages and must not all be merged
    into the target's `index.md`, so the name match is suppressed for them and
    they are routed by their children like any other overview.
    """
    # -- pass 1: artefact anchors -----------------------------------------
    for node in nodes:
        anchor, count, how = match_artefact(node.slug, artefacts, frequency)
        node.anchor = anchor
        node.anchor_candidates = count
        node.anchor_how = how

    # -- pass 2: branches 0-3 ---------------------------------------------
    for node in nodes:
        exact = agreed_slug.get(node.slug) or agreed_slug.get(node.slug.lower())
        by_label = agreed_title.get(compact(node.title)) if node.title else None
        if (folder_landing_pages and node.level > 1
                and node.slug.lower() == "index"):
            exact = by_label = None
            node.notes.append("folder landing page - NOT matched against the target's "
                              "index.md; routed by its own children")
        distinct_children = {c.anchor["id"] for c in node.children if c.anchor}
        node.is_family = len(node.children) >= 2 and len(distinct_children) >= 2

        if exact:
            node.branch = "3"
            node.destination = "%s.md" % exact
            node.measurement = "agreed page named '%s' exists in the target" % exact
        elif node.anchor and not node.is_family:
            node.branch = "1"
            node.destination = "input/intro-notes/%s-%s-intro.md" % (
                node.anchor["type"], node.anchor["id"])
            node.measurement = "%s match on %s (%d candidate artefact%s%s)" % (
                node.anchor_how, node.anchor["id"], node.anchor_candidates,
                "" if node.anchor_candidates == 1 else "s",
                "; intro note already present" if node.anchor["intro"] else "")
        elif node.is_family:
            node.branch = "2"
            types = Counter(c.anchor["type"] for c in node.children if c.anchor)
            dominant = types.most_common(1)[0][0]
            host = TYPE_INDEX_PAGE.get(dominant, "artifacts")
            if target_pages and host not in target_pages:
                node.notes.append("host '%s' is not an agreed page in this target - confirm the host" % host)
            node.destination = "h3/h4 section on %s.md" % host
            node.measurement = "%d children, %d anchoring distinct artefacts (%s)" % (
                len(node.children), len(distinct_children), dominant)
        elif by_label:
            node.branch = "3"
            node.destination = "%s.md" % by_label
            node.measurement = "menu label '%s' points at %s.html" % (node.title, by_label)
        else:
            node.branch = ""          # decided in pass 3

    # -- pass 3: inherited routing ----------------------------------------
    # A child of a single-artefact page belongs in the SAME intro note; a child
    # of a family overview without its own anchor is a subsection of that same
    # overview.  Both are measurements about the source tree, not judgements.
    for node in nodes:
        if node.branch or node.parent is None:
            continue
        parent = node.parent
        if parent.branch == "1" and not node.anchor:
            node.branch = "1"
            node.destination = parent.destination
            node.measurement = "child of single-artefact page %s (no anchor of its own)" % parent.filename
        elif parent.branch == "2" and not node.anchor:
            node.branch = "2"
            node.destination = parent.destination
            node.measurement = "child of family overview %s (no anchor of its own)" % parent.filename

    # -- pass 4: branch 4, presentation and visibility ---------------------
    queue1 = []
    for node in nodes:
        if node.branch:
            # rule 5, size gate on the SOURCE page being merged: a page that
            # already exceeds the gate on its own puts the host over it.
            if node.branch in ("2", "3") and node.words > GATE_WORDS:
                node.notes.append("source page is %d words > %d - merging it trips the "
                                  "host's size gate on its own (rule 5)"
                                  % (node.words, GATE_WORDS))
            # rule 5, size gate on the HOST of a branch-2 / branch-3 merge
            if node.branch in ("2", "3") and target_pages:
                host_slug = re.sub(r"\.md$", "", node.destination.split()[-1])
                host = target_pages.get(host_slug)
                if host and host["gate_reasons"]:
                    node.notes.append("host %s.md already trips the size gate (%s) - rule 5"
                                      % (host_slug, "; ".join(host["gate_reasons"])))
            continue

        node.branch = "4"
        child_count = len(node.children)
        presentation = "HUB" if child_count >= HUB_CHILDREN else "merged page"
        measure_bits = ["no artefact anchor", "no agreed page", "%d child page(s)" % child_count]

        if not budget.known:
            visibility = "menu decision UNKNOWN (no --target)"
            node.destination = "own page (%s), %s" % (presentation, visibility)
            node.measurement = "; ".join(measure_bits)
            continue

        if node.level == 1:
            extra = sum(1 for c in node.children if c.branch == "4") if child_count else 0
            ok, why = budget.can_add_top_level(extra)
            if ok:
                budget.add_top_level(extra)
                visibility = "MENU entry (top level); %s; remaining after: %s" % (
                    why, budget.headroom_text())
            else:
                name, free = budget.freest_dropdown()
                visibility = "pages:-NESTED under its host (menu budget: %s)" % why
                queue1.append(
                    "%s - proposed as its own page but the menu budget is full (%s); "
                    "nested in pages:/ToC instead. Remaining capacity is inside a dropdown "
                    "(%s: %d free) - the human may spend the budget differently."
                    % (node.filename, why, name if name else "-", free))
        else:
            parent_in_menu = (node.parent is not None
                              and node.parent.branch == "4"
                              and "MENU entry" in (node.parent.destination or ""))
            if parent_in_menu:
                visibility = "MENU entry (child of %s); depth 2 <= %d" % (
                    node.parent.filename, LIMIT_MENU_DEPTH)
            else:
                visibility = "pages:-NESTED under %s (its host has no menu entry)" % (
                    node.parent.filename if node.parent else "its host")
                queue1.append(
                    "%s - nested under %s because that host got no menu entry of its own; "
                    "giving this page one directly would put it at menu depth %d > %d, so it "
                    "only becomes visible if the human buys the host a top-level entry first."
                    % (node.filename,
                       node.parent.filename if node.parent else "-",
                       LIMIT_MENU_DEPTH + 1, LIMIT_MENU_DEPTH))
        node.destination = "own page (%s), %s" % (presentation, visibility)
        node.measurement = "; ".join(measure_bits)

    return queue1


# ==========================================================================
# report
# ==========================================================================

def md_escape(text):
    return text.replace("|", "\\|")


def render_tree(nodes, roots, lines, prefix=""):
    for index, node in enumerate(roots):
        last = index == len(roots) - 1
        lines.append("%s%s %s  `%s`" % (prefix, "`-" if last else "|-",
                                        node.title or node.slug, node.filename))
        if node.children:
            render_tree(nodes, node.children,
                        lines, prefix + ("   " if last else "|  "))


def build_report(args, source_info, target_info, nodes, roots, queue1, budget):
    out = []
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out.append("# Page-structure advice")
    out.append("")
    out.append("**This report PROPOSES and never edits.** It reads the source and target "
               "repositories read-only and writes nothing into either of them. Every routing "
               "row below is the branch the MEASUREMENTS support - a human (or the skill at "
               "step 5) decides and applies it.")
    out.append("")
    out.append("| Input | Value |")
    out.append("| --- | --- |")
    out.append("| source repo | `%s` |" % md_escape(args.source))
    out.append("| target repo | `%s` |" % md_escape(args.target or "(not given)"))
    out.append("| generated | %s |" % now)
    out.append("| script | `page-structure-advice.py` v%s |" % SCRIPT_VERSION)
    out.append("")
    out.append("Contract limits in force: menu total <= %d, dropdown children <= %d, "
               "top level <= %d, menu depth <= %d; size gate at > %d words, > %d merged "
               "sources, or ANY repeated heading title; hub at >= %d children."
               % (LIMIT_MENU_TOTAL, LIMIT_DROPDOWN_CHILDREN, LIMIT_TOP_LEVEL,
                  LIMIT_MENU_DEPTH, GATE_WORDS, GATE_MERGED_SOURCES, HUB_CHILDREN))
    out.append("")

    # ---- 1. source ------------------------------------------------------
    out.append("## 1. Source page tree")
    out.append("")
    out.append("The tree is taken from the FIRST of three inputs that yields pages: "
               "**(a)** the `pages:` block of the source `sushi-config.yaml`, **(b)** the "
               "authoritative Simplifier guide tree under `%s/` (spec 5.1a), "
               "**(c)** a flat count of `input/pagecontent/*.md`." % GUIDE_DIR_NAME)
    out.append("")
    out.append("**Input used: %s.**" % source_info["origin_label"])
    out.append("")

    guide = source_info.get("guide") or {}
    trees = guide.get("trees") or []
    if trees:
        out.append("### 1.0 Simplifier guide trees found")
        out.append("")
        out.append("Every tree under `%s/` is listed - the choice is never made silently. "
                   "Dispositions follow spec 5.1a: #1 authoritative, #2 parallel-language "
                   "harvest seed, #3 historical/shared retained, #4 unrecognized."
                   % GUIDE_DIR_NAME)
        out.append("")
        out.append("| Guide tree | Title | Version (dir name) | Version (guide.yaml) | Lang | "
                   "`*.page.md` on disk | Disposition |")
        out.append("| --- | --- | --- | --- | --- | ---: | --- |")
        for tree in trees:
            out.append("| `%s` | %s | %s | %s | %s | %d | %s |" % (
                tree["name"], md_escape(tree["title"] or "-"),
                tree["version_name"] or "-", tree["version_yaml"] or "-",
                tree["language"] or "-", tree["page_files"],
                md_escape(tree["disposition"])))
        out.append("")
        if guide.get("chosen"):
            out.append("**Chosen: `%s`** - %s." % (guide["chosen"]["name"],
                                                   md_escape(guide["reason"])))
        else:
            out.append("**No tree chosen** - %s." % md_escape(guide["reason"]))
        out.append("")
        out.append("The module's narrative language read from `sushi-config.yaml` "
                   "`language:` is **%s**." % (guide.get("module_language") or "not stated"))
        out.append("")
        for note in guide.get("notes") or []:
            out.append("- %s" % note)
        if guide.get("notes"):
            out.append("")
        out.append("**A human can override this choice**: re-run with "
                   "`--guide-tree <directory name>`. The ranking above is evidence, not a "
                   "verdict - confirm it against the rendered IG and record it in the "
                   "inventory (Gate B reviews it).")
        out.append("")
        if source_info["origin"] != "guide-tree":
            out.append("_These trees were NOT used: the `pages:` block already yielded a page "
                       "tree, and input (a) wins. They still need a disposition in the "
                       "inventory._")
            out.append("")

    if not nodes:
        out.append("### 1.1 No page tree could be built")
        out.append("")
        out.append("`sushi-config.yaml` has no usable `pages:` block and no guide tree under "
                   "`%s/` yielded pages, so the source page tree is **flat/unknown** - it is "
                   "not reconstructed here. Counted instead: **%d** files in "
                   "`input/pagecontent/`." % (GUIDE_DIR_NAME, source_info["file_count"]))
        out.append("")
        out.append("Every routing row below therefore carries no depth evidence; treat the "
                   "parent/child measurements as absent, not as zero.")
        out.append("")
    else:
        out.append("### 1.1 Depth histogram")
        out.append("")
        out.append(source_info["tree_note"])
        out.append("")
        out.append("| Level | Pages | Share |")
        out.append("| --- | ---: | ---: |")
        total = len(nodes)
        for level in sorted(source_info["histogram"]):
            count = source_info["histogram"][level]
            out.append("| %d | %d | %.0f%% |" % (level, count, 100.0 * count / total))
        out.append("| **total** | **%d** | 100%% |" % total)
        out.append("")
        out.append("Maximum depth used: **%d**. Total words across the %d source pages: "
                   "**%d**. Pages in `input/pagecontent/`: **%d**."
                   % (max(source_info["histogram"]), total,
                      sum(node.words for node in nodes), source_info["file_count"]))
        out.append("")
        if source_info["findings"]:
            out.append("### 1.1a Structural findings in the source tree")
            out.append("")
            out.append("Reported, never silently absorbed - each one is a page the migration "
                       "would otherwise lose or invent.")
            out.append("")
            for finding in source_info["findings"]:
                out.append("- %s" % finding)
            out.append("")
        out.append("### 1.2 Parent-child tree")
        out.append("")
        out.append("```")
        tree_lines = []
        render_tree(nodes, roots, tree_lines)
        out.extend(tree_lines)
        out.append("```")
        out.append("")

    # ---- 2. target pages ------------------------------------------------
    out.append("## 2. Target page measurements")
    out.append("")
    if not target_info["pages"]:
        out.append("_No target given (or `input/pagecontent/` is empty) - size gate not measured._")
        out.append("")
    else:
        out.append("Words = whitespace tokens after removing HTML comments, table separator "
                   "rows and the markup characters `>`, `|`, `*`, `_`, `` ` ``. Headings, list "
                   "items, table cells and fenced code all count: the gate measures what the "
                   "reader has to traverse. Repeated titles are compared case-sensitively; each "
                   "repeat costs one publisher-appended anchor (`-2`, `-3`, ...). Merged "
                   "sources are the distinct `<!-- source: X.md -->` section markers the "
                   "migration itself left behind.")
        out.append("")
        out.append("| Page | Words | h2 | h3 | h4 | other h | Repeated titles | Anchor collisions | Merged sources | Size gate |")
        out.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
        for slug, page in target_info["pages"].items():
            levels = page["by_level"]
            other = sum(count for level, count in levels.items() if level not in (2, 3, 4))
            gate = "**TRIPS** - " + "; ".join(page["gate_reasons"]) if page["gate_reasons"] else "ok"
            out.append("| `%s.md` | %d | %d | %d | %d | %d | %d | %d | %d | %s |" % (
                slug, page["words"], levels.get(2, 0), levels.get(3, 0), levels.get(4, 0),
                other, len(page["repeated"]), len(page["collisions"]),
                len(page["sources"]), md_escape(gate)))
        out.append("")
        tripped = [(s, p) for s, p in target_info["pages"].items() if p["gate_reasons"]]
        if tripped:
            out.append("### 2.1 Pages that trip the size gate")
            out.append("")
            for slug, page in tripped:
                out.append("- **`%s.md`** - %s." % (slug, "; ".join(page["gate_reasons"])))
                if page["repeated"]:
                    out.append("  - repeated titles: %s" % ", ".join(
                        '"%s" (x%d)' % (title, count) for title, count in page["repeated"].items()))
                if page["collisions"]:
                    out.append("  - collided anchors: %s" % ", ".join(
                        "`#%s`" % anchor for anchor in page["collisions"]))
                if len(page["sources"]) > GATE_MERGED_SOURCES:
                    out.append("  - merged sources: %s" % ", ".join(
                        "`%s`" % source for source in page["sources"]))
                out.append("  - rule 5: re-run routing preferring branches 1 and 2, or split.")
            out.append("")

    # ---- 3. menu budget -------------------------------------------------
    out.append("## 3. Menu budget")
    out.append("")
    menu = target_info["menu"]
    if not menu:
        out.append("_No `input/includes/menu.xml` (or no `--target`) - the menu budget is "
                   "UNKNOWN and no visibility decision is proposed below._")
        out.append("")
    else:
        clickable = len(menu["clickable"])
        top_level = len(menu["top_level"])
        widest = max(menu["dropdowns"].items(), key=lambda kv: len(kv[1])) if menu["dropdowns"] else ("-", [])
        out.append("Clickable entries are the menu's real destinations: every `<li><a>` except "
                   "the dropdown toggles, which only repeat their first child's href.")
        out.append("")
        out.append("| Metric | Measured | Contract limit | Headroom |")
        out.append("| --- | ---: | ---: | ---: |")
        out.append("| total clickable entries | %d | %d | %d |" % (
            clickable, LIMIT_MENU_TOTAL, LIMIT_MENU_TOTAL - clickable))
        out.append("| widest dropdown (%s) | %d | %d | %d |" % (
            widest[0], len(widest[1]), LIMIT_DROPDOWN_CHILDREN,
            LIMIT_DROPDOWN_CHILDREN - len(widest[1])))
        out.append("| top-level entries | %d | %d | %d |" % (
            top_level, LIMIT_TOP_LEVEL, LIMIT_TOP_LEVEL - top_level))
        out.append("| menu depth used | %d | %d | %d |" % (
            menu["max_depth"], LIMIT_MENU_DEPTH, LIMIT_MENU_DEPTH - menu["max_depth"]))
        out.append("")
        out.append("| Dropdown | Children | Free (of %d) |" % LIMIT_DROPDOWN_CHILDREN)
        out.append("| --- | ---: | ---: |")
        for name, children in menu["dropdowns"].items():
            out.append("| %s | %d | %d |" % (md_escape(name), len(children),
                                             LIMIT_DROPDOWN_CHILDREN - len(children)))
        out.append("")
        out.append("After the proposals in section 4: %s." % budget.headroom_text())
        out.append("")

    # ---- 4. routing proposal -------------------------------------------
    out.append("## 4. Routing proposal (spec 9d/9e)")
    out.append("")
    if not nodes:
        out.append("_No source page tree could be built (no `pages:` block and no guide tree "
                   "with pages) - no per-source-page routing is proposed. Route the %d files "
                   "in `input/pagecontent/` by hand, or add the block._"
                   % source_info["file_count"])
        out.append("")
    else:
        out.append("One row per source page. The branch number is the spec's; the measurement "
                   "column is the number that forced it. Branch-4 rows state the presentation "
                   "(4a) and the visibility (4b), and, where a menu entry fits, the remaining "
                   "budget after it. `Words` is the source page's own size, counted the same "
                   "way as the target pages in section 2.")
        out.append("")
        out.append("| # | Source page | Lvl | Children | Words | Branch | Proposed destination | Measurement |")
        out.append("| ---: | --- | ---: | ---: | ---: | --- | --- | --- |")
        branch_label = {
            "1": "1 intro-note",
            "2": "2 section on index page",
            "3": "3 merge into agreed page",
            "4": "4 own page",
        }
        for index, node in enumerate(nodes, 1):
            destination = node.destination
            if node.notes:
                destination += " <br>_(%s)_" % "; ".join(node.notes)
            out.append("| %d | `%s` | %d | %d | %d | %s | %s | %s |" % (
                index, node.filename, node.level, len(node.children), node.words,
                branch_label.get(node.branch, node.branch),
                md_escape(destination), md_escape(node.measurement)))
        out.append("")
        counts = Counter(node.branch for node in nodes)
        out.append("Branch totals: " + ", ".join(
            "%s = %d" % (branch_label.get(b, b), counts[b]) for b in sorted(counts)) + ".")
        out.append("")

    # ---- 5. queue 1 -----------------------------------------------------
    out.append("## 5. Report queue 1 items")
    out.append("")
    if queue1:
        out.append("The menu budget forced a ToC-nesting where a menu entry was otherwise "
                   "warranted. Allocation below is first-come-first-served in source document "
                   "order; the human may spend the budget differently.")
        out.append("")
        for item in queue1:
            out.append("- %s" % item)
        out.append("")
    else:
        out.append("_None from the menu budget._")
        out.append("")
    gate_items = [(s, p) for s, p in target_info["pages"].items() if p["gate_reasons"]] \
        if target_info["pages"] else []
    if gate_items:
        out.append("Size-gate trips (rule 5) needing a routing re-run or a split:")
        out.append("")
        for slug, page in gate_items:
            out.append("- `%s.md` - %s." % (slug, "; ".join(page["gate_reasons"])))
        out.append("")

    # ---- 6. run-log lines ----------------------------------------------
    if nodes:
        out.append("## 6. Suggested `5.4c page-routing` run-log lines")
        out.append("")
        out.append("One per source page, ready for the migration run log. The script does not "
                   "write them; it only formats them.")
        out.append("")
        out.append("```")
        for node in nodes:
            out.append("5.4c page-routing\t%s\tbranch=%s\t%s\t%s" % (
                node.filename, node.branch,
                node.destination.replace("\t", " "),
                node.measurement.replace("\t", " ")))
        out.append("```")
        out.append("")

    return "\n".join(out) + "\n"


# ==========================================================================
# main
# ==========================================================================

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Measure the evidence behind the spec 9d/9e page-routing decision. "
                    "Proposes only; never edits a repository.")
    parser.add_argument("--source", required=True, help="the ORIGINAL module repository")
    parser.add_argument("--target", help="the MIGRATED repository (optional)")
    parser.add_argument("--out", help="write the Markdown report here (default: stdout)")
    parser.add_argument("--guide-tree", dest="guide_tree",
                        help="HUMAN OVERRIDE: the directory name under "
                             "implementation-guides/ to treat as authoritative")
    args = parser.parse_args(argv)

    source_root = os.path.abspath(args.source)
    target_root = os.path.abspath(args.target) if args.target else None
    if not os.path.isdir(source_root):
        parser.error("--source is not a directory: %s" % source_root)
    if target_root and not os.path.isdir(target_root):
        parser.error("--target is not a directory: %s" % target_root)

    if args.out:
        out_path = os.path.abspath(args.out)
        # The rule this guard exists for is "never change a module": not the
        # source (read-only by definition) and no CONTENT of the target. The
        # target's `migration-log/` is the migration's own workspace, where
        # every other artefact of the run already lives and is committed with
        # the branch -- refusing it sent the report to /tmp, away from the
        # evidence it belongs beside (measured on the Onkologie try-run, where
        # the natural invocation failed outright).
        if source_root and (out_path == source_root
                            or out_path.startswith(source_root + os.sep)):
            parser.error("refusing to write inside the --source repository: %s "
                         "(the source is read-only)" % out_path)
        if target_root and (out_path == target_root
                            or out_path.startswith(target_root + os.sep)):
            log_dir = os.path.join(target_root, "migration-log") + os.sep
            if not out_path.startswith(log_dir):
                parser.error("refusing to write into the target's CONTENT: %s "
                             "(this script never edits a module; write to "
                             "%smigration-log/ instead)" % (out_path, target_root + os.sep))

    # ---- source ---------------------------------------------------------
    # Fallback order, spec 9d/9e: (a) the sushi-config `pages:` block, (b) the
    # authoritative Simplifier guide tree, (c) a flat file count.  A module that
    # authors its narrative on Simplifier - the normal MII shape - has no usable
    # `pages:` block, and reporting "0 source pages" for it made the routing
    # rule unusable exactly where it matters most.
    config_path = os.path.join(source_root, "sushi-config.yaml")
    if not os.path.isfile(config_path):
        config_path = os.path.join(source_root, "sushi-config.yml")
    config_text = read_text(config_path)
    config_rel = os.path.relpath(config_path, source_root)

    page_dir = os.path.join(source_root, "input", "pagecontent")
    file_count = len([n for n in os.listdir(page_dir) if n.endswith(".md")]) \
        if os.path.isdir(page_dir) else 0

    roots, nodes, found = parse_pages_block(config_text)
    for node in nodes:
        path = os.path.join(page_dir, node.filename)
        if os.path.isfile(path):
            node.words = count_words(read_text(path))

    module_language = source_language(config_text)
    trees = discover_guide_trees(source_root)
    guide_info = {
        "trees": trees,
        "chosen": None,
        "reason": "",
        "notes": [],
        "module_language": module_language,
    }
    findings = []
    origin = "pages-block" if found else "flat"
    origin_label = ("(a) the `pages:` block of `%s`" % config_rel) if found else \
                   ("(c) a flat count of `input/pagecontent/*.md` - "
                    "no page tree available")
    tree_note = "Parsed from `%s`, indentation-based." % config_rel
    folder_landing_pages = False

    if trees:
        chosen, reason, notes = choose_guide_tree(
            trees, module_language, None if found else args.guide_tree)
        if found and args.guide_tree:
            notes.append("`--guide-tree` was given but the `pages:` block already yielded a "
                         "page tree, and input (a) wins - the override had no effect.")
        guide_info.update({"chosen": chosen, "reason": reason, "notes": notes})
        label_dispositions(trees, chosen)

        if not found and chosen is not None:
            guide_roots, guide_nodes, walk = walk_guide_tree(chosen["path"])
            if guide_nodes:
                roots, nodes = guide_roots, guide_nodes
                origin = "guide-tree"
                origin_label = ("(b) the Simplifier guide tree `%s/%s`, walked from its "
                                "`toc.yaml`" % (GUIDE_DIR_NAME, chosen["name"]))
                folder_landing_pages = True
                tree_note = (
                    "Walked from `%s/%s/toc.yaml`: an entry whose `filename` ends in "
                    "`%s` is a page, any other `filename` is a sub-directory holding its "
                    "own `toc.yaml`. A sub-directory is a LEVEL, not a page, so every page "
                    "of one directory shares one level (that is how Simplifier renders a "
                    "folder), and the levels are shifted so the shallowest page sits at "
                    "level 1 - this guide's root `toc.yaml` lists only a folder, which adds "
                    "no page level. Routing still needs a page parent, so each directory is "
                    "represented by its `Index.page.md` and its remaining pages plus its "
                    "sub-folders' representatives become that page's children; a parent may "
                    "therefore share its children's level."
                    % (GUIDE_DIR_NAME, chosen["name"], PAGE_SUFFIX))
                for rel_dir in walk.dirs_without_toc:
                    findings.append("`%s/` has **no `toc.yaml`** - the hierarchy of that "
                                    "subtree is derived from DIRECTORY NESTING, not from a "
                                    "table of contents. Order and titles are the file "
                                    "system's, not the author's." % rel_dir)
                for rel_dir in walk.dirs_unreached:
                    findings.append("`%s/` holds pages but **no `toc.yaml` links to it** - "
                                    "its pages are placed by directory nesting and are "
                                    "invisible in the rendered guide's navigation."
                                    % rel_dir)
                for rel_toc, filename, why in walk.dangling:
                    findings.append("`%s` lists `%s`, but the **%s** - the entry is dangling "
                                    "and produced no page." % (rel_toc, filename, why))
                for rel_page, why in walk.unreferenced:
                    findings.append("`%s` exists on disk but is **%s** - it is in the tree "
                                    "below, flagged, so the migration cannot lose it."
                                    % (rel_page, why))
            else:
                guide_info["notes"].append(
                    "guide tree `%s` yielded no pages when walked; fell back to the flat "
                    "file count." % chosen["name"])

    source_info = {
        "found": found,
        "origin": origin,
        "origin_label": origin_label,
        "tree_note": tree_note,
        "guide": guide_info,
        "findings": findings,
        "file_count": file_count,
        "histogram": Counter(node.level for node in nodes),
        "config_rel": config_rel,
    }

    # ---- target ---------------------------------------------------------
    target_pages = measure_target_pages(target_root) if target_root else OrderedDict()
    menu = parse_menu(os.path.join(target_root, "input", "includes", "menu.xml")) \
        if target_root else None
    target_info = {"pages": target_pages, "menu": menu}

    # ---- routing --------------------------------------------------------
    artefacts = collect_artefacts(source_root, target_root)
    frequency = build_token_frequency(artefacts)
    slug_index, title_index = agreed_pages(target_root, menu, target_pages)
    budget = MenuBudget(menu)
    queue1 = route(nodes, artefacts, frequency, slug_index, title_index,
                   target_pages, budget, folder_landing_pages) if nodes else []

    report = build_report(args, source_info, target_info, nodes, roots, queue1, budget)

    if args.out:
        directory = os.path.dirname(os.path.abspath(args.out))
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(report)
        sys.stderr.write(
            "page-structure-advice: %d source pages (from %s), %d target pages, "
            "%d artefacts -> %s\n"
            % (len(nodes), source_info["origin"], len(target_pages),
               len(artefacts), args.out))
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
