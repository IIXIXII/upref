# Upref

Upref is a small Python library for storing an application's per-user
configuration in a YAML file. Its v2 API keeps persistence explicit: loading
configuration never opens a prompt, and collecting interactive values never
writes them automatically.

Upref supports Python 3.10 and later. It is typed, uses platform-native user
configuration directories, validates the complete value tree, and replaces
files atomically.

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

The source file is left untouched, and using it as the v2 target is rejected.
Migration checks for an existing v2 file unless `overwrite=True` is passed;
because this preflight check is not locked, applications with concurrent
writers must coordinate the migration externally.

## Security

An Upref YAML file is **not a secret vault**. `Field(secret=True)` asks the
built-in interfaces for protected input presentation, subject to terminal
support; a custom interface must honor that hint itself. Any saved value
remains plain text. Keep passwords, tokens, and private keys in the
operating-system keyring or a dedicated secrets manager, and store only a
reference in Upref.

## Documentation and examples

The complete user guide and API reference are available on
[Read the Docs](https://upref.readthedocs.io/). Runnable examples live in
[`examples`](https://github.com/IIXIXII/upref/tree/master/examples):

- `basic_store.py` covers a save/load cycle;
- `defaults_and_update.py` covers defaults, recursive updates, and deletion;
- `project_variables.py` collects required variables for one project;
- `environment_profiles.py` selects profiles with temporary environment overrides;
- `multiple_projects.py` stores independent settings for related projects;
- `tty_collection.py` collects missing values without a GUI;
- `migrate_v1.py` imports a historical configuration.

Except for the migration example, these programs use the platform's per-user
configuration directory. They do not create files in the repository.

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
