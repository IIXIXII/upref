.. _migration-guide:

Migrating from Upref v1
=======================

Upref v2 stores only raw configuration values. Upref v1 could instead store
field descriptors containing keys such as ``label``, ``description``,
``type``, and ``value``. Explicit migration extracts the values, writes a v2
file, and leaves the legacy source untouched.

Importing one file
------------------

Create the destination store and pass the historical configuration name
without the ``.conf`` extension:

.. code-block:: python

   from upref import ConfigStore, UprefError

   store = ConfigStore("my-application")

   try:
       config = store.import_legacy("my_personnal_data")
   except UprefError as error:
       print(f"Migration not performed: {error}")
   else:
       print(f"Migrated to {store.path}")

By default, Upref looks in the platform-specific v1 user-data directory used
for the ``.upref`` application. The legacy name is validated as a simple
component and ``.conf`` is appended.

For tests, portable installations, or a manually located source, pass an
absolute ``legacy_directory``:

.. code-block:: python

   from pathlib import Path
   from upref import ConfigStore

   store = ConfigStore("my-application")
   legacy_directory = Path.home() / "legacy-upref"
   config = store.import_legacy(
       "my_personnal_data",
       legacy_directory=legacy_directory,
   )

Migration behavior
------------------

``import_legacy`` has these guarantees:

* a missing source raises :exc:`~upref.MigrationError`;
* a target found during the preflight check is not replaced unless
  ``overwrite=True``;
* using the legacy source itself as the v2 target is always rejected;
* the source file is never modified or deleted;
* mappings not recognized as descriptors retain their shape;
* recognized descriptor mappings are converted to raw values and metadata
  entries and descriptors without a ``value`` member are omitted;
* the destination uses the same validation and atomic save as every v2 store;
* the returned mapping is the mapping written to the destination, or the
  proposed conversion when ``dry_run=True``.

Descriptor detection is necessarily structural because v1 files carry no
format version. Upref treats a document as descriptors when every
non-metadata top-level value is a mapping containing at least one of
``label``, ``description``, ``type``, or ``value``, and at least one field has
a ``value`` member. A raw configuration with that same shape is ambiguous and
may be converted. Use ``source_format="raw"`` to preserve every key of such
data. Use ``source_format="descriptors"`` to force extraction of ``value``
entries, dropping metadata and descriptors without a value. The default,
``source_format="auto"``, retains the historical detection behavior.

For example, ``{"timeout": {"value": 30, "unit": "seconds"}}`` becomes
``{"timeout": 30}`` in auto or descriptor mode. Raw mode preserves the full
mapping, including ``unit``.

Previewing a conversion
~~~~~~~~~~~~~~~~~~~~~~~~

Inspect the conversion without writing or creating the destination directory:

.. code-block:: python

   preview = store.import_legacy(
       "my_personnal_data", source_format="raw", dry_run=True
   )
   # Inspect or validate preview before choosing to perform the import.
   migrated = store.import_legacy("my_personnal_data", source_format="raw")

A dry run still checks that the source exists, source and target differ, and
the target does not already exist unless ``overwrite=True``. It does not test
write permissions or serialization at the destination. Previewing an existing
target with ``overwrite=True, dry_run=True`` leaves that target unchanged.
The returned tree is detached. A later import reads the source again; a preview
neither reserves the target nor freezes the source against other writers.

Overwriting a target
~~~~~~~~~~~~~~~~~~~~~

Use ``overwrite=True`` only after deciding that the legacy file is the source
of truth:

.. code-block:: python

   config = store.import_legacy("my_personnal_data", overwrite=True)

The existence check and save are separate operations and Upref does not lock
them. Another writer can create or replace the target between those steps.
Applications that can migrate concurrently must hold an external lock around
the complete operation.

Migration is intentionally not automatic during :meth:`~upref.ConfigStore.load`.
An application can therefore control when old data is discovered, how the
user is informed, and whether an existing v2 file takes precedence.

Deprecated compatibility API
----------------------------

The v1 functions remain available during the v2 series but emit
:class:`DeprecationWarning`. New application code should use these
replacements:

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - v1 function
     - v2 replacement
   * - ``load_data`` / ``current_upref``
     - :meth:`ConfigStore.load <upref.ConfigStore.load>`
   * - ``save_data``
     - :meth:`ConfigStore.save <upref.ConfigStore.save>`
   * - ``remove_pref``
     - :meth:`ConfigStore.delete <upref.ConfigStore.delete>`
   * - ``get_pref``
     - :func:`upref.collect`, followed by an explicit save
   * - ``set_pref``
     - :meth:`ConfigStore.update <upref.ConfigStore.update>`
   * - ``upref_filename``
     - :attr:`ConfigStore.path <upref.ConfigStore.path>`
   * - ``load_conf`` / ``save_conf``
     - A :class:`~upref.ConfigStore` with an explicit directory and filename

The compatibility layer preserves v1 locations and descriptor shape; it is
not the recommended way to create a new v2 file. See :doc:`legacy_api` for its
complete reference.

Removal schedule
~~~~~~~~~~~~~~~~

The compatibility wrappers remain supported throughout all 2.x releases.
Their removal is scheduled for 3.0, and their warnings name that boundary.
There is no calendar release date for 3.0. Migrate callers and run application
tests with deprecation warnings enabled before adopting that major version.

This schedule covers the deprecated functions listed above, both at package
level and in ``upref.legacy``. Explicit file migration through
``ConfigStore.import_legacy`` is retained; removing the wrappers will not
require users to abandon old files before they can upgrade.
