"""Split a Markdown file into its YAML frontmatter and its body.

This module has exactly one responsibility. It does not validate the catalog
contract, it does not know what a skill is, and it never touches the network.
Validation lives in `scripts/build_index.py`; keeping the two apart is what lets
the index builder stay deterministic and offline.
"""

from __future__ import annotations

from pathlib import Path

import yaml

FENCE = "---"


class FrontmatterError(Exception):
    """A file could not be split into frontmatter and body.

    Always carries the offending path, because these errors are read in CI logs
    where the traceback alone does not say which of forty skills is broken.
    """

    def __init__(self, path: Path | str, message: str) -> None:
        self.path = Path(path)
        self.message = message
        super().__init__(f"{self.path}: {message}")


def split(text: str, path: Path | str = "<string>") -> tuple[dict, str]:
    """Return ``(frontmatter, body)`` for the given Markdown source.

    The frontmatter is the YAML block delimited by a line containing exactly
    ``---`` at the very start of the file and the next such line. The body is
    everything after the closing fence, with the leading newline removed.

    Raises:
        FrontmatterError: if the opening or closing fence is missing, if the
            YAML is malformed, or if the YAML does not parse to a mapping.
    """
    lines = text.split("\n")

    if not lines or lines[0].rstrip("\r") != FENCE:
        raise FrontmatterError(
            path,
            "file does not start with a '---' frontmatter fence "
            "(the fence must be the very first line, with nothing before it)",
        )

    closing = None
    for index in range(1, len(lines)):
        if lines[index].rstrip("\r") == FENCE:
            closing = index
            break

    if closing is None:
        raise FrontmatterError(path, "frontmatter is never closed by a second '---' line")

    raw = "\n".join(lines[1:closing])
    body = "\n".join(lines[closing + 1 :])
    if body.startswith("\n"):
        body = body[1:]

    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise FrontmatterError(path, f"frontmatter is not valid YAML: {exc}") from exc

    if parsed is None:
        parsed = {}

    if not isinstance(parsed, dict):
        raise FrontmatterError(
            path,
            f"frontmatter must be a YAML mapping, got {type(parsed).__name__}",
        )

    return parsed, body


def load(path: Path | str) -> tuple[dict, str]:
    """Read a file from disk and split it. See :func:`split`."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FrontmatterError(path, f"cannot read file: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise FrontmatterError(path, f"file is not valid UTF-8: {exc}") from exc
    return split(text, path)
