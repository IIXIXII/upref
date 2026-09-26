# Contributing to Upref

Thank you for helping improve Upref. Contributions can include bug reports,
documentation, examples, tests, or code. Discuss substantial API changes in a
[GitHub issue](https://github.com/IIXIXII/upref/issues) before implementing them.

## Questions and bug reports

Start with the [documentation](https://upref.readthedocs.io/en/stable/) and
[troubleshooting guide](https://upref.readthedocs.io/en/stable/troubleshooting.html),
then search existing issues. A useful bug report includes:

- Upref and Python versions, operating system, and whether the GUI is involved;
- a small runnable reproduction and the expected and actual behavior;
- the relevant traceback, with credentials and personal data removed;
- a minimal configuration using invented values, if configuration is involved.

Report suspected vulnerabilities through
[GitHub's private reporting form](https://github.com/IIXIXII/upref/security/advisories/new).
See the [security policy](https://github.com/IIXIXII/upref/blob/master/SECURITY.md)
before sharing security-sensitive details.

## Development setup

Fork the repository, clone your fork, and create a branch for the change.
Use Python 3.10 or later and a repository-local `.venv`.

On Windows, run from the checkout root:

```console
.\make.bat setup
```

On Linux or macOS:

```console
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e '.[dev]'
```

GUI development additionally needs the `gui` extra and a desktop session.
See the [development guide](https://upref.readthedocs.io/en/stable/development.html)
for native GUI tests, minimum dependency checks, and optional Git Bonsai setup.

## Preparing a change

- Keep each pull request focused on one problem and explain the resulting behavior.
- Preserve explicit persistence: loading and prompting must not silently save.
- Add meaningful regression tests for behavior changes and fixes. Use temporary
  directories so tests do not modify real user preferences.
- Update relevant guides or examples when public behavior changes. Document
  compatibility changes in `CHANGELOG.md` under an `Unreleased` section.
- Keep generated files, local environments, downloaded tools, and credentials
  out of commits.

## Validation

For code changes on Windows:

```console
.\make.bat check
.\make.bat test
.\make.bat docs
```

Equivalent commands on Linux or macOS:

```console
./.venv/bin/python -m ruff format --check upref tests examples scripts docs/conf.py
./.venv/bin/python -m ruff check upref tests examples scripts docs/conf.py
./.venv/bin/python -m mypy upref examples
./.venv/bin/python -m pytest
./.venv/bin/python -m sphinx -E -a -W --keep-going -b html docs docs/_build/html
```

For documentation-only changes, build the documentation and check changed links
and runnable snippets. For packaging changes, also run `make.bat build` on
Windows, or `python -m build` and `python -m twine check dist/*` in the activated
environment on other platforms.

CI requires 100% statement and branch coverage, formatting, linting, strict
typing, a warning-free documentation build, and package verification. GUI tests
run separately. Do not reduce coverage thresholds to make a change pass.

## Opening a pull request

Target `master`. Describe the problem, link the relevant issue when one exists,
explain compatibility implications, and summarize the checks you ran. Mention
any check you could not run. Keep discussion respectful and focused on the
change; maintainer review determines whether it is ready to merge.
