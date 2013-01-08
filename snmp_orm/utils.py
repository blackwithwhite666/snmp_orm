"""Some useful tools."""
from __future__ import absolute_import

import sys
import inspect
import pkgutil
import importlib

from six import string_types, binary_type, b, reraise
from pyasn1.type.univ import ObjectIdentifier


def get_all_parents(cls):
    parents = []
    parents.extend(cls.__bases__)
    left_bases = []
    left_bases.extend(cls.__bases__)
    while left_bases:
        for base in left_bases[:]:
            left_bases.extend(base.__bases__)
            parents.extend(base.__bases__)
            left_bases.remove(base)
    parents.reverse()
    return tuple(parents)


def str_to_oid(s):
    if isinstance(s, string_types + (binary_type, )):
        return tuple(int(val) for val in s.split("."))
    elif isinstance(s, ObjectIdentifier):
        return tuple(s)
    else:
        return s


def oid_to_str(t):
    try:
        return ".".join(str(val) for val in t)
    except TypeError:
        return t


def symbol_by_name(name, aliases={}, imp=None, package=None,
                   sep='.', default=None, **kwargs):
    """Get symbol by qualified name.

    The name should be the full dot-separated path to the class::

        modulename.ClassName

    Example::

        celery.concurrency.processes.TaskPool
                                    ^- class name

    or using ':' to separate module and symbol::

        celery.concurrency.processes:TaskPool

    If `aliases` is provided, a dict containing short name/long name
    mappings, the name is looked up in the aliases first.

    Examples:

        >>> symbol_by_name("celery.concurrency.processes.TaskPool")
        <class 'celery.concurrency.processes.TaskPool'>

        >>> symbol_by_name("default", {
        ...     "default": "celery.concurrency.processes.TaskPool"})
        <class 'celery.concurrency.processes.TaskPool'>

        # Does not try to look up non-string names.
        >>> from celery.concurrency.processes import TaskPool
        >>> symbol_by_name(TaskPool) is TaskPool
        True

    """
    if imp is None:
        imp = importlib.import_module

    if not isinstance(name, string_types):
        return name                                 # already a class

    name = aliases.get(name) or name
    sep = ':' if ':' in name else sep
    module_name, _, cls_name = name.rpartition(sep)
    if not module_name:
        cls_name, module_name = None, package if package else cls_name
    try:
        try:
            module = imp(module_name, package=package, **kwargs)
        except ValueError as exc:
            exc = ValueError("Couldn't import %r: %s" % (name, exc))
            reraise(ValueError, exc, sys.exc_info()[2])
        return getattr(module, cls_name) if cls_name else module
    except (ImportError, AttributeError):
        if default is None:
            raise
    return default


def load_modules(packages):
    """Find all attributes of given modules."""
    for package in packages:
        for _, name, _ in pkgutil.walk_packages(package.__path__,
                                                package.__name__ + '.'):
            yield importlib.import_module(name)
    raise StopIteration()


def find_classes(cls, packages):
    """Find all subclass of given class."""
    entities = set()
    for module in load_modules(packages):
        for attr in dir(module):
            entity = getattr(module, attr)
            if inspect.isclass(entity) and \
                    issubclass(entity, cls) and \
                    entity is not cls:
                if entity not in entities:
                    yield entity
                    entities.add(entity)
    raise StopIteration()
