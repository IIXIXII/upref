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
* the returned mapping is the mapping written to the destination.

Descriptor detection is necessarily structural because v1 files carry no
format version. Upref treats a document as descriptors when every
non-metadata top-level value is a mapping containing at least one of
``label``, ``description``, ``type``, or ``value``, and at least one field has
a ``value`` member. A raw configuration with that same shape is ambiguous and
may be converted. For such data, load and transform it explicitly before
calling :meth:`~upref.ConfigStore.save`.

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
