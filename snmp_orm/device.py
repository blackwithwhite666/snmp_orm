from snmp_orm.utils import import_class, walklevel, oid_to_str
from snmp_orm.adapter import get_adapter
from snmp_orm.devices.default import Device as DefaultDevice
from snmp_orm.config import OID_OBJECT_ID
from snmp_orm.log import class_logger, instance_logger

import os

base = os.path.dirname(os.path.abspath(__file__))

class DeviceClassRegistry(dict):
    def __init__(self):
        self.default_device = DefaultDevice
        for klass in self.iter_devices(): 
            objectIds = self.format_objectId(klass.classId)
            if type(objectIds) not in (list, tuple):
                objectIds = (objectIds, )
            for objectId in objectIds:
                if objectId not in self:
                    self[objectId] = klass
        
    def format_objectId(self, objectId):
        if isinstance(objectId, str):
            return objectId
        return str(objectId)
        
    def iter_devices(self):
        groups = walklevel(os.path.join(base, "devices"), level=1)
        for group in list(groups)[1:]:
            mod_name = os.path.basename(group[0])
            for f in group[2]:
                root, ext = os.path.splitext(f)
                if ext != ".py" or root == "__init__": continue
                mod = import_class("snmp_orm.devices.%s.%s" % (mod_name, root))
                device = getattr(mod, "Device", None)
                if device is None: continue
                yield device
                
    def get_class(self, objectId):
        objectId = self.format_objectId(objectId)
        if objectId in self:
            return self[objectId]
        return self.default_device

registry = DeviceClassRegistry()

class DeviceManager:
    cls_logger = class_logger()
    inst_logger = instance_logger()
    
    def __init__(self):
        self.id_cache = {}
        
    def get_device_id(self, host, **kwargs):
        host = unicode(host).lower()
        self.inst_logger.debug("Get device class for %s" % host)
        if host in self.id_cache:
            objectId = self.id_cache[host]
        else:
            objectId = self.autodetect_id(host, **kwargs)
            self.id_cache[host] = objectId
        return objectId
    
    def autodetect_id(self, host, **kwargs):
        self.inst_logger.debug("Trying to detect objectId for %s" % host)
        adapter = get_adapter(host, **kwargs)
        id = oid_to_str(adapter.get_one(OID_OBJECT_ID))
        self.inst_logger.debug("objectId for %s is %s" % (host, id))
        return id
    
    def get_class(self, host, **kwargs):
        klass = registry.get_class(self.get_device_id(host, **kwargs))
        self.inst_logger.debug("Use %s for %s" % (repr(klass), host))
        return klass
        
manager = DeviceManager()
    
def get_device(host, **kwargs):
    ''' Return `Device` instance for specified host.
     Keyword arguments (for write access use `write_` prefix):
     host -- IP or hostname if snmp agent
     port -- agent UDP port, default 161
     version -- SNMP version, 1, 2 or 3
     class_name -- adapter class
     community -- SNMP community
     sec_name -- security name
     sec_level -- security level 
     auth_protocol -- auth protocol
     auth_passphrase -- auth passphrase
     priv_protocol -- priv protocol
     priv_passphrase -- priv passphrase
    '''
    cls = manager.get_class(host, **kwargs)
    return cls(host, **kwargs)