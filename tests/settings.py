"""Minimal Django project used by the test suite.

Deliberately does *not* install django CMS: the stylesheet split is driven by
``django.VERSION`` alone, so the CI matrix stays a pure Django matrix and is not
constrained by which django CMS release supports which Django. The templatetags
all guard their ``cms`` imports with ``try/except ImportError``; the tests that
need a ``cms`` module inject a fake one via ``sys.modules``.
"""

SECRET_KEY = "not-a-secret-test-key"
DEBUG = False
USE_TZ = True
ROOT_URLCONF = "tests.urls"

INSTALLED_APPS = [
    # Must precede django.contrib.admin so admin/base_site.html is overridden.
    "djangocms_simple_admin_style",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "tests.testapp",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
