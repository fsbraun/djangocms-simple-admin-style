"""Renders a representative sample of admin pages for the selector coverage test.

The sample exists to put every kind of markup the stylesheets target into at
least one document: forms with each widget type, a paginated and filtered
changelist, the delete-confirmation interstitial, a popup, and the logged-out
login page.
"""

from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.urls import reverse

from tests.testapp.models import Category, Note, Tag, Widget


def create_fixtures():
    """Create enough objects that the changelist paginates and filters have options."""
    category = Category.objects.create(name="Gadgets")
    other = Category.objects.create(name="Gizmos")
    tags = [Tag.objects.create(name=f"tag-{i}") for i in range(4)]
    widgets = []
    for i in range(12):
        widget = Widget.objects.create(
            title=f"Widget {i}",
            slug=f"widget-{i}",
            description=f"Description for widget {i}",
            homepage="https://example.com/",
            email="widget@example.com",
            quantity=i,
            price=i * 1.5,
            is_active=bool(i % 2),
            status="p" if i % 2 else "d",
            category=category if i % 2 else other,
        )
        widget.tags.set(tags[: (i % 4) + 1])
        Note.objects.create(widget=widget, body=f"Note for widget {i}")
        widgets.append(widget)
    return widgets[0]


def view_only_client():
    """A staff client that may view widgets but not change them.

    Django renders the submit row's `.closelink` only when the form cannot be
    saved: `show_close = not (show_save and can_save)` in
    admin_modify.submit_row. A read-only change page is the realistic way to
    reach that, and nothing else in this sample does.
    """
    user = User.objects.create_user("viewer", "viewer@example.com", "password", is_staff=True)
    content_type = ContentType.objects.get_for_model(Widget)
    user.user_permissions.add(Permission.objects.get(content_type=content_type, codename="view_widget"))
    client = Client()
    client.force_login(user)
    return client


def render_all(client, widget, user):
    """Return {page_name: html} for the sampled admin pages."""
    changelist = reverse("admin:testapp_widget_changelist")
    pages = {
        "index": client.get(reverse("admin:index")),
        "app_list": client.get(reverse("admin:app_list", kwargs={"app_label": "testapp"})),
        "changelist": client.get(changelist),
        "changelist_page2": client.get(changelist, {"p": 2}),
        "changelist_search": client.get(changelist, {"q": "Widget 1"}),
        "changelist_filtered": client.get(changelist, {"is_active__exact": 1}),
        "add": client.get(reverse("admin:testapp_widget_add")),
        "change": client.get(reverse("admin:testapp_widget_change", args=[widget.pk])),
        "delete": client.get(reverse("admin:testapp_widget_delete", args=[widget.pk])),
        "history": client.get(reverse("admin:testapp_widget_history", args=[widget.pk])),
        "popup": client.get(reverse("admin:testapp_category_add"), {"_popup": 1}),
        "password_change": client.get(reverse("admin:password_change")),
        # The auth user pages are styled by name (.auth-user, .app-auth.model-user).
        "user_changelist": client.get(reverse("admin:auth_user_changelist")),
        "user_add": client.get(reverse("admin:auth_user_add")),
        "user_change": client.get(reverse("admin:auth_user_change", args=[user.pk])),
        # The delete_selected interstitial: another .delete-confirmation layout.
        "action_confirm": client.post(
            changelist,
            {"action": "delete_selected", "_selected_action": [str(widget.pk)], "index": 0},
        ),
        # An invalid submission, so form errors (.errorlist) are on the page.
        "add_invalid": client.post(
            reverse("admin:testapp_widget_add"),
            {"title": "", "homepage": "not-a-url", "quantity": "abc"},
        ),
        # A read-only change page, which is where Django renders .closelink.
        "view_only_change": view_only_client().get(reverse("admin:testapp_widget_change", args=[widget.pk])),
        # A page carrying a success message, so .messagelist markup is present.
        "with_message": client.post(reverse("admin:testapp_tag_add"), {"name": "created"}, follow=True),
    }
    html = {}
    for name, response in pages.items():
        assert response.status_code == 200, f"{name} returned {response.status_code}"
        html[name] = response.content.decode()

    # The login page needs an anonymous client.
    client.logout()
    login = client.get(reverse("admin:login"))
    assert login.status_code == 200
    html["login"] = login.content.decode()
    return html


def login_superuser(client):
    user = User.objects.create_superuser("admin", "admin@example.com", "password")
    client.force_login(user)
    return user
