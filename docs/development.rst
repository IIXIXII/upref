.. _development:

Development environment
=======================

The repository uses a local ``.venv`` for tests, linting, typing,
documentation, and package builds. The environment is machine-specific and
is ignored by Git.

Windows setup
-------------

From the repository root, create or update the environment with:

.. code-block:: console

   .\make.bat setup

The bootstrap script creates ``.venv`` with an available Python 3.10 or later,
upgrades pip, installs ``.[dev]`` in editable mode, and checks the installed
dependency set.

Select a bootstrap interpreter explicitly when automatic discovery is not
appropriate during initial creation:

.. code-block:: console

   .\make.bat setup -Python "C:\path\to\python.exe"

An existing ``.venv`` is always reused with its current interpreter, even when
``-Python`` is supplied. To change Python, deliberately remove and recreate
the environment first; ``make.bat clean`` never removes it.

The commands invoke ``.venv\Scripts\python.exe`` directly, so activation is
optional. For an interactive PowerShell session:

.. code-block:: powershell

   .\.venv\Scripts\Activate.ps1

POSIX setup
-----------

The Windows helpers are convenience wrappers. On Linux and macOS, create the
same environment directly:

.. code-block:: console

   python3 -m venv .venv
   ./.venv/bin/python -m pip install --upgrade pip
   ./.venv/bin/python -m pip install -e '.[dev]'

Project checks
--------------

The main Windows entry points are:

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Command
     - Action
   * - ``.\make.bat test``
     - Run the pytest suite in an isolated temporary directory.
   * - ``.\make.bat check``
     - Check Ruff formatting and linting, then run mypy in strict mode.
   * - ``.\make.bat docs``
     - Build this Sphinx site with warnings treated as errors.
   * - ``.\make.bat build``
     - Build the source distribution and wheel.
   * - ``.\make.bat clean``
     - Remove generated builds and caches without deleting ``.venv``.

Equivalent tools can be run directly through the environment interpreter:

.. code-block:: console

   .\.venv\Scripts\python.exe -m pytest --basetemp=.pytest_tmp
   .\.venv\Scripts\python.exe -m ruff format --check upref tests examples scripts docs\conf.py
   .\.venv\Scripts\python.exe -m ruff check upref tests examples scripts docs\conf.py
   .\.venv\Scripts\python.exe -m mypy upref examples
   .\.venv\Scripts\python.exe -m sphinx -E -a -W --keep-going -b html docs docs\_build\html

Documentation workflow
----------------------

User guides live in ``docs/*.rst``. ``docs/readme_link.md`` includes the root
README through MyST, keeping installation and quickstart content in one
source. API pages use autodoc, so public docstrings must remain meaningful on
their own and all public objects should be reachable from the navigation.

Before submitting documentation changes, run ``.\make.bat docs``. A clean
build must have no missing references, duplicate targets, malformed markup,
or undocumented pages.

Ruff enforces Google-style docstrings on package, example, and maintenance
code. The test suite also checks every Python module, class, method, and
function in ``upref`` and ``scripts`` for a non-empty docstring, including
private helpers.

License header maintenance
--------------------------

``scripts/add_license_headers.py`` scans supported text files and reports
missing MIT headers without changing files by default:

.. code-block:: console

   .\.venv\Scripts\python.exe scripts\add_license_headers.py --root .

Review that dry-run output before adding ``--write``. Write mode edits files
directly without locking or atomic replacement, so keep the tree in version
control and avoid concurrent edits. Use ``--verbose`` to show every inspected
file. By default the scanner skips ``.git``, ``.venv``, ``.eggs``,
``__pycache__``, ``node_modules``, ``dist``, ``build``, ``.mypy_cache``,
``.pytest_cache``, ``.ruff_cache``, and ``tests``. ``--include-hidden``
disables that exclusion list. Symbolic-link files are never modified.
