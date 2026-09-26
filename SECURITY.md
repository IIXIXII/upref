# Security policy

## Reporting a vulnerability

Report suspected vulnerabilities privately using
[GitHub's vulnerability reporting form](https://github.com/IIXIXII/upref/security/advisories/new).
A GitHub account is required. Reports are shared with the repository's security
maintainers rather than posted as public issues.

Include:

- affected Upref and Python versions, operating system, and relevant dependencies;
- a minimal reproduction with invented configuration values;
- the impact, prerequisites, and whether an attacker controls a file or input;
- any workaround you have identified.

Do not include real credentials, private keys, or personal configuration files.
Avoid posting vulnerability details in public issues or pull requests before
coordinating disclosure with the maintainer. Continue the discussion in the
private report so reproduction details and a potential fix stay together.

## Versions

The current release line is 2.x, with a Beta maturity classification. When
possible, check whether the issue also affects the latest
[published release](https://github.com/IIXIXII/upref/releases), and report the
exact version tested. The project does not publish a long-term support or
backport schedule; consult release notes for fixes available in each version.

The presence of deprecated v1 wrappers in 2.x is a migration compatibility
feature. See the [migration guide](https://upref.readthedocs.io/en/stable/migration.html)
for moving old configuration files and application code to the v2 API.

## Security scope

Upref stores small local configuration files as plain-text YAML. Atomic file
replacement protects against partially written files, and POSIX saves use mode
`0600`. These properties do not provide encryption or coordinate concurrent
writers. `Field(secret=True)` changes input presentation, not persistence.

The YAML loader rejects duplicate keys and does not construct arbitrary Python
objects. It does not impose size, depth, CPU, or memory limits on untrusted
input. Applications must validate their own configuration semantics, constrain
untrusted data, and keep credentials in a secrets manager or system keyring.
See the [security guide](https://upref.readthedocs.io/en/stable/security.html)
for the full threat model and storage limits.

Ordinary bugs and usage questions belong in
[GitHub issues](https://github.com/IIXIXII/upref/issues). If an issue may expose
data or violate these documented guarantees, use the private reporting channel.
