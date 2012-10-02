import os
import sys
from pyasn1.type.univ import ObjectIdentifier

def get_all_parents(cls):
    parents = []
    parents.extend(cls.__bases__)
    left_bases = []
    left_bases.extend(cls.__bases__)
    while left_bases:
        for base in left_bases[:]:
            left_bases.extend(base.__bases__)
            parents.extend(base.__bases__)
            left_bases.remove(base)
    parents.reverse()
    return tuple(parents)

def str_to_oid(s):
    if type(s) in (str, unicode): 
        return tuple(map(int, s.split(".")))
    if isinstance(s, ObjectIdentifier):
        return tuple(s) 
    else:
        return s
    
def oid_to_str(t):
    try: 
        return ".".join(map(str, iter(t)))
    except TypeError:
        return t
        
def import_class(name, path=None):
    try:
        mod = __import__(name)
    except:
        if path: 
		path = os.path.dirname(os.path.abspath(path))
        base_import_dir = path.split(os.path.basename(path))[0]
        sys.path.append(base_import_dir)
        
        print base_import_dir
        
        mod = __import__(name)

    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)

    return mod

def walklevel(some_dir, level=0):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]
