.. _examples:

Examples
========

The 16 programs in ``examples`` are complete and runnable from a checkout with
the project installed in ``.venv``. The nine recipes listed first use memory
or automatically cleaned temporary directories. The seven persistent examples
below use distinct per-user configuration locations; migration reads an
existing historical file and creates a separate v2 file.

Run an example on Windows with:

.. code-block:: console

   .\.venv\Scripts\python.exe examples\basic_store.py

Progressive recipes
-------------------

These examples are explained with full source in :doc:`recipes`. Use the same
command above with the desired filename. On Linux or macOS, use
``./.venv/bin/python examples/portable_store.py``.

.. list-table::
   :header-rows: 1
   :widths: 17 33 50

   * - Level
     - Script
     - Input and file effects
   * - Simple
     - ``portable_store.py``
     - No input; temporary store with defaults and updates.
   * - Simple
     - ``boolean_collection.py``
     - Terminal; boolean and optional text, no file.
   * - Intermediate
     - ``edit_settings.py``
     - Terminal; retain values or edit JSON, no file.
   * - Intermediate
     - ``gui_collection.py``
     - GUI extra required; formatted prefill, no file.
   * - Intermediate
     - ``handle_errors.py``
     - No input; malformed YAML in a temporary directory.
   * - Advanced
     - ``nested_collection.py``
     - Terminal; edit a subsection and save a temporary file.
   * - Advanced
     - ``custom_interface.py``
     - Scripted answers with retries, no file.
   * - Advanced
     - ``typed_settings.py``
     - No input; dataclass validation and a temporary store.
   * - Advanced
     - ``schema_upgrade.py``
     - No input; idempotent transformation of a temporary file.

The remaining examples below progress from simple storage to project setup,
environment profiles, and migration. Persistent examples print their paths.

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
