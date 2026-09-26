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
     - Build the source distribution and wheel, then validate their metadata.
   * - ``.\make.bat clean``
     - Remove generated builds and caches without deleting ``.venv``.

Equivalent tools can be run directly through the environment interpreter:

.. code-block:: console

   .\.venv\Scripts\python.exe -m pytest --basetemp=.pytest_tmp
   .\.venv\Scripts\python.exe -m ruff format --check upref tests examples scripts docs\conf.py
   .\.venv\Scripts\python.exe -m ruff check upref tests examples scripts docs\conf.py
   .\.venv\Scripts\python.exe -m mypy upref examples
   .\.venv\Scripts\python.exe -m sphinx -E -a -W --keep-going -b html docs docs\_build\html

Continuous integration measures statement and branch coverage and requires
100 percent. Reproduce that gate locally with:

.. code-block:: console

   .\.venv\Scripts\python.exe -m pytest --cov=upref --cov-report=term-missing

Behavioral checks matter in addition to coverage. ``test_properties.py`` uses
Hypothesis to generate nested configurations and verify YAML round trips,
independence of mutable containers, merge identities, and preservation of the
original file after a failed replacement. NaN is excluded from equality-based
properties because it does not compare equal to itself.

``test_examples.py``
runs storage and advanced recipes in isolated directories, supplies deterministic
terminal answers, and verifies cancellation without saving. Tests for GUI
arguments and lifecycle use a wxPython substitute and do not require a display.
Native GUI integration tests run in a dedicated Windows CI job. Each scenario
uses a separate process with a 40-second timeout and drives real modal dialogs
through wx's event loop. They check app ownership, repeated dialogs, formatted
prefill, cancellation, password controls, and cleanup after an injected error.
They are skipped in the ordinary suite. Run them in a desktop session with:

.. code-block:: powershell

   .\.venv\Scripts\python.exe -m pip install -e '.[test,gui]'
   $env:UPREF_RUN_GUI_TESTS = '1'
   .\.venv\Scripts\python.exe -m pytest tests/integration -q --no-cov
   Remove-Item Env:UPREF_RUN_GUI_TESTS

The dedicated run disables coverage because the complete coverage gate belongs
to the ordinary unit suite. Missing wxPython is an error when native tests are
explicitly enabled. Visual layout can additionally be inspected with
``examples/gui_collection.py``.

CI also runs the ordinary suite on Python 3.10 with ``platformdirs==4.0.0`` and
``PyYAML==6.0`` to check the advertised minimum runtime dependencies. The wheel
job and release workflow invoke ``scripts/check_installed_package.py`` using
Python's isolated mode in a clean environment: it checks packaged resources
and the save/load/update/delete cycle without importing the checkout.

Documentation workflow
----------------------

The source distribution includes documentation, examples, and test support
files through ``MANIFEST.in``. Generated HTML is excluded. The packaging job
checks archive contents so tests and examples remain usable outside Git.

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
