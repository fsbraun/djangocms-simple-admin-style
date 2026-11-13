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
def project_template(name, html):
    """Make a project-level template with the given contents resolvable.

    It goes in ``DIRS``, which the loaders search before any app's templates --
    the same precedence a real project's own templates directory has.
    """
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html)
        templates = copy.deepcopy(settings.TEMPLATES)
        templates[0]["DIRS"] = [directory]
        with override_settings(TEMPLATES=templates):
            yield


def base_template(html):
    """Make ``base.html`` with the given contents resolvable by the loaders."""
    return project_template("base.html", html)


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

    def test_literal_legacy_markers_select_the_legacy_theme_without_a_request(self):
        for theme in ("3", "4"):
            with self.subTest(theme=theme), fake_cms("5.1.0"), base_template(f'<html data-cms-theme="{theme}">'):
                clear_style_cache()
                self.assertEqual(admin_theme_class(Context({})), "djangocms-simple-admin-style cms-4")


class LegacyStyleActiveTests(SimpleTestCase):
    def setUp(self):
        clear_style_cache()
        self.addCleanup(clear_style_cache)
        self.request = RequestFactory().get("/admin/")

    @override_settings(CMS_LEGACY_STYLE=True)
    def test_setting_takes_precedence(self):
        self.assertIs(_legacy_style_active(), True)

    def test_detection_does_not_need_a_request(self):
        with base_template(LEGACY_BASE):
            self.assertIs(_legacy_style_active(), True)

    @override_settings(CMS_LEGACY_STYLE=True)
    def test_the_setting_wins_over_the_base_template(self):
        """The setting is documented to skip auto-detection, not to seed it."""
        with base_template(CURRENT_BASE):
            self.assertIs(_legacy_style_active(self.request), True)

    @override_settings(CMS_LEGACY_STYLE=False)
    def test_the_setting_can_override_a_legacy_base_template(self):
        with base_template(LEGACY_BASE):
            self.assertIs(_legacy_style_active(self.request), False)

    @override_settings(CMS_LEGACY_STYLE=True)
    def test_the_setting_holds_when_there_is_no_base_template(self):
        """Regression: the setting was cached but not returned, so the render
        below it ran anyway and the answer flipped from False to True between
        the first admin page load of a worker and the second."""
        self.assertIs(_legacy_style_active(self.request), True)
        self.assertIs(_legacy_style_active(self.request), True)

    def test_base_template_is_not_rendered(self):
        """Regression for #41: detection must not execute frontend tags."""
        html = '<html data-cms-theme="4">{% url "missing-url-name" %}</html>'
        with base_template(html):
            self.assertIs(_legacy_style_active(self.request), True)

    def test_missing_base_template_is_not_an_error(self):
        """No base.html: the tag must fall back, not raise."""
        self.assertIs(_legacy_style_active(self.request), False)

    def test_invalid_base_template_is_not_an_error(self):
        with base_template("{% no_such_tag %}"):
            self.assertIs(_legacy_style_active(self.request), False)

    def test_failed_source_lookup_is_cached(self):
        with patch.object(admin_style_tags, "get_template", side_effect=RuntimeError("loader unavailable")) as lookup:
            self.assertIs(_legacy_style_active(), False)
            self.assertIs(_legacy_style_active(), False)
        lookup.assert_called_once_with("base.html")

    @override_settings(CMS_LEGACY_STYLE=True)
    def test_result_is_cached(self):
        self.assertIs(_legacy_style_active(), True)
        with override_settings(CMS_LEGACY_STYLE=False):
            # Still True: the cache is only cleared explicitly, which is exactly
            # why the tests above clear it.
            self.assertIs(_legacy_style_active(), True)


class LegacyStyleDetectionTests(SimpleTestCase):
    def setUp(self):
        clear_style_cache()
        self.addCleanup(clear_style_cache)
        self.request = RequestFactory(SERVER_NAME="beta-vm.de").get("/admin/")

    def test_legacy_marker_is_found(self):
        with base_template(LEGACY_BASE):
            self.assertIs(_legacy_style_active(self.request), True)

    def test_theme_3_marker_is_also_legacy(self):
        with base_template("<html data-cms-theme='3'></html>"):
            self.assertIs(_legacy_style_active(self.request), True)

    def test_without_the_marker_the_current_style_wins(self):
        with base_template(CURRENT_BASE):
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


class StylesheetTests(SimpleTestCase):
    def test_release_stylesheet(self):
        self.assertEqual(
            admin_style_tags.admin_style_css(),
            "djangocms_simple_admin_style/css/djangocms-simple-admin.css",
        )
        css_dir = REPO_ROOT / "djangocms_simple_admin_style" / "static" / "djangocms_simple_admin_style" / "css"
        self.assertEqual(sorted(p.name for p in css_dir.glob("*.css")), ["djangocms-simple-admin.css"])


class BaseTemplateTests(TestCase):
    def test_stylesheet_link_points_at_a_file_that_exists(self):
        """Catches a renamed or unbuilt stylesheet, which no other test would."""
        self.client.force_login(User.objects.create_superuser("admin", "admin@example.com", "password"))
        html = self.client.get(reverse("admin:index")).content.decode()
        hrefs = re.findall(r'href="([^"]*djangocms-simple-admin[^"]*\.css)"', html)
        self.assertTrue(hrefs, "base.html rendered no link to our stylesheet")
        for href in hrefs:
            relative = href.split("/static/", 1)[-1]
            path = REPO_ROOT / "djangocms_simple_admin_style" / "static" / relative
            self.assertTrue(path.is_file(), f"{href} does not exist at {path}")

    def test_stylesheet_loads_after_the_admin_responsive_styles(self):
        """Ours must be the last admin stylesheet, so it wins at equal specificity."""
        self.client.force_login(User.objects.create_superuser("admin", "admin@example.com", "password"))
        html = self.client.get(reverse("admin:index")).content.decode()
        hrefs = re.findall(r'<link rel="stylesheet" href="([^"]*)"', html)
        ours = [i for i, href in enumerate(hrefs) if "djangocms-simple-admin" in href]
        self.assertEqual(len(ours), 1, hrefs)
        self.assertEqual(ours[0], len(hrefs) - 1, hrefs)
        self.assertIn("admin/css/responsive.css", hrefs[ours[0] - 1])

    def test_project_styles_load_after_the_theme(self):
        """admin/inc/extrastyle.html is the project hook; it must follow our link."""
        self.client.force_login(User.objects.create_superuser("admin", "admin@example.com", "password"))
        marker = '<link rel="stylesheet" href="/static/project.css">'
        with project_template("admin/inc/extrastyle.html", marker):
            html = self.client.get(reverse("admin:index")).content.decode()
        self.assertIn(marker, html)
        self.assertGreater(html.index(marker), html.index("djangocms-simple-admin.css"))

    def test_base_site_is_left_to_the_project(self):
        """Overriding admin/base_site.html is how projects brand the admin."""
        shipped = REPO_ROOT / "djangocms_simple_admin_style" / "templates" / "admin"
        self.assertTrue((shipped / "base.html").is_file())
        self.assertFalse((shipped / "base_site.html").exists())

    def test_body_carries_the_theme_class(self):
        template = Template("{% load admin_style_tags %}{% admin_theme_class %}")
        self.assertIn("djangocms-simple-admin-style", template.render(Context({})))
