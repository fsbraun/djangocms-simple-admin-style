import uuid

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Widget(models.Model):
    """A model whose fields cover the widget types the stylesheets target."""

    STATUS_CHOICES = [("d", "Draft"), ("p", "Published")]

    title = models.CharField(max_length=100)
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True)
    homepage = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    quantity = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    published_at = models.DateTimeField(null=True, blank=True)
    available_on = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="d")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    identifier = models.UUIDField(default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.title


class Note(models.Model):
    widget = models.ForeignKey(Widget, on_delete=models.CASCADE, related_name="notes")
    body = models.TextField()

    def __str__(self):
        return self.body[:20]


class Attachment(models.Model):
    widget = models.ForeignKey(Widget, on_delete=models.CASCADE, related_name="attachments")
    label = models.CharField(max_length=50)
    url = models.URLField(blank=True)
    # A second FK so the tabular inline renders a .related-widget-wrapper.
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.label
