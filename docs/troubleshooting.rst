Troubleshooting
===============

Where is my file?
-----------------

Print ``store.path``. An explicit ``directory`` must be absolute and is used
directly; the application name is not appended. Constructing a store or loading
defaults does not create a file. Call ``save`` or ``update`` to persist data.

Why is my YAML rejected?
------------------------

The root must be a mapping with string keys at every level. Duplicate explicit
keys are errors, with a line and column indicating the repeated key. Remove
the ambiguity instead of expecting the last occurrence to win.

PyYAML resolves some unquoted text implicitly. Write dates as strings and quote
boolean-like keys:

.. code-block:: yaml

   release_date: "2026-09-19"
   "on": true
   port: 8080

Unsupported Python types such as ``Path`` and ``datetime`` need explicit
conversion (for example ``str(path)`` or ``date.isoformat()``) before saving.
Errors such as an impossible date are format errors, not filesystem errors.

Why does false become true?
---------------------------

``bool("false")`` is true because the string is non-empty. Use
``Field("Enabled", parser=parse_bool)`` after importing ``parse_bool`` from
``upref``. The parser also works for environment variables and rejects unknown
spellings rather than guessing.

Why is a bad saved value not requested again?
---------------------------------------------

``mode="missing"`` checks presence and required empty strings. It does not
run field validators on existing values. Use application-level validation
after ``load`` (the dataclass recipe in :doc:`recipes`) or ask for every field
with ``mode="all"``. ``required=True`` rejects an empty raw string, but does
not by itself reject whitespace, empty lists, or a parser returning ``None``;
add a validator for those application rules.

Why does Enter clear my field?
------------------------------

Blank input is submitted literally by default. For ordinary current values,
pass ``TTYPrompter(keep_current=True)`` as the interface to opt into reuse.
Retained values are parsed and validated again. Secrets are never reused.
To edit a list or mapping as JSON, pair ``json.loads`` with
``formatter=json.dumps``; the same formatter provides GUI prefill.

How do I remove a single setting?
---------------------------------

``update({"key": None})`` stores a null value; it does not delete a key.
Load, remove the key, and explicitly save the complete result:

.. code-block:: python

   settings = store.load()
   settings.pop("obsolete", None)
   store.save(settings)

Like ``update``, this read-modify-write sequence needs external coordination
when multiple writers can modify the same file.

Why is the GUI unavailable?
---------------------------

Install the optional dependency into the same interpreter that runs the
application: ``python -m pip install "upref[gui]"``. A desktop session is
required; headless services can use non-interactive configuration instead.
Choose ``interface="tty"`` for terminal applications. No automatic fallback
occurs, so applications can decide how to handle ``PromptUnavailableError``.

Why did another process overwrite my update?
--------------------------------------------

Atomic replacement prevents partial files, but does not lock a read-modify-write
sequence. Serialize writers or use an external lock covering the entire load,
edit, and save sequence. See :ref:`atomic-writes`.
