"""Default configuration for snmp_orm."""
from __future__ import absolute_import


#: Should we print debug info?
DEBUG = False

#: Which adapter we should use by default?
DEFAULT_ADAPTER = 'snmp_orm.adapters.pysnmp'

#: Default SNMP device's port to connect.
SNMP_PORT = 161

#: Default SNMP device's address to connect, used in unit-tests.
SNMP_TEST_AGENT_ADDRESS = ('localhost', 60161)

#: How many rows should be read in bulk-mode at once.
BULK_ROW = 50

#: Which OID should be used to detect device model.
OID_OBJECT_ID = '1.3.6.1.2.1.1.2.0'
