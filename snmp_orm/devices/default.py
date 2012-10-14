from snmp_orm.devices.abstract import AbstractDevice
from snmp_orm.defines import IANAifType, ifStatus, ipForwarding, ipRouteType, ipRouteProto, ipNetToMediaType
from snmp_orm.fields import Group, TableValueField, \
                            UnicodeField, OIDField, IntegerField, TimeTickField, FromDictField, LongIntegerField, \
                            IntegerTableField, UnicodeTableField, FromDictTableField, MacTableField, TimeTickTableField, \
                            LongIntegerTableField, OIDTableField, IPAddressTableField

class Device(AbstractDevice):
    # SNMP MIB-2 System (1.3.6.1.2.1.1)
    system = Group(
                   prefix = (1,3,6,1,2,1,1),
                   sysDescr = UnicodeField((1,3,6,1,2,1,1,1,0)),
                   sysObjectID = OIDField((1,3,6,1,2,1,1,2,0)),
                   sysUpTime = TimeTickField((1,3,6,1,2,1,1,3,0)),
                   sysContact = UnicodeField((1,3,6,1,2,1,1,4,0)),
                   sysName = UnicodeField((1,3,6,1,2,1,1,5,0)),
                   sysLocation = UnicodeField((1,3,6,1,2,1,1,6,0)),
                   sysServices = IntegerField((1,3,6,1,2,1,1,7,0)),
                   )
    
    # SNMP MIB-2 Interfaces (1.3.6.1.2.1.2)
    ifNumber = IntegerField((1,3,6,1,2,1,2,1,0))
    ifTable = Group(
                   prefix = (1,3,6,1,2,1,2,2),
                   ifIndex = IntegerTableField((1,3,6,1,2,1,2,2,1,1)),
                   ifDescr = UnicodeTableField((1,3,6,1,2,1,2,2,1,2)),
                   ifType = FromDictTableField((1,3,6,1,2,1,2,2,1,3), IANAifType, int),
                   ifMtu = IntegerTableField((1,3,6,1,2,1,2,2,1,4)),
                   ifSpeed = IntegerTableField((1,3,6,1,2,1,2,2,1,5)),
                   ifPhysAddress = MacTableField((1,3,6,1,2,1,2,2,1,6)),
                   ifAdminStatus = FromDictTableField((1,3,6,1,2,1,2,2,1,7), ifStatus, int),
                   ifOperStatus = FromDictTableField((1,3,6,1,2,1,2,2,1,8), ifStatus, int),
                   ifLastChange = TimeTickTableField((1,3,6,1,2,1,2,2,1,9)),
                   ifInOctets = LongIntegerTableField((1,3,6,1,2,1,2,2,1,10)),
                   ifInUcastPkts = LongIntegerTableField((1,3,6,1,2,1,2,2,1,11)),
                   ifInNUcastPkts = LongIntegerTableField((1,3,6,1,2,1,2,2,1,12)),
                   ifInDiscards = LongIntegerTableField((1,3,6,1,2,1,2,2,1,13)),
                   ifInErrors = LongIntegerTableField((1,3,6,1,2,1,2,2,1,14)),
                   ifInUnknownProtos = LongIntegerTableField((1,3,6,1,2,1,2,2,1,15)),
                   ifOutOctets = LongIntegerTableField((1,3,6,1,2,1,2,2,1,16)),
                   ifOutUcastPkts = LongIntegerTableField((1,3,6,1,2,1,2,2,1,17)),
                   ifOutNUcastPkts = LongIntegerTableField((1,3,6,1,2,1,2,2,1,18)),
                   ifOutDiscards = LongIntegerTableField((1,3,6,1,2,1,2,2,1,19)),
                   ifOutErrors = LongIntegerTableField((1,3,6,1,2,1,2,2,1,20)),
                   ifOutQLen = LongIntegerTableField((1,3,6,1,2,1,2,2,1,21)),
                   ifSpecific = OIDTableField((1,3,6,1,2,1,2,2,1,22)),
                   )
    
    # ip (1.3.6.1.2.1.4)
    ip = Group(
                    prefix = (1,3,6,1,2,1,4),
                    ipForwarding = FromDictField((1,3,6,1,2,1,4,1,0), ipForwarding, int),
                    ipDefaultTTL = IntegerField((1,3,6,1,2,1,4,2,0)),
                    ipInReceives = LongIntegerField((1,3,6,1,2,1,4,3,0)),
                    ipInHdrErrors = LongIntegerField((1,3,6,1,2,1,4,4,0)),
                    ipInAddrErrors = LongIntegerField((1,3,6,1,2,1,4,5,0)),
                    ipForwDatagrams = LongIntegerField((1,3,6,1,2,1,4,6,0)),
                    ipInUnknownProtos = LongIntegerField((1,3,6,1,2,1,4,7,0)),
                    ipInDiscards = LongIntegerField((1,3,6,1,2,1,4,8,0)),
                    ipInDelivers = LongIntegerField((1,3,6,1,2,1,4,9,0)),
                    ipOutRequests = LongIntegerField((1,3,6,1,2,1,4,10,0)),
                    ipOutDiscards = LongIntegerField((1,3,6,1,2,1,4,11,0)),
                    ipOutNoRoutes = LongIntegerField((1,3,6,1,2,1,4,12,0)),
                    ipReasmTimeout = LongIntegerField((1,3,6,1,2,1,4,13,0)),
                    ipReasmReqds = LongIntegerField((1,3,6,1,2,1,4,14,0)),
                    ipReasmOKs = LongIntegerField((1,3,6,1,2,1,4,15,0)),
                    ipReasmFails = LongIntegerField((1,3,6,1,2,1,4,16,0)),
                    ipFragOKs = LongIntegerField((1,3,6,1,2,1,4,17,0)),
                    ipFragFails = LongIntegerField((1,3,6,1,2,1,4,18,0)),
                    ipFragCreates = LongIntegerField((1,3,6,1,2,1,4,19,0)),
                    # ipAddrTable space
                    ipAdEntAddr = IPAddressTableField((1,3,6,1,2,1,4,20,1,1)),
                    ipAdEntIfIndex = IntegerTableField((1,3,6,1,2,1,4,20,1,2)),
                    ipAdEntNetMask = IPAddressTableField((1,3,6,1,2,1,4,20,1,3)),
                    ipAdEntBcastAddr = IPAddressTableField((1,3,6,1,2,1,4,20,1,4)),
                    ipAdEntReasmMaxSize = IntegerField((1,3,6,1,2,1,4,20,1,5,0)),
                    # ipRouteTable space
                    ipRouteDest = IPAddressTableField((1,3,6,1,2,1,4,21,1,1)),
                    ipRouteIfIndex = IntegerTableField((1,3,6,1,2,1,4,21,1,2)),
                    ipRouteMetric1 = IntegerTableField((1,3,6,1,2,1,4,21,1,3)),
                    ipRouteMetric2 = IntegerTableField((1,3,6,1,2,1,4,21,1,4)),
                    ipRouteMetric3 = IntegerTableField((1,3,6,1,2,1,4,21,1,5)),
                    ipRouteMetric4 = IntegerTableField((1,3,6,1,2,1,4,21,1,6)),
                    ipRouteNextHop = IPAddressTableField((1,3,6,1,2,1,4,21,1,7)),
                    ipRouteType = FromDictTableField((1,3,6,1,2,1,4,21,1,8), ipRouteType, int),
                    ipRouteProto = FromDictTableField((1,3,6,1,2,1,4,21,1,9), ipRouteProto, int),
                    ipRouteAge = IntegerTableField((1,3,6,1,2,1,4,21,1,10)),
                    ipRouteMask = IPAddressTableField((1,3,6,1,2,1,4,21,1,11)),
                    ipRouteMetric5 = IntegerTableField((1,3,6,1,2,1,4,21,1,12)),
                    ipRouteInfo = OIDTableField((1,3,6,1,2,1,4,21,1,13)),
                    # ipNetToMediaTable space
                    ipNetToMediaIfIndex = IntegerTableField((1,3,6,1,2,1,4,22,1,1)),
                    ipNetToMediaPhysAddress = MacTableField((1,3,6,1,2,1,4,22,1,2)),
                    ipNetToMediaNetAddress = IPAddressTableField((1,3,6,1,2,1,4,22,1,3)),
                    ipNetToMediaType = FromDictTableField((1,3,6,1,2,1,4,22,1,4), ipNetToMediaType, int),
                    
                    ipRoutingDiscards = LongIntegerField((1,3,6,1,2,1,4,23,0)),
                    )
    
