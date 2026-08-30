=====================================
Django CMS Simple Admin Style
=====================================

|PyPiVersion| |DjVersion| |CmsVersion|

Overview
--------
The **Django CMS Simple Admin Style** is a lightweight alternative to the comprehensive `Django CMS Admin Style <https://github.com/django-cms/djangocms-admin-style>`_. Its goal is to refine the Django CMS interface with minimalistic changes:

- Standardizing color schemes with Django CMS.
- Making minimal CSS adjustments like adding button borders for interface consistency.
- Restraining from interfering with Django's admin styling.
- Removing headers from Django CMS' sidebar and modal.

All stylesheets are combined into a single CSS file under 20kB.

Browser Support
---------------
The **Django CMS Simple Admin Style** uses CSS nesting to maintain a small stylesheet size, which makes it incompatible with Internet Explorer. It does work with all current versions of modern browsers. Visit `CanIUse <https://caniuse.com/css-nesting>`_ for more information on CSS features compatibility.

Installation
------------
For a manual installation:

- Run ``pip install djangocms-simple-admin-style``
- Add ``djangocms_simple_admin_style`` to your ``INSTALLED_APPS`` just before ``'django.contrib.admin'``

Configuration
-------------
While the Django CMS Simple Admin Style overrides Django admin's ``base_site.html``, you can still
customize this page using the source of ``templates/admin/base_site.html`` and override the templates
included in various blocks. For instance, you can insert your own CSS in ``templates/admin/inc/extrastyle.html``.

The following additional settings can be set:

* `CMS_ENABLE_UPDATE_CHECK = True` Set to False to disable the update notification.
* `CMS_UPDATE_CHECK_TYPE = 'patch'` Set to `'patch'` to get only patch notifications. (major = x.x.x, minor = 5.x.x, patch = 5.0.x)
* `CMS_LEGACY_STYLE` Force the legacy (django CMS 4) admin styling on or off. If unset, the legacy style is auto-detected on django CMS < 5.1 or when the project's ``base.html`` declares ``<html data-cms-theme="4">``. Set to ``True`` to force the legacy style, or ``False`` to force the new style and skip auto-detection.

The update checker does not gather or record any data - however, it does query pypi.org for the latest version number.

Contributing
------------
To contribute:

- Set up the development environment with ``nvm use`` and ``npm install``.
- Changes should be made in ``private/``, never in the built ``*.min.css``:

  - ``private/djangocms-simple-admin.css`` is served on Django 6.1 and later,
    which stacks admin form inputs beneath their labels natively (ticket
    #34643).
  - ``private/djangocms-simple-admin-legacy.css`` is served on Django 6.0 and
    earlier, and forces that layout itself.

  ``{% admin_style_css %}`` picks between them by ``django.VERSION``. A change
  that is not specific to one admin generation usually belongs in both.

- Use ``. ./minify-css`` to minify the updated CSS files. CI fails if the
  committed minified files do not match their sources.
- Lint the stylesheets with ``npx stylelint "private/*.css"``.

Running the tests
-----------------

The suite needs Django and a few small helpers, but *not* django CMS -- it runs
a plain Django admin, so it can be tested against every supported Django rather
than only the ones a given django CMS release pins::

    pip install django beautifulsoup4 soupsieve packaging
    python -m django test tests --settings=tests.settings

The package itself is deliberately not installed: the tests import it from the
working directory, so its ``django-cms`` dependency -- which would pin Django and
collapse the matrix -- never enters the picture. (``pip install -e ".[test]"``
installs the same helpers, but pulls django CMS in with them.)

CI runs this against Django 4.2, 5.0, 5.1, 5.2, 6.0, 6.1 and Django ``main``.
Each run tests whichever stylesheet ``admin_style_css()`` would actually serve
for that version, so the legacy sheet is exercised below 6.1 and the current one
from 6.1 up.

What the tests do
~~~~~~~~~~~~~~~~~

``tests/test_selector_coverage.py``
    Renders a sample of real admin pages and asserts that every rule in the
    stylesheet still matches something. When a new Django release renames or
    restructures admin markup, this names the exact rules that stopped applying
    instead of leaving you to spot it in a screenshot -- the failure mode that
    produced ``ol.breadcrumbs``, ``.titles-and-tools`` and
    ``[aria-current="page"]``.

``tests/test_stylesheet_sanity.py``
    Structural checks needing no rendered HTML, over both stylesheets. Most
    usefully, it rejects a type selector that names no real element, which is
    almost always a class selector that lost its leading dot -- valid CSS that
    silently matches nothing.

``tests/test_templatetags.py``
    Unit tests for the template tags, including the legacy-style auto-detection
    and its fallbacks.

Admin pages used for coverage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``tests/pages.py`` renders these pages against ``tests.testapp``, whose ``Widget``
model and ``ModelAdmin`` are built to exercise the widgets the stylesheets
target. A rule only counts as live if it matches on at least one of them, so
this list is what the coverage check is worth:

``index``, ``app_list``
    The dashboard and the single-app list: module tables, section links and the
    ``colMS`` sidebar layout.

``changelist``
    Result table, sortable headers, action bar, filter sidebar, search bar,
    date hierarchy and the paginator. ``list_per_page`` is 5 against 12
    fixtures, so the list really paginates.

``changelist_page2``, ``changelist_search``, ``changelist_filtered``
    The states the base changelist does not show: a current paginator page, a
    submitted search, and a selected filter.

``add``, ``change``
    The widest page by far. Between them they render text, slug, textarea, URL,
    email, integer, decimal, split date/time, date, checkbox, choice select and
    a read-only UUID field; a foreign key in a ``related-widget-wrapper``; a
    many-to-many as ``filter_horizontal``; ``wide``, ``collapse`` and multi-field
    (``.fieldBox``) fieldsets; a fieldset description; and both a stacked and a
    tabular inline.

``add_invalid``
    The same form submitted with errors, for ``.errorlist`` and the
    ``.flex-container.errors`` wrapper.

``delete``, ``action_confirm``
    Both delete-confirmation layouts: the single-object page and the
    ``delete_selected`` action interstitial.

``view_only_change``
    The change page as seen by a staff user with view-but-not-change
    permission. Django renders the submit row's ``.closelink`` only when the
    form cannot be saved, so this read-only page is the one place that markup
    appears.

``history``
    The object history table.

``popup``
    An add form with ``?_popup=1``, for the ``.popup`` body class and its
    submit row.

``user_changelist``, ``user_add``, ``user_change``
    The auth user pages, which the stylesheets target by name via the
    ``app-auth`` and ``model-user`` body classes and the password field.

``password_change``
    The admin password change form.

``with_message``
    A successful submission followed through the redirect, so ``.messagelist``
    markup is present.

``login``
    The logged-out login form.

When a coverage test fails
~~~~~~~~~~~~~~~~~~~~~~~~~~

A reported rule is dead on the Django version being tested. Either the admin
changed and the rule needs updating, or the rule is obsolete and should be
deleted. If neither applies, the rule belongs in one of three lists in
``tests/test_selector_coverage.py``, all of which carry a reason per entry:

``NOT_SERVER_RENDERED``
    Markup this suite can never see, because a script builds it in the browser
    (``.selector`` from ``SelectFilter2.js``, the ``.datetimeshortcuts`` icons)
    or another package ships it (django CMS, django-parler, django-select2). A
    browser-driven visual regression suite would cover these; this one says so
    rather than pretending.

``VERSION_GATED``
    Rules for markup a newer Django introduced, correctly dead below it. The
    boundaries are established by running the suite against each release, not
    guessed.

``KNOWN_STALE``
    Pre-existing dead rules, pinned so the suite starts green. Each entry is a
    to-do, not an excuse.

The first two lists are the interesting ones to keep short. Entries are checked
against the stylesheets, so a rule that is later deleted cannot linger in a list.

To add a page to the sample, add it to ``render_all()`` in ``tests/pages.py``;
adding a widget type usually means a field on ``tests/testapp/models.py`` and its
``ModelAdmin``.

Icons
-----

djangocms-simple-admin-style uses icons from `Bootstrap Icons <https://icons.getbootstrap.com/>`_. These icons are licensed under
`MIT License <https://opensource.org/licenses/MIT>`_.


.. |PyPiVersion| image:: https://img.shields.io/pypi/v/djangocms-simple-admin-style.svg?style=flat-square
    :target: https://pypi.python.org/pypi/djangocms-simple-admin-style
    :alt: Latest PyPI version

.. |DjVersion| image:: https://img.shields.io/pypi/frameworkversions/django/djangocms-simple-admin-style.svg?style=flat-square
    :target: https://pypi.python.org/pypi/djangocms-simple-admin-style
    :alt: Django versions

.. |CmsVersion| image:: https://img.shields.io/pypi/frameworkversions/django-cms/djangocms-simple-admin-style.svg?style=flat-square
    :target: https://pypi.python.org/pypi/djangocms-simple-admin-style
    :alt: django CMS versions
