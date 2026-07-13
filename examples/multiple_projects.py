"""Keep independent per-user settings for several related projects."""

from upref import Config, ConfigStore

PROJECT_DEFAULTS: dict[str, Config] = {
    "frontend": {
        "working_directory": "apps/frontend",
        "test_command": "npm test",
        "build_command": "npm run build",
        "enabled": True,
    },
    "backend": {
        "working_directory": "apps/backend",
        "test_command": "python -m pytest",
        "build_command": "python -m build",
        "enabled": True,
    },
}

for project_name, defaults in PROJECT_DEFAULTS.items():
    # Each project receives a separate file below the same application-specific
    # per-user configuration directory.
    store = ConfigStore(
        "upref-workspace-example",
        filename=f"{project_name}.yaml",
    )
    settings = store.load(defaults=defaults)
    if not store.exists():
        store.save(settings)

    print(f"{project_name}: {settings}")
    print(f"  file: {store.path}")
