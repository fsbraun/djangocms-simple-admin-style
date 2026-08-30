"""A small CSS reader that flattens nested rules into plain selectors.

The stylesheets in ``private/`` use native CSS nesting (``&``), and the minifier
preserves it, so neither the source nor the built file can be handed to a flat
selector parser. This module walks the rule tree and resolves nesting so the
coverage test can match each selector against rendered admin HTML.

It is deliberately not a general-purpose CSS parser: it only needs to get the
*selectors* right, and it ignores every declaration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# At-rules whose body contains nested style rules that should be walked into.
# Anything else (@font-face, @keyframes, @property, ...) has a body of
# declarations or keyframe selectors, never selectors we can match against HTML.
CONDITIONAL_AT_RULES = ("media", "supports", "layer", "container", "scope")

# Pseudo-classes describing a state the rendered HTML never has. Left in place
# they would make every rule that uses one look dead.
STATE_PSEUDO_CLASSES = (
    "hover",
    "focus",
    "focus-visible",
    "focus-within",
    "active",
    "visited",
    "target",
    "checked",
    "indeterminate",
    "disabled",
    "enabled",
    "placeholder-shown",
    "autofill",
    "user-invalid",
    "user-valid",
    "open",
)

# Pseudo-elements, including the legacy single-colon spellings the stylesheets
# still use (`label:after`).
LEGACY_PSEUDO_ELEMENTS = ("before", "after", "first-line", "first-letter", "marker", "selection")

_STATE_RE = re.compile(r":(?:{})\b(?!\()".format("|".join(STATE_PSEUDO_CLASSES)))
_PSEUDO_ELEMENT_RE = re.compile(r"::[a-zA-Z-]+(?:\([^)]*\))?|:(?:{})\b(?!\()".format("|".join(LEGACY_PSEUDO_ELEMENTS)))
_EMPTY_FUNCTIONAL_RE = re.compile(r":[a-zA-Z-]+\(\s*\)")


@dataclass(frozen=True)
class Rule:
    selector: str
    line: int
    group: int
    """Index of the declaration block this selector came from.

    A rule written as `.a, .b { ... }` yields two Rules sharing one group. The
    coverage test treats a group as live when *any* member matches: these
    stylesheets intentionally list selectors for several Django versions side by
    side, so a member that is dead on the Django under test is expected.
    """

    def __str__(self):
        return f"{self.selector}  (line {self.line})"


def _strip_comments(css: str) -> str:
    """Remove /* */ comments, preserving line numbers and ignoring strings.

    String awareness matters: the stylesheets embed SVG data URIs inside
    ``url("...")`` values, and a naive regex can chew through them.
    """
    out = []
    i, n = 0, len(css)
    quote = None
    while i < n:
        ch = css[i]
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(css[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
        elif ch in "\"'":
            quote = ch
            out.append(ch)
            i += 1
        elif ch == "/" and css.startswith("/*", i):
            end = css.find("*/", i + 2)
            end = n if end == -1 else end + 2
            # Keep the newlines so reported line numbers stay accurate.
            out.append("\n" * css.count("\n", i, end))
            i = end
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _split_top_level(text: str, sep: str = ",") -> list[str]:
    """Split on `sep`, ignoring separators inside (), [] or strings."""
    parts, buf = [], []
    depth = 0
    quote = None
    for ch in text:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == sep and depth == 0:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def _iter_blocks(css: str, start: int, end: int):
    """Yield (prelude, body_start, body_end, prelude_offset) for one nesting level."""
    i = start
    prelude_start = i
    depth = 0
    quote = None
    body_start = None
    while i < end:
        ch = css[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in "\"'":
            quote = ch
        elif ch == "{":
            depth += 1
            if depth == 1:
                body_start = i + 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                prelude = css[prelude_start : body_start - 1]
                lead = len(prelude) - len(prelude.lstrip())
                yield prelude.strip(), body_start, i, prelude_start + lead
                prelude_start = i + 1
                body_start = None
        elif ch == ";" and depth == 0:
            # A bare declaration or a statement at-rule (@import, @charset).
            prelude_start = i + 1
        i += 1


def _combine(parents: list[str], selector: str) -> list[str]:
    """Resolve one nested selector against its parent selectors."""
    if not parents:
        return _split_top_level(selector)
    parent = parents[0] if len(parents) == 1 else ":is({})".format(", ".join(parents))
    results = []
    for part in _split_top_level(selector):
        if "&" in part:
            results.append(part.replace("&", parent))
        elif part[0] in ">+~":
            results.append(f"{parent} {part}")
        else:
            results.append(f"{parent} {part}")
    return results


def _walk(css: str, start: int, end: int, parents: list[str], out: list[Rule], counter: list[int]) -> None:
    for prelude, body_start, body_end, offset in _iter_blocks(css, start, end):
        if prelude.startswith("@"):
            name = prelude[1:].split(None, 1)[0].split("(")[0].lower()
            if name in CONDITIONAL_AT_RULES:
                _walk(css, body_start, body_end, parents, out, counter)
            # Other at-rules hold declarations or keyframes, not selectors.
            continue
        line = css.count("\n", 0, offset) + 1
        selectors = _combine(parents, prelude)
        counter[0] += 1
        group = counter[0]
        for selector in selectors:
            out.append(Rule(selector=" ".join(selector.split()), line=line, group=group))
        _walk(css, body_start, body_end, selectors, out, counter)


def flatten(css: str) -> list[Rule]:
    """Return every style rule in `css` as a flat selector plus its source line."""
    css = _strip_comments(css)
    out: list[Rule] = []
    _walk(css, 0, len(css), [], out, [0])
    return out


def for_matching(selector: str) -> str:
    """Strip the parts of a selector that rendered HTML can never satisfy."""
    selector = _PSEUDO_ELEMENT_RE.sub("", selector)
    selector = _STATE_RE.sub("", selector)
    # `:not(:checked)` becomes `:not()` after the above; drop the empty husk.
    while _EMPTY_FUNCTIONAL_RE.search(selector):
        selector = _EMPTY_FUNCTIONAL_RE.sub("", selector)
    return " ".join(selector.split()).strip()
