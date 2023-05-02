=============================
django CMS Simple Admin Style
=============================

|pypi| |django| |djangocms| |djangocms4|

This is a simple alternative for the `django CMS Admin Style <https://github.com/django-cms/djangocms-admin-style>`_. While django CMS admin style reoganizes Django's admin to uffer a unified user experience, this package has a much simpler objective:

* Adjust colors to be consistent with django CMS.
* Minimally adapt the css (e.g., add button borders) to keep the user interface consistent.
* Exept this, Do not interfere with Django's admin styling

Hence, it does only mildly adapt Django's admin style but changes fonts, colors, and some form rendering to better fit into the django CMS look and feel.


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


.. |pypi| image:: https://badge.fury.io/py/djangocms-simple-admin-style.svg
    :target: http://badge.fury.io/py/djangocms-simple-admin-style
.. |django| image:: https://img.shields.io/badge/django-2.2%2B-blue.svg
    :target: https://www.djangoproject.com/
.. |djangocms| image:: https://img.shields.io/badge/django%20CMS-3.6%2B-blue.svg
    :target: https://www.django-cms.org/
.. |djangocms4| image:: https://img.shields.io/badge/django%20CMS-4-blue.svg
    :target: https://www.django-cms.org/
