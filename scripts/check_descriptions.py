#!/usr/bin/env python3
"""Detect trigger collisions between skill descriptions.

This is the dominant failure mode of a multi-domain catalog. An agent sees only
`name` and `description` before deciding which skill to activate, so two skills
whose descriptions compete for the same request do not merely look similar --
they make triggering depend on chance.

**This is a deterministic heuristic, not a semantic judgement.** It compares
token sets, so it finds descriptions that reuse each other's vocabulary. It
cannot see that two differently worded skills answer the same question, and it
will flag two genuinely distinct skills that happen to share jargon. A finding
is a prompt to look, not a verdict. The thresholds are tunable per repository
and the shared tokens are printed precisely so the finding is actionable.

Usage:
    python scripts/check_descriptions.py
    python scripts/check_descriptions.py --warn 0.30 --fail 0.55
    python scripts/check_descriptions.py --stopword kerndatensatz --stopword fhir
    python scripts/check_descriptions.py --stopwords-file scripts/domain-stopwords.txt

Exit codes:
    0  no pair at or above the failure threshold
    1  at least one pair at or above the failure threshold
    2  internal error
"""

from __future__ import annotations

import argparse
import re
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.frontmatter import FrontmatterError, load  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
DEFAULT_STOPWORDS_FILE = REPO_ROOT / "scripts" / "domain-stopwords.txt"


def configure(skills_dir: Path) -> None:
    """Point the checker at a different skills directory (see `--skills-dir`)."""
    global SKILLS_DIR
    SKILLS_DIR = skills_dir.resolve()

MIN_TOKEN_LENGTH = 3

# A small built-in English stopword list. Deliberately small: an aggressive list
# would strip the verbs that carry a description's meaning ("generate",
# "validate", "review") and make everything look similar to everything.
STOPWORDS = {
    "a", "about", "after", "all", "also", "an", "and", "any", "are", "as", "at",
    "be", "been", "before", "being", "both", "but", "by", "can", "do", "does",
    "each", "either", "for", "from", "has", "have", "how", "into", "is", "it",
    "its", "may", "more", "most", "must", "no", "not", "now", "of", "on", "one",
    "only", "or", "other", "over", "own", "same", "should", "since", "so",
    "some", "such", "than", "that", "the", "their", "them", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "use", "used", "uses", "using", "very", "was", "were", "what", "when",
    "where", "which", "while", "who", "why", "will", "with", "within",
    "without", "would", "you", "your",
}

TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str, stopwords: set[str]) -> set[str]:
    return {
        token
        for token in TOKEN.findall(text.lower())
        if len(token) >= MIN_TOKEN_LENGTH and token not in stopwords
    }


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    union = left | right
    return len(left & right) / len(union)


def load_skills(stopwords: set[str]) -> list[tuple[str, set[str]]]:
    if not SKILLS_DIR.is_dir():
        return []
    skills: list[tuple[str, set[str]]] = []
    for skill_dir in sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        try:
            frontmatter, _ = load(skill_md)
        except FrontmatterError as exc:
            print(f"skipping {skill_dir.name}: {exc.message}", file=sys.stderr)
            continue
        name = frontmatter.get("name") or skill_dir.name
        description = frontmatter.get("description") or ""
        if not isinstance(name, str) or not isinstance(description, str):
            print(f"skipping {skill_dir.name}: name/description is not a string", file=sys.stderr)
            continue
        skills.append((name, tokenize(f"{name} {description}", stopwords)))
    return sorted(skills, key=lambda pair: pair[0])


def resolve_stopwords(extra: list[str], files: list[Path]) -> set[str]:
    stopwords = set(STOPWORDS)
    for path in files:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            word = line.split("#", 1)[0].strip().lower()
            if word:
                stopwords.add(word)
    stopwords.update(word.strip().lower() for word in extra if word.strip())
    return stopwords


def run(warn: float, fail: float, stopwords: set[str]) -> int:
    skills = load_skills(stopwords)

    if len(skills) < 2:
        print(
            f"{len(skills)} skill(s) in the catalog: no pair to compare, nothing to collide."
        )
        return 0

    pairs = sorted(
        (
            (jaccard(left_tokens, right_tokens), left, right, sorted(left_tokens & right_tokens))
            for (left, left_tokens), (right, right_tokens) in combinations(skills, 2)
        ),
        key=lambda item: (-item[0], item[1], item[2]),
    )

    top_score, top_left, top_right, top_shared = pairs[0]
    print(
        f"highest similarity: {top_score:.3f}  {top_left} <-> {top_right}"
        + (f"  shared: {', '.join(top_shared)}" if top_shared else "")
    )

    flagged = [pair for pair in pairs if pair[0] >= warn]
    failing = [pair for pair in pairs if pair[0] >= fail]

    if flagged:
        print(f"\n{len(flagged)} pair(s) at or above the warn threshold ({warn:.2f}):")
        for score, left, right, shared in flagged:
            marker = "FAIL" if score >= fail else "warn"
            print(f"  [{marker}] {score:.3f}  {left} <-> {right}")
            print(f"           shared tokens: {', '.join(shared) if shared else '(none)'}")

    if failing:
        print(
            f"\n{len(failing)} pair(s) at or above the failure threshold ({fail:.2f}). "
            "Either merge the skills or sharpen both descriptions: name the situations each "
            "one is for, and add a delimitation clause to each naming the other.",
            file=sys.stderr,
        )
        return 1

    print(f"\nno pair reaches the failure threshold ({fail:.2f}).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report skill descriptions that compete for the same requests.",
    )
    parser.add_argument("--warn", type=float, default=0.40, help="report pairs at or above this")
    parser.add_argument("--fail", type=float, default=0.60, help="exit 1 at or above this")
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=None,
        help="compare the skills in this directory instead of ./skills; used by the reusable "
        "workflow for consuming repositories",
    )
    parser.add_argument(
        "--stopword",
        action="append",
        default=[],
        dest="stopwords",
        help="an additional domain stopword; repeatable",
    )
    parser.add_argument(
        "--stopwords-file",
        action="append",
        default=[],
        type=Path,
        dest="stopwords_files",
        help="a file of domain stopwords, one per line, '#' comments allowed; repeatable",
    )
    args = parser.parse_args(argv)

    if not 0.0 <= args.warn <= 1.0 or not 0.0 <= args.fail <= 1.0:
        print("thresholds must be between 0.0 and 1.0", file=sys.stderr)
        return 2
    if args.fail < args.warn:
        print("--fail must not be below --warn", file=sys.stderr)
        return 2

    if args.skills_dir is not None:
        if not args.skills_dir.is_dir():
            print(f"--skills-dir: {args.skills_dir} is not a directory", file=sys.stderr)
            return 2
        configure(args.skills_dir)

    files = list(args.stopwords_files) or [DEFAULT_STOPWORDS_FILE]

    try:
        return run(args.warn, args.fail, resolve_stopwords(args.stopwords, files))
    except Exception as exc:  # noqa: BLE001 - exit code 2 means "the tool broke"
        print(f"internal error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
