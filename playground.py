from snmp_orm import get_device
from pprint import pprint
from snmp_orm.devices.abstract import AbstractContainer
from pysnmp.proto import rfc1902
import logging
#logging.basicConfig(level=logging.DEBUG)

def play(ip):
    d = get_device(ip)
    print d.system.sysContact
    d.system.sysContact = str(ip)
   
    print 'row:', d.ifTable.ifAdminStatus
    print 'row[2]', d.ifTable.ifAdminStatus[(2,)]
    d.ifTable.ifAdminStatus[2] = 'down'
    print d.ifTable.ifAdminStatus[2]
    d.ifTable.ifAdminStatus[2] = 1
    print d.ifTable.ifAdminStatus[2]

    for k, i in d.__dict__.items():
        if isinstance(i, AbstractContainer):
            print '*' * 78
            print k, '=>'
            pprint( dict(i) )


if __name__ == '__main__':
    import sys
    ip = '127.0.0.1'
    if len(sys.argv) >= 2:
        ip = sys.argv[1]
    play(ip)
