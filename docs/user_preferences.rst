User preference scenarios
==========================

These ten programs cover the lifecycle of preferences in a desktop or terminal
application. They use only Upref and the Python standard library. Run them
from an installed checkout, for example:

.. code-block:: console

   python examples/first_run_preferences.py
   python examples/reset_preferences.py

On Windows, ``.\.venv\Scripts\python.exe`` can replace ``python`` without
activating the environment. Every file in these scenarios is temporary and
removed on exit, so each invocation begins with fresh demonstration data.
To adapt a recipe to real preferences, create ``ConfigStore("your-app")``
without a temporary ``directory`` override and remove the demo's seed data.

First-run setup
----------------

``first_run_preferences.py`` asks for theme, language, font size, and
notifications using :class:`~upref.Field`. Parsers and validators reject invalid
choices and out-of-range sizes. Press Enter four times to accept the defaults,
or try ``purple`` as the theme and ``9`` as the font size to see retries.

File presence marks completed setup in this recipe. No file is written if
collection is cancelled. A second startup is simulated in the same process and
reuses the saved preferences without asking again. Existing values are not
business-validated on that path; see ``typed_settings.py`` when manually edited
preferences need validation on every startup.

.. literalinclude:: ../examples/first_run_preferences.py
   :language: python

Editing and applying a draft
-----------------------------

``apply_preferences.py`` starts with saved preferences and edits a detached
draft. The final yes/no prompt defaults to ``False``: Enter discards the draft,
``yes`` saves it, and Ctrl+C cancels the interaction. A language preference
outside the editing schema survives a successful save.

For example, enter ``dark``, ``20``, and ``yes`` to apply changes. Repeat with
``no`` to observe the unchanged saved preferences. A load/edit/save interaction
assumes one writer; applications with simultaneous writers must coordinate the
whole operation as described in :doc:`storage`.

.. literalinclude:: ../examples/apply_preferences.py
   :language: python

Resetting preferences
-----------------------

``reset_preferences.py`` removes a saved font-size override, then the entire
appearance section, then the configuration file. The intermediate output shows
that notifications remain disabled while appearance returns to defaults.

Load the raw saved mapping when removing overrides. Loading with defaults and
saving that result would persist those default values. Likewise,
``update({"appearance": {}})`` does not clear a section because mappings merge
recursively. Remove the key from the loaded mapping and save explicitly.

.. literalinclude:: ../examples/reset_preferences.py
   :language: python

Recent documents
------------------

``recent_files.py`` normalizes paths, moves reopened documents to the front,
and limits the history to two entries in the demonstration. The result is
``['notes.txt', 'draft.md']``; the separate theme preference remains ``dark``.
No document is opened or created. Existing history entries are assumed to have
been normalized by this application; malformed lists are rejected before saving.

.. literalinclude:: ../examples/recent_files.py
   :language: python

Window position and size
--------------------------

``window_preferences.py`` restores a window saved on a larger monitor into a
1280 by 720 display. Invalid value types fall back to defaults; bounds are
clamped so the restored window is visible. The example does not open a window.

The geometry model uses the primary display's usable rectangle with origin
``(0, 0)``. For multiple monitors, obtain the actual work areas and offsets from
the GUI toolkit. Persist normal window bounds when closing, together with a
separate maximized flag; minimized bounds are not useful restoration data.

.. literalinclude:: ../examples/window_preferences.py
   :language: python

Several accounts in one application
------------------------------------

``account_preferences.py`` stores work and personal settings under separate
account keys. Updating the work theme preserves the personal account. Unknown
accounts receive defaults, and signing out removes the active selection while
retaining the saved preferences.

Account IDs are mapping keys, not filenames or credentials. These are accounts
inside the same OS user's application, not an access-control boundary between
different OS users. The recipe uses flat account preferences; nested defaults
would need an explicit recursive merge strategy.

.. literalinclude:: ../examples/account_preferences.py
   :language: python

Preferences for the current session
------------------------------------

``session_overrides.py`` makes precedence explicit: application defaults,
saved preferences, then command-line options. Try:

.. code-block:: console

   python examples/session_overrides.py --theme dark --font-size 20
   python examples/session_overrides.py --theme dark --remember

The first command prints a dark session while saved preferences remain light.
The second persists only the supplied theme override. It does not write every
application default. Both commands operate inside a temporary demo directory,
so ``--remember`` does not affect a later invocation of this example.

.. literalinclude:: ../examples/session_overrides.py
   :language: python

Importing and exporting portable preferences
---------------------------------------------

``import_export_preferences.py`` exports only theme, language, and font size
to JSON. Machine-local document history is excluded. Import rejects unknown
keys, invalid values, duplicate keys, and malformed JSON before the application
chooses to apply the preview. Boolean font sizes are rejected explicitly.

The demonstration transfers preferences between two stores while preserving
``['target-only.txt']`` as the target's local history. This is a small, local
file exchange example; its JSON export uses an ordinary file write. Configuration
persistence through ``ConfigStore`` continues to use atomic replacement.

.. literalinclude:: ../examples/import_export_preferences.py
   :language: python

Backing up and restoring settings
----------------------------------

``backup_restore.py`` saves a value snapshot in a separate configuration file,
changes preferences, then restores the snapshot. A missing or malformed backup
raises before the current file is replaced. The backup itself remains unchanged.

The snapshot preserves values rather than YAML comments or formatting. This
single-writer recipe does not provide backup rotation or a transaction across
the two files. Coordinate other writers when using it in a shared application.

.. literalinclude:: ../examples/backup_restore.py
   :language: python

Previewing a legacy migration
------------------------------

``migration_preview.py`` creates a temporary legacy file with a reminder value
and its unit. Automatic descriptor detection extracts the value but drops the
unit. ``source_format="raw"`` preserves both.

Both previews use ``dry_run=True`` and create no destination directory. The
example then explicitly applies the raw conversion and verifies that the old
file is unchanged. For migration of an actual v1 file, see ``migrate_v1.py``
and :doc:`migration`.

.. literalinclude:: ../examples/migration_preview.py
   :language: python
