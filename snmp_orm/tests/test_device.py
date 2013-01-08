from __future__ import absolute_import

import unittest

from mock import Mock, MagicMock

from snmp_orm.tests.utils import TestCase
from snmp_orm.tests.agent import Instr
from snmp_orm.device import DeviceClassRegistry, DeviceManager, get_device
from snmp_orm.devices import DefaultDevice, AbstractDevice


class ObjectID(Instr):

    name = (1, 3, 6, 1, 2, 1, 1, 2, 0)

    def execute(self, module):
        return module.ObjectIdentifier(
            (1, 3, 6, 1, 4, 1, 8072, 3, 2, 10)
        )


class TestDeviceClassRegistry(TestCase):
    pass


class TestDeviceManager(TestCase):

    instructions = (ObjectID(), )

    def setUp(self):
        self.manager = DeviceManager()
        super(TestDeviceManager, self).setUp()

    def test_custom_registry(self):
        obj = object()
        d = {'1.3.6.1.4.1.8072.3.2.10': obj}
        registry = MagicMock(spec_set=dict)
        registry.__getitem__.side_effect = lambda key: d[key]
        cls = self.manager.get_class(host=self.test_host, port=self.test_port,
                                     registry=registry)
        self.assertTrue(obj is cls)


class TestGetDevice(TestCase):

    instructions = (ObjectID(), )

    def test_get_device(self):
        device = get_device(host=self.test_host, port=self.test_port)
        self.assertTrue(isinstance(device, DefaultDevice))

    def test_custom_manager(self):
        manager = Mock()
        get_device(host=self.test_host, port=self.test_port,
                   manager=manager)
        self.assertTrue(manager.get_class.called)
        self.assertEqual(dict(host=self.test_host, port=self.test_port),
                         manager.get_class.call_args[1])

    def test_custom_device_cls(self):
        obj = object()
        NoopDevice = Mock(return_value=obj)
        device = get_device(host=self.test_host, port=self.test_port,
                            device_cls=NoopDevice)
        self.assertTrue(obj is device)


if __name__ == "__main__":
    unittest.main()
