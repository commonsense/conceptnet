#python-encoding: UTF-8

from csc.nl.ja.util import *
import re
import operator

class JaProperties():
    ''' Subclass-based inheritance aggregator.
    Properties are automatically added to this class through the use of shared_property
    That is, if a child class of JaProperties uses @shared_property, it will appear in the inheritance of all objects inherited from JaProperties
    If a property is defined multiple times, the last one used will be used and the order is undefined.
    All undefined properties return None as a value (to distinguish, you should return True/False in the case of booleans)
    '''

    def get_properties(self):
        prop   = {}
        ignore = {'get_properties': True}

        name_filter   = lambda k: not re.match('__.*__', k) and not ignore.has_key(k)
        class_prop = filter(name_filter, JaProperties.__dict__)

        for k in class_prop:
            prop[k] = operator.attrgetter(k)(self)

        return prop

class shared_property(object):
    ''' Same functionality as lazy_property but allows access of properties common to all through JaProperties '''

    def __init__(self, func):
        self.func     = func
        self.__name__ = func.__name__
        self.__doc__  = func.__doc__
        self.__dict__.update(func.__dict__)

        JaProperties.__dict__.update( \
        {
            func.func_name: None
        })

    def __get__(self, instance, cls):
        assert self.__name__ not in instance.__dict__
        result = instance.__dict__[self.__name__] = self.func(instance)
        return result

    @staticmethod
    def preset(cls, name, val):
        cls.__dict__[name] = val

