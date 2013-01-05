snmp_orm -- PySNMP Abstraction
==============================

.. note::
    Source code is hosted on `Github <https://github.com/blackwithwhite666/snmp_orm>`_

Introduction
------------

`snmp_orm` is a Python-based tool providing a simple interface to work
SNMP agents. Here is a very simplistic example that allows to display
the system information of a given host::

   from snmp_orm import get_device
   d = get_device("127.0.0.1")
   print dict(d.system)
  