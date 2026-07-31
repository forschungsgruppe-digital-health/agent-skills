#!/usr/bin/env python3
"""Watch upstream sources that have no version to track.

Dependabot watches manifests. Renovate can watch a version string in an
arbitrary file. Neither helps with an upstream that has no version at all -- a
living specification page, an open proposal, a working group's notes. This
script is the honest answer for those: fetch, normalize, hash, compare.

**It never writes to the repository, and it never opens an issue.** It reports.
The workflow that runs it does the issue upsert, which keeps the reporting logic
testable offline and keeps all GitHub interaction in one place.

**It never updates `last_seen_sha256`.** Acknowledging an upstream change is a
human act; an automatic acknowledgement would silently close the loop the watch
exists to open. Update the value by hand, in a pull request, once you have
assessed the impact -- that pull request *is* the acknowledgement.

Usage:
    python scripts/watch_specs.py --dry-run    # fetch and report; no side effects
    python scripts/watch_specs.py --json       # machine-readable report on stdout
    python scripts/watch_specs.py --print-hashes
                                               # id -> sha256, for seeding the watchlist by hand

Exit codes:
    0  every entry was fetched (whether or not anything changed -- a finding is
       not a failure, it is work to triage)
    1  at least one entry could not be fetched
    2  internal error (unreadable or malformed watchlist)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WATCHLIST = REPO_ROOT / "docs" / "watchlist.yaml"

USER_AGENT = "fgdh-agent-skills-watch/1 (+github.com/forschungsgruppe-digital-health/agent-skills)"
TIMEOUT_SECONDS = 30
EXCERPT_LINES = 40
UNSEEDED = "UNSEEDED"


class WatchError(Exception):
    """The watchlist itself is wrong. Distinct from an upstream being down."""


def load_watchlist(path: Path) -> list[dict]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise WatchError(f"cannot read {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise WatchError(f"{path} is not valid YAML: {exc}") from exc

    if not isinstance(raw, dict) or "watches" not in raw:
        raise WatchError(f"{path} must contain a top-level `watches:` list")
    watches = raw["watches"]
    if not isinstance(watches, list) or not watches:
        raise WatchError(f"{path}: `watches` must be a non-empty list")

    required = ("id", "url", "why", "owner", "last_seen_sha256")
    seen_ids: set[str] = set()
    for index, entry in enumerate(watches):
        if not isinstance(entry, dict):
            raise WatchError(f"{path}: watches[{index}] is not a mapping")
        missing = [key for key in required if key not in entry]
        if missing:
            raise WatchError(f"{path}: watches[{index}] is missing {missing}")
        if entry["id"] in seen_ids:
            raise WatchError(f"{path}: duplicate watch id {entry['id']!r}")
        seen_ids.add(entry["id"])
        if entry.get("kind", "text") not in ("text", "json"):
            raise WatchError(f"{path}: watches[{index}] has an unknown kind {entry.get('kind')!r}")
    return watches


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    if url.startswith("https://api.github.com/"):
        request.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
        return response.read()


def select_fields(payload, fields: list[str]):
    """Project a JSON payload down to the fields that actually matter.

    For a proposal, `state`, `merged` and `updated_at` answer the question; the
    prose of the diff does not, and watching the prose means the watch cries
    wolf every time someone fixes a typo.

    A list payload (`/commits?per_page=1`) is projected element-wise.
    """
    if not fields:
        return payload
    if isinstance(payload, list):
        return [select_fields(item, fields) for item in payload]
    if isinstance(payload, dict):
        return {field: payload.get(field) for field in fields}
    return payload


def normalize(body: bytes, kind: str, fields: list[str]) -> str:
    """Reduce a response to the stable text whose hash we compare."""
    if kind == "json":
        parsed = json.loads(body.decode("utf-8"))
        selected = select_fields(parsed, fields)
        return json.dumps(selected, sort_keys=True, indent=2, ensure_ascii=False) + "\n"

    text = body.decode("utf-8", errors="replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + "\n"


def excerpt(text: str) -> str:
    lines = text.split("\n")
    if len(lines) <= EXCERPT_LINES:
        return text.rstrip("\n")
    kept = "\n".join(lines[:EXCERPT_LINES])
    return f"{kept}\n… ({len(lines) - EXCERPT_LINES} more lines)"


def check(entry: dict) -> dict:
    watch_id = entry["id"]
    kind = entry.get("kind", "text")
    expected = str(entry["last_seen_sha256"])

    result = {
        "id": watch_id,
        "url": entry["url"],
        "kind": kind,
        "why": entry["why"],
        "owner": entry["owner"],
        "last_seen_sha256": expected,
        "status": "unknown",
        "sha256": None,
        "excerpt": None,
        "error": None,
    }

    try:
        body = fetch(entry["url"])
    except urllib.error.HTTPError as exc:
        result["status"] = "error"
        result["error"] = f"HTTP {exc.code} {exc.reason}"
        return result
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        result["status"] = "error"
        result["error"] = f"cannot fetch: {exc}"
        return result

    try:
        normalized = normalize(body, kind, entry.get("watch_fields") or [])
    except (UnicodeDecodeError, ValueError) as exc:
        result["status"] = "error"
        result["error"] = f"cannot normalize response: {exc}"
        return result

    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    result["sha256"] = digest

    if expected in ("", UNSEEDED):
        result["status"] = "unseeded"
    elif digest == expected:
        result["status"] = "unchanged"
    else:
        result["status"] = "changed"
    result["excerpt"] = excerpt(normalized)
    return result


def render_issue_body(result: dict) -> str:
    """The tracking issue for one watch id, rewritten in place on every run."""
    return "\n".join(
        [
            f"<!-- watch-id: {result['id']} -->",
            "",
            f"Upstream **{result['id']}** changed.",
            "",
            f"- Source: <{result['url']}>",
            f"- Why it is watched: {result['why']}",
            f"- Owner: {result['owner']}",
            f"- Recorded hash: `{result['last_seen_sha256']}`",
            f"- Current hash: `{result['sha256']}`",
            "",
            "### Impact assessment (due within one week)",
            "",
            "A finding is not a change request. Classify it, then act only on the last two:",
            "",
            "- [ ] Read the upstream change and classify it: **no impact** / "
            "**documentation only** / **skills affected** / **contract change** (MAJOR release).",
            "- [ ] If it affects the format contract, run the reference validator against "
            "**every** skill first, so the blast radius is measured rather than estimated.",
            "- [ ] Open one issue per affected skill, referencing this one.",
            "- [ ] Update `last_seen_sha256` for this entry in `docs/watchlist.yaml`, in a pull "
            "request. Nothing does this automatically, on purpose: that pull request is the "
            "acknowledgement.",
            "",
            "### Current normalized content",
            "",
            "Only the hash is stored, not the previous content, so this is the current state "
            "rather than a diff. Compare it against the upstream history if you need one.",
            "",
            "```",
            result["excerpt"] or "",
            "```",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch, normalize and hash each watched upstream; report what moved.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="fetch and report only; identical to the default, stated explicitly for CI",
    )
    parser.add_argument("--json", dest="as_json", action="store_true", help="JSON report on stdout")
    parser.add_argument(
        "--print-hashes",
        action="store_true",
        help="print `id: sha256` for every entry, for seeding the watchlist by hand",
    )
    parser.add_argument("--watchlist", type=Path, default=WATCHLIST)
    args = parser.parse_args(argv)

    try:
        watches = load_watchlist(args.watchlist)
    except WatchError as exc:
        print(f"internal error: {exc}", file=sys.stderr)
        return 2

    results = [check(entry) for entry in watches]

    if args.print_hashes:
        for result in results:
            print(f"{result['id']}: {result['sha256'] or '(fetch failed)'}")
        return 0 if all(r["status"] != "error" for r in results) else 1

    if args.as_json:
        payload = [
            {
                **{k: v for k, v in result.items() if k != "excerpt"},
                "issue_title": f"spec-watch: {result['id']} changed upstream",
                "issue_body": render_issue_body(result) if result["status"] == "changed" else None,
            }
            for result in results
        ]
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        width = max(len(result["id"]) for result in results)
        for result in results:
            detail = result["error"] or result["sha256"] or ""
            print(f"{result['id']:<{width}}  {result['status']:<9}  {detail}")

        changed = [r["id"] for r in results if r["status"] == "changed"]
        unseeded = [r["id"] for r in results if r["status"] == "unseeded"]
        errors = [r["id"] for r in results if r["status"] == "error"]
        print()
        print(f"{len(results)} watched, {len(changed)} changed, {len(unseeded)} unseeded, "
              f"{len(errors)} unreachable")
        if unseeded:
            print("seed these with `--print-hashes` and commit the values:", ", ".join(unseeded))
        if args.dry_run:
            print("dry run: nothing was written and no issue was opened")

    return 1 if any(result["status"] == "error" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
