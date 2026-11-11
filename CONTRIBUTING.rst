============
Contributing
============

Thank you for helping improve Django CMS Simple Admin Style. Bug reports, CSS
fixes, compatibility work, documentation improvements, and tests are all
welcome.

Reporting an issue
==================

Open an issue at
https://github.com/fsbraun/djangocms-simple-admin-style/issues and include:

* the versions of Python, Django, django CMS, and this package;
* the browser and operating system for visual problems;
* the admin page or widget affected;
* steps to reproduce the problem; and
* a screenshot for visual regressions, where possible.

Please check existing issues before opening a new one.

Development setup
=================

Clone the repository and create a virtual environment::

    git clone https://github.com/fsbraun/djangocms-simple-admin-style.git
    cd djangocms-simple-admin-style
    python -m venv .venv
    source .venv/bin/activate

Install the Python test and lint tools::

    python -m pip install django beautifulsoup4 soupsieve packaging "ruff~=0.16.0"

Install the pinned frontend tools. The repository's ``.nvmrc`` specifies the
Node.js version used by the project::

    nvm install
    npm ci

Optionally install the pre-commit hooks::

    python -m pip install pre-commit
    pre-commit install

The Python suite deliberately runs against a plain Django admin and does not
need django CMS. Do not install the package itself when checking a specific
Django version: its ``django-cms`` dependency can constrain Django and defeat
the purpose of the compatibility test.

Making changes
==============

Python and templates
--------------------

Python code lives in ``djangocms_simple_admin_style/``. Template-tag tests are
in ``tests/test_templatetags.py``. Add or update tests for any behaviour change.

CSS
---

Always edit the readable stylesheets in ``private/``; never edit the generated
``*.min.css`` files directly.

``private/djangocms-simple-admin.css`` contains the styles for Django 6.1.
This release branch ships only that stylesheet.

After changing CSS, lint and rebuild it::

    npx stylelint "private/*.css"
    ./minify-css

Commit the corresponding generated files under
``djangocms_simple_admin_style/static/djangocms_simple_admin_style/css/``.
CI rebuilds them and fails if they are stale.

Running checks
==============

Run the Python suite::

    python -m django test tests --settings=tests.settings

Run the Python linter::

    python -m ruff check .

Run all configured pre-commit hooks::

    pre-commit run --all-files

CI tests Django 6.1 on Python 3.12 and 3.14.

How the test suite works
========================

``tests/test_selector_coverage.py``
-----------------------------------

This test renders representative admin pages and asserts that every rule in
the active stylesheet matches something. It catches a common silent failure:
Django changes its admin markup, the CSS remains syntactically valid, but a
selector stops applying.

Coverage is measured per CSS rule rather than per individual selector. A rule
containing several selectors is live when at least one of them matches.

Some rules cannot match the server-rendered plain-Django fixture. Exceptions
are documented, with a reason for every entry, in two collections:

``NOT_SERVER_RENDERED``
    Markup created by JavaScript or supplied by another package, including
    django CMS, django-parler, and django-select2.

``KNOWN_STALE``
    Pre-existing dead rules kept visible as cleanup tasks. New dead rules
    should be fixed or removed, not added here by default.

The exception lists are checked against the stylesheets so entries cannot
remain after their associated rules are deleted.

``tests/test_stylesheet_sanity.py``
-----------------------------------

These structural checks run against the source stylesheet. In particular,
they reject unknown type selectors, which are usually class selectors that
lost their leading ``.`` and would otherwise fail silently.

``tests/test_templatetags.py``
------------------------------

These unit tests cover the release stylesheet, legacy-style detection, fallbacks,
and update-notification rendering. django CMS is stubbed where required so the
test matrix can choose its Django version independently.

Rendered admin pages
--------------------

``tests/pages.py`` renders the following representative states:

* dashboard and application index;
* changelists with pagination, search, and filtering;
* add, change, validation-error, view-only, history, and popup forms;
* single-object and bulk-action deletion confirmations;
* authentication user add, change, and changelist pages;
* the password-change and login pages; and
* a successful submission with a message.

The test app exercises text, numeric, date/time, choice, relation, read-only,
and many-to-many widgets, along with collapsed fieldsets and stacked and
tabular inlines.

When selector coverage fails
----------------------------

A reported rule is dead for the Django version under test. Determine whether
the admin markup changed or the rule is obsolete, then update or remove the
selector. Add an exception only when the rule genuinely belongs to one of the
documented categories above.

To cover another admin state, add it to ``render_all()`` in ``tests/pages.py``.
To exercise another widget, usually add a field to
``tests/testapp/models.py`` and configure it in ``tests/testapp/admin.py``.

Releases
========

Versions use ``x.y.z``, where ``x.y`` matches the target Django major and minor
version and ``z`` is this package's patch number. Patch numbers start at ``0``
and advance independently for each Django series, regardless of Django's own
patch releases.

Maintain each series on ``release/x.y.x`` (currently ``release/5.2.x``,
``release/6.0.x``, and ``release/6.1.x``), created from ``main``. Apply fixes
to each affected release branch and increment its ``__version__`` in
``djangocms_simple_admin_style/__init__.py`` when preparing a release. Record
the changes in ``CHANGELOG.rst`` on that branch.

Pull requests
=============

Before submitting a pull request:

* keep the change focused and explain the user-visible effect;
* add a test or explain why one is not practical;
* apply stylesheet fixes to each affected release branch;
* rebuild and commit minified CSS after a stylesheet change;
* update ``CHANGELOG.rst`` for user-visible changes; and
* run the relevant Python, CSS, and pre-commit checks.

Screenshots or short recordings are especially helpful for visual changes.
