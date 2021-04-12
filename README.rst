edx-sysadmin
=============================

This is a django app plugin extracted from `edx-platform <https://github.com/edx/edx-platform>`_ which enables certian users to perform some specific operations in Open edX environment (which are described under ``Features`` section below).
Earlier, ``Sysadmin Dashboard`` was a part of ``edx-platform``, however starting from `lilac release <https://github.com/edx/edx-platform/tree/open-release/lilac.master>`_ of Open edX the sysadmin panel has been removed
and transitioned to as separate plugin.

NOTE:
It is recommended that you use edx-sysadmin plugin with Open edX's `lilac <https://github.com/edx/edx-platform/tree/open-release/lilac.master>`_ release and successors.
If you wish to use the ``Sysadmin Dashboard`` with Open edX releases before ``lilac`` you should just enable ``ENABLE_SYSADMIN_DASHBOARD`` feature flag in environment files (e.g ``lms.yml`` or ``lms.env.json``) to access sysadmin dashboard features.

Overview
------------------------

The edx-sysadmin plugin equips the admin users with certain handy operation in Open edX which would otherwise be difficult to perform manually.
This plugin is just like other django applications except for the parts that really make it able to be integrated with edx-platform and to understand those you might want to take a look at `this link. <https://github.com/edx/edx-django-utils/tree/master/edx_django_utils/plugins>`_

Features
~~~~~~~~

edx-sysadmin provides different features such as:

* Register Users:
    * You can ``register new user accounts`` with an easy to use form via ``Users`` tab.
* Delete Courses:
    * You can ``delete any course by using a course ID or directory`` via ``Courses`` tab.
* Git Import:
    * You can ``import any course maintained through a git repository`` via ``Git Import`` tab.
* Git Logs
    * You can ``check the logs for all imported courses`` through git via ``Git Logs`` tab.

Installing The Plugin
~~~~~~~~~~~~~~~~~~~~~

* You can install the plugin into your Open edX environment using PyPI e.g. ``pip install edx-sysadmin`` or directly from github e.g. ``pip install https://github.com/mitodl/edx-sysadmin.git``
* Once you have installed the plugin you can visit ``<EDX_BASE_URL>/sysadmin`` to access the plugin features.
* If you decide to make your own changes in the plugin you can go to ``Development Workflow`` section below.

``Note``: In some cases you might need to restart edx-platform after installing the plugin to reflect the changes.


Development Workflow
--------------------

One Time Setup
~~~~~~~~~~~~~~

.. code-block::

  # Clone the repository
  git clone git@github.com:mitodl/edx-sysadmin.git
  cd edx-sysadmin
  # Set up a virtual environment and activate it
  virtualenv -p python3.8 venv_sysadmin && source venv_sysadmin/bin/activate

Every time you develop something in this repo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

  # Activate the virtualenv
  source venv_sysadmin/bin/activate
  # Get into edx-sysadmin repo directory
  cd edx-sysadmin
  # Grab the latest code
  git checkout master
  git pull
  # Install/update the dev requirements
  make requirements
  # Make a new branch for your changes
  git checkout -b <your_github_username>/<short_description>
  # Using your favorite editor, edit the code to make your change.
  e.g. vim …
  # Commit all your changes
  git commit …
  git push
  # Open a PR and ask for review.

License
-------

The code in this repository is licensed under the AGPL 3.0 unless
otherwise noted.
Please see `LICENSE.txt <LICENSE.txt>`_ for details.

How To Contribute
-----------------

Contributions are very welcome.
Even though they were written with ``edx-platform`` in mind, the guidelines should be followed for all Open edX projects.
