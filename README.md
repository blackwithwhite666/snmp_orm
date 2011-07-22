snmp_orm -- PySNMP Abstraction
==============================

 https://github.com/blackwithwhite666/snmp_orm

Introduction
------------

snmp_orm is a Python-based tool providing a simple interface to work
SNMP agents. Here is a very simplistic example that allows to display
the system information of a given host:

```python
from snmp_orm import get_device
d = get_device("192.168.0.225")
print dict(d.system)
```