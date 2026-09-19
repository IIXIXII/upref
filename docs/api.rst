.. _api-reference:

API reference
=============

.. currentmodule:: upref

The objects on this page form the supported Upref v2 API. Start with
:class:`ConfigStore` for persistence and use :func:`collect` only when the
application needs interactive input.

Public API summary
------------------

.. autosummary::

   ConfigStore
   Field
   Prompter
   collect
   parse_bool
   UprefError
   ConfigPathError
   ConfigFormatError
   ConfigReadError
   ConfigWriteError
   MigrationError
   PromptCancelled
   PromptUnavailableError

Configuration storage
---------------------

.. autoclass:: ConfigStore
   :members:
   :special-members: __init__

Configuration types
-------------------

.. py:data:: Config

   A configuration mapping with string keys and :data:`ConfigValue` values.

.. py:data:: ConfigValue

   A recursive type alias accepting ``None``, ``bool``, ``int``, ``float``,
   ``str``, lists of supported values, and dictionaries with string keys.

.. py:data:: prompt.PromptMode

   The collection mode literal: ``"missing"`` or ``"all"``.

Interactive schema and protocol
-------------------------------

.. autoclass:: Field
   :members:

.. autoclass:: Prompter
   :members:

.. autofunction:: collect

.. autofunction:: parse_bool

Built-in interfaces
-------------------

.. autoclass:: upref.tty.TTYPrompter
   :members:
   :special-members: __init__

.. autoclass:: upref.gui.GuiPrompter
   :members:
   :special-members: __init__, __enter__, __exit__

Exceptions
----------

.. autoexception:: UprefError
   :show-inheritance:

.. autoexception:: ConfigPathError
   :show-inheritance:

.. autoexception:: ConfigFormatError
   :show-inheritance:

.. autoexception:: ConfigReadError
   :show-inheritance:

.. autoexception:: ConfigWriteError
   :show-inheritance:

.. autoexception:: MigrationError
   :show-inheritance:

.. autoexception:: PromptCancelled
   :show-inheritance:

.. autoexception:: PromptUnavailableError
   :show-inheritance:

Package metadata
----------------

``upref.__version__`` contains the installed distribution version.
``upref.__author__``, ``upref.__license__``, and ``upref.__copyright__``
describe the package's authorship and license.
