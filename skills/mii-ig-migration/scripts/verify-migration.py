#!/usr/bin/env python3
"""verify-migration -- the migration's VERIFICATION PHASE: four mechanical layers
plus the run log as a second oracle, one verdict per check, and an exit status.

WHY THIS EXISTS. Until now `SKILL.md`'s *Verification* section was a list of
sentences a human was asked to perform: "every placeholder accounted for", "the
German pages render", "every step appears in the log". Four real migrations
(Dokument, Person, Consent, Labor) shipped with a GREEN build and a signed-off
prose checklist, and every one of the following defects survived it -- because a
passing build does not surface any of them and a human reading a checklist does
not either:

  * UNREACHABLE CONTENT. Consent renders SearchParameter pages that
    `artifacts.html` does not list. The artifact SET comparison passes: the
    artefacts are all present. They are simply unreachable from the index, which
    is a different property and was checked by nothing.
  * STALE PROVENANCE. A rendered IG whose header reports one template version
    while the tree carries another -- the same class as a published `demo/v0.5.1`
    directory whose pages read "Preview v0.5.0". Nothing compared the RENDERED
    output against the tree it was supposedly built from.
  * A RENDERED METADATA DEFECT. Dokument renders `Unknown region code '276'` in
    its page header (measured 2026-08-06 on the published preview,
    `<div id="ig-status">`). qa.txt reports zero errors for it.
  * SILENT TRUNCATION. An FSH parse error stopped SUSHI reading a file while it
    still EXPORTED the instance: nested provisions 1/1/1 before repair, 6/27/3
    after, zero errors reported for those files.
  * SILENT PARTIAL CONVERSION. goFSH exits 0 reporting "0 Errors" having
    converted 1 of 20 inputs when `-t json-and-xml` is omitted.
  * A WRONG DEPENDENCY PIN. A run resolved a parent from `dist-tags.latest`
    (2.0.3) where the source package pinned 2.0.2.
  * SILENT RELICENSING. The template ships `license: CC-BY-4.0` as a LITERAL
    that no placeholder check flags, while the module is CC0-1.0.

Each of those is mechanically detectable. So this script detects them, reports
each as a finding with its evidence, and EXITS NON-ZERO. A verification step that
cannot fail is decoration.

THE THREE VERDICTS. Two would be a lie. A check that genuinely cannot be
mechanised here must not be silently written as a pass:

  IDENTISCH      the check ran and the target matches its reference.
  DIVERGIERT     the check ran and found a divergence, NAMED, with evidence.
  NICHT PRUEFBAR the check could not run -- an input is absent, or the property
                 is a human judgement. It carries the exact reason and the exact
                 human action, and it is NOT a pass: the exit status distinguishes
                 it (3) from a clean run (0).

TWO ORACLES, AND WHY. The run log records what each step INTENDED AND MEASURED;
the target tree records the OUTCOME. Defects live in the gap between them, and
neither source reveals them alone: a log saying "converted 20 of 20" beside a
tree holding 19 resources is a finding that the log alone (all green) and the
tree alone (19 files, no reference point) both miss. So the layers below read the
source-versus-target comparison AND `migration-log/run.log`, and cross-check the
two -- conversion counts, page counts, artifact counts.

THE LAYERS

  1 CONSERVATION -- every source artefact present AND REACHABLE from the artifact
    index; every source guide page migrated (naming the target page), retired
    (with a reason) or MISSING (a failure); every source narrative text run
    present somewhere in the target; every menu entry leading somewhere and every
    narrative page IN a menu; every target page traceable to a source page or to
    the template; and, for text that survived, WHICH page it landed on.
  2 FIDELITY -- identity IDENTISCH; dependency pins identical to the source's;
    `license` explicitly asserted from a source tier, never silently defaulted.
  3 PROVENANCE -- the template package+version READ OUT OF THE RENDERED OUTPUT
    against the tree it was built from and against the latest release; the IG
    Publisher version; the pinned source-guide version.
  4 RENDERING INTEGRITY -- tables, structure views, tabs and images non-empty in
    the target where non-empty in the source; header/footer metadata sane;
    language parity (the translated variant actually translated, not a
    default-language fallback).
  L THE RUN LOG AS A SECOND ORACLE -- an emitted-and-never-actioned
    `silent-partial-success:` WARN; a step that emitted NO line at all (a step
    that did not run is invisible otherwise); an `identity-contradiction:` still
    open; and the log-versus-artefact cross-checks.

ONE MEASURED TRAP, ENCODED (spec section 11.3). The ig-template PACKAGE version
and the module-template REPO release are DIFFERENT NUMBERS. Measured 2026-08-06:
repo tag `v0.6.0` vendors `ig-template/package/package.json` version `0.5.1`, and
repo tag `v0.5.1` vendors `0.3.0`. A check that compares the rendered
`Templates: de.medizininformatikinitiative.template#0.5.1` against the repo's
latest release `v0.6.0` therefore reports a confident, WRONG finding. P1 compares
the rendered value against the VENDORED PACKAGE (like with like) and P2 compares
the vendored REPO REF against the latest release -- two checks, two references.

FALSE POSITIVES ARE WORSE THAN NO CHECK, because a verification phase that cries
wolf gets skipped. Where a property could plausibly be legitimate, this script
reports NICHT PRUEFBAR or an INFO note rather than a divergence, and every
finding carries the evidence needed to dismiss it in one look.

Usage:

  verify-migration.py --target DIR [options]

    --target DIR          the migrated module repository (default: `.`)
    --source DIR          the UNMIGRATED source tree. Without it the checks that
                          need a reference report NICHT PRUEFBAR, never a pass.
    --rendered DIR        the built site (default: <target>/output). Its per-
                          language variant directories are discovered by looking
                          for `artifacts.html`.
    --log FILE            the run log (default: <target>/migration-log/run.log)
    --harvest-tsv FILE    guide-harvest manifest (default: migration-log/guide-harvest.tsv)
    --harvest-dir DIR     harvested Markdown (default: migration-log/guide-harvest/pagecontent)
    --source-html DIR     harvested source HTML, for the comparative render checks
                          (default: migration-log/guide-harvest/html)
    --page-map FILE       source page -> target page ledger, TSV, written by step 5
                          (default: migration-log/page-map.tsv). Columns:
                          source_page, target_page (or RETIRED), reason.
    --source-lang LANG    the language the source narrative is written in
                          (default: de) -- the text-run check compares against
                          the target pages in THAT language, because the other
                          language is a translation and would never match.
    --template-latest V   the module template's latest RELEASE tag, e.g. v0.6.0.
                          Absent -> P2 is NICHT PRUEFBAR, never a pass.
    --publisher-pin V     the IG Publisher version pinned in the target's build
                          workflow. Absent -> read from the workflow if findable.
    --expected-steps FILE the step manifest (default: the skill's
                          references/expected-steps.tsv)
    --template-pages FILE the template's OWN narrative pages, so C5 can tell a
                          template scaffold from a page invented during the
                          migration (default: the skill's
                          references/template-pages.tsv)
    --shape A|B           source shape; inferred from the log when omitted.
    --layers LIST         comma-separated subset of
                          conservation,fidelity,provenance,rendering,log
    --findings FILE       findings TSV  (default: migration-log/verification-findings.tsv)
    --markdown FILE       report block  (default: migration-log/verification.md)
    --max-list N          how many subjects a WARN names inline (default 3)
    -h, --help            print this text and exit 0

Exit codes:
    0  every check IDENTISCH
    1  at least one DIVERGIERT
    2  setup error (nothing written)
    3  no divergence, but at least one NICHT PRUEFBAR -- verification INCOMPLETE,
       which is not the same as passed and must not be reported as one

Run-log lines (spec section 10.2) go to stdout, so this script is wrapped as
`bash "$ML" run 11 verify-migration --emits-runlog -- python3 .../verify-migration.py …`.

stdlib only, like the rest of the catalog's scripts.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sys
import time

# --- run-log convention (spec section 10) -----------------------------------
STEP = "11"          # SKILL.md step 7b
ACTION = "verify-migration"
_LEVEL = {"INFO": "INFO ", "WARN": "WARN ", "ERROR": "ERROR"}

# `migration-log.sh run` exports this; wrapped, our own opening/closing lines
# become `params`/`result` so one execution yields one `start` and one `done`.
WRAPPED = os.environ.get("MIGRATION_LOG_WRAPPED") == "1"
OPEN_WORD = "params" if WRAPPED else "start"
CLOSE_WORD = "result" if WRAPPED else "done"

IDENT = "IDENTISCH"
DIVERG = "DIVERGIERT"
UNMECH = "NICHT PRUEFBAR"   # ASCII in the machine-readable column; the report
                            # template prints it as "NICHT PRÜFBAR".

LAYERS = ("conservation", "fidelity", "provenance", "rendering", "log")


def log(level, detail, cont=(), step=STEP, action=ACTION):
    """One run-log line plus indented continuations, flushed immediately.

    The flush is not a nicety: stdout is block-buffered when it is a pipe while
    stderr is not, so without it an ERROR written last surfaces FIRST in the
    captured log (measured on this skill's other scripts).
    """
    stream = sys.stderr if level == "ERROR" else sys.stdout
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print("%s  %s  %s  %s  %s" % (ts, _LEVEL[level], step, action, detail),
          file=stream, flush=True)
    for c in cont:
        print("    %s" % c, file=stream, flush=True)


# --- findings ---------------------------------------------------------------

class Findings:
    """The findings table. One row per CHECKED SUBJECT, never one per opinion.

    `id` is a hash of (check, subject) and therefore STABLE ACROSS RUNS. The
    auto-fix loop needs exactly that: "did the finding this fix targeted clear?"
    is only answerable when the finding keeps its identity between two runs of
    this script. A sequence number would silently renumber on the next run and
    the loop would revert the wrong fix.
    """

    COLUMNS = ("id", "layer", "check", "verdict", "subject", "evidence",
               "autofix", "action")

    def __init__(self):
        self.rows = []

    def add(self, layer, check, verdict, subject, evidence, autofix="-", action="-"):
        fid = "%s-%s" % (check, hashlib.sha1(
            ("%s\t%s" % (check, subject)).encode("utf-8")).hexdigest()[:6])
        # Two rows sharing an id would make "did the finding this fix targeted
        # clear?" unanswerable, so a second row on the same subject is
        # disambiguated by its evidence -- still deterministic, still stable
        # across runs as long as the evidence is.
        if any(r["id"] == fid and r["evidence"] == _clean(evidence) for r in self.rows):
            return fid                        # the same finding twice is one finding
        if any(r["id"] == fid for r in self.rows):
            fid = "%s-%s" % (check, hashlib.sha1(
                ("%s\t%s\t%s" % (check, subject, evidence)).encode("utf-8")).hexdigest()[:6])
        self.rows.append({
            "id": fid, "layer": layer, "check": check, "verdict": verdict,
            "subject": _clean(subject), "evidence": _clean(evidence),
            "autofix": autofix, "action": _clean(action)})
        return fid

    def ok(self, layer, check, subject, evidence):
        return self.add(layer, check, IDENT, subject, evidence)

    def diverges(self, layer, check, subject, evidence, autofix="-", action="-"):
        return self.add(layer, check, DIVERG, subject, evidence, autofix, action)

    def unmechanisable(self, layer, check, subject, reason, action):
        return self.add(layer, check, UNMECH, subject, reason, "-", action)

    def by_verdict(self, verdict):
        return [r for r in self.rows if r["verdict"] == verdict]

    def checks(self):
        seen = []
        for r in self.rows:
            if r["check"] not in seen:
                seen.append(r["check"])
        return seen


def _clean(s):
    """TSV-safe: tabs and newlines are the only characters the format cannot
    carry, so they are folded rather than allowed to corrupt a row silently."""
    return re.sub(r"[\t\r\n]+", " ", str(s)).strip()


# --- small readers ----------------------------------------------------------

def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def read_json(path):
    txt = read_text(path)
    if txt is None:
        return None
    try:
        return json.loads(txt)
    except ValueError:
        return None


def yaml_scalar(text, key):
    """A top-level `key: value` out of a sushi-config. Deliberately NOT a YAML parser.

    The catalog's scripts are stdlib-only and PyYAML is not stdlib. Every value
    this script reads out of a sushi-config is a top-level scalar written on one
    line, which this handles exactly; anything nested (`publisher:` as a block)
    is read by its own regex below. A value that cannot be read this way returns
    None and the check reports NICHT PRUEFBAR rather than guessing.
    """
    if not text:
        return None
    m = re.search(r"^%s:[ \t]*(?:#.*)?$" % re.escape(key), text, re.M)
    if m:                                   # key with a nested block, no scalar
        return None
    m = re.search(r"^%s:[ \t]*(.+?)[ \t]*(?:#.*)?$" % re.escape(key), text, re.M)
    if not m:
        return None
    val = m.group(1).strip().strip('"').strip("'")
    return val or None


def yaml_dependencies(text):
    """The `dependencies:` block as {package: version}.

    Two shapes occur in real MII configs and both are handled:
        dependencies:
          de.basisprofil.r4: 1.5.0
        dependencies:
          de.einwilligungsmanagement:
            version: 2.0.3
    """
    out = {}
    if not text:
        return out
    m = re.search(r"^dependencies:[ \t]*$(.*?)(?=^\S|\Z)", text, re.M | re.S)
    if not m:
        return out
    block = m.group(1)
    cur = None
    for line in block.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        m2 = re.match(r"^[ \t]{2}([A-Za-z0-9._-]+):[ \t]*(.*?)[ \t]*(?:#.*)?$", line)
        if m2:
            cur = m2.group(1)
            val = m2.group(2).strip().strip('"').strip("'")
            if val:
                out[cur] = val
            continue
        m3 = re.match(r"^[ \t]{4,}version:[ \t]*(.+?)[ \t]*(?:#.*)?$", line)
        if m3 and cur:
            out[cur] = m3.group(1).strip().strip('"').strip("'")
    return out


def yaml_publisher(text):
    if not text:
        return None
    m = re.search(r"^publisher:\s*(?:#.*)?\n\s+name:\s*\"?([^\"#\n]+)", text, re.M)
    if m:
        return m.group(1).strip()
    return yaml_scalar(text, "publisher")


# --- HTML helpers -----------------------------------------------------------

TAGS = re.compile(r"(?s)<[^>]+>")
SCRIPTS = re.compile(r"(?s)<(script|style)\b.*?</\1>")
ALNUM = re.compile(r"[^0-9A-Za-zÀ-ÿ]+")


def html_text(html):
    return re.sub(r"\s+", " ", TAGS.sub(" ", SCRIPTS.sub(" ", html))).strip()


def reduce_text(s):
    """Letters and digits only, lowercased.

    The SAME normalisation `guide-page-to-md.py` uses for its `missing_runs=`
    count, so the two numbers are comparable: that script measures what the
    harvest lost, this one measures what the MIGRATION lost, and a reader
    comparing them must not be comparing two different definitions.
    """
    return ALNUM.sub("", s).lower()


def div_region(html, marker):
    """The <div> whose opening tag carries `marker`, by DEPTH-SCANNING div tags.

    A regex to the next `</div>` truncates at the first NESTED one -- the defect
    `guide-harvest.sh` documents for the Simplifier content region -- and a
    truncated header region is exactly where a header defect hides.
    """
    i = html.find(marker)
    if i < 0:
        return None
    start = html.rfind("<div", 0, i)
    if start < 0:
        return None
    depth = 0
    for m in re.finditer(r"<div\b|</div>", html[start:]):
        depth += 1 if m.group(0).startswith("<div") else -1
        if depth == 0:
            return html[start:start + m.end()]
    return html[start:]


# --- artefact collection ----------------------------------------------------

FHIR_XML_NS = "http://hl7.org/fhir"


# The IG resource is the guide, not one of its artefacts: it is regenerated on
# every build with the id the template decides, it has no artifacts.html row and
# the publisher renders no `ImplementationGuide-<id>.html` page for it. Counting
# it produced a guaranteed false finding in both C1 and C2 -- measured on the
# fixture built from a real rendered site.
NON_ARTEFACT_TYPES = ("ImplementationGuide",)


def collect_generated(root):
    """{Type/id: url} from `fsh-generated/resources/*.json`, artefacts only."""
    out = {}
    for path in sorted(glob.glob(os.path.join(root, "fsh-generated", "resources", "*.json"))):
        data = read_json(path)
        if not isinstance(data, dict):
            continue
        rt, rid = data.get("resourceType"), data.get("id")
        if rt and rid and rt not in NON_ARTEFACT_TYPES:
            out["%s/%s" % (rt, rid)] = data.get("url") or ""
    return out


def collect_source_artifacts(root):
    """{Type/id: url} for a source of EITHER shape, detected BY CONTENT.

    Shape A has `fsh-generated/` or FSH; shape B is a Forge repository of raw
    XML/JSON in hand-named (often German) directories, so no conventional-name
    glob finds them -- the skill's own rule, applied here as well.
    """
    gen = collect_generated(root)
    if gen:
        return gen, "fsh-generated/resources"
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in
                       (".git", "node_modules", "output", "temp", "template",
                        "input-cache", "migration-log", ".ai-log")]
        for name in filenames:
            path = os.path.join(dirpath, name)
            if name.endswith(".json"):
                data = read_json(path)
                if isinstance(data, dict) and data.get("resourceType") and data.get("id") \
                        and data["resourceType"] not in NON_ARTEFACT_TYPES:
                    out["%s/%s" % (data["resourceType"], data["id"])] = data.get("url") or ""
            elif name.endswith(".xml"):
                txt = read_text(path) or ""
                if FHIR_XML_NS not in txt:
                    continue
                mt = re.search(r"<([A-Za-z]+)\s[^>]*xmlns=\"%s\"" % re.escape(FHIR_XML_NS), txt)
                mi = re.search(r"<id\s+value=\"([^\"]+)\"", txt)
                mu = re.search(r"<url\s+value=\"([^\"]+)\"", txt)
                if mt and mi and mt.group(1) not in NON_ARTEFACT_TYPES:
                    out["%s/%s" % (mt.group(1), mi.group(1))] = mu.group(1) if mu else ""
    return out, "source tree, by content (resourceType / FHIR xmlns)"


def load_source_inventory(path):
    """`migration-log/source-inventory.json` from step 1, read tolerantly.

    Its shape is not fixed by the specification and two real migrations wrote
    two different ones, so this accepts a list of objects, or a dict with an
    `artifacts`/`resources`/`items` key, and takes whatever carries a
    resourceType+id or an id+url. A shape it cannot read yields None, which the
    caller reports as NICHT PRUEFBAR -- never as an empty inventory.
    """
    data = read_json(path)
    if data is None:
        return None
    items = None
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ("artifacts", "resources", "items", "inventory"):
            if isinstance(data.get(key), list):
                items = data[key]
                break
    if not items:
        return None
    out = {}
    for it in items:
        if not isinstance(it, dict):
            continue
        rt = it.get("resourceType") or it.get("type")
        rid = it.get("id") or it.get("name")
        if rt and rid and rt not in NON_ARTEFACT_TYPES:
            out["%s/%s" % (rt, rid)] = it.get("url") or ""
    return out or None


# --- layer 1: conservation --------------------------------------------------

def variant_dirs(rendered):
    """Rendered per-language variants: every directory carrying an artifacts.html."""
    out = []
    if not rendered or not os.path.isdir(rendered):
        return out
    if os.path.isfile(os.path.join(rendered, "artifacts.html")):
        out.append(rendered)
    for name in sorted(os.listdir(rendered)):
        sub = os.path.join(rendered, name)
        if os.path.isdir(sub) and os.path.isfile(os.path.join(sub, "artifacts.html")):
            out.append(sub)
    return out


# FHIR R4 canonical (conformance/terminology) resource types. A rendered page
# `<Type>-<id>.html` is an ARTEFACT page when Type is one of these, or a type the
# module itself generates (examples: Consent, Patient, Provenance …), which is
# read from fsh-generated rather than listed here. Deriving the set from the
# filename alone is not possible -- `security-and-privacy.html` splits to
# "security" and would be read as a type.
CANONICAL_TYPES = (
    "StructureDefinition", "ValueSet", "CodeSystem", "ConceptMap", "SearchParameter",
    "CapabilityStatement", "OperationDefinition", "NamingSystem", "StructureMap",
    "ExampleScenario", "GraphDefinition", "MessageDefinition", "CompartmentDefinition",
    "TerminologyCapabilities", "Questionnaire",
)

# The publisher renders several VIEWS of one artefact. Only the bare page counts
# as the artefact; the views are reachable from it, not from the index.
VIEW_SUFFIXES = ("-testing", "-mappings", "-examples", "-definitions", "-changes",
                 "-diff", "-json", "-xml", "-ttl")


def label_path(path, target):
    """A path as a finding should NAME it.

    Relative to the target where it sits inside it -- an absolute scratch path in
    a report is useless on another machine. But `os.path.relpath` of a rendered
    site that sits OUTSIDE the target produces `../../../../tmp/...`, which is
    worse than the absolute path it was avoiding (measured on the Labor run,
    whose preview was built outside the tree). So: relative when inside,
    absolute when not.
    """
    path, target = os.path.abspath(path), os.path.abspath(target)
    return os.path.relpath(path, target) if path.startswith(target + os.sep) \
        or path == target else path


def rendered_artifact_pages(vdir, generated):
    """Bare `<Type>-<id>.html` artefact pages actually rendered into `vdir`."""
    types = set(CANONICAL_TYPES) | set(k.split("/", 1)[0] for k in generated)
    out = set()
    for path in glob.glob(os.path.join(vdir, "*.html")):
        name = os.path.basename(path)
        stem = name[:-5]
        if "." in stem or "-" not in stem:
            continue                              # .change.history, index, qa …
        if stem.split("-", 1)[0] not in types:
            continue
        if stem.endswith(VIEW_SUFFIXES):
            continue
        out.add(name)
    return out


def layer_conservation(f, a, ctx):
    tgt = ctx["target"]

    # C1 -- every source artefact present in the target.
    src_arts, src_src = (None, None)
    if a.source:
        src_arts, src_src = collect_source_artifacts(a.source)
    if not src_arts:
        inv = load_source_inventory(os.path.join(ctx["logdir"], "source-inventory.json"))
        if inv:
            src_arts, src_src = inv, "migration-log/source-inventory.json"
    tgt_arts = ctx["generated"]
    if not src_arts:
        f.unmechanisable("conservation", "C1", "source artefact set",
                         "no source tree (--source) and no readable source-inventory.json",
                         "re-run with --source <unmigrated source>, or write step 1's inventory")
    elif not tgt_arts:
        f.unmechanisable("conservation", "C1", "target artefact set",
                         "target carries no fsh-generated/resources -- SUSHI has not run",
                         "run SUSHI (step 3/7), then re-run verification")
    else:
        missing = [k for k in sorted(src_arts) if k not in tgt_arts]
        for key in missing:
            f.diverges("conservation", "C1", key,
                       "in the source (%s), absent from the target's fsh-generated" % src_src,
                       action="transfer the artefact (step 4) or record it as deliberately retired")
        if not missing:
            f.ok("conservation", "C1", "%d source artefacts" % len(src_arts),
                 "all present in fsh-generated (source: %s)" % src_src)

    # C2 -- every artefact REACHABLE from the artifact index. THE consent defect:
    # present is not the same property as listed, and the set comparison of the
    # sibling skill only proves the first.
    variants = ctx["variants"]
    if not variants:
        f.unmechanisable("conservation", "C2", "artifact index",
                         "no rendered output with an artifacts.html under %s" % ctx["rendered_label"],
                         "build the IG (step 7), then re-run verification")
    elif not tgt_arts:
        f.unmechanisable("conservation", "C2", "artifact index",
                         "no fsh-generated/resources to check reachability for",
                         "run SUSHI, then re-run verification")
    else:
        for vdir in variants:
            index = read_text(os.path.join(vdir, "artifacts.html")) or ""
            linked = set(os.path.basename(h) for h in
                         re.findall(r'href="([^"]+\.html)"', index))
            rel = label_path(vdir, ctx["target"])
            unreachable, unrendered = [], []
            for key in sorted(tgt_arts):
                rtype, rid = key.split("/", 1)
                page = "%s-%s.html" % (rtype, rid)
                if not os.path.isfile(os.path.join(vdir, page)):
                    unrendered.append(page)
                elif page not in linked:
                    unreachable.append(page)

            # The REVERSE direction. The loop above can only ask about artefacts
            # SUSHI generated; an artefact supplied ready-made under
            # `input/resources/` is rendered by the publisher and is invisible to
            # it. Measured on Consent: `Parameters-mii-param-consent-manifest`
            # renders, is listed nowhere, and the forward pass cannot see it.
            #
            # Only ONE page per artefact is considered. The publisher writes
            # several views of the same artefact (`-testing`, `.change.history`,
            # `-mappings`); counting those would turn 6 unreachable
            # SearchParameters into 30 rows of the same defect and bury
            # everything else.
            for page in sorted(rendered_artifact_pages(vdir, tgt_arts)):
                stem = page[:-5]
                rtype, rid = stem.split("-", 1)
                if "%s/%s" % (rtype, rid) in tgt_arts:
                    continue                       # already judged above
                if page not in linked:
                    f.diverges("conservation", "C2", "%s/%s" % (rel, page),
                               "artefact page rendered from OUTSIDE fsh-generated (an "
                               "input/resources artefact) and NOT listed in %s/artifacts.html"
                               % rel,
                               action="unreachable content: add it to the IG resource's "
                                      "`definition.resource`, or to sushi-config's `resources:`")

            # An index that lists NOTHING is one defect, not N. Reported as one
            # row with the shape of what is missing, because 84 rows of "not
            # listed" is a report nobody reads -- and the per-artefact rows are
            # then redundant with it.
            if unreachable and not any(
                    h.startswith(tuple(t + "-" for t in
                                       set(k.split("/", 1)[0] for k in tgt_arts)))
                    for h in linked):
                by_type = {}
                for page in unreachable:
                    by_type.setdefault(page.split("-", 1)[0], 0)
                    by_type[page.split("-", 1)[0]] += 1
                f.diverges("conservation", "C2", "%s/artifacts.html" % rel,
                           "the artifact index lists NO artefact at all: %d rendered artefacts "
                           "are unreachable from it (%s)"
                           % (len(unreachable),
                              ", ".join("%dx %s" % (n, t) for t, n in sorted(by_type.items()))),
                           action="unreachable content -- the whole index is empty, so this is "
                                  "one defect in the IG resource's `definition.resource` list "
                                  "(or the template's artifacts page), not %d separate ones"
                                  % len(unreachable))
            else:
                for page in unreachable:
                    f.diverges("conservation", "C2", "%s/%s" % (rel, page),
                               "page rendered but NOT listed in %s/artifacts.html" % rel,
                               action="unreachable content: check the IG resource's "
                                      "`definition.resource` entry for this artefact")
            for page in unrendered:
                f.diverges("conservation", "C2", "%s/%s" % (rel, page),
                           "generated resource has no rendered page in %s" % rel,
                           action="check the build log for this resource")
            if not unreachable and not unrendered:
                f.ok("conservation", "C2", "%s (%d artefacts)" % (rel, len(tgt_arts)),
                     "every generated resource is rendered and listed in artifacts.html")

    # C3 -- every source guide page accounted for.
    pages, pages_src = ctx["source_pages"]
    page_map = ctx["page_map"]
    if not pages:
        f.unmechanisable("conservation", "C3", "source guide pages",
                         "no harvest manifest and no source pagecontent to enumerate",
                         "supply --harvest-tsv or --source; a migration whose source page "
                         "set is unknown cannot claim conservation")
    elif page_map is None:
        f.unmechanisable("conservation", "C3", "%d source pages" % len(pages),
                         "no page map at %s" % a.page_map,
                         "write step 5's ledger: source_page<TAB>target_page|RETIRED<TAB>reason")
    else:
        for entry_page in pages:
            page = entry_page["key"]
            entry = _map_lookup(page_map, entry_page)
            if entry is None:
                f.diverges("conservation", "C3", page,
                           "source page (%s) appears in no row of %s" % (pages_src, a.page_map),
                           action="MISSING: map it to a target page or record it retired with a reason")
                continue
            target_page, reason = entry
            if target_page.upper() == "RETIRED":
                if reason:
                    f.ok("conservation", "C3", page, "retired: %s" % reason)
                else:
                    f.diverges("conservation", "C3", page,
                               "retired with NO reason in %s" % a.page_map,
                               action="a retirement without a reason is indistinguishable "
                                      "from a forgotten page -- name the reason")
            else:
                where = _page_exists(ctx["target"], target_page)
                if where:
                    f.ok("conservation", "C3", page, "migrated -> %s (%s)" % (target_page, where))
                else:
                    f.diverges("conservation", "C3", page,
                               "mapped to %s, which does not exist in the target" % target_page,
                               action="fix the map or create the target page")

    # C4 -- every source narrative text run present somewhere in the target.
    corpus = ctx["target_corpus"]
    runs = ctx["source_runs"]
    if runs is None:
        f.unmechanisable("conservation", "C4", "narrative text runs",
                         "no harvested source narrative (%s) and no source pagecontent"
                         % a.harvest_dir,
                         "supply --harvest-dir or --source; without a source text there is "
                         "nothing to conserve against")
    elif not corpus:
        f.unmechanisable("conservation", "C4", "narrative text runs",
                         "the target carries no %s pagecontent to search" % a.source_lang,
                         "check --source-lang: the source narrative is compared against the "
                         "target pages in the SAME language, never against the translation")
    else:
        hay = reduce_text(corpus)
        for page, page_runs in sorted(runs.items()):
            missing = [r for r in page_runs if reduce_text(r) not in hay]
            rows = ctx["source_tabular"].get(page, 0)
            note = ("; %d generated table row(s) excluded -- migration replaces that "
                    "view with the artefact page (R1 checks THAT)" % rows) if rows else ""
            if missing:
                f.diverges("conservation", "C4", page,
                           "%d of %d PROSE runs of the source page are in no target page "
                           "(first: %s)%s"
                           % (len(missing), len(page_runs), _snip(missing[0]), note),
                           action="map the missing text to a target page section, or record "
                                  "the loss in the report's content map")
            elif page_runs:
                f.ok("conservation", "C4", page,
                     "all %d prose runs present in the target's %s corpus%s"
                     % (len(page_runs), a.source_lang, note))
            else:
                # A page of pure generated view has no prose to conserve. Saying
                # "all 0 runs present" would be a pass nobody earned.
                f.unmechanisable("conservation", "C4", page,
                                 "the source page carries NO prose -- %d generated table "
                                 "row(s) only" % rows,
                                 "conservation of a generated view is not a text question; "
                                 "confirm the artefact page replaces it (R1)")

    check_menu(f, a, ctx)          # C5
    check_placement(f, a, ctx)     # C6


# --- C5: the menu, and the reverse page question ----------------------------

MENU_HREF = re.compile(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S)


def read_menus(target):
    """{relative path: [(href, label)]} for every menu.xml in the tree.

    Both the default `input/includes/menu.xml` and each
    `input/translations/<lang>/includes/menu.xml`. The template's own comment
    says a per-language copy is the ONLY way to get a translated menu, so a
    module with one menu and two languages is a real finding, not a layout
    variant.
    """
    out = {}
    for path in sorted(glob.glob(os.path.join(target, "input", "**", "menu.xml"),
                                 recursive=True)):
        entries = []
        for m in MENU_HREF.finditer(read_text(path) or ""):
            label = re.sub(r"\s+", " ", TAGS.sub("", m.group(2))).strip()
            entries.append((m.group(1).strip(), label))
        out[os.path.relpath(path, target)] = entries
    return out


def read_template_pages(path):
    """references/template-pages.tsv -> {page: role}. None when unreadable."""
    txt = read_text(path)
    if txt is None:
        return None
    out = {}
    for line in txt.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) >= 2 and cols[0] != "page":
            out[cols[0].strip()] = cols[1].strip()
    return out or None


def check_menu(f, a, ctx):
    """C5 -- menu entries, and target pages that no source page explains.

    Three questions a file-set comparison cannot answer, in ascending order of
    how badly a reader is misled when nobody asks them:

      a  does every menu entry LEAD somewhere? A menu is the only navigation the
         rendered site has; an entry pointing at a page that does not exist is a
         dead end no build step reports.
      b  is every narrative page IN the menu? A page that renders and is in no
         menu is reachable only by typing its URL -- the same class as the
         Consent artifact index, one level up.
      c  which target pages have NO source counterpart and are not the
         template's? Those are pages that appeared during migration. Usually
         legitimate (a template scaffold the module filled), occasionally a page
         invented to hold text that belonged elsewhere -- so this reports, and
         does not fail, unless the page is the template's DEMO page, which step 3
         is supposed to delete.
    """
    target = ctx["target"]
    menus = ctx["menus"]
    narrative = ctx["narrative_page_names"]

    # C5a -- every menu entry resolves.
    if not menus:
        f.unmechanisable("conservation", "C5", "menu",
                         "no input/**/menu.xml in the target",
                         "the template renders navigation from menu.xml; a module without one "
                         "has whatever navigation sushi-config's `menu:` generated -- confirm "
                         "by hand which it is")
    else:
        for rel, entries in sorted(menus.items()):
            dead = []
            for href, label in entries:
                page = href.split("#")[0].split("?")[0]
                if not page or page.startswith(("http://", "https://", "mailto:")):
                    continue
                if not page.endswith(".html"):
                    continue
                stem = os.path.basename(page)[:-5]
                if stem in narrative or stem in ctx["generated_page_stems"]:
                    continue
                # Publisher-generated index pages have no .md and no resource.
                if stem in PUBLISHER_PAGES:
                    continue
                if any(os.path.isfile(os.path.join(v, os.path.basename(page)))
                       for v in ctx["variants"]):
                    continue
                dead.append((label or stem, page))
            for label, page in dead:
                f.diverges("conservation", "C5", "%s -> %s" % (rel, page),
                           "menu entry %r points at a page that exists in neither "
                           "input/pagecontent nor the rendered output" % label,
                           action="dead navigation: remove the entry or create the page "
                                  "(a menu is the site's only navigation -- nothing else "
                                  "reports this)")
            if not dead:
                f.ok("conservation", "C5", rel,
                     "all %d menu entries resolve to a real page" % len(entries))

        # The menu is per language, and a missing translated menu renders the
        # DEFAULT-language navigation over translated pages.
        langs = ctx["translation_langs"]
        for lang in sorted(langs):
            want = os.path.join("input", "translations", lang, "includes", "menu.xml")
            if want not in menus:
                f.diverges("conservation", "C5", want,
                           "the module ships translated pages for %r but no translated menu -- "
                           "the %s pages render with the DEFAULT-language navigation" % (lang, lang),
                           action="copy input/includes/menu.xml to %s and translate the labels, "
                                  "keeping the href targets identical" % want)

    # C5b -- every narrative page reachable from a menu.
    if menus and narrative:
        linked = set()
        for entries in menus.values():
            for href, _ in entries:
                base = os.path.basename(href.split("#")[0])
                if base.endswith(".html"):
                    linked.add(base[:-5])
        orphan = sorted(p for p in narrative if p not in linked)
        for page in orphan:
            f.diverges("conservation", "C5", "input/pagecontent/%s.md" % page,
                       "narrative page in NO menu entry -- rendered, but reachable only "
                       "by typing its URL",
                       action="add it to input/includes/menu.xml (and the per-language "
                              "copies), or retire the page")
        if not orphan:
            f.ok("conservation", "C5", "%d narrative pages" % len(narrative),
                 "every one is reachable from a menu entry")

    # C5c -- target pages with no source counterpart.
    tpl = ctx["template_pages"]
    pmap = ctx["page_map"]
    if tpl is None:
        f.unmechanisable("conservation", "C5", "target pages without a source counterpart",
                         "references/template-pages.tsv is unreadable, so a template page "
                         "cannot be told from an invented one",
                         "supply the list, read from the template tag this module was "
                         "scaffolded from")
    elif pmap is None:
        # Without a page map every non-template page looks unexplained. Naming
        # them is still useful; calling them divergences would not be.
        unexplained = sorted(p for p in narrative if p not in tpl)
        f.unmechanisable("conservation", "C5",
                         "target pages without a source counterpart",
                         "no page map at %s; %d target page(s) are not the template's (%s)"
                         % (a.page_map, len(unexplained),
                            ", ".join(unexplained[:5]) or "none"),
                         "write step 5's ledger, then re-run: only it says which target page "
                         "each source page became")
    else:
        mapped = set()
        for tgt_page, _reason in pmap.values():
            if tgt_page and tgt_page.upper() != "RETIRED":
                stem = os.path.basename(tgt_page)
                mapped.add(stem[:-3] if stem.endswith(".md") else
                           (stem[:-5] if stem.endswith(".html") else stem))
        unexplained = sorted(p for p in narrative if p not in tpl and p not in mapped)
        for page in unexplained:
            f.diverges("conservation", "C5", "input/pagecontent/%s.md" % page,
                       "target page is neither a template page nor the target of any "
                       "page-map row -- it appeared during migration",
                       action="name its provenance in the page map, or remove it; a page "
                              "nobody can trace to a source is content a reviewer cannot check")
        if not unexplained:
            f.ok("conservation", "C5", "target page set",
                 "every narrative page is either the template's or a page-map target")

    # The template's DEMO page must not survive migration (spec step 3).
    if tpl:
        for page in sorted(p for p, role in tpl.items()
                           if role == "demo" and p in narrative):
            f.diverges("conservation", "C5", "input/pagecontent/%s.md" % page,
                       "the template's DEMO page is still present in the migrated module",
                       action="delete it and its menu entry and `pages:` row (spec step 3)")


PUBLISHER_PAGES = frozenset((
    "artifacts", "toc", "qa", "downloads", "searchform", "history", "index"))


# --- C6: content placement --------------------------------------------------

def check_placement(f, a, ctx):
    """C6 -- text that survived, but on WHICH page.

    C4 asks whether a source text run exists ANYWHERE in the target. That is the
    conservation question and it is the right one to ask first, but it passes
    identically for a paragraph that landed on the page the migration intended
    and for one that was swept into `index.md` because nothing else fitted. The
    routing decision (spec section 9) is the part a reviewer actually has to
    judge, and it is invisible in a C4 pass.

    So: for each source page, the target pages its runs landed on, ranked. With a
    page map, the dominant landing page is compared against the mapped target and
    a mismatch is a divergence. WITHOUT a page map there is no declared intent to
    compare against -- the distribution is reported as NICHT PRUEFBAR with the
    evidence a human needs, never as a pass.
    """
    runs = ctx["source_runs"]
    per_page = ctx["target_page_texts"]
    pmap = ctx["page_map"]
    pages, _src = ctx["source_pages"]

    if not runs:
        f.unmechanisable("conservation", "C6", "content placement",
                         "no harvested source narrative to place",
                         "supply --harvest-dir or --source")
        return
    if not per_page:
        f.unmechanisable("conservation", "C6", "content placement",
                         "the target carries no %s pagecontent to attribute text to"
                         % a.source_lang,
                         "check --source-lang, or build the %s variant" % a.source_lang)
        return

    reduced = {name: reduce_text(text) for name, text in per_page.items()}
    alias = {}
    for p in pages:
        for key in p["aliases"]:
            alias.setdefault(key, p)

    for src_page in sorted(runs):
        landing = {}
        placed = 0
        for run in runs[src_page]:
            needle = reduce_text(run)
            if not needle:
                continue
            hits = [name for name, text in reduced.items() if needle in text]
            if not hits:
                continue                      # C4 already reports the loss
            placed += 1
            for name in hits:
                landing[name] = landing.get(name, 0) + 1
        if not placed:
            continue
        ranked = sorted(landing.items(), key=lambda kv: (-kv[1], kv[0]))
        shown = ", ".join("%s (%d)" % (n, c) for n, c in ranked[:3])
        entry = _map_lookup(pmap, alias[src_page]) if (pmap and src_page in alias) else None
        if entry is None or entry[0].upper() == "RETIRED":
            f.unmechanisable("conservation", "C6", src_page,
                             "%d of %d runs placed; landed on %s"
                             % (placed, len(runs[src_page]), shown),
                             "no page-map row declares where this page's text was MEANT to go, "
                             "so 'right page' has no mechanical meaning -- read the landing "
                             "distribution and confirm the routing (spec section 9)")
            continue
        want = os.path.basename(entry[0])
        want = want[:-3] if want.endswith(".md") else (
            want[:-5] if want.endswith(".html") else want)
        top = ranked[0][0]
        if top == want:
            f.ok("conservation", "C6", src_page,
                 "%d of %d runs placed, most on %s -- the mapped target"
                 % (placed, len(runs[src_page]), want))
        elif want in landing:
            f.unmechanisable("conservation", "C6", src_page,
                             "mapped to %s, which holds %d run(s), but MOST landed on %s"
                             % (want, landing[want], shown),
                             "a split is legitimate when the source page was deliberately "
                             "divided; confirm the routing or correct the page map")
        else:
            f.diverges("conservation", "C6", src_page,
                       "mapped to %s, but NONE of its %d placed runs are on that page -- "
                       "they are on %s" % (want, placed, shown),
                       action="the text survived on a DIFFERENT page than the migration "
                              "declares. Correct the page map, or move the content")


def _map_lookup(page_map, entry_page):
    """The page map keyed tolerantly.

    Step 5 writes the ledger by hand, and the three names a page has -- the
    harvested Markdown file, the guide's page title, the URL slug -- are all
    reasonable keys to have typed. Accepting any of them is cheap; reporting a
    page as MISSING because the operator wrote the title where the script
    expected the filename would be a defect in the check.
    """
    for key in entry_page["aliases"]:
        if key in page_map:
            return page_map[key]
    return None


def _page_exists(target, page):
    """Is `page` a real target page? Accepts a bare name, a path, or a .md/.html."""
    stem = os.path.basename(page)
    for ext in ("", ".md", ".html"):
        for base in ("input/pagecontent", "input/translations", "output", ""):
            cand = os.path.join(target, base, stem + ext)
            if os.path.isfile(cand):
                return os.path.relpath(cand, target)
    hits = glob.glob(os.path.join(target, "input", "**", stem + ".md"), recursive=True)
    return os.path.relpath(hits[0], target) if hits else None


def _snip(s, n=60):
    s = re.sub(r"\s+", " ", s).strip()
    return s[:n] + ("…" if len(s) > n else "")


GENERATED_ROW = re.compile(r"^\s*\|")


def strip_generated_rows(text):
    """(prose, generated-row count). Markdown table rows are NOT prose.

    Measured on Labor: the harvested
    `technischeimplementierung-fhir-profile-observation.md` is 242429 lines, and
    4687 of its 4692 "text runs" are rows of the Simplifier-rendered element
    tree. Migration replaces that view with the publisher's own profile page ON
    PURPOSE, so counting the rows as lost narrative reported ~11 000 missing runs
    across Consent and Labor -- three orders of magnitude more than the real
    prose losses on the same pages, which it buried.

    The rows are not ignored: the caller reports them separately, because a
    generated view that vanished with no replacement is still a finding -- it is
    just a DIFFERENT finding, and R1's source-versus-target comparison is what
    detects that one.
    """
    keep, dropped = [], 0
    for line in text.splitlines():
        if GENERATED_ROW.match(line):
            dropped += 1
            continue
        keep.append(line)
    return "\n".join(keep), dropped


def split_runs(text, run_length=40):
    """Text runs, split exactly as `guide-page-to-md.py` splits them.

    HTML comments are stripped FIRST. Measured on Consent: every harvested page
    opens with `<!-- Harvested from <url> on <date> by scripts/guide-harvest.sh -->`,
    which is long enough to pass the run-length filter, is a provenance stamp
    rather than narrative, and can never appear in the target -- so it reported
    as a lost text run on all 18 harvested pages and was the FIRST example named
    in each finding. A check whose headline evidence is its own tooling's
    footprint teaches a reader to ignore it.
    """
    text = re.sub(r"(?s)<!--.*?-->", " ", text)
    text, tabular = strip_generated_rows(text)
    out = []
    for run in re.split(r"(?<=[.!?:;])\s+", text):
        run = run.strip()
        if len(run) < run_length:
            continue
        needle = re.sub(r"https?://\S+", " ", run)
        if len(reduce_text(needle)) < run_length // 2:
            continue
        out.append(needle)
    return out, tabular


# --- layer 2: fidelity ------------------------------------------------------

IDENTITY_FIELDS = ("id", "packageId", "canonical", "version", "status", "title",
                   "license", "publisher", "fhirVersion")


def read_identity(root):
    sushi = read_text(os.path.join(root, "sushi-config.yaml"))
    pkg = read_json(os.path.join(root, "package.json")) or {}
    ident = {
        "id": yaml_scalar(sushi, "id"),
        "packageId": yaml_scalar(sushi, "packageId") or pkg.get("name"),
        "canonical": yaml_scalar(sushi, "canonical") or pkg.get("canonical"),
        "version": yaml_scalar(sushi, "version") or pkg.get("version"),
        "status": yaml_scalar(sushi, "status"),
        "title": yaml_scalar(sushi, "title") or pkg.get("title"),
        "license": yaml_scalar(sushi, "license") or pkg.get("license"),
        "publisher": yaml_publisher(sushi),
        "fhirVersion": yaml_scalar(sushi, "fhirVersion")
        or (pkg.get("fhirVersions") or [None])[0],
    }
    return ident, yaml_dependencies(sushi) or (pkg.get("dependencies") or {})


def read_claims(path):
    """migration-log/identity-claims.tsv -> {field: [(tier, source, value)]}."""
    txt = read_text(path)
    if txt is None:
        return None
    out = {}
    for line in txt.splitlines():
        cols = line.split("\t")
        if len(cols) < 5:
            continue
        out.setdefault(cols[1], []).append((cols[2], cols[3], cols[4]))
    return out or None


def layer_fidelity(f, a, ctx):
    tgt_ident, tgt_deps = ctx["identity"]
    src_ident, src_deps = ctx["source_identity"]
    claims = ctx["claims"]

    # F1 -- identity, field by field.
    for field in IDENTITY_FIELDS:
        tv = tgt_ident.get(field)
        sv = src_ident.get(field) if src_ident else None
        contested = None
        if sv is None and claims:
            vals = {v for (_t, _s, v) in claims.get(field, [])}
            if len(vals) == 1:
                sv = sorted(vals)[0]
            elif len(vals) > 1:
                # An unresolved contradiction is not a source value. Saying so
                # here rather than picking one is the same rule `log_claim`
                # applies: adopting a value mechanically would rename, relicense
                # or re-version a published module with nobody seeing it.
                contested = sorted(vals)
        if contested:
            f.unmechanisable("fidelity", "F1", field,
                             "the claims ledger holds %d contradicting readings (%s)"
                             % (len(contested), ", ".join(_snip(v, 40) for v in contested[:3])),
                             "decide the field at Gate A (check L3), then re-run verification")
            continue
        if field == "version":
            # The ONLY identity value the specification makes a human decision
            # (MII CalVer, defaulting to the source's), so an inequality here is
            # reported as a decision to confirm rather than as a defect.
            if tv and sv and tv != sv:
                f.unmechanisable("fidelity", "F1", "version",
                                 "target %s vs source %s -- the target version is a human "
                                 "decision (spec 2.1)" % (tv, sv),
                                 "confirm the target version at Gate A and record it")
                continue
        if sv is None:
            f.unmechanisable("fidelity", "F1", field,
                             "no source value (neither the source tree nor the claims ledger "
                             "yields one%s)" % ("" if claims else "; no ledger"),
                             "supply it at Gate A -- an identity field nobody can compare is "
                             "not a field that matches")
        elif tv is None:
            f.diverges("fidelity", "F1", field,
                       "source has %s, the target declares nothing" % _snip(sv),
                       action="carry the source value over unchanged (guardrail 1)")
        elif tv != sv:
            f.diverges("fidelity", "F1", field,
                       "target %s  vs  source %s" % (_snip(tv), _snip(sv)),
                       action="the SOURCE wins (spec 2.2); restore it or record the divergence "
                              "as a Gate-A decision -- never normalise silently")
        else:
            f.ok("fidelity", "F1", field, "%s (identical to the source)" % _snip(tv))

    # F2 -- dependency pins. A wrong pin is invisible in a green build: measured,
    # a run resolved a parent from dist-tags.latest 2.0.3 where the source pinned
    # 2.0.2, and everything built.
    if not src_deps:
        f.unmechanisable("fidelity", "F2", "dependency pins",
                         "no source dependency block to compare against",
                         "read the source's pins (sushi-config or the published package "
                         "manifest) and compare by hand at Gate A")
    else:
        for name, sver in sorted(src_deps.items()):
            tver = tgt_deps.get(name)
            if tver is None:
                f.diverges("fidelity", "F2", name,
                           "pinned %s in the source, ABSENT from the target" % sver,
                           action="carry the dependency over")
            elif tver != sver:
                f.diverges("fidelity", "F2", name,
                           "target %s  vs  source pin %s" % (tver, sver),
                           action="the source pin is the evidence; a registry dist-tag is not. "
                                  "Restore the pin or make the bump a Gate-A decision")
            else:
                f.ok("fidelity", "F2", name, "pinned %s, identical to the source" % sver)
        for name, tver in sorted(tgt_deps.items()):
            if name not in src_deps:
                # Legitimate: the template's CRMI meta.profile claims REQUIRE
                # hl7.fhir.uv.crmi. Named, not failed -- but never silent.
                f.unmechanisable("fidelity", "F2", name,
                                 "target-only dependency %s (not in the source)" % tver,
                                 "confirm at Gate A that this is template machinery "
                                 "(hl7.fhir.uv.crmi is) and not an accidental addition")

    # F3 -- licence, explicitly asserted. The template ships `license: CC-BY-4.0`
    # as a LITERAL: no placeholder check flags it, and MII modules commonly
    # declare CC0-1.0. Relicensing by default is the quietest defect in this list.
    tlic = tgt_ident.get("license")
    if not tlic:
        f.diverges("fidelity", "F3", "license",
                   "the target declares no licence at all",
                   action="declare the source's licence; a missing licence is not a default")
    else:
        tiers = [(t, s, v) for (t, s, v) in (claims or {}).get("license", [])]
        asserted = [(t, s, v) for (t, s, v) in tiers if v == tlic and t.upper() != "T"]
        if asserted:
            t, s, _v = asserted[0]
            f.ok("fidelity", "F3", "license",
                 "%s asserted from tier %s (%s)" % (tlic, t, _snip(s)))
        elif tiers:
            f.diverges("fidelity", "F3", "license",
                       "target declares %s; the evidence tiers say %s"
                       % (tlic, ", ".join("%s=%s" % (t, v) for (t, _s, v) in tiers)),
                       action="a licence the source does not assert is a RELICENSING. "
                              "Gate A decides; never default")
        else:
            f.unmechanisable("fidelity", "F3", "license",
                             "target declares %s with NO tier evidence behind it "
                             "(no claim in identity-claims.tsv)" % tlic,
                             "read the source's LICENSE (repo-identity.sh) and claim it, or "
                             "confirm the value at Gate A. The template's literal CC-BY-4.0 "
                             "reaches here unflagged otherwise")

    # F4 -- the two MECHANICAL goFSH residues, which are also the auto-fix
    # loop's only FSH-touching class.
    fsh_files = sorted(glob.glob(os.path.join(ctx["target"], "input", "fsh", "**", "*.fsh"),
                                 recursive=True))
    if not fsh_files:
        f.unmechanisable("fidelity", "F4", "FSH residue",
                         "no input/fsh/**/*.fsh in the target",
                         "check the transfer step (4) -- a migration with no FSH moved nothing")
    else:
        comments, unquoted = [], []
        for path in fsh_files:
            txt = read_text(path) or ""
            rel = os.path.relpath(path, ctx["target"])
            if re.search(r"^\s*\*\s.*\.fhir_comments\b", txt, re.M):
                comments.append(rel)
            if re.search(r"^\s*\*\s.*=\s*[A-Za-z][A-Za-z0-9_]*(?: [A-Za-z0-9_]+)+#", txt, re.M):
                unquoted.append(rel)
        for rel in comments:
            f.diverges("fidelity", "F4", rel,
                       "carries `.fhir_comments` assignment rules (an XML-serialization "
                       "construct SUSHI rejects)",
                       autofix="gofsh-residue",
                       action="postprocess-gofsh.py turns each into an FSH `//` comment")
        for rel in unquoted:
            f.diverges("fidelity", "F4", rel,
                       "carries a code reference whose system name contains whitespace "
                       "(unparseable FSH; the parse error TRUNCATES the rest of the file)",
                       autofix="gofsh-residue",
                       action="postprocess-gofsh.py rewrites it to the normalized name goFSH "
                              "itself reports, after confirming that entity exists")
        if not comments and not unquoted:
            f.ok("fidelity", "F4", "%d FSH files" % len(fsh_files),
                 "no fhir_comments rules, no whitespace-bearing code references")


# --- layer 3: provenance ----------------------------------------------------

def layer_provenance(f, a, ctx):
    qa_html = ctx["qa_html"]
    qa_txt = ctx["qa_txt"]

    # P1 -- the template package+version READ OUT OF THE RENDERED OUTPUT, against
    # the template the tree actually carries. Like with like: see the module
    # docstring's measured trap.
    vendored = read_json(os.path.join(ctx["target"], "ig-template", "package", "package.json"))
    vname = (vendored or {}).get("name")
    vver = (vendored or {}).get("version")
    rendered_tpl = None
    if qa_html:
        m = re.search(r"Templates:\s*([^<]+)", qa_html)
        if m:
            rendered_tpl = m.group(1).strip().split("-&gt;")[0].split("->")[0].strip()
    if rendered_tpl is None:
        f.unmechanisable("provenance", "P1", "rendered template version",
                         "no `Templates:` line in the rendered qa.html (%s)"
                         % (ctx["qa_html_path"] or "qa.html not found"),
                         "build the IG (step 7); the rendered output is the only place this "
                         "value can be READ rather than assumed")
    elif not vver:
        f.unmechanisable("provenance", "P1", "vendored template version",
                         "rendered output says %s; the tree carries no "
                         "ig-template/package/package.json" % rendered_tpl,
                         "confirm which template this site was built from")
    else:
        expect = "%s#%s" % (vname, vver)
        if rendered_tpl == expect:
            f.ok("provenance", "P1", "template", "rendered %s == vendored %s" % (rendered_tpl, expect))
        else:
            f.diverges("provenance", "P1", "template",
                       "rendered output was built from %s, the tree carries %s"
                       % (rendered_tpl, expect),
                       action="STALE RENDER: rebuild, then re-run verification. A published "
                              "site whose header names another version than its tree is the "
                              "'preview v0.5.0 under v0.5.1' class")

    # P2 -- the vendored REPO REF against the latest release. A different number
    # from P1's, on purpose.
    ref = ctx["log_values"].get("skeleton-vendored", {}).get("ref")
    if not ref:
        f.unmechanisable("provenance", "P2", "vendored template ref",
                         "no `5.2 skeleton-vendored … ref=` line in the run log",
                         "emit it when vendoring: "
                         "`bash \"$ML\" info 5.2 skeleton-vendored \"… ref=<tag> commit=<sha>\"`")
    elif not a.template_latest:
        f.unmechanisable("provenance", "P2", "vendored template ref",
                         "vendored at %s; the latest release was not supplied" % ref,
                         "re-run with --template-latest <tag> (it needs the network, which "
                         "this script deliberately does not use)")
    elif ref.lstrip("v") == a.template_latest.lstrip("v"):
        f.ok("provenance", "P2", "vendored template ref",
             "%s == latest release %s" % (ref, a.template_latest))
    else:
        f.diverges("provenance", "P2", "vendored template ref",
                   "vendored %s, latest release %s" % (ref, a.template_latest),
                   autofix="revendor-template",
                   action="re-vendor at the pinned ref and REBUILD -- the render check (P1) "
                          "is what confirms it, so without a rebuild command this is not "
                          "auto-fixable")

    # P3 -- the IG Publisher version, from the rendered output against the pin.
    pub = None
    for text in (qa_txt, qa_html):
        if not text:
            continue
        m = re.search(r"IG Publisher Version:\s*v?([0-9][0-9.]*)", text)
        if m:
            pub = m.group(1)
            break
    pin = a.publisher_pin or ctx["workflow_publisher_pin"]
    if pub is None:
        f.unmechanisable("provenance", "P3", "IG Publisher version",
                         "no `IG Publisher Version:` in the rendered qa output",
                         "build the IG (step 7)")
    elif not pin:
        f.unmechanisable("provenance", "P3", "IG Publisher version",
                         "rendered by %s; no pin found in the target's build workflow" % pub,
                         "supply --publisher-pin, or pin the publisher in the workflow's env: "
                         "block (spec 5.6)")
    elif pub.lstrip("v") == pin.lstrip("v"):
        f.ok("provenance", "P3", "IG Publisher version", "%s == the workflow pin" % pub)
    else:
        f.diverges("provenance", "P3", "IG Publisher version",
                   "rendered by %s, the workflow pins %s" % (pub, pin),
                   action="the site was not built by the toolchain the repository declares; "
                          "rebuild with the pin or correct the pin")
    if qa_txt and "Out of date" in (qa_txt or ""):
        m = re.search(r"IG Publisher Version:[^\n]*current version is ([0-9.]+)", qa_txt)
        if m:
            f.unmechanisable("provenance", "P3", "IG Publisher currency",
                             "the publisher reports itself out of date (current %s)" % m.group(1),
                             "upgrading the publisher is a target-repository decision, not a "
                             "migration one -- record it, do not act on it here")

    # P4 -- the pinned source-guide version. `?version=current` is the LIVE
    # EDITABLE project: a guide harvested from it is not reproducible.
    pin_ver, pin_src = ctx["guide_pin"]
    if pin_ver is None:
        f.unmechanisable("provenance", "P4", "source guide version",
                         "no `?version=` recorded in the run log or the harvest manifest",
                         "record the pinned, PUBLISHED guide version like the source commit SHA "
                         "(spec 5.1c.3)")
    elif pin_ver.lower() in ("current", "latest", "draft"):
        f.diverges("provenance", "P4", "source guide version",
                   "the recorded guide URL carries ?version=%s (%s) -- the live, editable "
                   "project, not a published version" % (pin_ver, pin_src),
                   action="re-harvest from a PUBLISHED version; `current` is not reproducible. "
                          "Where the guide has no published version at all, that is the finding "
                          "-- record it as such rather than leaving the pin unstated")
    else:
        f.ok("provenance", "P4", "source guide version",
             "pinned %s (%s)" % (pin_ver, pin_src))


# --- layer 4: rendering integrity -------------------------------------------

# Deliberately short and specific. A broad marker list (`null`, `error`) fires on
# legitimate FHIR prose; each of these has been seen in a rendered MII header.
HEADER_MARKERS = (
    "Unknown region code",      # measured: Dokument, <div id="ig-status">, 2026-08-06
    "Unknown code",
    "{{",                       # an unexpanded Liquid/placeholder expression
    "{%",
    "[object Object]",
    "#ERROR",
)
HEADER_REGIONS = ('id="ig-status"', 'id="publish-box"', 'id="segment-header"',
                  'id="segment-footer"')


def _render_features(html):
    """Counted rendering features of one page: tables WITH rows, tab strips, images.

    Counted inside the whole page rather than a content region, because the two
    sides are rendered by different engines (Simplifier's guide renderer and the
    IG Publisher) and no region id is common to both. That makes the count noisy
    in absolute terms, which is why only the ZERO/NON-ZERO transition is reported
    -- a page that had tables and now has none -- and never a difference in size.
    """
    tables = sum(1 for t in re.findall(r"(?s)<table\b.*?</table>", html) if "<tr" in t)
    tabs = len(re.findall(r'class="[^"]*nav-tabs', html))
    images = len(re.findall(r"<img\b", html))
    return {"tables": tables, "tabs": tabs, "images": images}


def layer_rendering(f, a, ctx):
    variants = ctx["variants"]
    if not variants:
        for check in ("R1", "R2", "R3"):
            f.unmechanisable("rendering", check, "rendered output",
                             "no built site under %s" % ctx["rendered_label"],
                             "build the IG (step 7); rendering integrity is not a property of "
                             "the sources")
    else:
        narrative_pages = ctx["narrative_page_names"]
        for vdir in variants:
            rel = label_path(vdir, ctx["target"])
            empty_tables, missing_images, empty_tabs = [], [], []
            for path in sorted(glob.glob(os.path.join(vdir, "*.html"))):
                name = os.path.basename(path)
                if name in ("qa.html", "qa-dep.html", "qa-tx.html"):
                    continue
                html = read_text(path) or ""
                for tbl in re.findall(r"(?s)<table\b.*?</table>", html):
                    if "<tr" not in tbl:
                        empty_tables.append(name)
                        break
                for src in re.findall(r'<img[^>]+src="([^"]+)"', html):
                    if src.startswith(("http://", "https://", "data:")):
                        continue
                    rel_src = src.split("#")[0].split("?")[0]
                    # Resolved against the variant directory AND the site root:
                    # the publisher writes `assets/` once at the root in some
                    # layouts, and resolving only against the variant reported
                    # every chrome icon of every page as missing (measured on a
                    # partial copy of a real site -- 60 rows for 4 real assets).
                    if any(os.path.isfile(os.path.join(base, rel_src))
                           for base in (vdir, ctx["rendered_root"])):
                        continue
                    missing_images.append((rel_src, name))
                for tabs in re.findall(r'(?s)<ul[^>]+class="[^"]*nav-tabs[^"]*".*?</ul>', html):
                    if "<li" not in tabs:
                        empty_tabs.append(name)
                        break
            # R1
            for name in sorted(set(empty_tables)):
                f.diverges("rendering", "R1", "%s/%s" % (rel, name),
                           "a <table> renders with no rows at all",
                           action="an empty table is a rendering failure of a view that had "
                                  "content in the source; check the artefact it renders")
            # One row per MISSING ASSET, not per page referencing it: a chrome
            # image absent from a build is one defect on N pages, and N rows for
            # it buries every other finding in the table.
            by_asset = {}
            for asset, page in missing_images:
                by_asset.setdefault(asset, []).append(page)
            for asset in sorted(by_asset):
                pages_ = sorted(set(by_asset[asset]))
                f.diverges("rendering", "R1", "%s image %s" % (rel, asset),
                           "referenced by %d page(s) (e.g. %s), present in neither %s nor the "
                           "site root" % (len(pages_), pages_[0], rel),
                           action="copy the asset into input/images/ (harvested assets are "
                                  "listed in guide-harvest-assets.tsv), or check that the build "
                                  "output being verified is complete")
            for name in sorted(set(empty_tabs)):
                f.diverges("rendering", "R1", "%s/%s" % (rel, name),
                           "a tab strip renders with no tabs",
                           action="check the artefact view's generation")
            if not (empty_tables or missing_images or empty_tabs):
                f.ok("rendering", "R1", rel,
                     "tables, tabs and images all non-empty and resolvable")
            # R2
            hits = []
            for path in sorted(glob.glob(os.path.join(vdir, "*.html"))):
                html = read_text(path) or ""
                for region_id in HEADER_REGIONS:
                    region = div_region(html, region_id)
                    if not region:
                        continue
                    for marker in HEADER_MARKERS:
                        if marker in region:
                            hits.append((os.path.basename(path), region_id, marker,
                                         _snip(html_text(region), 90)))
            seen_marker = set()
            for name, region_id, marker, snippet in hits:
                key = (region_id, marker)
                if key in seen_marker:      # one row per defect, not per page
                    continue
                seen_marker.add(key)
                count = sum(1 for h in hits if (h[1], h[2]) == key)
                f.diverges("rendering", "R2", "%s %s [%s]" % (rel, region_id, marker),
                           "on %d page(s), e.g. %s: %s" % (count, name, snippet),
                           action="rendered header/footer metadata defect -- qa.txt does not "
                                  "report it. Fix the metadata it renders (a jurisdiction code "
                                  "the template cannot resolve is the measured case)")
            if not hits:
                f.ok("rendering", "R2", rel, "header/footer regions carry no defect marker")

        # R1, comparative -- what was non-empty in the SOURCE rendering must be
        # non-empty in the target's. The per-variant pass above catches an empty
        # table; this catches a table, tab strip or image that is simply gone,
        # which an absolute check cannot see (nothing renders, so nothing is
        # empty). It runs only where the harvest kept the source HTML.
        src_pages, _src_label = ctx["source_pages"]
        pmap = ctx["page_map"]
        src_html_dir = a.source_html
        if not (src_pages and pmap and os.path.isdir(src_html_dir)):
            f.unmechanisable("rendering", "R1", "source-versus-target rendering",
                             "no harvested source HTML (%s) and/or no page map" % src_html_dir,
                             "harvest with --keep-html and write the page map; without a source "
                             "rendering, 'non-empty where non-empty in the source' has no "
                             "reference")
        else:
            compared = 0
            for sp in src_pages:
                hits = sorted(glob.glob(os.path.join(src_html_dir, "*%s.html" % sp["stem"])))
                entry = _map_lookup(pmap, sp)
                if not hits or not entry or entry[0].upper() == "RETIRED":
                    continue
                tpage = os.path.basename(entry[0])
                tpage = tpage[:-3] + ".html" if tpage.endswith(".md") else \
                    (tpage if tpage.endswith(".html") else tpage + ".html")
                tpath = None
                for vdir in ([d for d in variants if os.path.basename(d) == a.source_lang]
                             + variants):
                    cand = os.path.join(vdir, tpage)
                    if os.path.isfile(cand):
                        tpath = cand
                        break
                if not tpath:
                    continue
                s = _render_features(read_text(hits[0]) or "")
                t = _render_features(read_text(tpath) or "")
                compared += 1
                lost = [k for k in ("tables", "tabs", "images") if s[k] > 0 and t[k] == 0]
                if lost:
                    f.diverges("rendering", "R1", "%s -> %s" % (sp["key"], tpage),
                               "source rendering had %s; the target page has none"
                               % ", ".join("%d %s" % (s[k], k) for k in lost),
                               action="a live table or figure that vanished in migration is a "
                                      "CONTENT loss the build cannot see -- restore it or record "
                                      "the substitution in the report's content map")
            if compared:
                f.ok("rendering", "R1", "%d source pages compared to their target pages" % compared,
                     "tables, tabs and images non-empty in the target wherever they were "
                     "non-empty in the source")

        # R3 -- language parity, on the NARRATIVE pages only. Artefact pages are
        # generated and legitimately near-identical across languages (measured:
        # consent en/artifacts.html 29608 B vs de/ 29644 B), so checking them
        # would drown the real finding in noise.
        default_dir, trans_dirs = ctx["language_dirs"]
        if not default_dir or not trans_dirs:
            f.unmechanisable("rendering", "R3", "language parity",
                             "could not identify a default and a translated variant under %s"
                             % ctx["rendered_label"],
                             "build both language variants (step 6/7)")
        elif not narrative_pages:
            f.unmechanisable("rendering", "R3", "language parity",
                             "no input/pagecontent/*.md to identify the narrative pages",
                             "narrative pages are what a translation must differ on; "
                             "artefact pages are generated")
        else:
            for tdir in trans_dirs:
                rel = label_path(tdir, ctx["target"])
                same, missing = [], []
                for stem in sorted(narrative_pages):
                    dpath = os.path.join(default_dir, stem + ".html")
                    tpath = os.path.join(tdir, stem + ".html")
                    if not os.path.isfile(dpath):
                        continue
                    if not os.path.isfile(tpath):
                        missing.append(stem)
                        continue
                    dtext = reduce_text(html_text(read_text(dpath) or ""))
                    ttext = reduce_text(html_text(read_text(tpath) or ""))
                    if dtext and dtext == ttext:
                        same.append(stem)
                for stem in missing:
                    f.diverges("rendering", "R3", "%s/%s.html" % (rel, stem),
                               "the default language renders this page, the translation does not",
                               action="add the translated page under input/translations/<lang>/")
                for stem in same:
                    f.diverges("rendering", "R3", "%s/%s.html" % (rel, stem),
                               "byte-for-byte the same text as the default language -- a "
                               "DEFAULT-LANGUAGE FALLBACK, not a translation",
                               action="the page renders, so nothing fails; supply the "
                                      "translation or record the gap")
                if not same and not missing:
                    f.ok("rendering", "R3", rel,
                         "all %d narrative pages differ from the default language"
                         % len(narrative_pages))

    # R4 -- links to the template's example artefacts, which step 3 DELETES.
    # Such a link can only have come from the template: the module's own
    # narrative predates the template and cannot reference its examples. That
    # provenance argument is what makes this class auto-fixable at all.
    dangling = []
    for path in sorted(glob.glob(os.path.join(ctx["target"], "input", "**", "*.md"),
                                 recursive=True)) + \
            sorted(glob.glob(os.path.join(ctx["target"], "input", "**", "menu.xml"),
                             recursive=True)):
        txt = read_text(path) or ""
        rel = os.path.relpath(path, ctx["target"])
        for m in re.finditer(r"(?:\]\(|href=\")([^\")\s]*example-patient[^\")\s]*)", txt):
            dangling.append((rel, m.group(1)))
    for rel, href in dangling:
        f.diverges("rendering", "R4", "%s -> %s" % (rel, href),
                   "link to a TEMPLATE example artefact that step 3 deletes",
                   autofix="template-example-link",
                   action="remove the link, keep its text -- the fixer refuses unless the "
                          "file's text is byte-identical afterwards")
    if not dangling:
        f.ok("rendering", "R4", "template example links", "none")

    # R5 -- a page-title unit per page. Missing unit -> the title renders in the
    # default language; empty msgstr -> untranslated, which no machine can fix.
    ig_json = ctx["ig_resource"]
    po_path = ctx["po_path"]
    if not ig_json:
        f.unmechanisable("rendering", "R5", "page-title catalogue",
                         "no fsh-generated ImplementationGuide resource to read titles from",
                         "run SUSHI (step 3), then re-run")
    elif not po_path:
        f.unmechanisable("rendering", "R5", "page-title catalogue",
                         "no input/translations/<lang>/ImplementationGuide-<id>.po",
                         "generate it with gen-page-title-po.py (step 6)")
    elif not ctx["page_titles"]:
        # A catalogue with nothing to compare against passes trivially, which is
        # the shape of a false pass: report it as unreadable instead.
        f.unmechanisable("rendering", "R5", "page-title catalogue",
                         "the generated ImplementationGuide carries no titled pages",
                         "check the `pages:` tree in sushi-config -- a page set nobody can "
                         "enumerate cannot be checked for translation")
    else:
        titles = ctx["page_titles"]
        units = ctx["po_units"]
        rel = os.path.relpath(po_path, ctx["target"])
        missing = [t for t in titles if t not in units]
        empty = [t for t in titles if t in units and not units[t]]
        for t in missing:
            f.diverges("rendering", "R5", "%s [%s]" % (rel, _snip(t, 40)),
                       "page title in the IG's pages tree has NO unit in the catalogue",
                       autofix="po-missing-unit",
                       action="regenerate the catalogue; the unit is added with an EMPTY "
                              "msgstr -- never an invented translation")
        for t in empty:
            f.unmechanisable("rendering", "R5", "%s [%s]" % (rel, _snip(t, 40)),
                             "unit present, msgstr EMPTY (untranslated)",
                             "a translation is a human act -- queue it for Gate C")
        if not missing and not empty:
            f.ok("rendering", "R5", rel, "a translated unit for every one of the %d page titles"
                 % len(titles))


# --- the run log as a second oracle -----------------------------------------

LOG_LINE = re.compile(
    r"^(?P<ts>\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)  (?P<level>INFO |WARN |ERROR)  "
    r"(?P<step>\S+)  (?P<action>\S+)  (?P<detail>.*)$")


def parse_log(path):
    txt = read_text(path)
    if txt is None:
        return None
    out = []
    for line in txt.splitlines():
        m = LOG_LINE.match(line)
        if m:
            d = m.groupdict()
            d["level"] = d["level"].strip()
            out.append(d)
    return out


def read_expected_steps(path):
    """references/expected-steps.tsv -> [(step, action, applies, condition, why)]."""
    txt = read_text(path)
    if txt is None:
        return None
    rows = []
    for line in txt.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) < 5 or cols[0] == "step":
            continue
        rows.append(tuple(c.strip() for c in cols[:5]))
    return rows or None


def layer_log(f, a, ctx):
    entries = ctx["log"]
    if entries is None:
        f.diverges("log", "L0", a.log,
                   "there is NO run log -- the migration's primary record is absent",
                   action="a report written from recollection cannot be audited (spec 10.6). "
                          "Two of the four real migrations shipped without one; this is that "
                          "finding, made loud")
        return
    f.ok("log", "L0", a.log, "%d parsed lines, %d runs" % (
        len(entries), sum(1 for e in entries if e["action"] == "run-boundary")))

    # L1 -- a silent-partial-success WARN that was emitted and never acted on.
    for i, e in enumerate(entries):
        if e["level"] != "WARN" or not e["detail"].startswith("silent-partial-success:"):
            continue
        later = entries[i + 1:]
        resolved = any(
            l["action"] == e["action"] and (
                l["detail"].startswith("resolved:")
                or re.search(r"\bexpected=(\d+) actual=\1\b", l["detail"]))
            for l in later)
        if resolved:
            f.ok("log", "L1", "%s/%s @ %s" % (e["step"], e["action"], e["ts"]),
                 "silent-partial-success WARN, later resolved in the log")
        else:
            f.diverges("log", "L1", "%s/%s @ %s" % (e["step"], e["action"], e["ts"]),
                       _snip(e["detail"], 120),
                       action="the WARN this whole convention exists for was emitted and "
                              "NOTHING acted on it. Re-run the step, or record the resolution "
                              "with a `resolved:` line naming this action")

    # L2 -- a step that emitted NO line. A step that did not run is invisible
    # otherwise: nothing else in the tree records its absence.
    expected = ctx["expected_steps"]
    if expected is None:
        f.unmechanisable("log", "L2", "step coverage",
                         "no expected-steps manifest at %s" % a.expected_steps,
                         "supply --expected-steps; without the manifest a missing step cannot "
                         "be distinguished from a step that legitimately did not apply")
    else:
        seen = set((e["step"], e["action"]) for e in entries)
        seen_actions = set(e["action"] for e in entries)
        shape = ctx["shape"]
        for step, action, applies, condition, why in expected:
            if (step, action) in seen or action in seen_actions:
                f.ok("log", "L2", "%s %s" % (step, action), "present in the log")
                continue
            if applies in ("A", "B") and shape and applies != shape:
                continue                    # not applicable to this source shape
            if action == ACTION:
                # This run IS that step. Reporting its own absence as a
                # divergence would be theatre; reporting it as present would
                # hide the real defect, which is a verification whose result
                # never reaches the log. So: name the wrapper that fixes it.
                f.unmechanisable("log", "L2", "%s %s" % (step, action),
                                 "no line in the log — this very run is emitting one",
                                 "invoke it through the helper so the result is recorded: "
                                 "`bash \"$ML\" run 11 verify-migration --emits-runlog -- …`")
                continue
            if condition and condition != "always":
                f.unmechanisable("log", "L2", "%s %s" % (step, action),
                                 "no line in the log; the step is conditional (%s)" % condition,
                                 "confirm the condition did not hold -- %s" % why)
            elif applies in ("A", "B") and not shape:
                f.unmechanisable("log", "L2", "%s %s" % (step, action),
                                 "no line in the log; required only for source shape %s, "
                                 "which the log does not state" % applies,
                                 "record the shape (pre.2 classify-source-shape) -- %s" % why)
            else:
                f.diverges("log", "L2", "%s %s" % (step, action),
                           "the step emitted NO run-log line",
                           action="a step that did not run is invisible in the target: %s. "
                                  "Run it, or record why it was skipped" % why)

    # L3 -- an identity contradiction still open at verification time. ONE row
    # per FIELD, not per WARN: a field read from five tiers emits four WARNs and
    # is still one decision, and a queue with four rows for it invites three of
    # them to be closed as duplicates.
    contradictions = {}
    for e in entries:
        if e["level"] == "WARN" and e["detail"].startswith("identity-contradiction:"):
            m = re.search(r"field=(\S+)", e["detail"])
            contradictions.setdefault(m.group(1) if m else "?", []).append(e)
    for fname, evs in sorted(contradictions.items()):
        decided = any(
            l["detail"].startswith("decision:") and fname in l["detail"] for l in entries)
        if decided:
            f.ok("log", "L3", "identity field %s" % fname,
                 "%d contradicting readings, decided in the log" % len(evs))
        else:
            f.diverges("log", "L3", "identity field %s" % fname,
                       "%d unresolved contradiction WARN(s), first at %s: %s"
                       % (len(evs), evs[0]["ts"], _snip(evs[0]["detail"], 110)),
                       action="unresolved at verification time. It is a Gate-A decision, "
                              "never a precedence puzzle to settle mechanically -- record "
                              "it with a `decision:` line naming the field")
    claims_path = os.path.join(ctx["logdir"], "identity-claims.tsv")
    if not os.path.isfile(claims_path):
        f.unmechanisable("log", "L3", "identity ledger",
                         "no %s" % os.path.relpath(claims_path, ctx["target"]),
                         "run the identity recovery (step 2) -- without the ledger a "
                         "contradiction has nowhere to be seen")

    # L4 -- the cross-checks. THE point of two oracles: the log says N, the
    # target holds M, and neither number is wrong on its own.
    conv = ctx["log_values"].get("gofsh-convert", {})
    if conv.get("actual") is not None:
        n = int(conv["actual"])
        m = len(ctx["generated"])
        if m == 0:
            f.unmechanisable("log", "L4", "conversion count",
                             "log says %d resources converted; the target has no "
                             "fsh-generated to count" % n,
                             "run SUSHI, then re-run verification")
        elif m < n:
            f.diverges("log", "L4", "conversion count",
                       "the log measured %d converted, the target holds %d generated "
                       "resources" % (n, m),
                       action="resources went missing between conversion and build -- "
                              "reconcile against step 1's inventory")
        else:
            f.ok("log", "L4", "conversion count",
                 "log %d converted <= %d generated (SUSHI adds the IG resource itself)" % (n, m))
    else:
        f.unmechanisable("log", "L4", "conversion count",
                         "no `gofsh-convert … actual=` line in the log",
                         "shape B only; for shape A there is nothing to convert")

    harv = ctx["log_values"].get("guide-harvest", {})
    tsv_rows = ctx["harvest_rows"]
    if harv.get("actual") is not None and tsv_rows is not None:
        n = int(harv["actual"])
        m = sum(1 for r in tsv_rows if r.get("status") == "harvested")
        if n != m:
            f.diverges("log", "L4", "page count",
                       "the log says %d pages harvested, the manifest holds %d harvested rows"
                       % (n, m),
                       action="two records of one number disagree -- believe neither until "
                              "the harvest is re-run")
        else:
            f.ok("log", "L4", "page count", "log and manifest agree: %d harvested" % n)
    else:
        f.unmechanisable("log", "L4", "page count",
                         "no harvested count in the log and/or no harvest manifest",
                         "harvest the guide (step 2c) where the narrative is not in the repo")

    listed = ctx["indexed_artifact_count"]
    if listed is None:
        f.unmechanisable("log", "L4", "artifact count",
                         "no rendered artifacts.html to count",
                         "build the IG (step 7)")
    else:
        m = len(ctx["generated"])
        if listed < m:
            f.diverges("log", "L4", "artifact count",
                       "artifacts.html lists %d artefacts, fsh-generated holds %d"
                       % (listed, m),
                       action="the index is short of the tree -- the same class C2 names "
                              "page by page")
        else:
            f.ok("log", "L4", "artifact count",
                 "artifacts.html lists %d for %d generated resources" % (listed, m))


# --- context assembly -------------------------------------------------------

def build_context(a):
    target = os.path.abspath(a.target)
    logdir = os.path.dirname(os.path.abspath(a.log)) or os.path.join(target, "migration-log")
    ctx = {"target": target, "logdir": logdir}

    ctx["identity"] = read_identity(target)
    ctx["source_identity"] = read_identity(a.source) if a.source else (None, {})
    ctx["claims"] = read_claims(os.path.join(logdir, "identity-claims.tsv"))
    ctx["generated"] = collect_generated(target)

    rendered = os.path.abspath(a.rendered) if a.rendered else os.path.join(target, "output")
    a.rendered = rendered
    # Every message that names a path names it relative to the target where it
    # sits inside it: an absolute scratch path in a finding is unreadable in a
    # report and useless on another machine.
    ctx["rendered_label"] = label_path(rendered, target)
    ctx["rendered_root"] = rendered
    ctx["variants"] = variant_dirs(rendered)

    # qa output: at the site root, or in any variant directory.
    ctx["qa_html"] = ctx["qa_txt"] = None
    ctx["qa_html_path"] = None
    for base in [rendered] + ctx["variants"]:
        if ctx["qa_html"] is None:
            p = os.path.join(base, "qa.html")
            if os.path.isfile(p):
                ctx["qa_html"] = read_text(p)
                ctx["qa_html_path"] = label_path(p, target)
        if ctx["qa_txt"] is None:
            p = os.path.join(base, "qa.txt")
            if os.path.isfile(p):
                ctx["qa_txt"] = read_text(p)

    # The IG resource, its page titles, and the translation catalogue.
    ig_files = sorted(glob.glob(os.path.join(target, "fsh-generated", "resources",
                                             "ImplementationGuide-*.json")))
    ctx["ig_resource"] = read_json(ig_files[0]) if ig_files else None
    ctx["page_titles"] = _page_titles(ctx["ig_resource"])
    po = sorted(glob.glob(os.path.join(target, "input", "translations", "*",
                                       "ImplementationGuide-*.po")))
    ctx["po_path"] = po[0] if po else None
    ctx["po_units"] = _po_units(read_text(ctx["po_path"])) if po else {}

    # Narrative pages, and the target text corpus in the SOURCE's language.
    pc = sorted(glob.glob(os.path.join(target, "input", "pagecontent", "*.md")))
    ctx["narrative_page_names"] = set(os.path.basename(p)[:-3] for p in pc)
    lang_pc = sorted(glob.glob(os.path.join(target, "input", "translations", a.source_lang,
                                            "pagecontent", "*.md")))
    corpus_files = lang_pc or []
    if not corpus_files:
        # A German-only source whose text became the DEFAULT pages (the inverted
        # direction the skill's *Language* section describes) still has to be
        # searchable, so fall back to the default pages rather than reporting an
        # empty corpus.
        corpus_files = pc
    ctx["target_corpus"] = "\n".join(read_text(p) or "" for p in corpus_files)
    # The SAME corpus, kept per page. C6 needs to know which page a text run
    # landed on; C4 only needs to know that it landed somewhere, and a single
    # concatenated string cannot answer the first question.
    ctx["target_page_texts"] = {
        os.path.basename(p)[:-3]: (read_text(p) or "") for p in corpus_files}

    # Menus, the template's own page set, and the languages that have pages.
    ctx["menus"] = read_menus(target)
    ctx["template_pages"] = read_template_pages(a.template_pages)
    ctx["translation_langs"] = set(
        os.path.basename(os.path.dirname(d))
        for d in glob.glob(os.path.join(target, "input", "translations", "*", "pagecontent")))
    ctx["generated_page_stems"] = set(k.replace("/", "-") for k in ctx["generated"])

    # Source pages + their text runs: the harvest manifest first, the source
    # tree second.
    ctx["harvest_rows"] = _harvest_rows(a.harvest_tsv)
    pages, pages_src, runs = [], None, None
    if ctx["harvest_rows"]:
        for r in ctx["harvest_rows"]:
            if r.get("status") != "harvested":
                continue
            fname = os.path.basename(r.get("file") or "")
            stem = fname[:-3] if fname.endswith(".md") else fname
            title = (r.get("title") or "").strip()
            slug = os.path.basename((r.get("url") or "").split("?")[0].rstrip("/"))
            key = stem or title or slug
            pages.append({"key": key,
                          "aliases": [x for x in (key, fname, stem, title, slug) if x],
                          "stem": stem or slug, "url": r.get("url", "")})
        pages_src = os.path.relpath(a.harvest_tsv, target) \
            if a.harvest_tsv.startswith(target) else a.harvest_tsv
    src_md = sorted(glob.glob(os.path.join(a.harvest_dir, "*.md"))) if a.harvest_dir else []
    if not src_md and a.source:
        src_md = sorted(glob.glob(os.path.join(a.source, "input", "pagecontent", "*.md"))) \
            or sorted(glob.glob(os.path.join(a.source, "implementation-guides", "**", "*.md"),
                                recursive=True))
    if src_md:
        runs, tabular = {}, {}
        for p in src_md:
            prose, rows = split_runs(read_text(p) or "")
            runs[os.path.basename(p)] = prose
            tabular[os.path.basename(p)] = rows
        ctx_tabular = tabular
        if not pages:
            pages = [{"key": os.path.basename(p),
                      "aliases": [os.path.basename(p), os.path.basename(p)[:-3]],
                      "stem": os.path.basename(p)[:-3], "url": ""} for p in src_md]
            pages_src = a.harvest_dir if a.harvest_dir else "source pagecontent"
    ctx["source_pages"] = (pages, pages_src)
    ctx["source_runs"] = runs
    ctx["source_tabular"] = locals().get("ctx_tabular") or {}

    ctx["page_map"] = _page_map(a.page_map)

    # The log, and the values other layers read out of it.
    ctx["log"] = parse_log(a.log)
    ctx["log_values"] = _log_values(ctx["log"])
    ctx["expected_steps"] = read_expected_steps(a.expected_steps)
    ctx["shape"] = a.shape or _shape_from_log(ctx["log"])

    # The guide pin: the log's cmd= tokens first, the manifest second.
    ctx["guide_pin"] = _guide_pin(ctx["log"], ctx["harvest_rows"])

    # The publisher pin declared by the target's own build workflow.
    ctx["workflow_publisher_pin"] = _workflow_pin(target)

    # Language variant directories.
    ctx["language_dirs"] = _language_dirs(ctx["variants"], rendered)

    # How many artefacts the rendered index lists.
    ctx["indexed_artifact_count"] = None
    if ctx["variants"]:
        index = read_text(os.path.join(ctx["variants"][0], "artifacts.html")) or ""
        hrefs = set(os.path.basename(h) for h in re.findall(r'href="([^"]+\.html)"', index))
        types = set(k.split("/", 1)[0] for k in ctx["generated"]) or {"StructureDefinition"}
        ctx["indexed_artifact_count"] = sum(
            1 for h in hrefs if any(h.startswith(t + "-") for t in types))
    return ctx


def _page_titles(ig):
    out = []
    if not isinstance(ig, dict):
        return out

    def walk(page):
        if not isinstance(page, dict):
            return
        title = page.get("title")
        if title and title not in out:
            out.append(title)
        for sub in page.get("page", []) or []:
            walk(sub)
    walk(((ig.get("definition") or {}).get("page")) or {})
    return out


def _po_units(text):
    """{msgid: msgstr}. An empty msgstr is a real value here, not an absence."""
    out = {}
    if not text:
        return out
    msgid = None
    for line in text.splitlines():
        m = re.match(r'^msgid\s+"(.*)"$', line)
        if m:
            msgid = m.group(1)
            continue
        m = re.match(r'^msgstr\s+"(.*)"$', line)
        if m and msgid is not None:
            out[msgid] = m.group(1)
            msgid = None
    out.pop("", None)
    return out


def _harvest_rows(path):
    txt = read_text(path)
    if txt is None:
        return None
    lines = txt.splitlines()
    if not lines:
        return []
    header = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        cols = line.split("\t")
        rows.append(dict(zip(header, cols)))
    return rows


def _page_map(path):
    txt = read_text(path)
    if txt is None:
        return None
    out = {}
    for line in txt.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        if cols[0] in ("source_page", "source"):
            continue
        src = cols[0].strip()
        tgt = cols[1].strip() if len(cols) > 1 else ""
        reason = cols[2].strip() if len(cols) > 2 else ""
        out[src] = (tgt, reason)
    return out


def _log_values(entries):
    """Per ACTION, the last `key=value` tokens the log recorded for it."""
    out = {}
    for e in entries or []:
        d = out.setdefault(e["action"], {})
        for k, v in re.findall(r"\b([a-z_]+)=([^\s]+)", e["detail"]):
            d[k] = v
    return out


def _shape_from_log(entries):
    for e in entries or []:
        if e["action"] == "classify-source-shape":
            m = re.search(r"shape=([AB])", e["detail"])
            if m:
                return m.group(1)
    return None


def _guide_pin(entries, rows):
    """The guide version the run actually used, and where that was read.

    The manifest is preferred over the log: it records the URL each page was
    FETCHED from, while a log line may be a discovery hop, a warning about an
    unpinnable guide, or an example. Both are reported with their source so a
    reader can tell which one they are looking at.
    """
    for r in rows or []:
        m = re.search(r"[?&]version=([^\s&]+)", r.get("url", ""))
        if m:
            return m.group(1), "guide-harvest.tsv (the URL pages were fetched from)"
    for e in entries or []:
        m = re.search(r"[?&]version=([^\s&\"'`]+)", e["detail"])
        if m:
            return m.group(1), "run.log, action %s" % e["action"]
    return None, None


def _workflow_pin(target):
    for path in sorted(glob.glob(os.path.join(target, ".github", "workflows", "*.y*ml"))):
        txt = read_text(path) or ""
        m = re.search(r"^\s*(?:IG_)?PUBLISHER_VERSION:\s*['\"]?v?([0-9][0-9.]*)",
                      txt, re.M | re.I)
        if m:
            return m.group(1)
    return None


def _language_dirs(variants, rendered):
    """(default variant, [translated variants]).

    The IG Publisher writes each language into its own directory; which one is
    the default is not in the directory name, so it is read from the site root's
    redirect where there is one, and otherwise from the sushi default (`en`).
    """
    if not variants:
        return None, []
    named = {os.path.basename(v): v for v in variants}
    default = named.get("en") or (variants[0] if len(variants) == 1 else None)
    if default is None:
        return None, []
    others = [v for v in variants if v != default and os.path.basename(v) != os.path.basename(rendered)]
    return default, others


# --- output -----------------------------------------------------------------

def write_findings(path, findings):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(Findings.COLUMNS) + "\n")
        for r in findings.rows:
            fh.write("\t".join(str(r[c]) for c in Findings.COLUMNS) + "\n")


def write_markdown(path, findings, ctx, a):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    div = findings.by_verdict(DIVERG)
    unm = findings.by_verdict(UNMECH)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("## Verification (generated — do not retype)\n\n")
        fh.write("Produced by `verify-migration.py` from the target tree AND "
                 "`migration-log/run.log`, the two oracles. "
                 "**%d IDENTISCH · %d DIVERGIERT · %d NICHT PRÜFBAR.**\n\n"
                 % (len(findings.by_verdict(IDENT)), len(div), len(unm)))
        fh.write("| Layer | Check | IDENTISCH | DIVERGIERT | NICHT PRÜFBAR |\n")
        fh.write("|---|---|---|---|---|\n")
        for check in findings.checks():
            rows = [r for r in findings.rows if r["check"] == check]
            fh.write("| %s | %s | %d | %d | %d |\n" % (
                rows[0]["layer"], check,
                sum(1 for r in rows if r["verdict"] == IDENT),
                sum(1 for r in rows if r["verdict"] == DIVERG),
                sum(1 for r in rows if r["verdict"] == UNMECH)))
        fh.write("\n### DIVERGIERT — each one a stop or a recorded decision\n\n")
        if not div:
            fh.write("none\n")
        else:
            fh.write("| id | Check | Subject | Evidence | Next action | Auto-fixable |\n")
            fh.write("|---|---|---|---|---|---|\n")
            for r in div:
                fh.write("| `%s` | %s | %s | %s | %s | %s |\n" % (
                    r["id"], r["check"], r["subject"], r["evidence"], r["action"],
                    "yes — `%s`" % r["autofix"] if r["autofix"] != "-" else "no"))
        fh.write("\n### NICHT PRÜFBAR — not a pass; each needs a human\n\n")
        if not unm:
            fh.write("none\n")
        else:
            fh.write("| id | Check | Subject | Why not mechanisable | Who does what |\n")
            fh.write("|---|---|---|---|---|\n")
            for r in unm:
                fh.write("| `%s` | %s | %s | %s | %s |\n" % (
                    r["id"], r["check"], r["subject"], r["evidence"], r["action"]))
        fh.write("\n**Inputs:** target `%s` · source `%s` · rendered `%s` · log `%s`\n"
                 % (a.target, a.source or "— (not supplied)", a.rendered, a.log))


# --- main -------------------------------------------------------------------

def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--target", default=".")
    p.add_argument("--source")
    p.add_argument("--rendered")
    p.add_argument("--log")
    p.add_argument("--harvest-tsv", dest="harvest_tsv")
    p.add_argument("--harvest-dir", dest="harvest_dir")
    p.add_argument("--source-html", dest="source_html")
    p.add_argument("--page-map", dest="page_map")
    p.add_argument("--source-lang", dest="source_lang", default="de")
    p.add_argument("--template-latest", dest="template_latest")
    p.add_argument("--publisher-pin", dest="publisher_pin")
    p.add_argument("--expected-steps", dest="expected_steps",
                   default=os.path.join(here, "..", "references", "expected-steps.tsv"))
    p.add_argument("--template-pages", dest="template_pages",
                   default=os.path.join(here, "..", "references", "template-pages.tsv"))
    p.add_argument("--shape", choices=("A", "B"))
    p.add_argument("--layers", default=",".join(LAYERS))
    p.add_argument("--findings")
    p.add_argument("--markdown")
    p.add_argument("--max-list", dest="max_list", type=int, default=3)
    p.add_argument("-h", "--help", action="store_true")
    a = p.parse_args(argv)
    if a.help:
        print(__doc__)
        return 0

    if not os.path.isdir(a.target):
        log("ERROR", "setup: --target is not a directory  target=%s exit=2" % a.target)
        return 2
    logdir = os.path.join(a.target, "migration-log")
    a.log = a.log or os.path.join(logdir, "run.log")
    a.harvest_tsv = a.harvest_tsv or os.path.join(logdir, "guide-harvest.tsv")
    a.harvest_dir = a.harvest_dir or os.path.join(logdir, "guide-harvest", "pagecontent")
    a.source_html = a.source_html or os.path.join(logdir, "guide-harvest", "html")
    a.page_map = a.page_map or os.path.join(logdir, "page-map.tsv")
    a.findings = a.findings or os.path.join(logdir, "verification-findings.tsv")
    a.markdown = a.markdown or os.path.join(logdir, "verification.md")

    selected = [x.strip() for x in a.layers.split(",") if x.strip()]
    unknown = [x for x in selected if x not in LAYERS]
    if unknown:
        log("ERROR", "setup: unknown layer(s) %s  known=%s exit=2"
            % (",".join(unknown), ",".join(LAYERS)))
        return 2

    log("INFO", "%s  target=%s source=%s rendered=%s log=%s layers=%s"
        % (OPEN_WORD, a.target, a.source or "-", a.rendered or "<target>/output",
           a.log, ",".join(selected)))

    ctx = build_context(a)
    f = Findings()
    runners = {"conservation": layer_conservation, "fidelity": layer_fidelity,
               "provenance": layer_provenance, "rendering": layer_rendering,
               "log": layer_log}
    for name in selected:
        runners[name](f, a, ctx)

    # One line per check, then one WARN per check that diverged or could not run.
    for check in f.checks():
        rows = [r for r in f.rows if r["check"] == check]
        layer = rows[0]["layer"]
        nd = sum(1 for r in rows if r["verdict"] == DIVERG)
        nu = sum(1 for r in rows if r["verdict"] == UNMECH)
        ni = len(rows) - nd - nu
        log("INFO", "%s %s  identisch=%d divergiert=%d nicht_pruefbar=%d"
            % (layer, check, ni, nd, nu))
        if nd:
            subjects = [r["subject"] for r in rows if r["verdict"] == DIVERG]
            log("WARN", "verification-divergence: %s %s  count=%d subjects=%s%s"
                % (layer, check, nd, ", ".join(subjects[:a.max_list]),
                   " …" if nd > a.max_list else ""),
                ["Each is a row in %s with its evidence and its next action."
                 % os.path.relpath(a.findings, a.target)])
        if nu:
            subjects = [r["subject"] for r in rows if r["verdict"] == UNMECH]
            log("WARN", "not-mechanisable: %s %s  count=%d subjects=%s%s"
                % (layer, check, nu, ", ".join(subjects[:a.max_list]),
                   " …" if nu > a.max_list else ""),
                ["NOT a pass. Each names the human action it needs; they belong in the",
                 "report's decision queue, and the exit status distinguishes them (3)."])

    write_findings(a.findings, f)
    write_markdown(a.markdown, f, ctx, a)

    nd = len(f.by_verdict(DIVERG))
    nu = len(f.by_verdict(UNMECH))
    ni = len(f.by_verdict(IDENT))
    status = 1 if nd else (3 if nu else 0)
    log("INFO" if status == 0 else "WARN",
        "%s  identisch=%d divergiert=%d nicht_pruefbar=%d findings=%s markdown=%s exit=%d"
        % (CLOSE_WORD, ni, nd, nu, a.findings, a.markdown, status),
        [] if status == 0 else
        ["exit 1 = at least one DIVERGIERT; exit 3 = none, but verification is INCOMPLETE",
         "because a check could not be mechanised. Neither is a pass."])
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
