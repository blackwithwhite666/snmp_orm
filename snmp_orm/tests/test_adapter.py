"""Load and store all existed adapter's classes."""
from __future__ import absolute_import

import unittest

from pysnmp.proto.rfc1902 import TimeTicks

from snmp_orm.adapters.abstract_adapter import AbstractAdapter
from snmp_orm.adapter import get_adapter
from snmp_orm import config


class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.adapter = get_adapter("localhost", port=config.SNMP_TEST_AGENT_PORT)

    def test_adapter_class(self):
        self.assertTrue(isinstance(self.adapter, AbstractAdapter))

    def test_adapter_get(self):
        self.assertTrue(str(self.adapter.get_one("1.3.6.1.2.1.1.1.0")).startswith("PySNMP"))

    def test_adapter_result_type(self):
        self.assertTrue(isinstance(self.adapter.get_one("1.3.6.1.2.1.1.3.0"), TimeTicks))
