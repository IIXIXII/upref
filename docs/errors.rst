.. _error-handling:

Error handling
==============

All domain-specific exceptions declared by Upref inherit
:exc:`~upref.UprefError`. Applications can catch the base class at a boundary
or catch a specific error where recovery differs. Standard exceptions used
for programmer errors are listed separately below.

Exception hierarchy
-------------------

.. code-block:: text

   UprefError
   |-- ConfigPathError (also ValueError)
   |-- ConfigFormatError
   |-- ConfigReadError
   |-- ConfigWriteError
   |-- MigrationError
   |-- PromptCancelled
   `-- PromptUnavailableError

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Exception
     - Typical cause
   * - :exc:`~upref.ConfigPathError`
     - An unsafe application name or filename, a relative explicit directory,
       or a path that escapes its directory.
   * - :exc:`~upref.ConfigFormatError`
     - Invalid YAML or UTF-8, duplicate explicit keys, excessive nesting,
       a non-mapping root, a non-string key, a cyclic value, or an unsupported
       Python value.
   * - :exc:`~upref.ConfigReadError`
     - A filesystem error while opening or reading configuration.
   * - :exc:`~upref.ConfigWriteError`
     - A filesystem error while creating, replacing, or deleting a file.
   * - :exc:`~upref.MigrationError`
     - A missing legacy file, identical source and target, an existing target
       without ``overwrite=True``, or a failure while saving migrated data.
   * - :exc:`~upref.PromptCancelled`
     - The user cancelled, interrupted, or ended an interactive prompt.
   * - :exc:`~upref.PromptUnavailableError`
     - The requested GUI dependency is absent or cannot initialize.

Malformed YAML errors include the path and, when PyYAML provides it, the line
and column. Read and write messages also include the relevant path. The
original Python, operating-system, or YAML exception is preserved as the
exception cause.

Recovering by operation
-----------------------

A typical application distinguishes a missing file—which ``load`` handles as
an empty mapping—from a present but invalid file, which should be reported and
left untouched:

.. code-block:: python

   from upref import (
       ConfigFormatError,
       ConfigReadError,
       ConfigStore,
       ConfigWriteError,
   )

   store = ConfigStore("my-app")

   try:
       config = store.load(defaults={"theme": "dark"})
   except ConfigFormatError as error:
       # Ask the user to repair or deliberately replace the malformed file.
       print(f"Invalid configuration: {error}")
   except ConfigReadError as error:
       print(f"Cannot read configuration: {error}")
   else:
       try:
           store.save(config)
       except ConfigWriteError as error:
           print(f"Cannot save configuration: {error}")

Do not automatically overwrite malformed configuration unless that is an
explicit application policy. The invalid file may contain recoverable user
data.

Programmer errors
-----------------

Some API misuse raises standard exceptions rather than an ``UprefError``:

* an unknown collection mode or string interface raises :class:`ValueError`;
* a non-string schema key, a schema value that is not :class:`~upref.Field`,
  or an object that does not implement :class:`~upref.Prompter` raises
  :class:`TypeError`;
* an invalid field option, a non-mapping schema, non-callable prompter methods,
  or an ``ask`` result other than a string or ``None`` raises :class:`TypeError`;
* a parser or validator :class:`ValueError` is treated as correctable input
  and causes another prompt;
* asking through or reporting an error with a closed
  :class:`upref.gui.GuiPrompter` raises :class:`RuntimeError`;
* unexpected exceptions from application parsers, validators, or custom
  prompters propagate unchanged.

Catch exceptions only at a level that can make a meaningful recovery choice.
In particular, catching :exc:`~upref.UprefError` around an entire
application may hide whether user input, file content, or filesystem access
needs attention.
