from snmp_orm import get_device
from pprint import pprint

import logging
#logging.basicConfig(level=logging.DEBUG)

def main():
    d = get_device("127.0.0.1") 
    pprint(dict(d.system))
    pprint(dict(d.ifTable))
    pprint(dict(d.ip))

main()
