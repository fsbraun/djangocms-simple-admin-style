from functools import cache
from packaging.version import Version
import re

from django import template
from django.conf import settings
from django.template.loader import render_to_string, TemplateDoesNotExist

# We follow the Semantic versioning convention
# minor - Refers to the minor release track (5.0.1)
# patch - Refers to the patch release track (5.1.x)
VALID_VERSION_CHECK_TYPES = ("minor", "patch")

register = template.Library()


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
    """Check if a potential base template contains data-cms-theme="4" for legacy style."""
    try:
        from sekizai.context_processors import sekizai

        base_template = render_to_string("base.html", sekizai())
        return bool(re.search(r'<html[^>]*\bdata-cms-theme=["\']4["\']', base_template))
    except (TemplateDoesNotExist, ImportError):
        pass
    return False
