import sys
import logging             

#copy public content of logging package 
for name in dir(logging): 
    if not name.startswith('_'): 
        globals()[name] = getattr(logging, name)             

def _get_instance_name(instance): 
    return instance.__class__.__module__ + "." + instance.__class__.__name__ + ".0x.." + hex(id(instance))[-2:]  

class class_logger(object): 
    '''Class logger descriptor''' 
    def __init__(self): 
        self._logger = None             

    def __get__(self, instance, owner): 
        if self._logger is None: 
            self._logger = logging.getLogger(owner.__module__ + "." + owner.__name__) 
        return self._logger             

class instance_logger(object): 
    '''Instance logger descriptor''' 
    def __init__(self): 
        self._logger = None             

    def __get__(self, instance, owner): 
        if self._logger is None: 
            self._logger = logging.getLogger(_get_instance_name(instance)) 
        return self._logger 