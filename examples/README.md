# Runnable examples

From the repository root, install the checkout into your Python environment:

```console
python -m pip install -e .
python examples/portable_store.py
```

On Windows without activation, replace `python` with
`.\.venv\Scripts\python.exe`. GUI examples additionally require
`python -m pip install -e ".[gui]"` and a desktop session.

| Level | Script | Input | Files and purpose |
| --- | --- | --- | --- |
| Simple | [portable_store.py](portable_store.py) | None | Temporary directory; defaults, save/load, update |
| Simple | [basic_store.py](basic_store.py) | None | Per-user `upref-basic-example`; save/load |
| Simple | [defaults_and_update.py](defaults_and_update.py) | None | Per-user example; updates, then deletes its file |
| Simple | [boolean_collection.py](boolean_collection.py) | Terminal | No files; booleans and optional text |
| Simple | [tty_collection.py](tty_collection.py) | Terminal | Per-user example; saves collected values |
| Intermediate | [edit_settings.py](edit_settings.py) | Terminal | No files; Enter to keep a value, JSON lists |
| Intermediate | [gui_collection.py](gui_collection.py) | GUI | No files; custom title, JSON prefill, cancellation |
| Intermediate | [handle_errors.py](handle_errors.py) | None | Temporary directory; duplicate YAML diagnostics |
| Intermediate | [project_variables.py](project_variables.py) | Terminal | Per-user project variables |
| Intermediate | [multiple_projects.py](multiple_projects.py) | None | Per-user directory with distinct project files |
| Advanced | [nested_collection.py](nested_collection.py) | Terminal | Temporary directory; collect a section, then save |
| Advanced | [custom_interface.py](custom_interface.py) | Scripted | No files; protocol implementation and validation retry |
| Advanced | [typed_settings.py](typed_settings.py) | None | Temporary directory; application validation with a dataclass |
| Advanced | [schema_upgrade.py](schema_upgrade.py) | None | Temporary directory; idempotent schema migration |
| Advanced | [environment_profiles.py](environment_profiles.py) | Environment | Per-user profiles with transient overrides |
| Advanced | [migrate_v1.py](migrate_v1.py) | Existing v1 file | Creates v2 settings; leaves the source intact |

Temporary directories are automatically removed at the end of each example.
Persistent examples print their exact paths and may replace their own previous
example settings. Change `LEGACY_NAME` before running the real v1 migration.

Suggested progression:

1. Run `portable_store.py`: the loaded network port is `9000`, while the
   earlier snapshot still contains `8080`.
2. Run `boolean_collection.py`: enter `maybe` to see an error, then `no` and
   an empty note. The result contains `False` and `""`.
3. Run `edit_settings.py`: press Enter twice to retain `False` and `["work"]`.
   Enter `[]` at the second prompt to clear the list instead.
4. Run `custom_interface.py`: it produces `{'enabled': False, 'retries': 3}`
   and one validation error without waiting for input.
5. Run `typed_settings.py` and `schema_upgrade.py` for application-level
   validation and versioned configuration transformations.

`Ctrl+C` cancels terminal examples. In the new examples, cancelled collection
does not save partial values. A GUI Cancel button has the same effect.

The [Sphinx examples guide](../docs/examples.rst),
[advanced recipes](../docs/recipes.rst), and
[troubleshooting guide](../docs/troubleshooting.rst) explain the API decisions.
