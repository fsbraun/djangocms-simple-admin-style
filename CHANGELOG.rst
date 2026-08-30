=========
Changelog
=========

Version 2.1.0 (2026-08-30)
==========================

* feat: Add a lean stylesheet for the redesigned Django 6.1+ admin forms
  (inputs stacked beneath labels, #34643). ``base_site.html`` now selects the
  stylesheet by Django version; the previous stylesheet is kept as
  ``djangocms-simple-admin-legacy.min.css`` for Django 6.0 and earlier.
* feat: Full-width inputs and full-width labels above each field, building on
  the native Django 6.1 layout instead of overriding it.
* feat: Show the split date and time pickers side by side on wide screens and
  tint the calendar/clock icons with the CMS colour.
* feat: Render field help text below the field instead of above it.
* fix: Centre checkboxes with their labels and tint checkboxes/radios with the
  theme colour via ``accent-color``.
* fix: Consistent button spacing in the submit row and on the delete
  confirmation page.

Version 2.0.2 (2026-04-12)
==========================

* fix: Label width inconsistent for composite widgets by @fsbraun in https://github.com/fsbraun/djangocms-simple-admin-style/pull/20
* fix: Password reset button line height by @fsbraun in https://github.com/fsbraun/djangocms-simple-admin-style/pull/21

Version 2.0.1 (2026-02-11)
==========================

* Adjustments for Django 6.0

Version 2.0.0 (2025-11-14)
==========================

* More modern redesign
* Support of new django CMS design language (django CMS 5.1+)
* Configurable update notification

Version 1.1.5
=============

* fix: Color versioning menu for third party models
* fix: Related object icon size
* fix: Summary caret margin styling

Version 1.1.4
=============

* fix: Parler language tabs
* fix: Page content language tabs

Version 1.1.3
=============

* fix: Multicolumn flexbox issues
* feat: Show h1 headings, hide h2
* feat: Consistently position object tools

Version 1.1.2
=============

* fix: No border on fieldset titles
* fix: Action buttons, site title size#
* fix: Object tools
* fix: Checkbox label alignment
* fix: Show title in delete confirmations in the sidebar

Version 1.1.0
=============

* Add support for Django 5.1 fieldsets
* Update on admin header styling


Version 1.0.5
=============

* Fix multicolumn flexbox issues
* Fix responsive bug for changelists with filters
* Better font sizes for filters

Version 1.0.2
=============

* Better contrast in dark mode in alignment with django CMS 4

Version 1.0.0
=============
* Refactor CSS using nesting
* Optimize text and icon sizes
* Improve compatibility for with Django 5 admin
* Fix select2 styling for 4 admin action buttons

Version 0.4.9
=============

* Improve styling of non-submit admin buttons
* Improve styling of form errors


Version 0.4.8
=============

Bugfix:

* More complete adaptation to Django dark mode
* Allow for admin pages with object tools in modal


Version 0.4.6
=============

Feature

* Start of the changelog

Bugfix:

* Fix color issue on admin start page

Version 0.4.4
=============

Bugfix:

* Remove responsive artefacts

Version 0.4.3
=============

Bugfixes:

* Leave space in sidebar object tools for sidebar navigation buttons
* Hide title in plugin change form in modal view

Version 0.4.1
=============

Bugfixes:

* Second cancel link removed on delete confirmation
* Better width of select boxes
