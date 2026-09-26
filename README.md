# Upref

[![PyPI version](https://img.shields.io/pypi/v/upref)](https://pypi.org/project/upref/)
[![Python versions](https://img.shields.io/pypi/pyversions/upref)](https://pypi.org/project/upref/)
[![CI](https://github.com/IIXIXII/upref/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/IIXIXII/upref/actions/workflows/ci.yml)
[![CodeQL](https://github.com/IIXIXII/upref/actions/workflows/codeql.yml/badge.svg?branch=master)](https://github.com/IIXIXII/upref/actions/workflows/codeql.yml)
[![Documentation status](https://readthedocs.org/projects/upref/badge/?version=stable)](https://upref.readthedocs.io/en/stable/)
[![License: MIT](https://img.shields.io/pypi/l/upref)](https://github.com/IIXIXII/upref/blob/master/LICENSE.md)

Upref is a small Python library for storing an application's per-user
configuration in a YAML file. Its v2 API keeps persistence explicit: loading
configuration never opens a prompt, and collecting interactive values never
writes them automatically.

Upref supports Python 3.10 and later. It is typed, uses platform-native user
configuration directories, validates the complete value tree, and replaces
files atomically.

Read the [documentation on Read the Docs](https://upref.readthedocs.io/en/stable/)
for the user guide, practical examples, and complete API reference.

## Installation

Install the core package, including the dependency-free terminal interface:

```console
pip install upref
```

The wxPython graphical interface is optional:

```console
pip install "upref[gui]"
```

Importing `upref` does not import wxPython or open an interface.

## Quickstart

Create one store for one application configuration:

```python
from upref import ConfigStore

store = ConfigStore("my-application")

config = store.load(
    defaults={
        "theme": "dark",
        "network": {"host": "localhost", "port": 8080},
    }
)

store.save(config)
store.update({"network": {"port": 9000}})

print(store.load())
print(f"Configuration file: {store.path}")
```

`load()` returns an empty dictionary when the file is absent, empty, or an
explicit YAML `null`. Saved values recursively override `defaults`, but
loading defaults does not write them. `save()` validates and persists the
entire mapping.

To merge and persist only selected changes, use `update()`:

```python
config = store.update({
    "network": {"port": 9001},
    "notifications": False,
})
```

Nested dictionaries are merged. Lists and scalar values are replaced.
Duplicate explicit YAML keys are rejected with a file location instead of
silently discarding earlier values. YAML merge directives may still provide
defaults that explicit keys override.
`store.exists()` checks for the file, while `store.delete()` removes only that
file and reports whether it existed.

## Configuration values

The document root must be a mapping with string keys. Values may be `None`,
booleans, integers, floats, strings, lists, or nested mappings with string
keys. `False`, `0`, empty strings, and empty lists are valid values. Custom
objects such as `Path` and `datetime` must be converted before saving.

Every operation that accepts or returns configuration data works with a
detached tree: mutating the result of `load()` does not mutate defaults,
earlier results, or caller-owned input.

## Paths and portable mode

Without an explicit directory, Upref uses the current platform's per-user
configuration location through `platformdirs`:

```python
store = ConfigStore(
    "my-application",
    filename="settings.yaml",
    app_author="Example Corp",
)
```

For tests or portable applications, pass an absolute final directory. Upref
does not append the application name to this override:

```python
from pathlib import Path

portable_directory = Path.cwd().resolve() / "configuration"
store = ConfigStore(
    "my-application",
    directory=portable_directory,
)
```

Constructing or loading the store does not create the directory; `save()`
creates it as needed. Application names, authors, and filenames must be safe
single path components.

## Interactive collection

Interactive collection is separate from storage and uses the terminal by
default:

```python
from upref import ConfigStore, Field, PromptCancelled, collect

store = ConfigStore("my-application")
schema = {
    "service_url": Field("Service URL"),
    "timeout": Field(
        "Timeout in seconds",
        parser=int,
        validator=lambda value: isinstance(value, int) and value > 0,
    ),
}

try:
    values = collect(
        schema,
        initial=store.load(),
        interface="tty",
        mode="missing",
    )
except PromptCancelled:
    print("Configuration unchanged")
else:
    store.save(values)
```

In `missing` mode, absent values, `None`, and required empty strings are
requested. `False` and `0` already count as values. Use `mode="all"` to ask
for every field, or `interface="gui"` after installing `upref[gui]`.

For boolean input, use the public `parse_bool` parser; it accepts `yes/no`,
`true/false`, `on/off`, `y/n`, and `1/0`, ignoring case and whitespace.
Python's `bool("false")` returns `True` and is unsuitable for this purpose.

```python
from upref import Field, collect, parse_bool
from upref.tty import TTYPrompter

values = collect(
    {"enabled": Field("Enable notifications", parser=parse_bool)},
    initial={"enabled": False},
    interface=TTYPrompter(keep_current=True),
    mode="all",
)
```

With `keep_current=True`, Enter reuses a current non-secret value and runs it
through the parser and validator again. By default, blank input remains blank.
For structured input, pair a parser with a compatible keyword-only formatter:
`Field("Tags", parser=json.loads, formatter=json.dumps)` (after `import json`).
The GUI uses this formatter to prefill existing values correctly.

`collect` validates newly entered values. Existing values skipped in `missing`
mode are not passed through field validators; validate application constraints
after loading when stored files may have been edited manually.

## Storage guarantees and limits

Upref writes UTF-8 YAML to a temporary file in the destination directory,
flushes it, and replaces the destination with `os.replace()`. Invalid data is
rejected before the existing file is touched. On POSIX systems, newly written
files receive mode `0600`.

Saving rewrites the YAML document, so comments, anchors, and custom formatting
are not preserved. Concurrent writers cannot produce a partial YAML file, but
there is no locking: the last successful atomic replacement wins, and
simultaneous read-modify-write operations can lose updates.

## Migrating from v1

The v1 API remains available during the v2 transition and emits
`DeprecationWarning`. Import an existing v1 file explicitly:

```python
from upref import ConfigStore

store = ConfigStore("my-application")
config = store.import_legacy("my_personnal_data")
```

For ambiguous files, choose ``source_format="raw"`` to retain the entire
mapping, or ``source_format="descriptors"`` to extract v1 values explicitly.
Add ``dry_run=True`` to inspect the conversion without writing. Previewing
still performs source and target preflight checks. The default ``"auto"``
format retains the historical heuristic.

The source file is left untouched, and using it as the v2 target is rejected.
Migration checks for an existing v2 file unless `overwrite=True` is passed;
because this preflight check is not locked, applications with concurrent
writers must coordinate the migration externally.
Deprecated v1 wrappers remain available throughout 2.x and are scheduled for
removal in 3.0; explicit file migration remains supported.

## Security

An Upref YAML file is **not a secret vault**. `Field(secret=True)` asks the
built-in interfaces for protected input presentation, subject to terminal
support; a custom interface must honor that hint itself. Any saved value
remains plain text. Keep passwords, tokens, and private keys in the
operating-system keyring or a dedicated secrets manager, and store only a
reference in Upref.

## Documentation and examples

The complete user guide and API reference are available on
[Read the Docs](https://upref.readthedocs.io/en/stable/). The
[example catalog](docs/examples.rst) lists 26 runnable programs by difficulty,
input method, and file effects. Start with these:

| Level | Example | What it demonstrates |
| --- | --- | --- |
| Simple | `portable_store.py` | Defaults, save/load, and updates in a temporary directory |
| Simple | `boolean_collection.py` | Boolean parsing, optional input, and cancellation |
| Simple | `first_run_preferences.py` | Initial user setup and reuse on the next startup |
| Intermediate | `apply_preferences.py` | Edit a draft, then confirm or discard changes |
| Intermediate | `reset_preferences.py` | Restore one preference, a section, or all defaults |
| Intermediate | `session_overrides.py` | CLI overrides with explicit `--remember` persistence |
| Advanced | `import_export_preferences.py` | Validated preference transfer with local history retained |
| Intermediate | `edit_settings.py` | Enter to keep values and editable JSON lists |
| Intermediate | `gui_collection.py` | GUI ownership, formatted prefill, and cancellation |
| Intermediate | `handle_errors.py` | Reporting malformed YAML while retaining the file |
| Advanced | `nested_collection.py` | Editing a subsection before an explicit save |
| Advanced | `custom_interface.py` | A deterministic custom prompter with validation retries |
| Advanced | `typed_settings.py` | Application validation with a dataclass |
| Advanced | `schema_upgrade.py` | An idempotent application schema migration |

The new demonstrations use memory or automatically cleaned temporary
directories. Earlier examples that demonstrate persistent settings use named
per-user directories; their effects are listed in the catalog. Run examples
from an installed checkout (`python -m pip install -e .`):

```console
python examples/portable_store.py
python examples/custom_interface.py
```

The [user preference walkthroughs](docs/user_preferences.rst) also cover recent
documents, window geometry, multiple accounts, backup/restore, and previewing
legacy migration. Every scenario in that guide uses temporary files.

See also the [troubleshooting guide](docs/troubleshooting.rst) and the
[code review and compatibility notes](docs/review.rst).

## Development with `.venv`

On Windows, create or update the repository-local environment with:

```console
.\make.bat setup
```

All project commands call `.venv\Scripts\python.exe` directly, so activation
is optional:

```console
.\make.bat test
.\make.bat check
.\make.bat docs
.\make.bat build
```

Activate it in an interactive PowerShell session when convenient:

```powershell
.\.venv\Scripts\Activate.ps1
```

If automatic Python discovery fails while creating the environment, use
`.\make.bat setup -Python "C:\path\to\python.exe"`. An existing `.venv`
always keeps its current interpreter; remove and recreate it deliberately to
change Python. The `.venv` directory is machine-specific and ignored by Git.
`make.bat clean` removes generated artifacts without deleting it.

## License

Upref is distributed under the
[MIT license](https://github.com/IIXIXII/upref/blob/master/LICENSE.md).
