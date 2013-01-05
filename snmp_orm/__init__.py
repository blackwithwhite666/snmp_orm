"""Python-based tool providing a simple interface to work SNMP agents."""

VERSION = (0, 1, 0)

__version__ = '.'.join(map(str, VERSION[0:3]))
__author__ = 'Xiongfei(Alex) GUO, Lei(Carmack) Jia, Lipin Dmitriy'
__contact__ = 'xfguo@credosemi.com, jialer.2007@gmail.com, blackwithwhite666@gmail.com'
__homepage__ = 'https://github.com/blackwithwhite666/snmp_orm'
__docformat__ = 'restructuredtext'

# -eof meta-

from snmp_orm.device import get_device


__all__ = ['get_device']
