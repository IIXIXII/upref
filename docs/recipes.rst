Practical recipes
=================

These programs complement the persistent examples in :doc:`examples`. Run
them from an installed checkout with ``python examples/<name>.py``. All files
created by the recipes below use automatically cleaned temporary directories;
the interactive collection examples otherwise work entirely in memory.

For first-run setup, Apply/Cancel, resets, recent documents, window geometry,
account preferences, session overrides, and preference transfer, see the ten
additional walkthroughs in :doc:`user_preferences`.

A first store without persistent files
--------------------------------------

The result contains port ``9000`` while the original snapshot retains ``8080``.
The exact temporary path differs each run.

.. literalinclude:: ../examples/portable_store.py
   :language: python

Boolean and optional input
--------------------------

Try ``maybe`` and then ``no``: the first answer triggers a retry and the
second produces ``False``. Enter submits an empty optional note. Ctrl+C
cancels collection.

.. literalinclude:: ../examples/boolean_collection.py
   :language: python

Editing current values in a terminal
------------------------------------

Press Enter twice to retain the existing values. Supply ``[]`` to replace the
list with an empty list. Custom formatters keep the displayed text compatible
with the parser. Parser and validator failures are retried.

.. literalinclude:: ../examples/edit_settings.py
   :language: python

Graphical collection
--------------------

Install ``upref[gui]`` first. This example uses the context manager to close
only the GUI resources it owns. It also reports an unavailable GUI without a
traceback. Existing JSON values are prefilled in valid JSON syntax.

.. literalinclude:: ../examples/gui_collection.py
   :language: python

Editing a nested section
------------------------

Schemas describe top-level keys, so collect a section and then put it back
into the complete mapping. Saving happens only after every prompt succeeds;
cancellation leaves the stored data untouched. The unrelated theme remains.

.. literalinclude:: ../examples/nested_collection.py
   :language: python

A custom interface without a terminal
-------------------------------------

This deterministic prompter can also serve as a starting point for application
tests. It implements the two public protocol methods and cancels when answers
run out. The example returns ``{'enabled': False, 'retries': 3}`` and records
one recoverable error. It never logs raw input or current secret values.

.. literalinclude:: ../examples/custom_interface.py
   :language: python

Application constraints and typed settings
------------------------------------------

Upref validates representability; the application validates its business
rules. This recipe checks loaded values even when no interactive fields are
missing. It rejects a boolean used as a port, despite Python's ``bool`` being
a subclass of ``int``. Dataclasses must be converted to plain mappings before
saving. Unknown keys are intentionally omitted by this fixed application
model; preserve the raw mapping if your application needs extension keys.

.. literalinclude:: ../examples/typed_settings.py
   :language: python

Versioning an application's configuration
-----------------------------------------

This is independent of Upref's v1 import. An application-owned schema version
controls an idempotent transformation. It preserves unrelated keys, rejects
future versions and ambiguous input, and leaves the original mapping intact.
Coordinate production migrations with other writers and keep a backup when
rollback is required; a save is atomic but not a transaction with other files.

.. literalinclude:: ../examples/schema_upgrade.py
   :language: python

Recovering from malformed YAML
------------------------------

A missing file may use defaults. A malformed existing file needs an explicit
repair decision. This example reports a duplicate key with its source location
and confirms the original bytes are still available.

.. literalinclude:: ../examples/handle_errors.py
   :language: python
