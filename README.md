# Upref

[![PyPI version](https://img.shields.io/pypi/v/upref)](https://pypi.org/project/upref/)
[![Python versions](https://img.shields.io/pypi/pyversions/upref)](https://pypi.org/project/upref/)
[![CI](https://github.com/IIXIXII/upref/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/IIXIXII/upref/actions/workflows/ci.yml)
[![CodeQL](https://github.com/IIXIXII/upref/actions/workflows/codeql.yml/badge.svg?branch=master)](https://github.com/IIXIXII/upref/actions/workflows/codeql.yml)
[![Documentation status](https://readthedocs.org/projects/upref/badge/?version=stable)](https://upref.readthedocs.io/en/stable/)
[![License: MIT](https://img.shields.io/pypi/l/upref)](https://github.com/IIXIXII/upref/blob/master/LICENSE.md)

**Small, explicit user preferences for Python applications.**

Upref stores per-user configuration in YAML for desktop applications, CLI tools,
and scripts. Load and save preferences through a typed API, then optionally
collect values through terminal prompts or wxPython dialogs. Your application
decides when to ask and when to write.

[Documentation](https://upref.readthedocs.io/en/stable/) ·
[Installation](#installation) · [Quickstart](#quickstart) ·
[Examples](#examples) · [Contributing](#contributing) ·
[Changelog](https://github.com/IIXIXII/upref/blob/master/CHANGELOG.md)

## Why Upref?

- **User-specific storage:** configuration directories follow Windows, macOS,
  and Linux conventions; an explicit directory enables portable mode.
- **Explicit persistence:** loading defaults and collecting input do not write
  files. `save()` and `update()` make persistence a deliberate step.
- **Validated YAML:** supported values are checked before writing; malformed
  files and duplicate keys produce configuration exceptions.
- **Atomic replacement:** saves replace the destination file after writing a
  temporary file, so readers do not see a partially written YAML document.
- **Optional interfaces:** terminal prompts are included; wxPython is loaded
  only when the GUI is requested. Type information ships with the package.

## Installation

Requires **Python 3.10 or later**:

```console
python -m pip install upref
```

For the optional graphical interface:

```console
python -m pip install "upref[gui]"
```

The core runtime dependencies are `platformdirs` and `PyYAML`. The GUI extra
adds `wxPython` and requires a desktop session.

## Quickstart

Create a store, load defaults, and save selected changes:

```python
from upref import ConfigStore

store = ConfigStore("my-application")
settings = store.load(
    defaults={"theme": "dark", "network": {"port": 8080}}
)

store.save(settings)
store.update({"network": {"port": 9000}})

print(store.load())
# {'theme': 'dark', 'network': {'port': 9000}}
print(store.path)
```

This example writes to your platform's per-user configuration directory.
`load()` alone never creates a file. Nested mappings are merged; lists and
scalar values are replaced. `exists()` checks for a file and `delete()` removes
it. Try the [portable example](https://github.com/IIXIXII/upref/blob/master/examples/portable_store.py)
to use an automatically cleaned temporary directory.

See the [storage guide](https://upref.readthedocs.io/en/stable/storage.html)
for supported values and the [path guide](https://upref.readthedocs.io/en/stable/paths.html)
for portable mode.

## Optional interactive preferences

To edit the preferences from the quickstart, collect a draft and save only
after successful completion:

```python
from upref import Field, PromptCancelled, collect, parse_bool

schema = {"notifications": Field("Enable notifications", parser=parse_bool)}

try:
    values = collect(schema, store.load(), interface="tty", mode="all")
except PromptCancelled:
    print("Preferences unchanged.")
else:
    store.update(values)
```

Use `interface="gui"` after installing `upref[gui]`. The
[prompting guide](https://upref.readthedocs.io/en/stable/prompting.html) covers
validation, optional fields, formatting, and custom interfaces.

## Examples

The [example catalog](https://upref.readthedocs.io/en/stable/examples.html)
describes all 26 runnable programs, their difficulty, and their file effects.
Start with one of these:

| Scenario | Runnable example |
| --- | --- |
| Save, load, and merge in a temporary directory | [portable_store.py](https://github.com/IIXIXII/upref/blob/master/examples/portable_store.py) |
| First-run preferences and subsequent startup | [first_run_preferences.py](https://github.com/IIXIXII/upref/blob/master/examples/first_run_preferences.py) |
| Apply or discard an edited draft | [apply_preferences.py](https://github.com/IIXIXII/upref/blob/master/examples/apply_preferences.py) |
| Temporary CLI overrides and explicit persistence | [session_overrides.py](https://github.com/IIXIXII/upref/blob/master/examples/session_overrides.py) |
| Native dialogs with formatted current values | [gui_collection.py](https://github.com/IIXIXII/upref/blob/master/examples/gui_collection.py) |
| Preview a legacy migration | [migration_preview.py](https://github.com/IIXIXII/upref/blob/master/examples/migration_preview.py) |

Clone the repository and install it with `python -m pip install -e .`, then run
an example with `python examples/portable_store.py`. The
[preference walkthroughs](https://upref.readthedocs.io/en/stable/user_preferences.html)
also cover resets, recent files, account settings, import/export, and backups.

## Guarantees and limits

Upref is intended for small application preference files. Saves replace the
complete YAML document; comments and original formatting are not preserved.
Atomic replacement does not lock concurrent writers: coordinate read/modify/write
operations externally when lost updates are unacceptable. Validate application
rules after loading, and bound untrusted input before parsing it.

**Saved values are plain text.** `Field(secret=True)` hides input in compatible
interfaces; it does not encrypt storage. Keep credentials in an operating-system
keyring or secrets manager. Read the
[security guide](https://upref.readthedocs.io/en/stable/security.html) for the
full storage and input limits.

## Status, compatibility, and releases

Upref uses the v2 API and is currently classified **Beta** on PyPI. Consult the
release notes when upgrading; the version number does not change that maturity
classification.

- Python 3.10–3.14 are tested in CI, with platform checks on Windows, macOS,
  and Linux. The GUI has a separate native Windows test job.
- Deprecated v1 wrappers remain available throughout 2.x and are scheduled for
  removal in 3.0. Explicit file migration remains supported; see the
  [migration guide](https://upref.readthedocs.io/en/stable/migration.html).
- Read the [changelog](https://github.com/IIXIXII/upref/blob/master/CHANGELOG.md)
  for behavior changes and the [GitHub releases](https://github.com/IIXIXII/upref/releases)
  for published archives. Install published versions from
  [PyPI](https://pypi.org/project/upref/).

## Support and security reports

Maintained by [Florent Tournois](https://github.com/IIXIXII).

For usage questions, start with the
[troubleshooting guide](https://upref.readthedocs.io/en/stable/troubleshooting.html).
For bugs and feature requests, search the
[GitHub issues](https://github.com/IIXIXII/upref/issues), then open an issue with
your Upref and Python versions, operating system, and a minimal example.
Remove credentials and personal configuration data from reproductions.

For vulnerabilities, use
[GitHub's private reporting form](https://github.com/IIXIXII/upref/security/advisories/new)
and follow the [security policy](https://github.com/IIXIXII/upref/blob/master/SECURITY.md).

## Contributing

Bug reports, documentation improvements, examples, and focused pull requests
are welcome. Read the [contribution guide](https://github.com/IIXIXII/upref/blob/master/CONTRIBUTING.md)
for setup, reporting guidelines, and validation commands. The
[development guide](https://upref.readthedocs.io/en/stable/development.html)
contains the detailed Windows and POSIX workflows.

From a Windows checkout:

```console
.\make.bat setup
.\make.bat check
.\make.bat test
.\make.bat docs
```

### Git Bonsai

For optional Git branch maintenance on Windows x64:

```console
.\make.bat bonsai-setup
git bonsai
```

Setup installs Git Bonsai 0.3.0 locally and protects `master`. Commit or stash
changes, including untracked files, before running it. The tool updates local
tracking branches and prompts before deletion. Use `git bonsai -h` for options;
see the development guide for setup details and other platforms.

## License

Upref is distributed under the
[MIT license](https://github.com/IIXIXII/upref/blob/master/LICENSE.md).
