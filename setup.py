from distutils.core import setup

setup(name="snmp_orm",
      version="0.1",
      description="Python-based tool providing a simple interface to work SNMP agents",
      author="alex",
      author_email="supereic@gmail.com",
      url="http://www.credosemi.com",
      packages=['snmp_orm', 'snmp_orm.adapters', 'snmp_orm.devices'])
