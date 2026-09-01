"""Unit tests for the template tags.

``cms`` is not installed in the test environment (see tests/settings.py), so the
no-cms fallbacks are exercised for real and the with-cms paths get a stub module
injected into ``sys.modules`` -- which is what the tags' own local imports read.
"""

import copy
import re
import sys
import tempfile
import types
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from djangocms_simple_admin_style.templatetags import admin_style_tags
from djangocms_simple_admin_style.templatetags.admin_style_tags import (
    _legacy_style_active,
    admin_theme_class,
    render_update_notification,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

LEGACY_BASE = '<html data-cms-theme="4"><link rel="canonical" href="{{ request.build_absolute_uri }}"/></html>'
CURRENT_BASE = '<html><link rel="canonical" href="{{ request.build_absolute_uri }}"/></html>'


def clear_style_cache():
    """Reset the once-per-process detection result.

    Easy to miss, and the failures it causes look unrelated: without this the
    first test to detect a style decides the answer for every test after it.
    """
    admin_style_tags._legacy_style_cache = None


@contextmanager
def fake_cms(version):
    """Make `import cms` inside the tags resolve to a stub of the given version."""
    module = types.ModuleType("cms")
    module.__version__ = version
    original = sys.modules.get("cms")
    sys.modules["cms"] = module
    try:
        yield module
    finally:
        if original is None:
            del sys.modules["cms"]
        else:
            sys.modules["cms"] = original


@contextmanager
def fake_sekizai():
    """Provide the sekizai context processor that the style detection imports.

    sekizai comes with django CMS, which the test environment deliberately does
    not install; without this stub the detection bails out at the import and
    never reaches the base.html render the tests below are about.
    """
    package = types.ModuleType("sekizai")
    processors = types.ModuleType("sekizai.context_processors")
    processors.sekizai = lambda request: {}
    package.context_processors = processors
    names = ("sekizai", "sekizai.context_processors")
    originals = {name: sys.modules.get(name) for name in names}
    sys.modules.update(zip(names, (package, processors)))
    try:
        yield
    finally:
        for name, module in originals.items():
            if module is None:
                del sys.modules[name]
            else:
                sys.modules[name] = module


@contextmanager
def base_template(html):
    """Make ``base.html`` with the given contents resolvable by the loaders."""
    with tempfile.TemporaryDirectory() as directory:
        (Path(directory) / "base.html").write_text(html)
        templates = copy.deepcopy(settings.TEMPLATES)
        templates[0]["DIRS"] = [directory]
        with override_settings(TEMPLATES=templates):
            yield


class AdminThemeClassTests(SimpleTestCase):
    def setUp(self):
        clear_style_cache()
        self.addCleanup(clear_style_cache)

    def test_without_cms_installed(self):
        self.assertEqual(admin_theme_class(Context({})), "djangocms-simple-admin-style")

    def test_cms_before_5_1_gets_the_legacy_theme(self):
        with fake_cms("5.0.1"):
            self.assertEqual(admin_theme_class(Context({})), "djangocms-simple-admin-style cms-4")

    def test_cms_5_1_gets_the_current_theme(self):
        with fake_cms("5.1.0"):
            self.assertEqual(admin_theme_class(Context({})), "djangocms-simple-admin-style")

    def test_prerelease_of_5_1_counts_as_5_1(self):
        with fake_cms("5.1.0rc1"):
            self.assertEqual(admin_theme_class(Context({})), "djangocms-simple-admin-style")

    @override_settings(CMS_LEGACY_STYLE=True)
    def test_legacy_style_setting_forces_the_legacy_theme(self):
        with fake_cms("5.1.0"):
            self.assertEqual(admin_theme_class(Context({})), "djangocms-simple-admin-style cms-4")

    @override_settings(CMS_LEGACY_STYLE=False)
    def test_legacy_style_setting_can_be_switched_off(self):
        with fake_cms("5.1.0"):
            self.assertEqual(admin_theme_class(Context({})), "djangocms-simple-admin-style")


class LegacyStyleActiveTests(SimpleTestCase):
    def setUp(self):
        clear_style_cache()
        self.addCleanup(clear_style_cache)
        self.request = RequestFactory().get("/admin/")

    @override_settings(CMS_LEGACY_STYLE=True)
    def test_setting_takes_precedence(self):
        self.assertIs(_legacy_style_active(), True)

    def test_without_a_request_nothing_is_detected(self):
        """No request, nothing to render against: not legacy, and not cached."""
        with fake_sekizai(), base_template(LEGACY_BASE):
            self.assertIs(_legacy_style_active(), False)
            self.assertIs(_legacy_style_active(self.request), True)

    @override_settings(CMS_LEGACY_STYLE=True)
    def test_the_setting_wins_over_the_base_template(self):
        """The setting is documented to skip auto-detection, not to seed it."""
        with fake_sekizai(), base_template(CURRENT_BASE):
            self.assertIs(_legacy_style_active(self.request), True)

    @override_settings(CMS_LEGACY_STYLE=False)
    def test_the_setting_can_override_a_legacy_base_template(self):
        with fake_sekizai(), base_template(LEGACY_BASE):
            self.assertIs(_legacy_style_active(self.request), False)

    @override_settings(CMS_LEGACY_STYLE=True)
    def test_the_setting_holds_when_there_is_no_base_template(self):
        """Regression: the setting was cached but not returned, so the render
        below it ran anyway and the answer flipped from False to True between
        the first admin page load of a worker and the second."""
        self.assertIs(_legacy_style_active(self.request), True)
        self.assertIs(_legacy_style_active(self.request), True)

    def test_the_render_gets_a_prepared_copy_of_the_request(self):
        """The live request is mid-render in the admin, so it must come out
        untouched -- while the copy carries what a CMS base.html reads:
        `{% page_attribute %}` reads request.current_page in Python, where a
        missing attribute is a hard AttributeError."""
        self.request.toolbar = object()
        captured = {}

        def capture(template_name, context):
            captured["request"] = context["request"]
            return ""

        with fake_sekizai(), patch.object(admin_style_tags, "render_to_string", capture):
            _legacy_style_active(self.request)

        self.assertIsNot(captured["request"], self.request)
        self.assertIsNone(captured["request"].current_page)
        self.assertIsNone(captured["request"].toolbar)
        self.assertFalse(hasattr(self.request, "current_page"))
        self.assertIsNotNone(self.request.toolbar)

    def test_missing_base_template_is_not_an_error(self):
        """No base.html and no sekizai: the tag must fall back, not raise."""
        self.assertIs(_legacy_style_active(self.request), False)

    @override_settings(CMS_LEGACY_STYLE=True)
    def test_result_is_cached(self):
        self.assertIs(_legacy_style_active(), True)
        with override_settings(CMS_LEGACY_STYLE=False):
            # Still True: the cache is only cleared explicitly, which is exactly
            # why the tests above clear it.
            self.assertIs(_legacy_style_active(), True)


class LegacyStyleDetectionRenderTests(SimpleTestCase):
    """End-to-end detection against a base.html that needs a valid host.

    The django CMS frontend base templates render ``request.build_absolute_uri``
    for the canonical link, which calls ``get_host()``. Rendering against the
    admin request means that host is the real one and passes ALLOWED_HOSTS --
    a synthetic request used to raise DisallowedHost with DEBUG off and report
    "not legacy" for every project on the legacy style.
    """

    def setUp(self):
        clear_style_cache()
        self.addCleanup(clear_style_cache)
        self.request = RequestFactory(SERVER_NAME="beta-vm.de").get("/admin/")

    @override_settings(ALLOWED_HOSTS=[".beta-vm.de"])
    def test_legacy_marker_is_found(self):
        with fake_sekizai(), base_template(LEGACY_BASE):
            self.assertIs(_legacy_style_active(self.request), True)

    @override_settings(ALLOWED_HOSTS=[".beta-vm.de"])
    def test_without_the_marker_the_current_style_wins(self):
        with fake_sekizai(), base_template(CURRENT_BASE):
            self.assertIs(_legacy_style_active(self.request), False)

    @override_settings(ALLOWED_HOSTS=[".beta-vm.de"])
    def test_a_failed_render_is_not_retried(self):
        """Regression: failures went uncached, so an unrenderable base.html was
        re-rendered -- and a traceback re-logged -- on every admin request."""
        with (
            fake_sekizai(),
            base_template("{% load i18n %}{% no_such_tag %}"),
            self.assertLogs("djangocms_simple_admin_style", "WARNING") as logs,
        ):
            self.assertIs(_legacy_style_active(self.request), False)
            self.assertIs(_legacy_style_active(self.request), False)
        self.assertEqual(len(logs.records), 1)

    @override_settings(ALLOWED_HOSTS=[".beta-vm.de"])
    def test_a_base_template_we_cannot_render_is_not_fatal(self):
        """A tag needing state we cannot fake must degrade, not 500 the admin."""
        with (
            fake_sekizai(),
            base_template("{% load i18n %}{% no_such_tag %}"),
            self.assertLogs("djangocms_simple_admin_style", "WARNING"),
        ):
            self.assertIs(_legacy_style_active(self.request), False)


class RenderUpdateNotificationTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _context(self, url_name="index"):
        request = self.factory.get("/admin/")
        request.user = AnonymousUser()
        request.resolver_match = types.SimpleNamespace(url_name=url_name)
        return Context({"request": request})

    def test_renders_nothing_without_cms(self):
        self.assertEqual(render_update_notification(self._context()), "")

    def test_renders_on_the_index_page(self):
        with fake_cms("5.1.0"):
            output = render_update_notification(self._context())
        self.assertIn("cms-update-template", output)
        self.assertIn("5.1.0", output)

    def test_renders_nothing_off_the_index_page(self):
        with fake_cms("5.1.0"):
            self.assertEqual(render_update_notification(self._context("changelist")), "")

    def test_renders_nothing_without_a_resolver_match(self):
        request = self.factory.get("/admin/")
        with fake_cms("5.1.0"):
            self.assertEqual(render_update_notification(Context({"request": request})), "")

    def test_renders_nothing_without_a_request(self):
        with fake_cms("5.1.0"):
            self.assertEqual(render_update_notification(Context({})), "")

    @override_settings(CMS_ENABLE_UPDATE_CHECK=False)
    def test_can_be_disabled(self):
        with fake_cms("5.1.0"):
            self.assertEqual(render_update_notification(self._context()), "")

    @override_settings(CMS_UPDATE_CHECK_TYPE="major")
    def test_unknown_check_type_renders_nothing(self):
        with fake_cms("5.1.0"):
            self.assertEqual(render_update_notification(self._context()), "")

    @override_settings(CMS_UPDATE_CHECK_TYPE="minor")
    def test_minor_check_type_is_accepted(self):
        with fake_cms("5.1.0"):
            self.assertIn("cms-update-template", render_update_notification(self._context()))

    def test_writes_nothing_to_stdout(self):
        """The tag runs on every superuser admin index load; it must stay quiet."""
        with fake_cms("5.1.0"), patch("sys.stdout", new=StringIO()) as stdout:
            render_update_notification(self._context())
        self.assertEqual(stdout.getvalue(), "")


class BaseSiteTemplateTests(TestCase):
    def test_stylesheet_link_points_at_a_file_that_exists(self):
        """Catches a renamed or unbuilt stylesheet, which no other test would."""
        self.client.force_login(User.objects.create_superuser("admin", "admin@example.com", "password"))
        html = self.client.get(reverse("admin:index")).content.decode()
        hrefs = re.findall(r'href="([^"]*djangocms-simple-admin[^"]*\.css)"', html)
        self.assertTrue(hrefs, "base_site.html rendered no link to our stylesheet")
        for href in hrefs:
            relative = href.split("/static/", 1)[-1]
            path = REPO_ROOT / "djangocms_simple_admin_style" / "static" / relative
            self.assertTrue(path.is_file(), f"{href} does not exist at {path}")

    def test_body_carries_the_theme_class(self):
        template = Template("{% load admin_style_tags %}{% admin_theme_class %}")
        self.assertIn("djangocms-simple-admin-style", template.render(Context({})))
