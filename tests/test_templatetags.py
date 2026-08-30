"""Unit tests for the template tags.

``cms`` is not installed in the test environment (see tests/settings.py), so the
no-cms fallbacks are exercised for real and the with-cms paths get a stub module
injected into ``sys.modules`` -- which is what the tags' own local imports read.
"""

import re
import sys
import types
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser, User
from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from djangocms_simple_admin_style.templatetags.admin_style_tags import (
    _legacy_style_active,
    admin_theme_class,
    render_update_notification,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


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


class AdminThemeClassTests(SimpleTestCase):
    def setUp(self):
        # _legacy_style_active is @cache'd, so state leaks between tests unless
        # it is cleared. Easy to miss, and the failures look unrelated.
        _legacy_style_active.cache_clear()
        self.addCleanup(_legacy_style_active.cache_clear)

    def test_without_cms_installed(self):
        self.assertEqual(admin_theme_class(), "djangocms-simple-admin-style")

    def test_cms_before_5_1_gets_the_legacy_theme(self):
        with fake_cms("5.0.1"):
            self.assertEqual(admin_theme_class(), "djangocms-simple-admin-style cms-4")

    def test_cms_5_1_gets_the_current_theme(self):
        with fake_cms("5.1.0"):
            self.assertEqual(admin_theme_class(), "djangocms-simple-admin-style")

    def test_prerelease_of_5_1_counts_as_5_1(self):
        with fake_cms("5.1.0rc1"):
            self.assertEqual(admin_theme_class(), "djangocms-simple-admin-style")

    @override_settings(CMS_LEGACY_STYLE=True)
    def test_legacy_style_setting_forces_the_legacy_theme(self):
        with fake_cms("5.1.0"):
            self.assertEqual(admin_theme_class(), "djangocms-simple-admin-style cms-4")

    @override_settings(CMS_LEGACY_STYLE=False)
    def test_legacy_style_setting_can_be_switched_off(self):
        with fake_cms("5.1.0"):
            self.assertEqual(admin_theme_class(), "djangocms-simple-admin-style")


class LegacyStyleActiveTests(SimpleTestCase):
    def setUp(self):
        _legacy_style_active.cache_clear()
        self.addCleanup(_legacy_style_active.cache_clear)

    @override_settings(CMS_LEGACY_STYLE=True)
    def test_setting_takes_precedence(self):
        self.assertIs(_legacy_style_active(), True)

    def test_missing_base_template_is_not_an_error(self):
        """No base.html and no sekizai: the tag must fall back, not raise."""
        self.assertIs(_legacy_style_active(), False)

    @override_settings(CMS_LEGACY_STYLE=True)
    def test_result_is_cached(self):
        self.assertIs(_legacy_style_active(), True)
        with override_settings(CMS_LEGACY_STYLE=False):
            # Still True: the cache is only cleared explicitly, which is exactly
            # why the tests above clear it.
            self.assertIs(_legacy_style_active(), True)


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
