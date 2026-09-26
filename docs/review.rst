Code review and compatibility notes
===================================

This review covers the configuration model, paths, YAML persistence, public
API, terminal and GUI collection, legacy migration, examples, and development
checks. The initial suite passed 171 tests with 100% statement coverage on
Windows; three platform-dependent checks were skipped. The findings below
illustrate why statement coverage alone does not establish behavioral coverage.

Findings addressed
------------------

.. list-table::
   :header-rows: 1
   :widths: 12 38 50

   * - Priority
     - Finding
     - Applied change
   * - High
     - Duplicate YAML keys silently discarded earlier values, including
       nested values in manually edited files.
     - A SafeLoader subclass rejects duplicate explicit keys with source
       locations. Merge directives retain inherited-default semantics.
   * - Medium
     - ``exists`` relied on ``Path.is_file``, which can suppress operating-system
       errors instead of fulfilling the documented error contract.
     - Explicit ``stat`` checks distinguish absent files and directories from
       inspection failures reported as ``ConfigReadError``.
   * - Medium
     - Invalid YAML scalar construction could report a format problem as a
       read error; deep trees could leak ``RecursionError``.
     - Scalar, normalization, and serialization recursion failures are converted
       to ``ConfigFormatError``;
       read failures and invalid UTF-8 retain their specific diagnostics.
   * - Medium
     - Invalid Field options and non-callable custom prompter methods failed
       late, potentially after an interface had opened.
     - Runtime checks reject invalid options, schemas, and protocol results
       with clear ``TypeError`` messages.
   * - Medium
     - GUI prefill used Python string representations that may be invalid input
       for the configured parser (for example JSON lists with booleans).
     - Keyword-only ``Field.formatter`` pairs display/prefill with the parser.
       Secret values are neither formatted nor prefilled.
   * - Usability
     - Terminal editing required retyping existing values; required/optional
       status and cancellation instructions were implicit.
     - Opt-in Enter-to-keep behavior reparses and validates the retained value.
       Prompts now explain input status and cancellation.
   * - Usability
     - Boolean text parsing was duplicated in an example and easy to misuse
       with Python's ``bool`` constructor.
     - Public ``parse_bool`` accepts explicit boolean spellings and retries
       invalid text through the collection API.
   * - Documentation
     - Advanced UI integration, application validation, schema upgrades, and
       example file effects were not demonstrated together.
     - Nine runnable examples, a difficulty/effects catalog, practical recipes,
       troubleshooting, and regression checks for examples were added.
   * - Tooling
     - Windows checkout line endings could conflict with Ruff's configured LF
       formatting, producing repeated formatting changes.
     - Git attributes now enforce LF for Python files; Windows command scripts
       retain CRLF.

Additional packaging finding
----------------------------

The source archive contained tests but omitted the example and maintenance
script files needed by those tests, as well as documentation sources. An
explicit manifest now includes examples, documentation, scripts, and pytest
configuration while excluding generated HTML. CI checks the archive contents.

Compatibility
-------------

Existing valid store calls and the positional Field constructor arguments
remain supported. ``formatter`` and terminal ``keep_current`` are optional;
blank terminal input keeps its existing meaning by default. Terminal and GUI
presentation text now includes required/optional hints.

Files containing duplicate explicit keys now fail instead of choosing the last
value. Resolve duplicates before loading such files. YAML merge-based defaults
and explicit overrides still work. Invalid Field definitions now fail at
construction; custom prompters must provide callable methods and return text
or ``None``. No package version or legacy migration heuristic was changed.

Validation and limits
---------------------

Regression tests exercise duplicates (including merges and aliases), malformed
scalars, nesting errors, filesystem inspection failures, parser/formatter
integration, value reuse, secret suppression, and runnable examples. Project
checks include strict mypy, Ruff, Sphinx warnings as errors, and the existing
100% statement coverage gate. See :doc:`development` for reproducible commands.

The local environment is Windows with Python 3.14. GUI contracts are verified
using a wxPython substitute; wxPython is not installed locally, so real dialog
rendering was not exercised. Symlink creation and POSIX permission checks
require suitable platforms or privileges. The repository CI matrix provides
Linux, macOS, and supported Python-version checks; those remote jobs were not
run by this local review.

Existing documented boundaries remain: no cross-process locking, no resource
budget for hostile YAML, and no secret encryption. The legacy descriptor
heuristic can be ambiguous for raw mappings that resemble descriptors. These
constraints are described in :doc:`security`, :doc:`storage`, and
:doc:`migration`; addressing them requires separate API and compatibility
decisions.

Follow-up hardening
-------------------

The subsequent implementation adds explicit migration format selection and
dry-run previews while preserving the default heuristic. Invalid scalar-tagged
YAML keys now report format errors, null characters in directories are rejected
at construction, and string subclass keys are normalized to ordinary strings.

Generated round-trip tests found that PyYAML folds Unicode NEL (U+0085) into a
space when emitted literally. Upref's safe dumper now escapes that character
in keys and values while retaining readable ordinary Unicode. Temporary-file
cleanup is registered when the file is created and runs after the stream closes,
including on write, flush, permission, and replacement failures.

The local Windows/Python 3.14 suite passes 267 tests with 100% statement and
branch coverage. Three platform-dependent checks and the two opt-in native GUI
scenarios are skipped by the ordinary command. The two native scenarios were
also run separately with wxPython 4.3.1 and passed, exercising both owned and
borrowed applications with real dialogs.

CI now includes native GUI and minimum-runtime-dependency jobs. CI and release
automation check installed-wheel resources and persistence in isolated mode.
The 2.x/3.0 wrapper removal schedule is documented in :doc:`migration`;
criteria for adding locking or resource budgets are in :doc:`security`.
