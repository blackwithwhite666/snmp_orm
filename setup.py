from distutils.core import setup

setup(name = "snmp_orm",
      version = "0.1",
      description = "Python-based tool providing a simple interface to work SNMP agents",
      author = "Lipin Dmitriy, Xiongfei GUO",
      author_email = "xfguo@credosemi.com",
      url = "https://github.com/xfguo/snmp_orm",
      packages = ['snmp_orm', 'snmp_orm.adapters', 'snmp_orm.devices'])
