"""Load and store all existed adapter's classes."""
from __future__ import absolute_import

from .utils import import_class
from .settings import SnmpV2Settings, SnmpV3Settings
from .config import DEFAULT_ADAPTER


class AdapterRegistry(dict):
    """Storage for adapter's classes."""

    def __init__(self):
        self.get_class(DEFAULT_ADAPTER)

    def get_class(self, class_name):
        if class_name in self:
            return self[class_name]
        else:
            mod = import_class(class_name)
            cls = getattr(mod, "Adapter")
            self[class_name] = cls
            return cls


#: Global storage of adapters.
registry = AdapterRegistry()


def get_adapter(host, version=None, class_name=None, **kwargs):
    """Create adapter instance for given host with given settings."""
    cls = registry.get_class(class_name or DEFAULT_ADAPTER)

    if not host:
        raise ValueError('Provided host name is empty!')

    version = version if version in (1, 2, 3) else 2
    kwargs.update({"host": host,
                   "version": version})

    settings_cls = SnmpV3Settings if version == 3 else SnmpV2Settings
    settings_read_kwargs = dict((key, value)
                                for key, value in kwargs.items()
                                if not key.startswith("write_"))
    for key in settings_read_kwargs.keys():
        del kwargs[key]
    settings_write_kwargs = dict((key.replace("write_", ""), value)
                                 for key, value in kwargs.items())

    return cls(settings_read=settings_cls(**settings_read_kwargs),
               settings_write=settings_cls(**settings_write_kwargs))
