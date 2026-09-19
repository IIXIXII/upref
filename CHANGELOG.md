# Changelog

## 2.1.0

### Added

- Public `parse_bool` parser for yes/no, true/false, on/off, y/n, and 1/0 input.
- Keyword-only `Field.formatter` to format current values for terminal display
  and GUI prefill, including JSON lists and mappings.
- Opt-in `TTYPrompter(keep_current=True)` to retain a non-secret current value
  with Enter, while still parsing and validating it.
- Nine runnable examples covering portable storage, boolean input, editing,
  GUI collection, custom interfaces, nested settings, application validation,
  schema upgrades, and error handling; 16 examples are now available.
- Practical recipes, troubleshooting, and a documented code review.

### Fixed

- Reject duplicate explicit YAML keys with source locations while preserving
  YAML merge defaults and explicit overrides.
- Report invalid YAML scalar construction and excessive recursion during
  parsing, normalization, or serialization as `ConfigFormatError`.
- Preserve the documented `ConfigReadError` behavior for file inspection
  failures in `ConfigStore.exists()`.
- Reject malformed fields, schemas, and custom prompter contracts early.
- Clarify required/optional input and cancellation in the bundled interfaces.
- Include examples, documentation, scripts, and pytest configuration in source
  distributions, with an archive-content check in CI.
- Align Python checkout line endings with the formatter on Windows.

### Compatibility

- Files with duplicate explicit YAML keys must be corrected before loading.
  Previous releases silently selected the last value. YAML merge directives
  remain supported.
- Invalid `Field` definitions now raise `TypeError` at construction. Custom
  prompter methods must be callable, and `ask()` must return text or `None`.
- Existing positional `Field` arguments remain supported. The formatter and
  terminal value-reuse option are optional; blank input is still submitted
  literally by default. Secret current values are never formatted or reused.
- Python 3.10 and later remain supported. No new runtime dependency is required.

### Validation

- 230 tests passed locally on Windows with 100% statement coverage; three
  platform-specific tests were skipped.
- Ruff, strict mypy, Sphinx, source-distribution tests, wheel persistence smoke
  checks, and distribution metadata validation passed.
- GUI contracts use a wxPython substitute in the tests; actual window rendering
  was not verified in the local environment.
