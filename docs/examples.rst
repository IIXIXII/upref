.. _examples:

Examples
========

The programs below are complete and runnable from a checkout with the project
installed in ``.venv``. Except for migration, they write to a distinct
platform-specific per-user configuration directory, not to the source tree.

Run an example on Windows with:

.. code-block:: console

   .\.venv\Scripts\python.exe examples\basic_store.py

Basic storage
-------------

This example saves a mapping, loads a fresh copy, and prints the exact path.
Running it again replaces the same example configuration.

.. literalinclude:: ../examples/basic_store.py
   :language: python
   :linenos:

Defaults, update, and delete
----------------------------

Defaults are merged recursively in memory. The resolved mapping is then saved,
selected changes are merged and persisted, and the example removes its file.

.. literalinclude:: ../examples/defaults_and_update.py
   :language: python
   :linenos:

Required project variables
--------------------------

This terminal-based setup asks only for project variables that have not been
saved yet: directories, the expected Python version, and whether tests should
run before a build. Boolean input accepts common forms such as ``yes``, ``no``,
``on``, and ``off``.

.. literalinclude:: ../examples/project_variables.py
   :language: python
   :linenos:

Environment profiles and runtime overrides
------------------------------------------

This example stores development, testing, and production profiles. The
``UPREF_PROFILE``, ``UPREF_SERVICE_URL``, and ``UPREF_TIMEOUT`` environment
variables can temporarily override the selected values without modifying the
saved YAML file.

For example, in PowerShell:

.. code-block:: powershell

   $env:UPREF_PROFILE = "production"
   $env:UPREF_TIMEOUT = "45"
   .\.venv\Scripts\python.exe examples\environment_profiles.py

.. literalinclude:: ../examples/environment_profiles.py
   :language: python
   :linenos:

Multiple projects
-----------------

Related projects can share one application configuration directory while
using a distinct YAML filename for each project. This is useful for a
workspace containing a frontend, backend, worker, or other independently
configured component.

.. literalinclude:: ../examples/multiple_projects.py
   :language: python
   :linenos:

Terminal collection
-------------------

On the first run, missing values are requested in the terminal. Later runs
reuse saved values. Cancelling before ``save`` leaves the existing file
unchanged.

.. literalinclude:: ../examples/tty_collection.py
   :language: python
   :linenos:

Migrating from v1
-----------------

This program imports an existing historical file. Change ``LEGACY_NAME`` to
the old configuration name. Migration leaves its source untouched and checks
for an existing v2 target before saving. Concurrent migrations require an
external lock.

.. literalinclude:: ../examples/migrate_v1.py
   :language: python
   :linenos:

.. warning::

   Upref configuration files contain plain YAML. Masked interactive input is
   not encrypted storage; use a system keyring or secrets manager for
   passwords and tokens.
