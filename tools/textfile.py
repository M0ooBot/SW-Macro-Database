"""Reading the repo's text files the way the package requires them.

Every text file in the package is UTF-8 without a byte-order mark (SPEC/03
§8.3), and SW-Agent's reader decodes strictly. read() refuses the same files,
as a problem line rather than a traceback. Python 3 stdlib only.
"""

from __future__ import annotations

import pathlib

BOM = b"\xef\xbb\xbf"


def problem(data: bytes) -> str | None:
    """Why bytes are not package text (a BOM, or not UTF-8), or None."""
    if data.startswith(BOM):
        return "starts with a byte-order mark; save it as UTF-8 without one"
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return f"not valid UTF-8 (byte {exc.start}: {exc.reason})"
    return None


def read(path: pathlib.Path, rel: str):
    """(text, None) or (None, "<rel>: why"). Newlines are read as LF, as open() does."""
    try:
        data = path.read_bytes()
    except OSError as exc:
        return None, f"{rel}: cannot be read ({exc.strerror or exc})"
    why = problem(data)
    if why:
        return None, f"{rel}: {why}"
    return data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n"), None
