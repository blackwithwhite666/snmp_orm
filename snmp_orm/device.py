"""Manager for devices."""
from __future__ import absolute_import

import logging

from six import b, string_types, binary_type
from pyasn1.type.univ import ObjectIdentifier

from snmp_orm import devices
from snmp_orm.utils import find_classes, oid_to_str
from snmp_orm.adapter import get_adapter
from snmp_orm.config import OID_OBJECT_ID

logger = logging.getLogger(__name__)


class DeviceClassRegistry(dict):

    def __init__(self):
        self.default_device = devices.DefaultDevice

        for klass in self.iter_devices():
            objectIds = self.format_objectId(klass.classId)
            if not isinstance(objectIds, (list, tuple)):
                objectIds = (objectIds, )
            for objectId in objectIds:
                objectId = self.format_objectId(objectId)
                if objectId and objectId not in self:
                    self[objectId] = klass

    def format_objectId(self, objectId):
        if objectId is None:
            return None
        elif isinstance(objectId, binary_type):
            return objectId
        elif isinstance(objectId, string_types):
            return b(objectId)
        elif isinstance(objectId, ObjectIdentifier):
            return b(objectId)
        elif isinstance(objectId, (tuple, list)):
            return oid_to_str(objectId)
        else:
            raise ValueError('Unknown OID %r' % objectId)

    def iter_devices(self):
        """Find existed device classes."""
        for cls in find_classes(devices.AbstractDevice, [devices]):
            yield cls

    def get_class(self, objectId):
        objectId = self.format_objectId(objectId)
        try:
            return self[objectId]
        except KeyError:
            return self.default_device


class DeviceManager(object):

    def __init__(self):
        self.id_cache = {}
        self.registry = DeviceClassRegistry()

    def get_device_id(self, host, **kwargs):
        host = unicode(host).lower()
        logger.debug("Get device class for %s" % host)
        if host in self.id_cache:
            objectId = self.id_cache[host]
        else:
            objectId = self.autodetect_id(host, **kwargs)
            self.id_cache[host] = objectId
        return objectId

    def autodetect_id(self, host, **kwargs):
        logger.debug("Trying to detect objectId for %s" % host)
        adapter = get_adapter(host, **kwargs)
        id_ = oid_to_str(adapter.get_one(OID_OBJECT_ID))
        logger.debug("objectId for %s is %s" % (host, id_))
        return id_

    def get_class(self, host, **kwargs):
        cls = self.registry.get_class(self.get_device_id(host, **kwargs))
        logger.debug("Use %s for %s" % (repr(cls), host))
        return cls

manager = DeviceManager()


def get_device(host, **kwargs):
    """Return `Device` instance for specified host.
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
    """
    cls = manager.get_class(host, **kwargs)
    return cls(host, **kwargs)
