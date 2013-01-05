from __future__ import absolute_import

from unittest import TestCase as BaseTestCase

from snmp_orm.tests.agent import BackgroundAgent, SysDescr, Uptime
from snmp_orm.config import SNMP_TEST_AGENT_ADDRESS


class TestCase(BaseTestCase):

    instructions = None

    def setUp(self):
        host, port = SNMP_TEST_AGENT_ADDRESS
        agent = self.agent = BackgroundAgent(host, port)
        instructions = self.instructions or (SysDescr(), Uptime())
        for instr in instructions:
            agent.registerInstr(instr)
        agent.start()
        self.addCleanup(agent.stop)
        super(TestCase, self).setUp()
