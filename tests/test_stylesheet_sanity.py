"""Cheap structural checks on the stylesheet that need no rendered HTML."""

import re
from pathlib import Path

from django.test import SimpleTestCase

from tests.cssflat import flatten

REPO_ROOT = Path(__file__).resolve().parent.parent
STYLESHEET = REPO_ROOT / "private" / "djangocms-simple-admin.css"

# Every element name the admin could plausibly render. A type selector outside
# this set is almost always a class selector that lost its leading dot -- the
# selector stays valid CSS and silently matches nothing, so nothing else catches
# it. (The per-rule coverage test cannot: `.changelink, inline-changelink` is
# "live" because the first member matches.)
HTML_ELEMENTS = {
    "a",
    "abbr",
    "address",
    "area",
    "article",
    "aside",
    "audio",
    "b",
    "base",
    "bdi",
    "bdo",
    "blockquote",
    "body",
    "br",
    "button",
    "canvas",
    "caption",
    "cite",
    "code",
    "col",
    "colgroup",
    "data",
    "datalist",
    "dd",
    "del",
    "details",
    "dfn",
    "dialog",
    "div",
    "dl",
    "dt",
    "em",
    "embed",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "head",
    "header",
    "hgroup",
    "hr",
    "html",
    "i",
    "iframe",
    "img",
    "input",
    "ins",
    "kbd",
    "label",
    "legend",
    "li",
    "link",
    "main",
    "map",
    "mark",
    "menu",
    "meta",
    "meter",
    "nav",
    "noscript",
    "object",
    "ol",
    "optgroup",
    "option",
    "output",
    "p",
    "picture",
    "pre",
    "progress",
    "q",
    "rp",
    "rt",
    "ruby",
    "s",
    "samp",
    "script",
    "search",
    "section",
    "select",
    "slot",
    "small",
    "source",
    "span",
    "strong",
    "style",
    "sub",
    "summary",
    "sup",
    "table",
    "tbody",
    "td",
    "template",
    "textarea",
    "tfoot",
    "th",
    "thead",
    "time",
    "title",
    "tr",
    "track",
    "u",
    "ul",
    "var",
    "video",
    "wbr",
    # Inline SVG, used by the admin's colour theme toggle.
    "svg",
    "circle",
    "clippath",
    "defs",
    "ellipse",
    "g",
    "line",
    "mask",
    "path",
    "polygon",
    "polyline",
    "rect",
    "text",
    "tspan",
    "use",
}

# A bare type selector: an identifier not preceded by . # : [ or a name character.
TYPE_SELECTOR_RE = re.compile(r"(?<![.#:\[\w-])([a-zA-Z][\w-]*)(?![\w-]*\s*\()")


class StylesheetSanityTests(SimpleTestCase):
    def test_no_unknown_element_selectors(self):
        unknown = []
        for rule in flatten(STYLESHEET.read_text()):
            # Ignore what is inside functional pseudo-classes and attribute
            # values; only the bare type selectors matter here.
            bare = re.sub(r"\[[^\]]*\]", "", rule.selector)
            bare = re.sub(r":[a-zA-Z-]+\([^)]*\)", "", bare)
            for name in TYPE_SELECTOR_RE.findall(bare):
                if name.lower() not in HTML_ELEMENTS:
                    unknown.append(f"{STYLESHEET.name}:{rule.line}  {rule.selector}  -> {name!r}")
        self.assertEqual(
            unknown,
            [],
            "These selectors name an element that does not exist -- almost "
            "always a class selector missing its leading dot:\n  " + "\n  ".join(unknown),
        )

    def test_stylesheet_parses_to_rules(self):
        """A parse failure would make every other check vacuously pass."""
        rules = flatten(STYLESHEET.read_text())
        self.assertGreater(len(rules), 100)
        self.assertTrue(all(r.selector.strip() for r in rules))
