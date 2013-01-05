from snmp_orm.adapters.abstract_adapter import AbstractAdapter, AbstractException
from snmp_orm.utils import str_to_oid 

from pysnmp.entity.rfc3413.oneliner.cmdgen import CommunityData, UsmUserData, UdpTransportTarget, CommandGenerator
from pysnmp import error as pysnmp_error

class PySNMPError(AbstractException): pass

class AbstractSession(object):
    def __init__(self, host, port=None):
        self.transportTarget = UdpTransportTarget((host, port))
        self.authData = None
        self.generator = CommandGenerator()

    def format_varBinds(self, varBinds):
        return [ (str_to_oid(oid), value) for oid, value in varBinds ]

    def format_varBindTable(self, varBindTable):
        result = []
        for varBinds in varBindTable:
            result.extend(self.format_varBinds(varBinds))
        return result

    def handle_error(self, errorIndication, errorStatus, errorIndex, varBinds=None, varBindTable=None):
        if errorIndication:
            raise PySNMPError(errorIndication)
        elif errorStatus:
            vars = varBinds or varBindTable[-1]
            text = errorStatus.prettyPrint()
            position = errorIndex and vars[int(errorIndex)-1] or '?'
            raise PySNMPError("%s at %s" % (text, position))
        
    def get(self, *args):
        try:
            errorIndication, errorStatus, \
                errorIndex, varBinds = self.generator.getCmd(self.authData, self.transportTarget, *args)
        except pysnmp_error.PySnmpError, e:
            # handle origin PySNMPError from pysnmp module.
            errorIndication = e
            errorStatus, errorIndex, varBinds = None, None, []
        
        
        self.handle_error(errorIndication, errorStatus, errorIndex, varBinds)
        return self.format_varBinds(varBinds)
        
    def set(self, *args):
        errorIndication, errorStatus, \
                 errorIndex, varBinds = self.generator.setCmd(self.authData, self.transportTarget, *args)
        self.handle_error(errorIndication, errorStatus, errorIndex, varBinds)
        return self.format_varBinds(varBinds)
    
    def getnext(self, *args):
        errorIndication, errorStatus, errorIndex, \
                 varBindTable = self.generator.nextCmd(self.authData, self.transportTarget, *args)
        self.handle_error(errorIndication, errorStatus, errorIndex, None, varBindTable)
        return self.format_varBindTable(varBindTable)
            
    def getbulk(self, rows, *args):
        errorIndication, errorStatus, errorIndex, \
                 varBindTable = self.generator.bulkCmd(self.authData, self.transportTarget, 0, rows, *args)
        self.handle_error(errorIndication, errorStatus, errorIndex, None, varBindTable)
        return self.format_varBindTable(varBindTable)

    
class Session(AbstractSession):
    def __init__(self, host, port, version, community):
        super(Session, self).__init__(host, port)
        self.authData = CommunityData('agent', community, None if version == 2 else 0)

class UsmSession(AbstractSession):
    def __init__(self, host, port=None, sec_name=None, sec_level=None, 
                auth_protocol=None, auth_passphrase=None, 
                priv_protocol=None, priv_passphrase=None):
        super(UsmSession, self).__init__(host, port)
        self.authData = UsmUserData(sec_name, auth_passphrase, priv_passphrase)
        
class Adapter(AbstractAdapter):
    def get_snmp_v2_session(self, host, port, version, community, **kwargs):
        if community is None: raise TypeError("community can`t be None")
        return Session(host, port, version, community)
    
    def get_snmp_v3_session(self, host, port, version, sec_name, sec_level, 
                                   auth_protocol, auth_passphrase, 
                                   priv_protocol, priv_passphrase, **kwargs):
        if sec_name is None: raise TypeError("sec_name can`t be None")
        if auth_passphrase is None: raise TypeError("auth_passphrase can`t be None")
        if priv_passphrase is None: raise TypeError("priv_passphrase can`t be None")
        return UsmSession(host, port, sec_name, sec_level, 
                          auth_protocol, auth_passphrase, 
                          priv_protocol, priv_passphrase)
