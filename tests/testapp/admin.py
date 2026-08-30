from django.contrib import admin

from tests.testapp.models import Attachment, Category, Note, Tag, Widget


class NoteInline(admin.StackedInline):
    model = Note
    extra = 1


class AttachmentInline(admin.TabularInline):
    """Renders `.tabular` markup, which the stylesheets style separately."""

    model = Attachment
    extra = 1


@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "status", "is_active", "published_at")
    list_filter = ("is_active", "status", "category")
    search_fields = ("title", "description")
    date_hierarchy = "published_at"
    filter_horizontal = ("tags",)  # renders the .selector / .selector-chooseall widget
    readonly_fields = ("identifier",)
    list_per_page = 5  # small enough that the fixtures span several paginator pages
    actions = ["mark_active"]
    fieldsets = (
        (None, {"fields": ("title", "slug", "status", "category")}),
        (
            "Content",
            {
                "fields": ("description", "homepage", "email"),
                # Rendered with |safe, so a description may carry markup --
                # which is what the stylesheet's `.description p` rule styles.
                "description": "<p>Free text fields.</p>",
                "classes": ("wide",),  # renders the .wide fieldset layout
            },
        ),
        # A tuple inside `fields` renders .form-multiline / .fieldBox
        ("Numbers", {"fields": (("quantity", "price"),)}),
        ("Dates", {"fields": ("published_at", "available_on"), "classes": ("collapse",)}),
        ("Flags", {"fields": ("is_active", "tags", "identifier")}),
    )
    inlines = [NoteInline, AttachmentInline]

    @admin.action(description="Mark selected widgets as active")
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)
