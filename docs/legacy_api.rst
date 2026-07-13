.. _legacy-api:

Legacy v1 API reference
=======================

The functions below exist for v1 compatibility and migration. Functions
marked as deprecated emit :class:`DeprecationWarning`; new code should use
:class:`upref.ConfigStore` and :func:`upref.collect`. See :doc:`migration` for
the transition guide.

File and raw-value helpers
--------------------------

.. automodule:: upref.legacy
   :noindex:

.. autofunction:: upref.legacy.load_conf

.. autofunction:: upref.legacy.save_conf

.. autofunction:: upref.legacy.upref_filename

.. autofunction:: upref.legacy.current_upref

.. autofunction:: upref.legacy.load_data

.. autofunction:: upref.legacy.save_data

Descriptor and merge helpers
----------------------------

.. autofunction:: upref.legacy.default_conf

.. autofunction:: upref.legacy.dict_merge

.. autofunction:: upref.legacy.conv_raw_to_description

.. autofunction:: upref.legacy.conv_description_to_raw

.. autofunction:: upref.legacy.all_values_are_set

Interactive compatibility helpers
---------------------------------

.. autofunction:: upref.legacy.get_pref

.. autofunction:: upref.legacy.set_pref

.. autofunction:: upref.legacy.remove_pref

Explicit migration function
---------------------------

Most applications should call :meth:`upref.ConfigStore.import_legacy`. The
function below is the underlying compatibility entry point.

.. autofunction:: upref.legacy.import_legacy
