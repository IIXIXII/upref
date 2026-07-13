Release automation
==================

Upref releases are built and published by GitHub Actions from Git tags. The
workflow builds the source distribution and wheel once, verifies those files,
publishes the exact artifacts to PyPI with OpenID Connect, and then attaches
them to a GitHub Release. No long-lived PyPI token is stored in GitHub.

One-time service configuration
------------------------------

The repository configuration cannot create the service-side trust policies.
An administrator must complete these steps once before the first automated
release:

* In GitHub, create an environment named ``pypi``. Restrict deployments to
  release tags matching ``v*`` and require approval by a maintainer. If the
  historical manual-recovery path is needed, also authorize ``master`` for the
  duration of that reviewed run, then remove that exception.
* In the PyPI ``upref`` project, add a GitHub Trusted Publisher for owner
  ``IIXIXII``, repository ``upref``, workflow ``release.yml``, and environment
  ``pypi``. Remove any obsolete PyPI API-token secret from GitHub after the
  trusted publisher succeeds.
* In GitHub, protect ``master`` with a ruleset that requires the ``CI success``,
  ``Dependency review``, and ``Analyze Python`` checks before merging. Protect
  ``v*`` tags against unauthorized creation, update, and deletion.
* Connect the project through the Read the Docs GitHub App, enable pull-request
  builds, and add an automation rule that activates semantic-version tags.
  Keep the default branch as ``latest`` and select ``stable`` as the public
  default after the first v2 release is built.
* Enable Dependabot alerts and security updates in the repository security
  settings. Version updates are configured by ``.github/dependabot.yml``.
* Enable immutable GitHub Releases after the first workflow-driven release has
  succeeded. The release workflow uploads every asset before publishing the
  generated release.

Preparing a release
-------------------

Release tags use a ``v`` prefix while Python package metadata does not. For
example, package version ``2.0.1`` is released with tag ``v2.0.1``.

#. Update ``project.version`` in ``pyproject.toml`` and the source-tree fallback
   ``upref.__version__`` in ``upref/__init__.py`` to the same PEP 440 version.
#. Add and review the release notes or ensure merged pull requests have the
   labels used by ``.github/release.yml``.
#. Run the complete local verification set:

   .. code-block:: console

      .\make.bat check
      .\make.bat test
      .\make.bat docs
      .\make.bat build

#. Commit the version change, merge it into ``master``, and wait for every
   required check to pass.
#. Create and push an annotated tag from that verified commit:

   .. code-block:: console

      git tag -a v2.0.1 -m "Release v2.0.1"
      git push origin v2.0.1

The release workflow rejects a tag that does not match ``project.version``,
does not identify the checked-out commit, or does not belong to ``master``.
PyPI publication uses the protected ``pypi`` environment. After publication
succeeds, the workflow creates the GitHub Release with generated notes, the
wheel, the source archive, and SHA-256 checksums. The Read the Docs GitHub
integration sees the same tag and builds the corresponding documentation
version.

Recovery and the historical 2.0.0 tag
-------------------------------------

Adding a workflow does not replay a tag event that already happened. The
manual ``workflow_dispatch`` input exists only to recover a release from an
existing version tag. It accepts the historical ``2.0.0`` form as well as the
standard ``v2.0.0`` form, verifies that the tag exists, and still passes
through the protected ``pypi`` environment.

PyPI versions are immutable. Never move a published tag or attempt to replace
published files. If a release is incorrect, increment the version and publish
a new tag.
