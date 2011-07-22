from snmp_orm.devices.default import Device as DefaultDevice
from snmp_orm.fields import SingleValueField, Group

class Device(DefaultDevice):
    classId = "1.3.6.1.4.1.171.10.94.1"