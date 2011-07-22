from snmp_orm.config import SNMP_PORT, BULK_ROW

class SettingsMeta(type):
    def __new__(cls, name, bases, attrs):
        cls = super(SettingsMeta, cls).__new__(cls, name, bases, attrs)
        allowed_keys = list(getattr(cls, "allowed_keys", ()))
        default_values = {}
        for klass in bases:
            allowed_keys.extend(getattr(klass, "allowed_keys", ()))
            default_values.update(getattr(klass, "default_values", {}))
        cls.allowed_keys = tuple(allowed_keys)
        default_values.update(getattr(cls, "default_values", {}))
        cls.default_values = default_values
        return cls

class BaseSettings(dict):
    __metaclass__ = SettingsMeta
    
    allowed_keys = ("host", "port", "version", "use_bulk", "bulk_rows")
    default_values = {"port": SNMP_PORT,
                      "version": lambda v: v if v in (1, 2, 3) else 2,
                      "use_bulk": True,
                      "bulk_rows": BULK_ROW,
                      }
    
    def __init__(self, **kwargs):
        self.update(kwargs)
        for key, value in self.__class__.default_values.items():
            self.set_default(key, value)
    
    def set_default(self, key, default):
        if key in self.allowed_keys:
            if callable(default):
                self[key] = default(key)
            elif key not in self or not self[key]:
                self[key] = default
                
    def prepare_kwargs(self):
        return dict([ (key, value) 
                     for key, value in self.items() 
                     if key in self.__class__.allowed_keys ])
    
class SnmpV2Settings(BaseSettings):
    allowed_keys = ("community", )
    default_values = {"community": "public"}
    
class SnmpV3Settings(BaseSettings):
    allowed_keys = ("sec_name", "sec_level", 
                    "auth_protocol", "auth_passphrase", 
                    "priv_protocol", "priv_passphrase")
