from snmp_orm.adapter import get_adapter
from snmp_orm.fields import Field, TableField, Group
from snmp_orm.utils import get_all_parents

import inspect


def load(f):
    def wrapper(self, *args, **kwargs):
        self.load()
        return f(self, *args, **kwargs)
    return wrapper

class TableListProxy(list):
    for methodName in set(dir(list)) - set(dir(object)):
        f = getattr(list, methodName)
        locals()[methodName] = load(f)
        
    def __init__(self, adapter, field):
        list.__init__(self)
        self.adapter = adapter
        self.d = None
        self.field = field
        self.loaded = False
    
    @load
    def __str__(self): return list.__str__(self)
    @load
    def __repr__(self): return list.__repr__(self)
    
    def oid(self, key):
        if self.loaded:
            if self.d is None:
                self.d = dict([ (oid[-1], value) for oid, value in self ])
            return self.d.get(int(key), None)
        else:
            vars = self.field.load_one(self.adapter, key)
            return self.field.prepare(vars)
    
    def load(self):
        if not self.loaded:
            vars = self.field.load_many(self.adapter)
            list.extend(self, self.field.prepare_many(vars))
            self.loaded = True
            

def get(adapter, field):
    if isinstance(field, TableField):
        return TableListProxy(adapter, field)
    else:
        vars = field.load(adapter)
        return field.prepare(vars)
    
    
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
        
    def __iter__(self):
        if self.__class__.prefix is None:
            result = iter([ (name, prop.__get__(self, self.__class__)) 
                        for name, prop in self.__class__.__dict__.items() 
                        if type(prop) == property ])
        else:
            result = []
            fields = dict([ (field.oid, (name, field)) for name, field in self.meta.groups[self.__class__.group].items() ])
            for oid, vars in self.adapter.getbulk(len(fields), self.__class__.prefix):
                if oid in fields:
                    name, field = fields[oid]
                    result.append((name, field.form(vars)))
        return iter(result)
    
    def _get(self, field):
        return get(self.adapter, field)
        
            
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
        for klass in parents:
            all_fields.update(klass.meta.fields)
            all_groups.update(klass.meta.groups)
        
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
        
        all_fields.update(fields)
        all_groups.update(groups)
            
        meta.fields = all_fields
        meta.groups = all_groups
        
        # create containers class
        for group_name in groups.keys():
            klass = type('Container', (AbstractContainer, ), {"prefix": prefixes[group_name], "group": group_name})
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
    
    def __repr__(self):
        return "<%s.%s object for host %s>" % (inspect.getmodule(self.__class__).__name__, self.__class__.__name__, self.host)