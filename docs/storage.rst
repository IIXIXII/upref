.. _storage-guide:

Using ConfigStore
=================

:class:`~upref.ConfigStore` represents one YAML file. Constructing a store
validates and resolves its path, but does not create a directory or read the
file.

.. code-block:: python

   from upref import ConfigStore

   store = ConfigStore(
       "my-application",
       filename="config.yaml",
       app_author="Example Corp",
       roaming=False,
   )

The :attr:`~upref.ConfigStore.app_name`,
:attr:`~upref.ConfigStore.filename`, and :attr:`~upref.ConfigStore.path`
properties expose the resolved identity. See :doc:`paths` for platform and
portable locations.

Loading values
--------------

Call :meth:`~upref.ConfigStore.load` whenever the application needs a fresh
snapshot:

.. code-block:: python

   config = store.load()

A missing, zero-byte, whitespace-only, comment-only, or explicit YAML ``null``
document represents an empty mapping. Valid YAML is decoded as UTF-8 and
normalized to the :ref:`supported value model <config-values>`. Invalid YAML,
invalid UTF-8, a non-mapping root, and non-string keys are reported rather than
silently replaced.

Duplicate explicit mapping keys are rejected at every nesting level with
:exc:`~upref.ConfigFormatError`, including the filename, line, and column.
Correct the duplicate before retrying; the file is left untouched. YAML merge
directives (``<<``) remain supported: inherited defaults may be overridden by
explicit keys, and the first mapping in a merge sequence takes precedence.

Invalid YAML scalar values, such as an impossible calendar date, and excessive
nesting also raise :exc:`~upref.ConfigFormatError`. Quote date-like text when
you intend to store a string. YAML's implicit boolean resolution also applies:
quote keys such as ``"on"`` or ``"yes"`` so they remain string keys.

Using defaults
~~~~~~~~~~~~~~

Pass defaults when the application has values that need not be present in the
file:

.. code-block:: python

   config = store.load(
       defaults={
           "theme": "dark",
           "network": {"host": "localhost", "port": 8080},
       }
   )

Saved values override defaults according to the :ref:`recursive merge rules
<merge-semantics>`. Defaults are copied and never modified. Supplying defaults
does **not** write them; call ``store.save(config)`` if the fully resolved
mapping should become persistent.

Saving the complete mapping
---------------------------

:meth:`~upref.ConfigStore.save` validates the complete mapping and replaces
the complete YAML document:

.. code-block:: python

   config["theme"] = "light"
   store.save(config)

Validation and YAML serialization happen before the destination directory or
temporary file is created. Unsupported values therefore cannot damage an
existing configuration. A valid save attempt creates the parent directory as
needed before opening its temporary file; the directory can therefore remain
even if a later filesystem operation fails.

The document is written in UTF-8 with Unicode characters preserved and keys
kept in insertion order. YAML comments, anchors, aliases, quoting choices,
and custom formatting are not part of the configuration model and are not
preserved on save.

Applying selected changes
-------------------------

:meth:`~upref.ConfigStore.update` is a convenience read, recursive merge, and
save operation:

.. code-block:: python

   updated = store.update(
       {
           "network": {"port": 9000},
           "notifications": False,
       }
   )

The returned mapping is exactly the merged mapping that was saved. Existing
nested keys are retained, while lists and scalar values are replaced. If the
file does not exist, the normalized changes become its initial content.

``update`` does not accept defaults. Load and save explicitly when defaults
must participate in the persisted result:

.. code-block:: python

   config = store.load(defaults=application_defaults)
   config["theme"] = "light"
   store.save(config)

Existence and deletion
----------------------

:meth:`~upref.ConfigStore.exists` reports whether the resolved path currently
identifies a regular file. :meth:`~upref.ConfigStore.delete` deletes only that
file and returns ``True`` when a file was removed or ``False`` when it was
already absent:

.. code-block:: python

   if store.exists():
       removed = store.delete()

These are separate filesystem operations. Another process may change the
file between an ``exists`` check and a later load, save, or delete, so callers
should still handle the operation's documented exceptions.

.. _atomic-writes:

Atomicity and concurrent access
-------------------------------

Saving uses this sequence:

1. validate and serialize all data in memory;
2. create a uniquely named temporary file in the destination directory;
3. write UTF-8 YAML, flush Python and operating-system file buffers, and call
   ``fsync``;
4. on POSIX, set the temporary file mode to ``0600``;
5. atomically replace the destination with ``os.replace``;
6. attempt to remove any remaining temporary file after failure.

Because the temporary file is on the same filesystem, readers see either the
old complete document or the new complete document, not a partially written
one. If replacement fails, the previous file remains available. A uniquely
named temporary file can remain if both the primary operation and best-effort
cleanup fail; Upref never treats that file as configuration.

Upref deliberately provides no process or thread lock. The last successful
``os.replace`` wins. In particular, two simultaneous ``update`` calls can both
read the same old value and one can overwrite the other's changes.
Applications that need coordinated read-modify-write transactions must place
an appropriate lock around the whole operation.

Atomic replacement also does not turn YAML into a database: it provides file
integrity, not conflict detection, revision history, or multi-file
transactions.
