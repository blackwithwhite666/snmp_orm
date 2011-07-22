from snmp_orm.utils import str_to_oid

from datetime import timedelta
import math

from pyasn1.type.univ import Null
from netaddr import EUI, IPAddress

#
# Base Class
#
class NotImplemented(Exception):
    pass
        
class Mapper(object):
    def form(self, var):
        ''' form method must convert pyasn1 format to base python objects '''
        if isinstance(var, Null):
            return None
        else:
            return var   

class Field(Mapper):
    def __init__(self, oid):
        self.oid = str_to_oid(oid)
    
    def load(self, adapter):
        raise NotImplemented
    
    def prepare(self, vars):
        return self.form(vars)
    
class Group(object):
    def __init__(self, **fields):
        # get prefix from args for bulk loading
        if "prefix" in fields:
            self.prefix = fields["prefix"]
            del fields["prefix"]
        else:
            self.prefix = None
        
        # check fields type
        for field in fields.values():
            if isinstance(field, Field): continue
            raise TypeError("Object `%s` must be instance of Field" % repr(field))
        
        self.fields = fields
        
    def __getattr__(self, name):
        if name in self.fields:
            return self.fields[name]
        else:
            raise AttributeError

#
# Table field
# 
class TableField:    
    def load_many(self, adapter):
        return adapter.walk(self.oid)
    
    def load_one(self, adapter, key):
        if type(key) == list: key = tuple(key)
        if type(key) != tuple: key = (key, )
        return adapter.get_one(self.oid + key)
    
    def prepare_many(self, vars):
        return [ (oid, self.form(value)) for oid, value in vars ]

#
# Key-value field
#
class SingleValueField(Field):    
    def load(self, adapter):
        return adapter.get_one(self.oid)

class TableValueField(Field, TableField):
    pass


#
# FromDict Field
#
class FromDictMapper(Mapper):
    def form(self, var):
        var = super(FromDictMapper, self).form(var)
        if var is None: 
            return None
        else:
            return self.d.get(self.conv_to(var), None)
    
class FromDictField(SingleValueField, FromDictMapper):
    ''' Convert data to dict value '''
    def __init__(self, oid, d, conv_to=None):
        super(FromDictField, self).__init__(oid)
        self.d = d
        self.conv_to = conv_to or (lambda x: x)
    
class FromDictTableField(FromDictField, TableField):
    ''' Convert data to dict value '''
    pass

#
# Unicode Field
#
class UnicodeMapper(Mapper):
    def form(self, var):
        var = super(UnicodeMapper, self).form(var)
        if var is None: 
            return None
        else:
            return unicode(var)
    
class UnicodeField(SingleValueField, UnicodeMapper):
    ''' Convert data to unicode '''
    pass
    
class UnicodeTableField(UnicodeField, TableField):
    ''' Convert data to unicode '''
    pass

#
# OID Field
#
class OIDMapper(Mapper):
    def form(self, var):
        var = super(OIDMapper, self).form(var)
        if var is None: 
            return None
        else:
            return str_to_oid(var)
    
class OIDField(SingleValueField, OIDMapper):
    ''' Convert data to oid tuple '''
    pass

class OIDTableField(OIDField, TableField):
    ''' Convert data to oid tuple '''
    pass

#
# Integer Field
#
class IntegerMapper(Mapper):
    def form(self, var):
        var = super(IntegerMapper, self).form(var)
        if var is None: 
            return None
        else:
            return int(var)
    
class IntegerField(SingleValueField, IntegerMapper):
    ''' Convert data to int '''
    pass

class IntegerTableField(IntegerField, TableField):
    ''' Convert data to int '''
    pass

#
# Long Integer Field
#
class LongIntegerMapper(Mapper):
    def form(self, var):
        var = super(LongIntegerMapper, self).form(var)
        if var is None: 
            return None
        else:
            return long(var)
    
class LongIntegerField(SingleValueField, LongIntegerMapper):
    ''' Convert data to long '''
    pass

class LongIntegerTableField(LongIntegerField, TableField):
    ''' Convert data to long '''
    pass

#
# TimeTick Field
#
class TimeTickMapper(IntegerMapper):
    def form(self, var):
        var = super(TimeTickMapper, self).form(var)
        if var is None: 
            return None
        else:
            milliseconds, seconds = math.modf(var * 0.01)
            return timedelta(seconds=seconds, milliseconds=milliseconds * 1000)
    
class TimeTickField(SingleValueField, TimeTickMapper):
    ''' Convert data to timedelta '''
    pass

class TimeTickTableField(TimeTickField, TableField):
    ''' Convert data to timedelta '''
    pass

#
# Mac Field
#
class MacMapper(Mapper):
    def form(self, var):
        var = super(MacMapper, self).form(var)
        if var is None: 
            return None
        else:
            return EUI(':'.join([('%x' % ord(x)).ljust(2, "0") for x in var]))
    
class MacField(SingleValueField, MacMapper):
    ''' Convert data to mac '''
    pass

class MacTableField(MacField, TableField):
    ''' Convert data to mac '''
    pass

#
# IPAddress Field
#
class IPAddressMapper(Mapper):
    def form(self, var):
        var = super(IPAddressMapper, self).form(var)
        if var is None: 
            return None
        else:
            return IPAddress(var.prettyPrint())
    
class IPAddressField(SingleValueField, IPAddressMapper):
    ''' Convert data to mac '''
    pass

class IPAddressTableField(IPAddressField, TableField):
    ''' Convert data to mac '''
    pass