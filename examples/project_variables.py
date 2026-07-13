"""Collect and persist the variables required to work on one project."""

from upref import ConfigStore, ConfigValue, Field, PromptCancelled, collect


def parse_boolean(raw: str) -> bool:
    """Parse a human-friendly boolean entered in the terminal."""
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError("Enter yes/no, true/false, on/off, or 1/0")


def is_non_empty_string(value: ConfigValue) -> bool:
    """Return whether a parsed configuration value is a non-empty string."""
    return isinstance(value, str) and bool(value.strip())


store = ConfigStore("upref-project-example", filename="variables.yaml")
schema = {
    "project_name": Field(
        "Project name",
        description="A human-readable name, for example customer-portal",
        validator=is_non_empty_string,
    ),
    "source_directory": Field(
        "Source directory",
        description="Path relative to the project root, for example src",
        validator=is_non_empty_string,
    ),
    "build_directory": Field(
        "Build directory",
        description="Path relative to the project root, for example dist",
        validator=is_non_empty_string,
    ),
    "python_version": Field(
        "Python version",
        description="Version expected by the project, for example 3.12",
        validator=is_non_empty_string,
    ),
    "run_tests_before_build": Field(
        "Run tests before building",
        parser=parse_boolean,
    ),
}

try:
    variables = collect(
        schema,
        initial=store.load(),
        interface="tty",
        mode="missing",
    )
except PromptCancelled:
    print("Setup cancelled; the existing project variables were not changed.")
else:
    store.save(variables)
    print("Project variables:")
    for variable_name in schema:
        print(f"  {variable_name}: {variables[variable_name]}")
    print(f"Saved to: {store.path}")
