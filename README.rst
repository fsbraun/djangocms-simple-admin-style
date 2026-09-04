=============================
Django CMS Simple Admin Style
=============================

|PyPiVersion| |DjVersion| |CmsVersion| |Tests|

A lightweight theme that makes Django's admin feel at home in django CMS.
It aligns colours, spacing, forms, buttons, and icons with the django CMS
interface while deliberately preserving Django's familiar admin structure and
behaviour.

``djangocms-simple-admin-style`` is included by the `official django CMS
project template <https://docs.django-cms.org/en/latest/tutorials/00-installing-django-cms.html>`_.

See the difference
==================

The comparisons below show the same django CMS admin dashboard with Django's
native styling and with Django CMS Simple Admin Style.

Light mode
----------

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Django admin
     - Django CMS Simple Admin Style
   * - |DjangoLight|
     - |StyleLight|

Dark mode
---------

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - Django admin
     - Django CMS Simple Admin Style
   * - |DjangoDark|
     - |StyleDark|

Why use it?
===========

* **Consistent:** the Django admin and django CMS editing interface share one
  visual language, including light and dark colour schemes.
* **Conservative:** small, targeted overrides leave Django's admin styling and
  behaviour intact.
* **Compatible:** dedicated stylesheets support both the established admin
  markup and the redesigned forms introduced in Django 6.1.
* **Compact:** each production stylesheet is a single minified CSS file under
  16 kB.
* **Tested:** CI renders real admin pages and checks that CSS rules still match
  across supported Django versions.

Alternative: Django Unfold
==========================

This package intentionally stays close to Django's native admin. Projects that
prefer the more comprehensive `Django Unfold <https://unfoldadmin.com/>`_ theme
can instead use MetaForX's `Django Unfold Extra
<https://github.com/metaforx/django-unfold-extra>`_. That unofficial extension
integrates Unfold with django CMS, including the page tree, plugin forms,
versioning, and light/dark theme synchronisation.

Installation
============

Install the package::

    python -m pip install djangocms-simple-admin-style

Then add it to ``INSTALLED_APPS`` immediately before
``django.contrib.admin``::

    INSTALLED_APPS = [
        # ...
        "djangocms_simple_admin_style",
        "django.contrib.admin",
        # ...
    ]

Projects created with the official django CMS project template already include
the package.

Configuration
=============

Colour scheme
-------------

The theme follows django CMS' ``CMS_COLOR_SCHEME`` setting. For example::

    CMS_COLOR_SCHEME = "auto"  # "light", "dark", or "auto"

See the `django CMS colour-scheme documentation
<https://docs.django-cms.org/en/latest/explanation/colorscheme.html>`_ for
details.

Update notifications
--------------------

Superusers see a notification on the admin index when a newer applicable
django CMS release is available. The check requests current release metadata
from PyPI; it does not send project or user data.

``CMS_ENABLE_UPDATE_CHECK``
    Defaults to ``True``. Set it to ``False`` to disable the check.

``CMS_UPDATE_CHECK_TYPE``
    Defaults to ``"patch"`` and accepts ``"patch"`` or ``"minor"``.
    ``"patch"`` stays within the installed ``x.y`` series; ``"minor"`` stays
    within the installed major series.

Legacy django CMS styling
-------------------------

The package automatically uses the legacy visual language with django CMS
versions earlier than 5.1, or when the project's ``base.html`` contains
``<html data-cms-theme="3">`` or ``<html data-cms-theme="4">``.

Set ``CMS_LEGACY_STYLE`` to override detection:

* ``True`` forces the legacy django CMS 4 style.
* ``False`` forces the current style and skips auto-detection.
* If unset, the style is detected automatically.

Custom styling
--------------

The package overrides ``admin/base_site.html``. To add project-specific CSS,
create ``templates/admin/inc/extrastyle.html`` in your project; that template
is included in the admin's ``extrastyle`` block.

Contributing
============

Bug reports and pull requests are welcome. See the `contribution guide
<https://github.com/fsbraun/djangocms-simple-admin-style/blob/main/CONTRIBUTING.rst>`_
for the development setup, CSS workflow, and test-suite guide. Release details
are recorded in the `changelog
<https://github.com/fsbraun/djangocms-simple-admin-style/blob/main/CHANGELOG.rst>`_.

Licensing
=========

The package is distributed under the BSD 3-Clause License. Bundled Bootstrap
Icons are distributed under the MIT License; see the `license file
<https://github.com/fsbraun/djangocms-simple-admin-style/blob/main/LICENSE>`_
for details.


.. |PyPiVersion| image:: https://img.shields.io/pypi/v/djangocms-simple-admin-style.svg?style=flat-square
    :target: https://pypi.org/project/djangocms-simple-admin-style/
    :alt: Latest PyPI version

.. |DjVersion| image:: https://img.shields.io/pypi/frameworkversions/django/djangocms-simple-admin-style.svg?style=flat-square
    :target: https://pypi.org/project/djangocms-simple-admin-style/
    :alt: Supported Django versions

.. |CmsVersion| image:: https://img.shields.io/pypi/frameworkversions/django-cms/djangocms-simple-admin-style.svg?style=flat-square
    :target: https://pypi.org/project/djangocms-simple-admin-style/
    :alt: Supported django CMS versions

.. |Tests| image:: https://github.com/fsbraun/djangocms-simple-admin-style/actions/workflows/tests.yml/badge.svg?branch=main
    :target: https://github.com/fsbraun/djangocms-simple-admin-style/actions/workflows/tests.yml
    :alt: Test status

.. |DjangoLight| image:: https://raw.githubusercontent.com/fsbraun/djangocms-simple-admin-style/main/private/django-light.jpg
    :alt: django CMS dashboard with native Django admin styling in light mode
    :width: 100%

.. |StyleLight| image:: https://raw.githubusercontent.com/fsbraun/djangocms-simple-admin-style/main/private/style-light.jpg
    :alt: django CMS dashboard with Django CMS Simple Admin Style in light mode
    :width: 100%

.. |DjangoDark| image:: https://raw.githubusercontent.com/fsbraun/djangocms-simple-admin-style/main/private/django-dark.jpg
    :alt: django CMS dashboard with native Django admin styling in dark mode
    :width: 100%

.. |StyleDark| image:: https://raw.githubusercontent.com/fsbraun/djangocms-simple-admin-style/main/private/style-dark.jpg
    :alt: django CMS dashboard with Django CMS Simple Admin Style in dark mode
    :width: 100%
