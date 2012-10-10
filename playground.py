from snmp_orm import get_device
from pprint import pprint
from snmp_orm.devices.abstract import AbstractContainer

import logging
#logging.basicConfig(level=logging.DEBUG)

def play(ip):
    d = get_device(ip)
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
