#!/usr/bin/env python3
"""license-align -- make the migrated module's LICENSE file carry the SOURCE
module's licence, and TELL the person migrating what was replaced with what.

WHY THIS EXISTS. The module template scaffold ships a LICENSE file (the CC BY
4.0 legal code -- its first line, "Attribution 4.0 International", is the
licence's formal title). A migrated module inherits that file, while its
DECLARED licence scalar (sushi-config.yaml / package.json `license:`) is
carried from the source. Measured across the medizininformatik-initiative
kerndatensatz repositories (2026-08-27): 11 modules declare CC-BY-4.0, 6
declare CC0-1.0 -- and NONE of the CC0 modules ships a LICENSE file, so every
CC0 migration used to end with a declared CC0 next to a shipped CC-BY file: a
real licence contradiction, flagged by F3 and the pre/post delta, parked at
Gate A. This script closes the class mechanically and HONESTLY: the source's
licence wins, the replacement is announced (from -> to), and only the cases no
tool may decide -- no licence anywhere, or a licence this catalog has no text
for -- stay human.

THE CONTRACT, in priority order (first matching row acts):

  | source state                          | action                          |
  |---------------------------------------|---------------------------------|
  | LICENSE(.md/.txt) file exists         | copy it BYTE-FAITHFULLY over    |
  |                                       | the target's LICENSE; announce  |
  |                                       | from -> to                      |
  | no file, declared SPDX id with a      | write the vendored OFFICIAL     |
  | vendored legal code (references/      | legal code; announce from -> to |
  | licenses/<id>.txt)                    |                                 |
  | no file, declared id WITHOUT a        | change nothing; WARN and exit 1 |
  | vendored text (or an id that is not   | -- a human supplies the text    |
  | a plain SPDX name)                    |                                 |
  | no file, no declaration               | change nothing; WARN and exit 1 |
  |                                       | -- the template's licence stays |
  |                                       | in effect ONLY if Gate A says so|

  * If the source's own file CONTRADICTS its declared scalar, the FILE is
    copied (the shipped text is the operative grant) and the contradiction is
    WARNed with the `identity-contradiction:` token -- never silently
    resolved.
  * If the target already carries the source's licence (byte-identical file,
    or a text recognized as the declared id), nothing is rewritten -- but a
    variant file name (`LICENSE.md`/`.txt`) is normalized to `LICENSE`
    (`license-variant-normalized:`), so the canonical name never depends on
    whether bytes happened to match.
  * The copy is BINARY: a legal text is never re-encoded, its line endings
    never rewritten. A source or target licence file that EXISTS but cannot
    be READ is a loud exit-2 error, never an empty string -- an unreadable
    source must not erase the target's licence.
  * Writes are atomic (temp file + rename) and every partial state a failing
    filesystem can leave is NAMED in the error: nothing is ever silently
    half-done.
  * Only the LICENSE file is aligned. Licence MENTIONS inside template pages
    (a metadata page naming CC-BY, an index footer naming Creative Commons)
    are page content, handled by the page steps and still caught by F3 and
    the delta -- this script never edits pages.

Usage:

  license-align.py --source <source-repo> --target <migrated-repo>
                   [--declared <SPDX id>] [--licenses-dir DIR]

    --source DIR     the ORIGINAL module repository
    --target DIR     the migrated repository whose LICENSE is aligned
    --declared ID    override the declared licence (default: read from the
                     source's sushi-config.yaml `license:` or package.json /
                     package/package.json `license`)
    --licenses-dir   where the vendored official legal codes live (default:
                     the references/licenses/ sibling of this script).
                     Lookups are CONFINED to this directory: an id that is
                     not a plain SPDX name (letters, digits, ., +, -) is
                     refused, and a resolved path outside the directory is
                     refused too -- a hostile `license:` value in a source
                     repository must not read arbitrary files.

Exit codes:
    0  aligned (replaced or already aligned) -- the announcement was printed
    1  attention required: no licence anywhere, no vendored text for the
       declared id, or a source-internal contradiction was carried visibly
    2  setup or filesystem error -- the run changed nothing, or the error
       names exactly what it left behind

Run-log lines follow the catalog convention (spec section 10.2); wrapped as
`bash "$ML" run 5.2 license-align --emits-runlog -- python3 .../license-align.py ...`.

stdlib only, like the rest of the catalog's scripts.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time

STEP = "5.2"
ACTION = "license-align"
WRAPPED = os.environ.get("MIGRATION_LOG_WRAPPED") == "1"
OPEN_WORD = "params" if WRAPPED else "start"
CLOSE_WORD = "result" if WRAPPED else "done"
_LEVEL = {"INFO": "INFO ", "WARN": "WARN ", "ERROR": "ERROR"}

LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt")

# A plain SPDX-shaped id: the only thing the vendored lookup accepts, so a
# hostile `license:` value ("../evil", an absolute path) can never leave
# references/licenses/.
SPDX_SHAPE = re.compile(r"[A-Za-z0-9][A-Za-z0-9.+-]*\Z")

# Text recognition, shared vocabulary with the verifier's F3: the marker
# phrase each legal code is identified by, scanning the file's first lines.
RECOGNITION = (
    ("Attribution 4.0 International", "CC-BY-4.0"),
    ("CC0 1.0 Universal", "CC0-1.0"),
    ("Creative Commons Zero", "CC0-1.0"),
    ("Apache License", "Apache-2.0"),
    ("MIT License", "MIT"),
)


def log(level, detail, cont=()):
    stream = sys.stdout if level == "SUMMARY" else sys.stderr
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print("%s  %s  %s  %s  %s"
          % (ts, _LEVEL.get(level, _LEVEL["INFO"]), STEP, ACTION, detail),
          file=stream, flush=True)
    for c in cont:
        print("    %s" % c, file=stream, flush=True)


def read_bytes(path):
    """The file's exact bytes, or None on ANY read failure.  The caller must
    treat None loudly: an unreadable licence read as empty text is how a
    target licence gets erased by a permissions problem."""
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError:
        return None


def read_config_text(path):
    """Config files (sushi-config, package.json) read as text; unreadable is
    empty here because absence and unreadability both mean 'this source did
    not declare' -- the LICENSE files themselves never go through this."""
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


def fail(message, cont=()):
    log("ERROR", message, cont)
    log("SUMMARY", "%s  FAILED: %s  exit=2" % (CLOSE_WORD, message))
    return 2


def write_license(target, data):
    """Write `data` as the target's `LICENSE` -- atomically (temp file +
    rename, so an unwritable directory fails BEFORE anything changes) -- and
    remove every other licence-file variant.  Returns "" on success or the
    failure message; a failure after the rename NAMES what was left behind."""
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(prefix=".license-align-", dir=target)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp, os.path.join(target, "LICENSE"))
        tmp = None
    except OSError as error:
        if tmp:
            try:
                os.remove(tmp)
            except OSError:
                pass
        return ("cannot write the target LICENSE (%s) - the target is "
                "UNCHANGED" % error)
    for name in LICENSE_NAMES[1:]:
        path = os.path.join(target, name)
        if os.path.isfile(path):
            try:
                os.remove(path)
                log("INFO", "license-variant-removed: %s (superseded by the "
                            "aligned LICENSE)" % name)
            except OSError as error:
                return ("the aligned LICENSE was written, but the OLD %s "
                        "could NOT be removed (%s) - two licence files now "
                        "disagree; remove %s by hand and re-run"
                        % (name, error, name))
    return ""


def normalize_variant(target, path):
    """An already-aligned licence living under a variant name is renamed to
    the canonical `LICENSE`, and every OTHER variant file is removed -- the
    already-aligned path must leave the same single-file state the replace
    path does, or a stale LICENSE.md keeps contradicting the aligned text.
    Returns (kept_name, leftovers): a rename or removal the filesystem
    refuses is WARNed and returned, never silent -- the CONTENT is correct
    either way, but a leftover contradicting file demands attention."""
    kept = os.path.basename(path)
    if kept != "LICENSE":
        try:
            os.replace(path, os.path.join(target, "LICENSE"))
            log("INFO", "license-variant-normalized: %s -> LICENSE (content "
                        "unchanged)" % kept)
            kept = "LICENSE"
        except OSError as error:
            log("WARN", "license-variant-kept: %s could not be renamed to "
                        "LICENSE (%s) - the content is aligned, the name is "
                        "not" % (kept, error))
    leftovers = []
    for name in LICENSE_NAMES:
        other = os.path.join(target, name)
        if name != kept and os.path.isfile(other):
            try:
                os.remove(other)
                log("INFO", "license-variant-removed: %s (superseded by the "
                            "aligned %s)" % (name, kept))
            except OSError as error:
                leftovers.append(name)
                log("WARN", "license-variant-kept: the OLD %s could NOT be "
                            "removed (%s) - it may CONTRADICT the aligned "
                            "%s; remove it by hand" % (name, error, kept))
    return kept, leftovers


def find_license_file(root):
    for name in LICENSE_NAMES:
        path = os.path.join(root, name)
        if os.path.isfile(path):
            return path
    return None


def recognize(data):
    """The SPDX id a licence text reads as, from its opening lines (decoded
    tolerantly FOR MATCHING ONLY -- the bytes written are never these); the
    CC texts open with a generic 'Creative Commons Legal Code' line, so the
    scan covers the first 40 lines, not just the first."""
    if data is None:
        return None
    head = "\n".join(data.decode("utf-8", "replace").splitlines()[:40])
    for marker, spdx in RECOGNITION:
        if marker.lower() in head.lower():
            return spdx
    return None


def declared_license(source_root):
    """The source's declared licence scalar and where it was read.  Never
    guessed: sushi-config `license:` first, then the package manifests."""
    sushi = os.path.join(source_root, "sushi-config.yaml")
    if not os.path.isfile(sushi):
        sushi = os.path.join(source_root, "sushi-config.yml")
    if os.path.isfile(sushi):
        match = re.search(r"^license:\s*([^#\s]+)\s*(?:#.*)?$",
                          read_config_text(sushi), re.M)
        if match:
            return match.group(1).strip().strip("'\""), \
                os.path.relpath(sushi, source_root)
    for manifest in ("package.json", os.path.join("package", "package.json"),
                     os.path.join("Package", "package.json")):
        path = os.path.join(source_root, manifest)
        if os.path.isfile(path):
            try:
                value = json.load(open(path, encoding="utf-8")).get("license")
            except (OSError, ValueError):
                continue
            if value:
                return str(value).strip(), manifest
    return None, None


def vendored_path(licenses_dir, declared):
    """The vendored legal code for a declared id, CONFINED to licenses_dir:
    a non-SPDX-shaped id or a path resolving outside the directory returns
    None -- refused, never read."""
    if not SPDX_SHAPE.match(declared or ""):
        return None
    path = os.path.realpath(os.path.join(licenses_dir, "%s.txt" % declared))
    root = os.path.realpath(licenses_dir)
    if path != os.path.join(root, "%s.txt" % declared):
        return None
    return path if os.path.isfile(path) else None


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Align the migrated module's LICENSE file with the "
                    "source's licence, announcing every replacement.")
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--declared")
    parser.add_argument("--licenses-dir", dest="licenses_dir")
    args = parser.parse_args(argv)

    source = os.path.abspath(args.source)
    target = os.path.abspath(args.target)
    if not os.path.isdir(source) or not os.path.isdir(target):
        log("ERROR", "setup: --source and --target must be directories  "
                     "source=%s target=%s exit=2" % (source, target))
        return 2
    licenses_dir = os.path.abspath(args.licenses_dir) if args.licenses_dir \
        else os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "references", "licenses")

    log("INFO", "%s  source=%s target=%s" % (OPEN_WORD, source, target))

    target_path = find_license_file(target)
    target_data = None
    if target_path:
        target_data = read_bytes(target_path)
        if target_data is None:
            return fail("the target's %s exists but cannot be read - "
                        "refusing to align against an unreadable file"
                        % os.path.basename(target_path))
    from_id = recognize(target_data)
    from_label = from_id or ("unrecognized text" if target_data
                             else "no LICENSE file")

    declared, declared_source = (args.declared, "--declared") \
        if args.declared else declared_license(source)
    source_file = find_license_file(source)
    status = 0

    if source_file:
        source_data = read_bytes(source_file)
        if source_data is None:
            return fail("the source's %s exists but cannot be read - an "
                        "unreadable source must never erase the target's "
                        "licence; nothing changed"
                        % os.path.basename(source_file))
        to_id = recognize(source_data)
        to_label = to_id or "unrecognized text"
        if declared and to_id and declared.strip().lower() != to_id.lower():
            log("WARN", "identity-contradiction: the source's own LICENSE "
                        "file (%s) reads as %s but its declared scalar (%s) "
                        "says %s" % (os.path.basename(source_file), to_id,
                                     declared_source, declared),
                ["The FILE is copied -- the shipped text is the operative "
                 "grant -- and the contradiction stays visible for Gate A;",
                 "this script never resolves a source-internal conflict."])
            status = 1
        if target_data is not None and source_data == target_data:
            kept, leftovers = normalize_variant(target, target_path)
            verdict = ("already aligned: the target %s is byte-identical to "
                       "the source's (%s)%s"
                       % (kept, to_label,
                          "; LEFTOVER variant file(s) demand attention: %s"
                          % ", ".join(leftovers) if leftovers else ""))
            if leftovers:
                status = 1
        else:
            error = write_license(target, source_data)
            if error:
                return fail(error)
            verdict = ("REPLACED the target LICENSE: %s (template scaffold) "
                       "-> %s (copied byte-faithfully from the source's %s)"
                       % (from_label, to_label,
                          os.path.basename(source_file)))
            log("INFO", "license-replaced: from=%s to=%s mode=source-file "
                        "file=%s" % (from_label, to_label,
                                     os.path.basename(source_file)))
    elif declared:
        vendored = vendored_path(licenses_dir, declared)
        if from_id and from_id.lower() == declared.strip().lower():
            kept, leftovers = normalize_variant(target, target_path)
            verdict = ("already aligned: the target %s reads as the "
                       "declared %s%s"
                       % (kept, declared,
                          "; LEFTOVER variant file(s) demand attention: %s"
                          % ", ".join(leftovers) if leftovers else ""))
            if leftovers:
                status = 1
        elif vendored:
            vendored_data = read_bytes(vendored)
            if vendored_data is None:
                return fail("the vendored text %s cannot be read; nothing "
                            "changed" % vendored)
            error = write_license(target, vendored_data)
            if error:
                return fail(error)
            verdict = ("REPLACED the target LICENSE: %s (template scaffold) "
                       "-> %s (the OFFICIAL legal code, vendored with this "
                       "skill, because the source declares %s in %s but "
                       "ships no LICENSE file)"
                       % (from_label, declared, declared, declared_source))
            log("INFO", "license-replaced: from=%s to=%s "
                        "mode=declared-vendored declared_in=%s"
                % (from_label, declared, declared_source))
        else:
            shape_note = "" if SPDX_SHAPE.match(declared) else \
                " (the id is not a plain SPDX name - refused, never a path)"
            verdict = ("NOT aligned: the source declares %s (%s) but ships "
                       "no LICENSE file and this catalog vendors no text "
                       "for that id%s -- a human supplies the official text "
                       "at Gate A; the target keeps %s meanwhile"
                       % (declared, declared_source, shape_note, from_label))
            log("WARN", "license-unvendored: declared=%s -- no vendored "
                        "legal code%s; the target LICENSE (%s) is UNCHANGED "
                        "and stays a Gate-A item"
                % (declared, shape_note, from_label),
                ["Add references/licenses/<id>.txt (the official text, "
                 "verbatim) and re-run."])
            status = 1
    else:
        verdict = ("NOT aligned: the source ships NO licence -- no file, no "
                   "declaration. The template's %s stays in effect ONLY if "
                   "Gate A decides so; licensing a module is a human act, "
                   "never this script's" % from_label)
        log("WARN", "license-missing: the source carries no licence "
                    "evidence at all -- target LICENSE (%s) UNCHANGED, "
                    "Gate-A decision required" % from_label)
        status = 1

    log("SUMMARY", "%s  %s  exit=%d" % (CLOSE_WORD, verdict, status))
    return status


if __name__ == "__main__":
    sys.exit(main())
