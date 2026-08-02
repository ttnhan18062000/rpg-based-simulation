"""Give this suite a unique pytest module namespace.

The executor suite also has a ``test_preflight.py``.  Keeping this directory a
package prevents pytest from treating both files as the same top-level module.
"""
