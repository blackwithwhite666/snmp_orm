from snmp_orm.config import DEBUG
from snmp_orm.settings import SnmpV2Settings, SnmpV3Settings
from snmp_orm.utils import str_to_oid
from snmp_orm.log import class_logger, instance_logger

from pprint import pformat
from pyasn1.type.univ import Null
from functools import wraps

class AbstractException(Exception):
    pass

class NotImplemented(Exception):
    pass

def log(f):
    @wraps(f)
    def wrapper(self, *args):
        self.inst_logger.debug( "[%s] Call %s%s" % (self.host, f.__name__, pformat(args)) )
        result = f(self, *args)
        self.inst_logger.debug( "[%s] %s return %s" % (self.host, f.__name__, pformat(result)) )
        return result
    if DEBUG: return wrapper
    else: return f

class Walker(object):
    """SNMP walker class"""

    def __init__(self, agent, baseoid, use_bulk=True, bulk_rows=None):
        self.baseoid = baseoid
        self.baseoid_len = len(baseoid)
        self.lastoid = baseoid
        self.agent = agent
        self.use_bulk = use_bulk
        self.bulk_rows = bulk_rows
        self.raise_stop = False

    def __iter__(self):
        return self
    
    def next(self):
        if self.raise_stop:
            raise StopIteration
        if self.use_bulk:
            rows = self.agent.getbulk(self.bulk_rows, self.lastoid)
        else:
            rows = self.agent.getnext(self.lastoid)
        if not rows:
            raise StopIteration
        if self.use_bulk:
            slice = 0
            for oid, _ in reversed(rows):
                diff = self.baseoid_len - len(oid)
                if (diff == 0 and oid[:-1] == self.baseoid[:-1]) or \
                    (diff != 0 and oid[:diff] == self.baseoid):
                    break
                else:
                    slice += 1
            if slice > 0: 
                rows = rows[:0-slice]
                self.raise_stop = True
                if not rows:
                    raise StopIteration
        self.lastoid = rows[-1][0]
        return rows

    def __del__(self):
        del self.agent

class AbstractAdapter:
    cls_logger = class_logger()
    inst_logger = instance_logger()
    
    def __init__(self, settings_read, settings_write=None):        
        settings_write = settings_write or settings_read.__class__()
        assert settings_write.__class__ == settings_read.__class__
        
        _settings_write = settings_write.__class__()
        _settings_write.update(settings_read)
        _settings_write.update(settings_write)
        
        # Create session for host
        if isinstance(settings_read, SnmpV3Settings):
            session_getter = self.get_snmp_v3_session
        elif isinstance(settings_read, SnmpV2Settings):
            session_getter = self.get_snmp_v2_session
        else:
            raise TypeError
        
        self.host = settings_read["host"]
        self.settings_read = settings_read
        self.settings_write = _settings_write
        
        self.session_read = session_getter(**settings_read.prepare_kwargs())
        if settings_read == _settings_write:
            self.session_write = self.session_read
        else:
            self.session_write = session_getter(**_settings_write.prepare_kwargs())
    
    def get_snmp_v2_session(self, host, port, version, community, **kwargs):
        raise NotImplemented
    
    def get_snmp_v3_session(self, host, port, version, sec_name=None, sec_level=None, 
                                   auth_protocol=None, auth_passphrase=None, 
                                   priv_protocol=None, priv_passphrase=None, **kwargs):
        raise NotImplemented
        
    @log
    def get(self, *args):
        ''' Return tuple of pairs:
            ((1, 3, 6, 1, 2, 1, 1, 1, 0),
                      OctetString('DGS-3100-24 Gigabit stackable L2 Managed Switch'))
        '''
        return self.session_read.get(*map(str_to_oid, args))
    
    def get_one(self, oid):
        ''' Return oid value
        '''
        vars = self.get(oid)
        if vars:
            result = vars[0][1]
            if not isinstance(result, Null):
                return result
        return None
    
    @log
    def getnext(self, *args):
        ''' Return table:
                [   ((1, 3, 6, 1, 2, 1, 1, 1, 0),
                      OctetString('DGS-3100-24 Gigabit stackable L2 Managed Switch')),
                    ((1, 3, 6, 1, 2, 1, 1, 2, 0), ObjectIdentifier('1.3.6.1.4.1.171.10.94.1')),
                    ((1, 3, 6, 1, 2, 1, 1, 3, 0), TimeTicks('512281800')),
                    ((1, 3, 6, 1, 2, 1, 1, 4, 0), OctetString('')) ]
        '''
        return self.session_read.getnext(*map(str_to_oid, args))
    
    @log
    def getbulk(self, rows=None, *args):
        ''' Return same as getnext method, but use rows number
        '''
        if rows is None: rows = self.settings_read["bulk_rows"]
        return self.session_read.getbulk(rows, *map(str_to_oid, args))
        
    @log
    def set(self, *args):
        #TODO: set more than one values
        return self.session_write.set(args)
    
    def walk(self, oid):
        oid = str_to_oid(oid)
        result = []
        walker = Walker(self, oid, use_bulk=self.settings_read["use_bulk"], bulk_rows=self.settings_read["bulk_rows"])
        [ result.extend(rows) for rows in walker ]
        return result
