import copy
import logging
import re

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
    """Check if a potential base template contains data-cms-theme="4" for legacy style.

    This renders the *project's* base.html against the admin request we were
    called from, so it is inherently best-effort: that template may use any tag,
    and those tags may read request attributes even a real admin request does not
    carry. A failure therefore degrades to "not the legacy style" instead of
    propagating out of ``{% admin_theme_class %}`` and taking down every admin
    page that renders it.

    The answer is detected once per process and cached -- failures included, so a
    base.html we cannot render is not re-rendered (and re-logged) on every admin
    request. Without a request there is nothing to render against; that answer is
    *not* cached, leaving a later call that has one free to detect.
    """
    global _legacy_style_cache

    if _legacy_style_cache is not None:
        return _legacy_style_cache

    if hasattr(settings, "CMS_LEGACY_STYLE"):
        _legacy_style_cache = bool(settings.CMS_LEGACY_STYLE)
        return _legacy_style_cache
    if request is None:
        return False

    try:
        from sekizai.context_processors import sekizai

        # Render against a copy: we run in the middle of the admin page's own
        # render, so nothing we set here may reach the live request. The toolbar
        # goes with it -- reading an <html> attribute does not need one, and
        # `{% cms_toolbar %}` would otherwise populate and render the in-flight
        # request's own toolbar object a second time.
        request = copy.copy(request)
        request.toolbar = None
        # Tags such as `{% page_attribute %}` read request.current_page in
        # Python, where a missing attribute is a hard AttributeError rather than
        # an empty template variable. An admin request never went through the
        # CMS page view, so it has no current page -- and None is what CMS code
        # reads for "no page" anyway.
        request.current_page = getattr(request, "current_page", None)
        context = sekizai(request)
        context["request"] = request
        base_template = render_to_string("base.html", context)
        _legacy_style_cache = bool(re.search(r'<html[^>]*\bdata-cms-theme=["\']4["\']', base_template))
    except (TemplateDoesNotExist, ImportError):
        # No base.html, or django CMS/sekizai is not installed. Expected: quiet.
        _legacy_style_cache = False
    except Exception:
        logger.warning(
            "Could not render base.html to auto-detect the admin style; falling "
            "back to the current style. Set CMS_LEGACY_STYLE to select it "
            "explicitly and skip this check.",
            exc_info=True,
        )
        _legacy_style_cache = False
    return _legacy_style_cache
