# Changelog

## 2.2.0 - 2026-09-26

### Added

- Ten runnable user-preference scenarios: first-run setup, Apply/Cancel, resets,
  recent documents, window geometry, account settings, CLI session overrides,
  portable JSON import/export, backup/restore, and legacy migration preview.
  The catalog now contains 26 examples, with a dedicated walkthrough guide.
- Explicit `source_format="auto" | "raw" | "descriptors"` selection and
  `dry_run=True` previews for legacy migration, retaining the default heuristic
  and target preflight checks.
- Hypothesis properties for persistence, copying, merging, and failed writes.
- Native wxPython integration scenarios with process timeouts and a dedicated
  Windows CI job; minimum runtime dependency testing on Python 3.10.
- Functional installed-wheel and resource checks in CI and release automation.
- A release-based deprecation schedule: v1 wrappers remain through 2.x and are
  scheduled for removal in 3.0. Explicit migration remains supported.

### Fixed

- Preserve Unicode NEL (U+0085) in YAML keys and values instead of folding it
  into a space; ordinary Unicode remains readable.
- Reject non-scalar YAML keys carrying scalar tags with `ConfigFormatError`
  and a source location instead of leaking a `TypeError`.
- Reject null characters in configuration directories during construction.
- Normalize string subclass keys to plain strings, preserving their underlying
  text so string-backed enum keys can be saved. Scalar enum values still need
  explicit conversion; normalized key collisions are rejected.
- Measure branch coverage as well as statement coverage, retaining the 100%
  gate and covering application reuse and pre-write failures.
- Exercise POSIX and Windows permission branches on every platform so the
  coverage gate behaves consistently on Linux, macOS, and Windows.

### Compatibility

- Python 3.10 and later remain supported, with no new runtime dependency.
- Existing migration calls retain their behavior; format selection and previews
  are optional. Deprecated v1 wrappers remain available throughout 2.x.
- Malformed YAML keys and invalid configuration directories now consistently
  raise the documented configuration exceptions. Duplicate normalized keys are
  rejected instead of silently replacing an existing value.

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
