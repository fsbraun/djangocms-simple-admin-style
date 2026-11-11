"""Check that stylesheet rules match real Django 6.1 admin pages."""

from pathlib import Path

import soupsieve
from bs4 import BeautifulSoup
from django.test import TestCase

from tests.cssflat import flatten, for_matching
from tests.pages import create_fixtures, login_superuser, render_all

REPO_ROOT = Path(__file__).resolve().parent.parent
PRIVATE = REPO_ROOT / "private"
ALL_STYLESHEETS = sorted(PRIVATE.glob("*.css"))


STYLESHEET = PRIVATE / "djangocms-simple-admin.css"

# Markup that a server-rendered, plain-Django admin can never contain: either a
# script builds it in the browser, or another package ships it. Verified against
# the rendered HTML rather than assumed -- e.g. the admin emits
# `<select class="selectfilter">` and SelectFilter2.js builds the `.selector`
# DOM around it, so no `.selector` rule can ever match here.
# A visual-regression suite driving a real browser would cover these; this test
# cannot, and says so rather than pretending.
NOT_SERVER_RENDERED = {
    # Built by the admin's own JavaScript.
    ".selector": "SelectFilter2.js builds it from <select class='selectfilter'>",
    ".main.shifted": "nav sidebar toggle state, set by JS",
    ".datetimeshortcuts": (
        "DateTimeShortcuts.js builds the today/now links and the calendar and "
        "clock icons; the admin renders only the bare date/time inputs"
    ),
    # Injected by django CMS (toolbar, sideframe, modal, page tree).
    ".cms-admin": "django CMS admin wrapper",
    ".cms-pagetree-dropdown-menu": "django CMS page tree",
    ".cms-update-notification": "rendered by our own update-notification.js",
    ".cms-btn": "django CMS toolbar buttons",
    ".cms-action-btn": "django CMS toolbar buttons",
    ".cms-empty-action": "django CMS page tree",
    ".cms-4": "theme class applied for django CMS < 5.1",
    ".jstree-anchor": "django CMS page tree (jstree)",
    ".insertlinkButton": "django CMS text plugin",
    "#page_form_lang_tabs": "django CMS page form",
    ".parler-language-tabs": "django-parler",
    ".select2-container": "django-select2 / django-autocomplete-light",
    ".accent": "object-tools variant added by django CMS",
    # Set by a host project's <html>, or by the admin's theme toggle JS.
    "data-cms-theme": "set on <html> by the host project",
    "data-theme": "set by the admin colour theme toggle",
}

# Existing obsolete rules, kept visible until their rendering is corrected.
KNOWN_STALE = {
    "#changelist-filter :is(.module .fieldset-heading, .module fieldset details > summary)::before": (
        "the filter sidebar is <search id='changelist-filter'> holding <h2> and "
        "<details><summary> -- there is no .module ancestor and no "
        ".fieldset-heading, on any supported Django. The rule most likely meant "
        "`#changelist-filter details > summary::before`; fixing it changes "
        "rendering, so it is pinned here rather than edited silently"
    ),
}

def _excused(selector):
    return any(token in selector for token in NOT_SERVER_RENDERED)


class SelectorCoverageTests(TestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.widget = create_fixtures()

    def setUp(self):
        user = login_superuser(self.client)
        self.pages = render_all(self.client, self.widget, user)
        self.soups = {name: BeautifulSoup(html, "html.parser") for name, html in self.pages.items()}

    def _rule_groups(self):
        groups = {}
        for rule in flatten(STYLESHEET.read_text()):
            groups.setdefault(rule.group, []).append(rule)
        return groups

    def test_stylesheet_has_no_dead_rules(self):
        dead = []
        for _, members in sorted(self._rule_groups().items()):
            selectors = ", ".join(r.selector for r in members)
            if selectors in KNOWN_STALE or any(_excused(r.selector) for r in members):
                continue
            live = False
            for rule in members:
                selector = for_matching(rule.selector)
                if not selector:
                    live = True
                    break
                if any(soupsieve.select_one(selector, soup) is not None for soup in self.soups.values()):
                    live = True
                    break
            if not live:
                dead.append(f"{STYLESHEET.name}:{members[0].line}  {selectors}")

        self.assertEqual(
            dead,
            [],
            "These rules no longer match any admin markup. Either the admin "
            "changed and the rule needs updating, or the rule is obsolete and "
            "should be deleted:\n  " + "\n  ".join(dead),
        )

    def test_known_stale_rules_still_exist(self):
        """Keeps KNOWN_STALE honest: a rule that was deleted must leave the list."""
        present = {", ".join(r.selector for r in members) for members in self._rule_groups().values()}
        self.assertEqual(
            sorted(set(KNOWN_STALE) - present),
            [],
            "These KNOWN_STALE entries no longer exist in the stylesheet; delete them.",
        )

    def test_exclusion_tokens_are_used(self):
        """Keeps NOT_SERVER_RENDERED honest: an unused token is dead weight."""
        css = "\n".join(sheet.read_text() for sheet in ALL_STYLESHEETS)
        self.assertEqual(
            sorted(token for token in NOT_SERVER_RENDERED if token not in css),
            [],
            "These NOT_SERVER_RENDERED tokens appear in no stylesheet; delete them.",
        )

    def test_sample_pages_render(self):
        """Guards the fixture itself: an empty page set would make coverage vacuous."""
        self.assertGreaterEqual(len(self.pages), 17)
        for name, html in self.pages.items():
            self.assertIn("djangocms-simple-admin", html, f"{name} is missing our stylesheet")
