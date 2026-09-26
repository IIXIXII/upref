.. _security-guide:

Security and secrets
====================

Upref is a configuration file library, not a credential store. Its security
features protect file integrity and reduce accidental exposure; they do not
provide encryption, authentication, or access control management.

Plain-text storage
------------------

All values passed to :meth:`upref.ConfigStore.save` are serialized as readable
YAML. ``Field(secret=True)`` changes only presentation in compatible prompt
implementations:

* terminal input asks ``getpass`` for non-echoing entry, but the standard
  library can fall back to echoed input when the terminal cannot disable echo;
* GUI input uses a password-style text control;
* an existing secret value is not displayed as the prompt default.

Custom prompters receive the current value in plaintext and must honor the
``secret`` hint themselves. Upref replaces parser and validator
``ValueError`` details with a generic message for secret fields, but callbacks
and custom interfaces remain responsible for not logging raw input.

If that value is later saved, it remains plain text. Do not put passwords,
API tokens, private keys, session cookies, recovery codes, or comparable
credentials directly in an Upref mapping.

Use the operating-system keyring or a dedicated secrets manager and store a
non-secret identifier in Upref instead:

.. code-block:: yaml

   account: florent@example.org
   credential_name: my-application/production

File permissions
----------------

Newly saved files receive mode ``0600`` on POSIX, limiting access to the
owner according to normal filesystem semantics. Upref does not change the
permissions of parent directories. On Windows it relies on the destination
directory's existing NTFS access-control list.

Permissions are defense in depth, not encryption. Administrators, malware
running as the user, backups, synchronization tools, and diagnostic bundles
may still access the file.

Integrity and concurrency
-------------------------

Atomic replacement prevents readers from observing a half-written YAML
document. It does not detect malicious modification, protect against a
compromised account, or decide which concurrent writer is correct. See
:ref:`Atomicity and concurrent access <atomic-writes>` for the exact
guarantees.

Resource limits and untrusted files
-----------------------------------

Upref is designed for small, local application configuration files. It does
not impose a byte-size, nesting-depth, alias-count, CPU, or memory limit before
or during YAML parsing. Upref's loader subclasses ``yaml.SafeLoader`` to reject
duplicate keys while preventing construction of arbitrary Python objects,
but it is not a denial-of-service boundary. Alias-heavy or
deeply nested attacker-controlled YAML can exhaust resources or exceed
Python's recursion limit, especially because normalization detaches repeated
containers. Recursion failures during parsing, normalization, and serialization are reported
as ``ConfigFormatError``; this error conversion is not a resource limit.

An application that accepts configuration from an untrusted party should
enforce an input-size limit before loading, validate an application-specific
depth and shape, and use process isolation when resource exhaustion is in its
threat model.

Application practices
---------------------

Applications using Upref should also:

* avoid logging or printing complete configurations when sensitive values may
  be present;
* use an application-specific directory and a conservative filename;
* validate business meaning after loading—Upref validates representation, not
  hostnames, URLs, port ranges, or authorization policy;
* treat configuration imported from another machine as untrusted input;
* keep backups and crash reports from collecting secrets accidentally;
* add cross-process locking when lost updates are unacceptable.

Criteria for expanding the storage contract
-------------------------------------------

Upref's current scope remains small, local configuration files. If an
application allows several processes to write the same file and cannot accept
lost updates, coordinate the complete read/merge/write operation with an
external lock. A future built-in transaction API would need portable locking,
timeouts, failure recovery, and multiprocess tests before becoming a guarantee.

If configurations will be accepted from external parties, input byte limits
alone are insufficient: aliases can expand during normalization. A bounded
loader would need explicit limits for depth and expanded nodes as well as
input size. Such limits should be opt-in initially to avoid silently changing
the accepted configuration model. They are not implemented by this release;
use the isolation and validation measures described above for those inputs.
