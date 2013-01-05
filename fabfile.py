from fabric.api import *


@task
def generate_docs(clean='no'):
    """Generate the Sphinx documentation."""
    c = ""
    local('sphinx-apidoc -f -o docs/source/api snmp_orm')
    if clean.lower() in ['yes', 'y']:
        c = "clean "
    with lcd('docs'):
        local('make %shtml' % c)
