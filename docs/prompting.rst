.. _prompting-guide:

Interactive collection
======================

Interactive collection is an optional layer above the configuration value
model. A schema describes how to ask for values, while
:func:`~upref.collect` returns a new mapping. The caller decides whether and
when to save it.

Defining fields
---------------

Each schema entry maps a configuration key to an immutable
:class:`~upref.Field`:

.. code-block:: python

   from upref import Field

   schema = {
       "service_url": Field(
           label="Service URL",
           description="For example: https://api.example.org",
       ),
       "timeout": Field(
           label="Timeout in seconds",
           parser=int,
           validator=lambda value: isinstance(value, int) and value > 0,
       ),
       "note": Field(
           label="Optional note",
           required=False,
       ),
   }

A secret field can be declared separately when an application needs to
collect a credential for immediate use or transfer to a real secret store:

.. code-block:: python

   token_field = Field(label="API token", secret=True)

Do not add the resulting plaintext token to a mapping passed to
:meth:`~upref.ConfigStore.save`.

Field options have the following behavior:

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Option
     - Meaning
   * - ``label``
     - Human-readable field name. Interfaces fall back to the schema key when
       it is empty.
   * - ``description``
     - Optional explanatory text displayed with the prompt.
   * - ``required``
     - When true, an empty string is rejected and an existing empty string is
       missing in ``mode="missing"``.
   * - ``secret``
     - Requests password-style input from compatible interfaces and asks them
       to hide the current value. It does not encrypt a saved value; see
       :doc:`security`.
   * - ``parser``
     - Converts raw text to a supported configuration value. The default is
       :class:`str`.
   * - ``validator``
     - Receives the parsed value. Returning ``False`` or raising
       :class:`ValueError` displays an error and asks again. Returning ``True``
       or ``None`` accepts the value.
   * - ``formatter``
     - Keyword-only callable converting a current value to parser-compatible
       text. Defaults to ``str``. Built-in interfaces use it for ordinary
       display, GUI prefill, and optional terminal value reuse; secret values
       are never passed to it.

Field definitions are checked at construction: labels and descriptions must
be strings, flags must be booleans, and callbacks must be callable. This catches
configuration mistakes before a user interface is opened.

Use :func:`~upref.parse_bool` for textual boolean answers, rather than
``bool`` (which treats every non-empty string, including ``"false"``, as true).
It accepts ``yes/no``, ``true/false``, ``on/off``, ``y/n``, and ``1/0`` after
trimming whitespace and ignoring case. Unknown input raises ``ValueError``
and is therefore retried by ``collect``.

The parser result is validated against the :ref:`configuration value model
<config-values>`. A parser should raise :class:`ValueError` for user-correctable
input; unexpected exception types propagate to the application.
For a secret field, Upref replaces parser or validator :class:`ValueError`
text with a generic message so raw input is not echoed by the bundled error
display.

Collecting missing or all values
--------------------------------

Use an existing configuration as ``initial`` and save only after collection
has succeeded:

.. code-block:: python

   from upref import ConfigStore, PromptCancelled, collect

   store = ConfigStore("my-app")

   try:
       values = collect(
           schema,
           initial=store.load(),
           interface="tty",
           mode="missing",
       )
   except PromptCancelled:
       print("No changes saved")
   else:
       store.save(values)

``mode="missing"`` asks for a field when its key is absent, its value is
``None``, or its required string is empty. ``False``, ``0``, empty lists,
empty dictionaries, and optional empty strings are already populated.

``mode="all"`` asks every schema field and supplies its current value to the
interface. Keys in ``initial`` that are not in the schema are preserved in
both modes. The input mapping is never mutated, and the result is detached.

The schema applies to top-level keys; dots in names are literal characters,
not paths. To edit a nested mapping, collect that section and put the result
back into the complete configuration before saving. See :doc:`recipes`.

Fields skipped in ``missing`` mode are not parsed or checked by their field
validators. ``load`` checks the configuration data model, not application
constraints such as port ranges. Validate loaded settings separately when
those constraints matter (see the dataclass example in :doc:`recipes`).

When no field needs to be asked, ``collect`` returns immediately and does not
initialize the selected interface. This permits an application to specify
``interface="gui"`` without requiring wxPython when all values are already
present.

Terminal interface
------------------

``interface="tty"`` is the default and has no optional dependency. It prints
the label and description, shows a non-secret current value, and reads one
line with ``input``. Secret fields use ``getpass.getpass`` and never display
the current value. Non-echoing input depends on terminal support; the standard
library can warn and fall back to echoed input when it cannot control echo.

End-of-file and ``Ctrl+C`` while reading are treated as cancellation and
become :exc:`~upref.PromptCancelled`.

Applications that need direct control can instantiate
:class:`upref.tty.TTYPrompter` and inject input, password, and output
functions. Passing this object as ``interface`` also satisfies the
:class:`~upref.Prompter` protocol.

The terminal indicates whether a field is required or optional and reminds
the user how to cancel. To allow Enter to retain a current value:

.. code-block:: python

   from upref import Field, collect, parse_bool
   from upref.tty import TTYPrompter

   values = collect(
       {"enabled": Field("Enabled", parser=parse_bool)},
       {"enabled": False},
       interface=TTYPrompter(keep_current=True),
       mode="all",
   )

Value reuse is opt-in. The formatter produces text which is parsed and
validated again; ``False`` and ``0`` can be retained. Secret values and
``None`` are never reused. With the default ``keep_current=False``, Enter
submits empty text, allowing an optional string to be cleared. With reuse
enabled, an empty current value still follows the field's required rule.

Graphical interface
-------------------

Install the optional dependency and select the interface explicitly:

.. code-block:: console

   pip install "upref[gui]"

.. code-block:: python

   values = collect(schema, initial=store.load(), interface="gui")

The GUI uses wxPython modal text-entry dialogs. Cancelling a dialog raises
:exc:`~upref.PromptCancelled`. If wxPython is missing or cannot initialize a
GUI, Upref raises :exc:`~upref.PromptUnavailableError`.

Dialogs show required/optional status. For complex values, provide a formatter
whose output the parser can read; Python's default string representation of
a list containing booleans or ``None`` is not JSON:

.. code-block:: python

   import json

   json_field = Field(
       "Options", parser=json.loads, formatter=json.dumps,
       validator=lambda value: isinstance(value, list),
   )

Call the GUI from the desktop application's main thread. The automated suite
uses a wxPython substitute to verify dialog arguments and resource ownership;
real window rendering should also be checked in a desktop session.

When ``collect`` creates the built-in GUI object, it also closes it. Code that
passes its own :class:`upref.gui.GuiPrompter` instance owns that instance and
should close it, preferably with its context manager:

.. code-block:: python

   from upref.gui import GuiPrompter

   with GuiPrompter(title="Application preferences") as prompter:
       values = collect(schema, initial=store.load(), interface=prompter)

Custom interfaces
-----------------

A custom interface implements the two-method :class:`~upref.Prompter`
protocol:

.. code-block:: python

   class ApplicationPrompter:
       def ask(self, name, field, current):
           """Return raw text, or None to cancel."""
           ...

       def show_error(self, message):
           """Present a parser or validator error."""
           ...

   values = collect(schema, initial={}, interface=ApplicationPrompter())

Custom prompters are useful for integrating an application's existing UI and
for deterministic tests. Upref does not call ``close`` on caller-owned
prompters. A custom implementation receives ``current`` in plaintext even for
a secret field. It is responsible for checking ``field.secret``, avoiding
display or prefill of that value, protecting diagnostic logs, and using an
appropriate password-entry control.
