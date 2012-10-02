from snmp_orm import get_device
from pprint import pprint

import logging
logging.basicConfig(level=logging.DEBUG)

def main():
    d = get_device("192.168.0.253")
    print dict(d.system)

main()
