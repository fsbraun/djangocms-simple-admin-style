=====================================
Django CMS Simple Admin Style
=====================================

|pypi| |django| |djangocms| |djangocms4|

Overview
--------
The **Django CMS Simple Admin Style** is a lightweight alternative to the comprehensive `Django CMS Admin Style <https://github.com/django-cms/djangocms-admin-style>`_. Its goal is to refine the Django CMS interface with minimalistic changes:

- Standardizing color schemes with Django CMS.
- Making minimal CSS adjustments like adding button borders for interface consistency.
- Restraining from interfering with Django's admin styling.
- Removing headers from Django CMS' sidebar and modal.

All stylesheets are combined into a single CSS file under 10kB.

Browser Support
---------------
The **Django CMS Simple Admin Style** uses CSS nesting to maintain a small stylesheet size, which makes it incompatible with Internet Explorer. It does work with all current versions of modern browsers. Visit `CanIUse <https://caniuse.com/css-nesting>`_ for more information on CSS features compatibility.

Installation
------------
For a manual installation:

- Run ``pip install djangocms-simple-admin-style``
- Add ``djangocms_simple_admin_style`` to your ``INSTALLED_APPS`` just before ``'django.contrib.admin'``

Customization
-------------
While the Django CMS Simple Admin Style overrides Django admin's ``base_site.html``, you can still customize this page using the source of ``templates/admin/base_site.html`` and override the templates included in various blocks. For instance, you can insert your own CSS in ``templates/admin/inc/extrastyle.html``.

Contributing
------------
To contribute:

- Set up the development environment with ``nvm use`` and ``npm install``.
- Changes should be made in ``private/djangocms-simple-admin.css``.
- Use ``. ./minify-css`` to minify the updated CSS file.

.. |pypi| image:: https://badge.fury.io/py/djangocms-simple-admin-style.svg
    :target: http://badge.fury.io/py/djangocms-simple-admin-style
.. |django| image:: https://img.shields.io/badge/django-2.2%2B-blue.svg
    :target: https://www.djangoproject.com/
.. |djangocms| image:: https://img.shields.io/badge/django%20CMS-3.6%2B-blue.svg
    :target: https://www.django-cms.org/
.. |djangocms4| image:: https://img.shields.io/badge/django%20CMS-4-blue.svg
    :target: https://www.django-cms.org/
