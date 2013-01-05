"""Implement fields here."""
from __future__ import absolute_import

import math
from datetime import timedelta

from netaddr import EUI, IPAddress
from pyasn1.type.univ import Null, ObjectIdentifier
from pyasn1.type.base import Asn1ItemBase
from pysnmp.proto import rfc1902
from six import itervalues, integer_types, string_types

from snmp_orm.utils import str_to_oid


def format_key(key):
    if isinstance(key, list):
        key = tuple(key)
    elif not isinstance(key, tuple):
        key = (key, )
    return key


class Mapper(object):

    def form(self, var):
        """Form method must convert pyasn1 format to base python objects"""
        if isinstance(var, Null):
            return None
        else:
            return var

    def toAsn1(self, var):
        """toAsn1 method must convert base python objects to pyasn1 format"""
        if var is None:
            return Null
        else:
            return var


class Field(Mapper):

    def __init__(self, oid):
        self.oid = str_to_oid(oid)

    def __get__(self, instance, owner):
        """Descriptor for retrieving a value from a field."""
        if instance is None:
            return self

        return instance._get(self)

    def load(self, adapter):
        raise NotImplementedError()

    def set(self, adapter, value):
        raise NotImplementedError()

    def prepare(self, vars):
        return self.form(vars)


class Group(object):

    def __init__(self, **fields):
        # get prefix from args for bulk loading
        if "prefix" in fields:
            self.prefix = fields.pop("prefix")
        else:
            self.prefix = None

        # check fields type
        for field in itervalues(fields):
            if isinstance(field, Field):
                continue
            raise TypeError("Object %r must be instance of Field" % field)

        self.fields = fields

    def __getattr__(self, name):
        try:
            return self.fields[name]
        except KeyError:
            raise AttributeError()


class TableField(object):

    def load_many(self, adapter):
        return adapter.walk(self.oid)

    def load_one(self, adapter, key):
        key = format_key(key)
        return adapter.get_one(self.oid + key)

    def set_one(self, adapter, key, value):
        key = format_key(key)
        value = self.toAsn1(value)
        return adapter.set(self.oid + key, value)

    def prepare_many(self, vars):
        return [(oid, self.form(value)) for oid, value in vars]


class SingleValueField(Field):

    def load(self, adapter):
        return adapter.get_one(self.oid)

    def set(self, adapter, value):
        value = self.toAsn1(value)
        return adapter.set(self.oid, value)


class TableValueField(Field, TableField):
    pass


class FromDictMapper(Mapper):

    def form(self, var):
        var = super(FromDictMapper, self).form(var)
        if var is None:
            return None
        else:
            return self.d.get(self.conv_to(var), None)

    def toAsn1(self, var):
        var = super(FromDictMapper, self).toAsn1(var)
        if not (not var in self.d.values() and isinstance(var, integer_types)):
            # var is value but not index
            var = self.d.keys()[self.d.values().index(var)]
        var = rfc1902.Integer(var)
        return var


class FromDictField(SingleValueField, FromDictMapper):
    """Convert data to dict value"""

    def __init__(self, oid, d, conv_to=None):
        super(FromDictField, self).__init__(oid)
        self.d = d
        self.conv_to = conv_to or (lambda x: x)


class FromDictTableField(FromDictField, TableField):
    """Convert data to dict value"""
    pass


class UnicodeMapper(Mapper):

    def form(self, var):
        var = super(UnicodeMapper, self).form(var)
        if var is None:
            return None
        else:
            return unicode(var)

    def toAsn1(self, var):
        var = super(UnicodeMapper, self).toAsn1(var)
        var = rfc1902.OctetString(var)
        return var


class UnicodeField(SingleValueField, UnicodeMapper):
    """Convert data to unicode"""
    pass


class UnicodeTableField(UnicodeField, TableField):
    """Convert data to unicode"""
    pass


class OIDMapper(Mapper):

    def form(self, var):
        var = super(OIDMapper, self).form(var)
        if var is None:
            return None
        else:
            return str_to_oid(var)

    def toAsn1(self, var):
        var = super(OIDMapper, self).toAsn1(var)
        if not isinstance(var, Asn1ItemBase):
            if isinstance(var, string_types):
                var = tuple(map(int, var.split('.')))
            var = ObjectIdentifier(var)
        return var


class OIDField(SingleValueField, OIDMapper):
    """Convert data to OID tuple"""
    pass


class OIDTableField(OIDField, TableField):
    """Convert data to OID tuple"""
    pass


class IntegerMapper(Mapper):

    def form(self, var):
        var = super(IntegerMapper, self).form(var)
        if var is None:
            return None
        else:
            return int(var)

    def toAsn1(self, var):
        var = super(IntegerMapper, self).toAsn1(var)
        if not isinstance(var, Asn1ItemBase):
            var = rfc1902.Integer(var)
        return var


class IntegerField(SingleValueField, IntegerMapper):
    """Convert data to int"""
    pass


class IntegerTableField(IntegerField, TableField):
    """Convert data to int"""
    pass


class LongIntegerMapper(Mapper):

    def form(self, var):
        var = super(LongIntegerMapper, self).form(var)
        if var is None:
            return None
        else:
            return long(var)

    def toAsn1(self, var):
        # FIXME: should the LongInteger type be equal to Integer?
        var = super(IntegerMapper, self).toAsn1(var)
        if not isinstance(var, Asn1ItemBase):
            var = rfc1902.Integer(var)
        return var


class LongIntegerField(SingleValueField, LongIntegerMapper):
    """Convert data to long"""
    pass


class LongIntegerTableField(LongIntegerField, TableField):
    """Convert data to long"""
    pass


class TimeTickMapper(IntegerMapper):

    def form(self, var):
        var = super(TimeTickMapper, self).form(var)
        if var is None:
            return None
        else:
            milliseconds, seconds = math.modf(var * 0.01)
            return timedelta(seconds=seconds,
                             milliseconds=milliseconds * 1000)

    def toAsn1(self, var):
        # TODO: Convert TimeTick object to Asn1 Integer.
        pass


class TimeTickField(SingleValueField, TimeTickMapper):
    """Convert data to timedelta"""
    pass


class TimeTickTableField(TimeTickField, TableField):
    """Convert data to timedelta"""
    pass


class MacMapper(Mapper):

    def form(self, var):
        var = super(MacMapper, self).form(var)
        if var is None:
            return None
        else:
            # sometime net-snmp return blank string
            if var == '':
                return ''
            else:
                return EUI(':'.join([('%x' % ord(x)).ljust(2, "0") for x in var]))

    def toAsn1(self, var):
        var = super(IntegerMapper, self).toAsn1(var)
        if isinstance(var, string_types) and len(var) != 6:
            var = EUI(var)
        if isinstance(var, EUI):
            var = var.packed
        if not isinstance(var, Asn1ItemBase):
            var = rfc1902.OctetString(var)
        return var


class MacField(SingleValueField, MacMapper):
    """Convert data to MAC"""
    pass


class MacTableField(MacField, TableField):
    """Convert data to MAC"""
    pass


class IPAddressMapper(Mapper):

    def form(self, var):
        var = super(IPAddressMapper, self).form(var)
        if var is None:
            return None
        else:
            return IPAddress(var.prettyPrint())

    def toAsn1(self, var):
        var = super(IPAddressMapper, self).toAsn1(var)
        if isinstance(var, string_types) and len(var) != 4:
            var = IPAddress(var)
        if isinstance(var, IPAddress):
            var = var.packed
        if not isinstance(var, Asn1ItemBase):
            var = rfc1902.IpAddress(var)
        return var


class IPAddressField(SingleValueField, IPAddressMapper):
    """Convert data to IP"""
    pass


class IPAddressTableField(IPAddressField, TableField):
    """Convert data to IP"""
    pass

