"""Manager for devices."""
from __future__ import absolute_import

import logging

from six import b, u, string_types, binary_type
from pyasn1.type.univ import ObjectIdentifier

from snmp_orm import devices
from snmp_orm.utils import find_classes, oid_to_str, symbol_by_name
from snmp_orm.adapter import get_adapter
from snmp_orm.config import OID_OBJECT_ID

logger = logging.getLogger(__name__)


def maybe_oid_to_str(objectId):
    """Convert given OID to string if needed."""
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


class DeviceClassRegistry(dict):
    """Store mapping of OID to device class.

    Arguments:

    - **packages**, iterable, contains list of packages with defined
        :class:`devices.Device`;
    - **default**, default class, that should returned if no class found;

    """

    #: Abstract device class, used to find other devices in package.
    AbstractDevice = devices.AbstractDevice

    def __init__(self, packages=None, default=None):
        self.packages = tuple(symbol_by_name(maybe_path)
                              for maybe_path in (packages or [devices]))
        self.default_device = symbol_by_name(default or devices.DefaultDevice)

        for cls in self.find_devices():
            self.add(cls)

    def find_devices(self):
        """Find existed device classes."""
        for cls in find_classes(self.AbstractDevice, self.packages):
            yield cls

    def add(self, cls):
        """Add class to registry."""
        assert issubclass(cls, self.AbstractDevice), 'wrong cls given'
        objectIds = cls.classId
        if not isinstance(objectIds, (list, tuple, set)):
            objectIds = (objectIds, )
        for objectId in objectIds:
            objectId = maybe_oid_to_str(objectId)
            if objectId and objectId not in self:
                self[objectId] = cls

    def __getitem__(self, key):
        """Get class by it's OID or return default."""
        objectId = maybe_oid_to_str(key)
        try:
            return super(DeviceClassRegistry, self).__getitem__(objectId)
        except KeyError:
            return self.default_device
    get_class = __getitem__


class DeviceManager(object):
    """Used to get class of given host."""

    Registry = DeviceClassRegistry

    def __init__(self, registry=None):
        self._cache = {}
        self.registry = registry or self.Registry()

    def _get_device_id(self, host, **kwargs):
        host = u(host).lower()
        logger.debug("Get device class for %s" % host)
        try:
            oid = self._cache[host]
        except KeyError:
            oid = self._cache[host] = self._autodetect_id(host, **kwargs)
        return oid

    def _autodetect_id(self, host, **kwargs):
        logger.debug("Trying to detect objectId for %s" % host)
        adapter = get_adapter(host, **kwargs)
        id_ = oid_to_str(adapter.get_one(OID_OBJECT_ID))
        assert id_ is not None, 'empty OID returned'
        logger.debug("objectId for %s is %s" % (host, id_))
        return id_

    def get_class(self, host, **kwargs):
        registry = kwargs.pop('registry', None)
        registry = self.registry if registry is None else registry
        cls = registry[self._get_device_id(host, **kwargs)]
        logger.debug("Use %r for %s" % (cls, host))
        return cls

#: Default device manager instance.
default_manager = DeviceManager()


def get_device(host, **kwargs):
    """Return `Device` instance for specified host.

    Arguments for device (for write access use `write_` prefix):

    - **host** -- IP or hostname if snmp agent;
    - **port** -- agent UDP port, default 161;
    - **version** -- SNMP version, 1, 2 or 3;
    - **registry** -- custom registry class for class lookup;
    - **class_name** -- adapter class;
    - **community** -- SNMP community;
    - **sec_name** -- security name;
    - **sec_level** -- security level;
    - **auth_protocol** -- auth protocol;
    - **auth_passphrase** -- auth passphrase;
    - **priv_protocol** -- priv protocol;
    - **priv_passphrase** -- priv passphrase.

    Other arguments:

    - **manager** custom instance of manager class;
    - **device_cls** custom device class, will be used instead of autolookup.

    """
    manager = symbol_by_name(kwargs.pop('manager', default_manager))
    cls = symbol_by_name(kwargs.pop('device_cls', None))
    cls = manager.get_class(host=host, **kwargs) if cls is None else cls
    return cls(host, **kwargs)
