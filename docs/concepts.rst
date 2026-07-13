.. _concepts:

Configuration model
===================

Upref deliberately has a small data model and an explicit lifecycle. An
application normally performs three independent steps:

1. create a :class:`~upref.ConfigStore` and :meth:`~upref.ConfigStore.load`
   values;
2. optionally use :func:`~upref.collect` to ask for values;
3. explicitly :meth:`~upref.ConfigStore.save` the final mapping.

Loading never opens a terminal or window. Collecting never writes a file.
This separation makes startup, cancellation, testing, and error recovery
predictable.

.. _config-values:

Supported values
----------------

The document root is always a mapping with string keys. Each value can be one
of the following:

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Python value
     - YAML representation
   * - ``None``
     - ``null``
   * - ``bool``
     - ``true`` or ``false``
   * - ``int`` or ``float``
     - A YAML number
   * - ``str``
     - A Unicode YAML string
   * - ``list``
     - A sequence whose items are supported values
   * - ``dict[str, ConfigValue]``
     - A nested mapping with string keys

Empty strings, empty containers, ``False``, and ``0`` are valid values. An
empty document or explicit YAML ``null`` at the root represents an empty
mapping. A list or non-null scalar at the document root is invalid. Mapping
keys at every level must be strings.

Objects such as ``pathlib.Path``, ``datetime``, tuples, sets, enum
members, and application classes are not converted implicitly. Convert them
to a supported representation before calling
:meth:`~upref.ConfigStore.save`.

Cycles are rejected because YAML configuration must be a finite tree. Shared
mutable objects are copied independently when accepted.

Detached values and no cache
----------------------------

Upref validates and copies the complete value tree at its public boundaries.
Inputs are never mutated, and returned dictionaries do not share nested lists
or dictionaries with caller-owned defaults or changes.

Every :meth:`~upref.ConfigStore.load` reads the file again; a store has no
implicit configuration cache. Mutating a loaded dictionary therefore changes
only that Python object until :meth:`~upref.ConfigStore.save` is called.

.. _merge-semantics:

Recursive merge rules
---------------------

Defaults and updates use the same merge rules:

* nested mappings are merged recursively;
* a value from the overriding mapping wins;
* lists and scalars are replaced in full, not concatenated;
* keys found only in the overriding mapping are retained;
* both inputs and the result remain independent.

For example, given these defaults and saved values:

.. code-block:: python

   defaults = {
       "network": {"host": "localhost", "ports": [8000, 8001]},
       "enabled": True,
   }
   saved = {
       "network": {"ports": [9000]},
       "enabled": False,
   }

the resolved configuration is:

.. code-block:: python

   {
       "network": {"host": "localhost", "ports": [9000]},
       "enabled": False,
   }

See :doc:`storage` for the difference between in-memory defaults and persisted
updates.
