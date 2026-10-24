"""A small reader for Valve's VDF text format.

The format is a tree of keys and values, either strings or nested blocks:

    "root"
    {
        "name"   "Half-Life 2"
        "child"  { "x" "1" }
    }

Comments start with ``//`` and run to the end of the line. Values may be
quoted (with the usual backslash escapes) or bare. Keys are matched
case-insensitively by :func:`get`, because Steam is inconsistent about case.

Implemented from the public description of the format; no third-party code.
"""

from __future__ import annotations

from typing import Iterator, Union

VdfDict = dict[str, "VdfValue"]
VdfValue = Union[str, VdfDict]

_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"'}
_WHITESPACE = " \t\r\n"


class VdfError(ValueError):
    """The text is not a valid VDF document."""


def _tokens(text: str) -> Iterator[str]:
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch in _WHITESPACE:
            i += 1
        elif ch == "/" and text.startswith("//", i):
            end = text.find("\n", i)
            i = n if end < 0 else end + 1
        elif ch in "{}":
            yield ch
            i += 1
        elif ch == '"':
            i += 1
            buf: list[str] = []
            while i < n and text[i] != '"':
                if text[i] == "\\" and i + 1 < n:
                    nxt = text[i + 1]
                    buf.append(_ESCAPES.get(nxt, nxt))
                    i += 2
                else:
                    buf.append(text[i])
                    i += 1
            if i >= n:
                raise VdfError("unterminated quoted string")
            i += 1
            yield "".join(buf)
        else:
            start = i
            while i < n and text[i] not in _WHITESPACE and text[i] not in '{}"':
                i += 1
            yield text[start:i]


def _block(tokens: list[str], i: int) -> tuple[VdfDict, int]:
    node: VdfDict = {}
    while True:
        if i >= len(tokens):
            raise VdfError("unclosed block")
        key = tokens[i]
        if key == "}":
            return node, i + 1
        if key == "{":
            raise VdfError("unexpected '{'")
        if i + 1 >= len(tokens):
            raise VdfError(f"key {key!r} has no value")
        value = tokens[i + 1]
        if value == "{":
            child, i = _block(tokens, i + 2)
            node[key] = child
        elif value == "}":
            raise VdfError(f"key {key!r} has no value")
        else:
            node[key] = value
            i += 2


def parse(text: str) -> VdfDict:
    """Parse a whole document into nested dictionaries."""
    tokens = list(_tokens(text))
    root: VdfDict = {}
    i = 0
    while i < len(tokens):
        key = tokens[i]
        if key in "{}":
            raise VdfError(f"unexpected {key!r} at the top level")
        if i + 1 >= len(tokens):
            raise VdfError(f"key {key!r} has no value")
        value = tokens[i + 1]
        if value == "{":
            child, i = _block(tokens, i + 2)
            root[key] = child
        elif value == "}":
            raise VdfError(f"key {key!r} has no value")
        else:
            root[key] = value
            i += 2
    return root


def get(node: VdfValue, key: str, default: str | None = None) -> str | None:
    """Case-insensitive lookup of a string value."""
    if not isinstance(node, dict):
        return default
    if key in node:
        value = node[key]
        return value if isinstance(value, str) else default
    wanted = key.casefold()
    for candidate, value in node.items():
        if candidate.casefold() == wanted and isinstance(value, str):
            return value
    return default


def get_block(node: VdfValue, key: str) -> VdfDict | None:
    """Case-insensitive lookup of a nested block."""
    if not isinstance(node, dict):
        return None
    if key in node and isinstance(node[key], dict):
        return node[key]
    wanted = key.casefold()
    for candidate, value in node.items():
        if candidate.casefold() == wanted and isinstance(value, dict):
            return value
    return None
