=============================
django CMS Simple Admin Style
=============================

|pypi| |django| |djangocms| |djangocms4|

This is a simple alternative for the `django CMS Admin Style <https://github.com/django-cms/djangocms-admin-style>`_. While django CMS admin style reorganizes Django's admin to offer a unified user experience, this package has a much simpler objective:

* Adjust colors to be consistent with django CMS.
* Minimally adapt the css (e.g., add button borders) to keep the user interface consistent.
* Except this, avoid interfering with Django's admin styling: no `!important` statements, for example.
* Remove headers in django CMS' sidebar
* Remove headers, navigation and breadcrumbs in django CMS' modal

Also, no javascript is needed and all CSS is contained in a simple CSS file with less than 10kB in size.

Documentation
=============

See ``REQUIREMENTS`` in the `setup.py <https://github.com/fsbraun/djangocms-simple-admin-style/blob/master/setup.py>`_
file for additional dependencies:

Installation
------------

For a manual install:

* run ``pip install djangocms-simple-admin-style``
* add ``djangocms_simple_admin_style`` to your ``INSTALLED_APPS`` just before ``'django.contrib.admin'``


Configuration
-------------

The django CMS Admin Style overrides django admin's ``base_site.html``,
but you can still partially customize this page. Look at the source of
``templates/admin/base_site.html`` and override the templates that are included in various blocks. For example, you can add your own CSS in
``templates/admin/inc/extrastyle.html``.

Contributing
------------

Contributions are highly welcome! Install the development environment by typing

.. code-block::

    nvm use
    npm install

Changes are made in the ``private/djangocms-simple-admin.css`` file. Minify the file using ``. ./minify-css`` command.


.. |pypi| image:: https://badge.fury.io/py/djangocms-simple-admin-style.svg
    :target: http://badge.fury.io/py/djangocms-simple-admin-style
.. |django| image:: https://img.shields.io/badge/django-2.2%2B-blue.svg
    :target: https://www.djangoproject.com/
.. |djangocms| image:: https://img.shields.io/badge/django%20CMS-3.6%2B-blue.svg
    :target: https://www.django-cms.org/
.. |djangocms4| image:: https://img.shields.io/badge/django%20CMS-4-blue.svg
    :target: https://www.django-cms.org/
