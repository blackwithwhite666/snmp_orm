"""Contains abstract device from which all other should be inherited."""
from __future__ import absolute_import

import inspect
from collections import namedtuple, defaultdict
from types import IntType

from six import with_metaclass, iteritems, iterkeys, next

from snmp_orm.adapter import get_adapter
from snmp_orm.fields import Field, TableField, Group
from snmp_orm.utils import get_all_parents


def load(fn):
    """Ensure that class will be initialized before method call."""

    def inner_wrapper(self, *args, **kwargs):
        self.load()
        return fn(self, *args, **kwargs)

    return inner_wrapper


class TableListProxy(dict):
    """Proxy that support :class:`TableField`."""

    # Decorate class methods here.
    for method_name in set(dir(dict)) - set(dir(object)):
        locals()[method_name] = load(getattr(dict, method_name))

    def __init__(self, adapter, field):
        dict.__init__(self)
        self.adapter = adapter
        self.d = None
        self.field = field
        self.loaded = False

    @load
    def __str__(self):
        return dict.__str__(self)

    @load
    def __repr__(self):
        return dict.__repr__(self)

    def get_by_index(self, key):
        if type(key) is IntType:
            key = (key,)
        if self.loaded:
            if self.d is None:
                self.d = dict(self)
            return self.d.get(key, None)
        else:
            variables = self.field.load_one(self.adapter, key)
            return self.field.prepare(variables)

    def load(self):
        if not self.loaded:
            oid_len = len(self.field.oid)
            variables = self.field.load_many(self.adapter)
            self.loaded = True
            for oid, v in self.field.prepare_many(variables):
                idx = oid[oid_len:]
                if len(idx) == 1:
                    idx = idx[0]
                self.update({idx: v})

    def __setitem__(self, key, value):
        self.field.set_one(self.adapter, key, value)

    def __getitem__(self, key):
        return self.get_by_index(key)


def get(adapter, field, index=None):
    if isinstance(field, TableField):
        return TableListProxy(adapter, field)
    else:
        variables = field.load(adapter)
        return field.prepare(variables)


def set_one(adapter, field, value):
    # TODO: Implement set table value
    return field.set(adapter, value)


class DeviceMeta:
    """Meta-data for each device type."""

    #: Device's fields mapping.
    fields = None

    #: Device's group mapping.
    groups = None

    #: Device's lookup table. OID to field mapping.
    lut = None

    def __init__(self):
        self.adapter_kwargs = {}

    def get_adapter(self, host, **kwargs):
        params = self.adapter_kwargs.copy()
        params.update(kwargs)
        return get_adapter(host, **params)


class AbstractContainer(object):
    """Container for group of fields. Created for each device and provide
    access to fields in given group.

    """

    prefix = None
    group = None
    items_list = None

    def __init__(self, adapter, meta):
        self.adapter = adapter
        self.meta = meta

    def __iter__(self):
        cls = type(self)
        prefix = cls.prefix
        if prefix is None:
            result = ((name, prop.__get__(self, cls))
                      for name, prop in iteritems(vars(cls))
                      if type(prop) == property)
        else:
            result = list()
            result_dict = defaultdict(dict)
            fields = dict((field.oid, (name, field))
                          for name, field in iteritems(self.meta.groups[cls.group]))
            prefix_len = len(prefix)
            for oid, variables in self.adapter.getbulk(len(fields), prefix):
                if oid[:prefix_len] != prefix:
                    break
                if oid in fields:
                    name, field = fields[oid]
                    result.append((name, field.form(variables)))
                else:
                    # TODO: better way to handle table
                    for field_oid in fields:
                        field_oid_len = len(field_oid)
                        if oid[:field_oid_len] == field_oid:
                            name, field = fields[field_oid]
                            if isinstance(field, TableField):
                                idx = oid[field_oid_len:]
                                if len(idx) == 1:
                                    idx = idx[0]
                                result_dict[name][idx] = field.form(variables)
                                break
            result.extend(iteritems(result_dict))

        return iter(result)

    def keys(self):
        """Return all field's names."""
        return list(type(self).items_list)

    def __dir__(self):
        attrs = set(dir(type(self)) + list(vars(self)))
        attrs.update(self.keys())
        return list(attrs)

    def __contains__(self, name):
        return name in type(self).items_list

    def _get(self, field):
        """Shortcut to get function."""
        return get(self.adapter, field)

    def _set(self, field, value):
        """Shortcut to set_one function."""
        # FIXME: how could I handle the return value
        return set_one(self.adapter, field, value)

    def __setattr__(self, name, value):
        if name in type(self).items_list:
            self._set(self._get_field_by_name(name), value)
        else:
            super(AbstractContainer, self).__setattr__(name, value)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __getattr__(self, name):
        field = self._get_field_by_name(name)
        if field:
            return self._get(field)
        else:
            raise AttributeError("name %r is not defined" % name)

    def __getitem__(self, key):
        try:
            return self.__getattr__(key)
        except AttributeError:
            raise KeyError("key %r is not defined" % key)

    def _get_field_by_name(self, name):
        """Return field class from group by it's name."""
        cls = type(self)
        if name in cls.items_list:
            return self.meta.groups[cls.group][name]
        else:
            return None

    def __repr__(self):
        cls = type(self)
        return '<%s for "%s" at %s>' % (cls.__name__, cls.group, hex(id(self)))


#: Contains information about field.
FieldInfo = namedtuple('FieldInfo', ('name', 'cls'))


class DeviceBase(type):

    def __new__(cls, name, bases, attrs):
        cls = super(DeviceBase, cls).__new__(cls, name, bases, attrs)
        meta = DeviceMeta()
        parents = get_all_parents(cls)[1:]

        # compute adapter params
        adapter_params_klass = [getattr(klass, "AdapterParams", None)
                                for klass in parents + (cls, )]
        adapter_kwargs = {}
        for klass in adapter_params_klass:
            if klass is None:
                continue
            adapter_kwargs.update(vars(klass))
        meta.adapter_kwargs = dict((k, v)
                                   for (k, v) in iteritems(adapter_kwargs)
                                   if not k.starstwith("_"))

        # get parent fields and groups and populate ours dictionaries
        meta.fields = all_fields = {}
        meta.groups = all_groups = {}
        meta.lut = all_lut = {}
        for klass in parents:
            all_fields.update(klass.meta.fields)
            all_groups.update(klass.meta.groups)
            all_lut.update(klass.meta.lut)

        # get class fields and groups
        fields = {}
        groups = {}
        prefixes = {}
        for name, obj in iteritems(attrs):
            if name.startswith("__"):
                continue
            if isinstance(obj, Field):
                fields[name] = obj
            elif isinstance(obj, Group):
                prefixes[name] = obj.prefix
                groups[name] = obj.fields

        # create OID to field look up table
        lut = {}
        for group in groups.values():
            for name, field in group.items():
                lut[field.oid] = FieldInfo(name, field)

        all_fields.update(fields)
        all_groups.update(groups)
        all_lut.update(lut)

        # create containers class
        for group_name in iterkeys(groups):
            klass = type('Container', (AbstractContainer, ), dict(
                prefix=prefixes[group_name],
                group=group_name,
                items_list=set(iterkeys(meta.groups[group_name])),
            ))
            setattr(cls, group_name, klass)

        cls.meta = meta
        return cls


class AbstractDevice(with_metaclass(DeviceBase)):
    """Abstract device class."""

    #: Device meta-data.
    meta = None

    #: Used to find device class by object OID.
    classId = None

    def __init__(self, host, **kwargs):
        self.host = host
        cls = type(self)
        meta = cls.meta
        adapter = self.adapter = meta.get_adapter(host, **kwargs)
        # initialize associated containers
        for name in iterkeys(meta.groups):
            setattr(self, name, getattr(cls, name)(adapter, meta))

    def _get(self, field):
        return get(self.adapter, field)

    def prepare_val_by_oid(self, oid, var):
        """Prepare value for given OID."""
        meta = self.meta
        field = name = index = prep_var = None
        oid = tuple(oid)
        if oid in meta.lut.viewkeys():
            # OID found, use field associated with it
            name, field = meta.lut[oid]
        else:
            # Try to find first matching OID
            g = (key for key in iterkeys(meta.lut)
                 if oid[:len(key)] == key)
            try:
                toid = next(g)
            except StopIteration:
                pass
            else:
                name, field = meta.lut[toid]
                index = oid[len(toid):]
        if field is not None:
            prep_var = field.prepare(var)
        return (name, prep_var, index)

    def __repr__(self):
        cls = type(self)
        return "<%s.%s object for host %s at %s>" % (
            inspect.getmodule(cls).__name__, cls.__name__, self.host,
            hex(id(self))
        )
