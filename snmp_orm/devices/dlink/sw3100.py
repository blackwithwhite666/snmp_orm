"""Implement custom OID for D-link SW-3100 switch."""
from __future__ import absolute_import

from snmp_orm.devices.default import Device as DefaultDevice
from snmp_orm.fields import SingleValueField, Group


class Device(DefaultDevice):
    classId = "1.3.6.1.4.1.171.10.94.1"
