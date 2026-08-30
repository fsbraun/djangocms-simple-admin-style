"""Fails when a stylesheet rule no longer matches any admin markup.

The recurring failure mode for this package is silent: Django renames or
restructures admin markup, our rules keep parsing fine, and they simply stop
applying. Django 6.0 renamed the paginator's ``.this-page`` to
``[aria-current="page"]``; 6.1 turned ``div.breadcrumbs`` into ``ol.breadcrumbs``
and moved the object tools into a ``.titles-and-tools`` wrapper. Nothing failed
-- the admin just quietly looked wrong.

This test renders real admin pages and asserts every rule in the stylesheet
still matches something. Run across the Django matrix, it names the exact rules
a new Django release orphaned.

Granularity is per *rule*, not per selector: a rule listing several selectors is
live as soon as one of them matches, because these stylesheets deliberately
carry selectors for several Django versions side by side.
"""

from pathlib import Path

import django
import soupsieve
from bs4 import BeautifulSoup
from django.test import TestCase

from djangocms_simple_admin_style.templatetags.admin_style_tags import admin_style_css
from tests.cssflat import flatten, for_matching
from tests.pages import create_fixtures, login_superuser, render_all

REPO_ROOT = Path(__file__).resolve().parent.parent
PRIVATE = REPO_ROOT / "private"
ALL_STYLESHEETS = sorted(PRIVATE.glob("*.css"))


def active_stylesheet():
    """The source file for the stylesheet this Django version actually serves.

    This mirrors production rather than hardcoding a path: ``admin_style_css()``
    serves the legacy sheet below Django 6.1 and the lean 6.1+ sheet above it, so
    the coverage test always checks the file really in use. Hardcoding one sheet
    would test the 6.1 stylesheet against Django 4.2 markup, where its rules are
    *correctly* dead.
    """
    return PRIVATE / Path(admin_style_css()).name.replace(".min.css", ".css")


STYLESHEET = active_stylesheet()

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
    ".collapse-toggle": "pre-5.1 collapse JS; modern Django uses <details>",
    ".collapsed": "collapse state class added by JS",
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

# Rules that look genuinely obsolete on the Django versions under test. They are
# pre-existing, so the suite pins them here instead of failing on day one; each
# entry is a to-do, not an excuse. Keyed by the rule's full selector list so a
# rule that changes shape shows up again. Entries are NOT asserted to still be
# dead, because that varies by Django version (the checkbox rules below do match
# on Django 4.2) -- but every entry must still exist in the stylesheet, which is
# checked below, so deleted rules cannot linger here.
# Stale in *both* stylesheets.
_SHARED_STALE = {
    ".mini": "no .mini element on any sampled page",
    "#changelist-filter :is(.module .fieldset-heading, .module fieldset details > summary)::before": (
        "filter sidebar has no .module ancestor in modern Django"
    ),
    "form .description p": "fieldset descriptions render as a bare <div class='description'>",
}

KNOWN_STALE = {
    "djangocms-simple-admin-legacy.css": {
        **_SHARED_STALE,
        ".auth-user.change-form div.form-row:not([hidden])": (
            "the user change form's body class is 'app-auth model-user', never 'auth-user'"
        ),
        ".colMS .aligned .vLargeTextField, .colMS .aligned .vXMLLargeTextField": (
            "colMS is the dashboard layout; change forms are colM, so this never applies"
        ),
        "form fieldset .fieldBox + .fieldBox": (
            "adjacent .fieldBox siblings only exist from Django 6.1, which is served "
            "the other stylesheet -- so this rule can never apply and should be deleted"
        ),
    },
    "djangocms-simple-admin.css": dict(_SHARED_STALE),
}

# Rules that style markup a *newer* Django introduced. They are correctly dead on
# older versions, so the check only applies from the given version up. The
# boundaries below were established by running this suite against each release,
# not guessed.
VERSION_GATED = {
    "djangocms-simple-admin-legacy.css": {
        ".module .fieldset-heading, .module fieldset details > summary": (
            (5, 1),
            "Django 5.1 rebuilt collapsible fieldsets on <details>/<summary>",
        ),
        "form .collapse summary .fieldset-heading, form .collapse summary .inline-heading": (
            (5, 1),
            "same <details> rework",
        ),
    },
    "djangocms-simple-admin.css": {},
}


def known_stale():
    return KNOWN_STALE[STYLESHEET.name]


def version_gated():
    return VERSION_GATED[STYLESHEET.name]


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
            if selectors in known_stale() or any(_excused(r.selector) for r in members):
                continue
            gate = version_gated().get(selectors)
            if gate and django.VERSION[:2] < gate[0]:
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
            sorted(set(known_stale()) - present),
            [],
            "These KNOWN_STALE entries no longer exist in the stylesheet; delete them.",
        )

    def test_version_gated_rules_still_exist(self):
        """A gated rule that was deleted must leave the list."""
        present = {", ".join(r.selector for r in members) for members in self._rule_groups().values()}
        self.assertEqual(
            sorted(set(version_gated()) - present),
            [],
            "These VERSION_GATED entries no longer exist in the stylesheet; delete them.",
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
