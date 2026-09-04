import re

from django import template
from django.conf import settings
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import get_template, render_to_string
from packaging.version import Version

# We follow the Semantic versioning convention
# minor - Refers to the minor release track (5.0.1)
# patch - Refers to the patch release track (5.1.x)
VALID_VERSION_CHECK_TYPES = ("minor", "patch")

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
        context = {
            "cms_version": cms_version,
            "cms_version_check_type": check_type,
        }
        return render_to_string("admin/inc/cms_upgrade_notification.html", context)
    return ""


@register.simple_tag(takes_context=True)
def admin_theme_class(context):
    try:
        import cms

        request = context.get("request")
        if Version(cms.__version__) < Version("5.1.0dev") or _legacy_style_active(request):
            return "djangocms-simple-admin-style cms-4"
    except ImportError:  # pragma: no cover
        pass
    return "djangocms-simple-admin-style"


_legacy_style_cache = None


def _legacy_style_active(request=None):
    """Check if a base template declares django CMS theme 3 or 4.

    Inspect the template source rather than rendering it. Rendering the project's
    frontend template from an admin request can execute arbitrary template tags
    that expect page, toolbar, or middleware state unavailable in the admin.

    The answer is detected once per process and cached.
    """
    global _legacy_style_cache

    if _legacy_style_cache is not None:
        return _legacy_style_cache

    if hasattr(settings, "CMS_LEGACY_STYLE"):
        _legacy_style_cache = bool(settings.CMS_LEGACY_STYLE)
        return _legacy_style_cache

    try:
        base_template = get_template("base.html")
        source = base_template.template.source
        _legacy_style_cache = bool(re.search(r'<html[^>]*\bdata-cms-theme=["\'][34]["\']', source))
    except Exception:
        # Template lookup/source inspection is best effort; fall back on any failure.
        _legacy_style_cache = False
    return _legacy_style_cache
