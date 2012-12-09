from snmp_orm.adapter import get_adapter
from snmp_orm.fields import Field, TableField, Group
from snmp_orm.utils import get_all_parents

import inspect


def load(f):
    def wrapper(self, *args, **kwargs):
        self.load()
        return f(self, *args, **kwargs)
    return wrapper

class TableListProxy(dict):
    for methodName in set(dir(dict)) - set(dir(object)):
        f = getattr(dict, methodName)
        locals()[methodName] = load(f)
        
    def __init__(self, adapter, field):
        dict.__init__(self)
        self.adapter = adapter
        self.d = None
        self.field = field
        self.loaded = False
    
    @load
    def __str__(self): return dict.__str__(self)
    @load
    def __repr__(self): return dict.__repr__(self)
    
    def get_by_index(self, key):
        from types import IntType
        if type(key) is IntType:
            key = (key,)
        if self.loaded:
            if self.d is None:
                self.d = dict(self)
            return self.d.get(key, None)
        else:
            vars = self.field.load_one(self.adapter, key)
            return self.field.prepare(vars)
    
    def load(self):
        if not self.loaded:
            oid_len = len(self.field.oid)
            vars = self.field.load_many(self.adapter)
            self.loaded = True
            for oid, v in self.field.prepare_many(vars):
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
        vars = field.load(adapter)
        return field.prepare(vars)

def set_one(adapter, field, value):
    # TODO: Implement set table value
    return field.set(adapter, value)
    
    
class DeviceMeta:
    def __init__(self):
        self.adapter_kwargs = {}

    def get_adapter(self, host, **kwargs):
        params = self.adapter_kwargs.copy()
        params.update(kwargs)
        return get_adapter(host, **params)

class AbstractContainer(object):
    prefix = None
    group = None
    
    def __init__(self, adapter, meta):
        self.adapter = adapter
        self.meta = meta
        self.items_list = []
        
    def __iter__(self):
        if self.__class__.prefix is None:
            result = iter([ (name, prop.__get__(self, self.__class__)) 
                        for name, prop in self.__class__.__dict__.items() 
                        if type(prop) == property ])
        else:
            result = list()
            result_dict = dict()
            fields = dict([ (field.oid, (name, field)) for name, field in self.meta.groups[self.__class__.group].items() ])
            prefix = self.__class__.prefix
            prefix_len = len(prefix)
            for oid, vars in self.adapter.getnext(prefix):
                if oid[:prefix_len] != prefix:
                    break
                if oid in fields:
                    name, field = fields[oid]
                    result.append((name, field.form(vars)))
                else:
                    # TODO: better way to handle table
                    for field_oid in fields:
                        field_oid_len = len(field_oid)
                        if oid[:field_oid_len] == field_oid:
                            name, field = fields[field_oid]
                            if isinstance(field, TableField):
                                if not result_dict.has_key(name):
                                    result_dict[name] = dict()
                                idx = oid[field_oid_len:]
                                if len(idx) == 1: idx = idx[0]
                                result_dict[name][idx] = field.form(vars)
                                break
            result += result_dict.items()

        return iter(result)
    def __setattr__(self, name, value):
        if name in self.__class__.items_list:
            self._set(self._get_field_by_name(name), value)
        else:
            super(AbstractContainer, self).__setattr__(name, value)
    def __getattr__(self, name):
        field = self._get_field_by_name(name)
        if field:
            return self._get(field)
        else:
            raise NameError("name '%s' is not defined" % name)
    def _get_field_by_name(self, name):
        if name in self.__class__.items_list:
            return self.meta.groups[self.__class__.group][name]
        else:
            return None
    def _get(self, field):
        return get(self.adapter, field)

    def _set(self, field, value):
        # FIXME: how could I handle the return value
        return set_one(self.adapter, field, value)

    def __call__(self, *args):
        # FIXME: what's this
        print args
            
class DeviceBase(type):
    def __new__(cls, name, bases, attrs):
        cls = super(DeviceBase, cls).__new__(cls, name, bases, attrs)
        meta = DeviceMeta()
        parents = get_all_parents(cls)[1:]
        
        # compute adapter params
        adapter_params_klass = [ getattr(klass, "AdapterParams", None) for klass in parents + (cls, ) ]
        adapter_kwargs = {}
        for klass in adapter_params_klass:
            if klass is None: continue
            adapter_kwargs.update(klass.__dict__)
        meta.adapter_kwargs = dict([(k, v) for (k, v) in adapter_kwargs.iteritems() if not k.starstwith("_")])
        
        # get parent fields and groups
        all_fields = {}
        all_groups = {}
        all_lut = {}
        for klass in parents:
            all_fields.update(klass.meta.fields)
            all_groups.update(klass.meta.groups)
            all_lut.update(klass.meta.lut)
        
        # get class fields and groups
        fields = {}
        groups = {}
        prefixes = {}
        for name, obj in attrs.items():
            if name.startswith("__"):
                continue
            if isinstance(obj, Field):
                fields[name] = obj
            elif isinstance(obj, Group):
                prefixes[name] = obj.prefix
                groups[name] = obj.fields
        
        # create oid -> field look up table
        lut = {}
        for group in groups.values():
            for name, field in group.items():
                lut[field.oid] = (name, field)

        all_fields.update(fields)
        all_groups.update(groups)
        all_lut.update(lut)
        
        meta.fields = all_fields
        meta.groups = all_groups
        meta.lut = lut
        
        # create containers class
        for group_name in groups.keys():
            klass = type(
                'Container', 
                (AbstractContainer, ), 
                {
                    "prefix": prefixes[group_name], 
                    "group": group_name,
                    "items_list": meta.groups[group_name].keys()
                })
            setattr(cls, group_name, klass)
        
        cls.meta = meta
        return cls


class AbstractDevice(object):
    __metaclass__ = DeviceBase
    
    classId = None
    
    def __init__(self, host, **kwargs):
        self.host = host
        self.meta = self.__class__.meta
        self.adapter = self.meta.get_adapter(host, **kwargs)
        # init containers
        for name in self.__class__.meta.groups.keys():
            obj = getattr(self.__class__, name)(self.adapter, self.meta)
            setattr(self, name, obj)
            
    def _get(self, field):
        return get(self.adapter, field)

    def prepare_val_by_oid(self, oid, var):
        field = None
        name = None
        index = None
        oid = tuple(oid)
        if oid in self.meta.lut.keys():
            name, field = self.meta.lut[oid]
        else:
            tf = filter(lambda x:oid[:len(x)] == x, self.meta.lut.keys())
            if tf:
                toid = tf[0]
                name, field = self.meta.lut[toid]
                index = oid[len(toid):]
        if field:
            field = field.prepare(var)
        return (name, field, index)
    
    def __repr__(self):
        return "<%s.%s object for host %s>" % (inspect.getmodule(self.__class__).__name__, self.__class__.__name__, self.host)
