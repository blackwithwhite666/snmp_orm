import logging
from pprint import pprint

from pysnmp.proto import rfc1902

from snmp_orm import get_device

#logging.basicConfig(level=logging.DEBUG)


def play(ip):
    d = get_device(ip)
    print "System Contact is", d.system.sysContact
    print "Now set to 'Admin of " + str(ip)
    #d.system.sysContact = 'Admin of ' + str(ip)


if __name__ == '__main__':
    import sys
    ip = '127.0.0.1'
    if len(sys.argv) >= 2:
        ip = sys.argv[1]
    play(ip)
