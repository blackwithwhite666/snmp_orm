from __future__ import absolute_import

import snmp_orm.tests.agent as agent

import unittest
import os
import threading

base = os.path.dirname(os.path.abspath(__file__))


if __name__ == '__main__':
    thread = threading.Thread(target=agent.start)
    thread.daemon = True
    thread.start()
    suite = unittest.TestLoader().discover(start_dir=os.path.join(base, "tests"))
    unittest.TextTestRunner(verbosity=2).run(suite)
    agent.stop()
    thread.join()
