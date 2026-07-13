.. _paths-guide:

Configuration paths
===================

Upref resolves a store's absolute path during
:class:`~upref.ConfigStore` construction. The default directory comes from
``platformdirs.user_config_path`` and follows the current operating system's
conventions.

Typical default locations are:

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Platform
     - Typical path for ``ConfigStore("my-app")``
   * - Linux
     - ``$XDG_CONFIG_HOME/my-app/config.yaml`` or
       ``~/.config/my-app/config.yaml``
   * - macOS
     - ``~/Library/Application Support/my-app/config.yaml``
   * - Windows
     - ``%LOCALAPPDATA%\my-app\config.yaml``

The exact path can vary with the environment and ``platformdirs`` version;
:attr:`~upref.ConfigStore.path` is authoritative:

.. code-block:: python

   from upref import ConfigStore

   store = ConfigStore("my-app")
   print(store.path)

Application author and roaming data
-----------------------------------

``app_author`` is optional and mainly affects Windows directory layout. Upref
does not duplicate the application name as its author when it is omitted:

.. code-block:: python

   store = ConfigStore("my-app", app_author="Example Corp")

``roaming=True`` requests the platform's roaming configuration location. It
is relevant on Windows; other platforms may map it to their normal user
configuration location. The default is ``False``.

Custom filenames
----------------

``filename`` defaults to ``config.yaml``. It is a filename only, not a
relative path:

.. code-block:: python

   store = ConfigStore("my-app", filename="preferences.yaml")

Using a distinct filename can be useful for independent profiles, but each
file should have its own :class:`~upref.ConfigStore` instance.

.. _portable-mode:

Explicit directories and portable mode
--------------------------------------

Pass ``directory`` to bypass the platform location. The value must be an
absolute path and is the **final containing directory**; Upref does not append
``app_name`` to it:

.. code-block:: python

   from pathlib import Path
   from upref import ConfigStore

   portable_directory = Path(__file__).resolve().parent / "configuration"
   store = ConfigStore("my-app", directory=portable_directory)

This is also the recommended pattern for isolated tests:

.. code-block:: python

   def test_application_config(tmp_path):
       store = ConfigStore("my-app", directory=tmp_path)
       store.save({"enabled": True})
       assert store.load() == {"enabled": True}

The directory need not exist when the store is constructed. Construction and
loading do not create it; a valid save attempt creates it as needed. A
portable application must choose a directory that is writable on the target
machine; an installed application directory is often read-only.

Name validation and confinement
-------------------------------

``app_name``, ``app_author`` (when present), and ``filename`` must each be a
non-empty, safe, single path component. Upref rejects, among other cases:

* ``.`` and ``..``;
* forward and backward slashes;
* absolute or drive-qualified paths;
* leading or trailing whitespace and trailing dots;
* ASCII control characters and unsafe filename characters;
* Windows reserved device names such as ``NUL`` and ``COM1``.

This cross-platform validation keeps the same configuration identifiers safe
when an application moves between operating systems. The resolved file must
remain a direct child of its configuration directory; an existing symlink
that escapes the directory is rejected.

Invalid names, a relative explicit directory, and an unresolvable path raise
:exc:`~upref.ConfigPathError` before any file is created.
