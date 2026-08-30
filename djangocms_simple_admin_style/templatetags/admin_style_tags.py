import logging
import re
from functools import cache

from django import template
from django.conf import settings
from django.template.loader import TemplateDoesNotExist, render_to_string
from packaging.version import Version

# We follow the Semantic versioning convention
# minor - Refers to the minor release track (5.0.1)
# patch - Refers to the patch release track (5.1.x)
VALID_VERSION_CHECK_TYPES = ("minor", "patch")

logger = logging.getLogger(__name__)

register = template.Library()


@register.simple_tag
def admin_style_css():
    """Return the admin stylesheet matching the running Django version.

    Django 6.1 redesigned admin forms to stack inputs beneath their labels
    (ticket #34643). From 6.1 on we ship a lean stylesheet that builds on that
    native layout; for 6.0 and earlier we keep the original stylesheet that
    forces the labels-above layout itself.
    """
    import django

    base = "djangocms_simple_admin_style/css/"
    if django.VERSION >= (6, 1):
        return base + "djangocms-simple-admin.min.css"
    return base + "djangocms-simple-admin-legacy.min.css"


@register.simple_tag(takes_context=True)
def render_update_notification(context):
    try:
        from cms import __version__ as cms_version
    except ImportError:  # pragma: no cover
        check_type = None
        notifications_enabled = False
    else:
        check_type = getattr(settings, "CMS_UPDATE_CHECK_TYPE", "patch")
        notifications_enabled = getattr(settings, "CMS_ENABLE_UPDATE_CHECK", True)

    request = context.get("request")

    try:
        index_page = request.resolver_match.url_name == "index"
    except AttributeError:
        notifications_enabled = False
    else:
        notifications_enabled = index_page and notifications_enabled

    if notifications_enabled and check_type in VALID_VERSION_CHECK_TYPES:
        print(cms_version)
        context = {
            "cms_version": cms_version,
            "cms_version_check_type": check_type,
        }
        return render_to_string("admin/inc/cms_upgrade_notification.html", context)
    return ""


@register.simple_tag
def admin_theme_class():
    try:
        import cms

        if Version(cms.__version__) < Version("5.1.0dev") or _legacy_style_active():
            return "djangocms-simple-admin-style cms-4"
    except ImportError:  # pragma: no cover
        pass
    return "djangocms-simple-admin-style"


@cache
def _legacy_style_active():
    """Check if a potential base template contains data-cms-theme="4" for legacy style.

    This renders the *project's* base.html against a synthetic request, so it is
    inherently best-effort: that template may use any tag, and those tags may
    read request attributes that only middleware sets. We pre-set the ones django
    CMS templates rely on most, but the list can never be complete -- so a
    failure here degrades to "not the legacy style" instead of propagating out of
    ``{% admin_theme_class %}`` and taking down every admin page that renders it.
    """
    if hasattr(settings, "CMS_LEGACY_STYLE"):
        return bool(settings.CMS_LEGACY_STYLE)
    try:
        from django.contrib.auth.models import AnonymousUser
        from django.test import RequestFactory
        from sekizai.context_processors import sekizai

        request = RequestFactory().get("/")
        # The request bypasses the CMS middleware, so attributes those templates
        # read are absent. Tags such as `{% page_attribute %}` read
        # request.current_page in Python, where a missing attribute is a hard
        # AttributeError rather than an empty template variable.
        request.current_page = None
        request.user = AnonymousUser()
        context = sekizai(request)
        context["request"] = request
        base_template = render_to_string("base.html", context)
        return bool(re.search(r'<html[^>]*\bdata-cms-theme=["\']4["\']', base_template))
    except (TemplateDoesNotExist, ImportError):
        # No base.html, or django CMS/sekizai is not installed. Expected: quiet.
        pass
    except Exception:
        # The project's base.html needs request state we cannot fake (a toolbar,
        # a session, a resolver match...). Never fatal: the admin must still
        # render. Projects can set CMS_LEGACY_STYLE to skip detection entirely.
        logger.warning(
            "Could not render base.html to auto-detect the admin style; falling "
            "back to the current style. Set CMS_LEGACY_STYLE to select it "
            "explicitly and skip this check.",
            exc_info=True,
        )
    return False
