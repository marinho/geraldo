from reportlab.lib.units import * # Check this - is the source of units
from reportlab.lib.pagesizes import * # Check this - is the source of page sizes

from exceptions import AttributeNotFound

try:
    from functools import wraps
except ImportError:
    wraps = None

### Copied from Django Framework - django.utils.functional.memoize  #########

#  Copyright (c) 2005 - 2009 Django Software Foundation.
#  All Rights Reserved.

def memoize(func, cache, num_args):
    """
    Wrap a function so that results for any argument tuple are stored in
    'cache'. Note that the args to the function must be usable as dictionary
    keys.

    Only the first num_args are considered when creating the key.
    """
    if not wraps:
        return func

    def wrapper(*args):
        mem_args = args[:num_args]
        if mem_args in cache:
            return cache[mem_args]
        result = func(*args)
        cache[mem_args] = result
        return result
    return wraps(func)(wrapper)

### End of copied code from Django  #########################################

def get_attr_value(obj, attr_path):
    """This function gets an attribute value from an object. If the attribute
    is a method with no arguments (or arguments with default values) it calls
    the method. If the expression string has a path to a child attribute, it
    supports.
    
    Examples:
        
        attribute_name = 'name'
        attribute_name = 'name.upper'
        attribute_name = 'customer.name.lower'
    """
    if not attr_path:
        raise Exception('Invalid attribute path \'%s\''%attr_path)

    parts = attr_path.split('.')

    try:
        val = getattr(obj, parts[0])
    except AttributeError:
        try:
            val = obj[parts[0]]
        except KeyError:
            raise AttributeNotFound('There is no attribute nor key "%s" in the object "%s"'%(parts[0], repr(obj)))
        except TypeError:
            raise AttributeNotFound('There is no attribute nor key "%s" in the object "%s"'%(parts[0], repr(obj)))

    if len(parts) > 1:
        val = get_attr_value(val, '.'.join(parts[1:]))

    if callable(val):
        val = val()
        
    return val

def calculate_size(size):
    """Calculates the informed size. If this is a string or unicode, it is
    converted to float using evaluation function"""
    if isinstance(size, basestring):
        return eval(size) # If you are thinking this is a semanthic bug, you must
                          # be aware this 'eval' is necessary to calculate sizes
                          # like '10*cm' or '15.8*rows'
                          # I want to check if eval is better way to do it than
                          # do a regex matching and calculate. TODO
    
    return size
_calculate_size = {}
calculate_size = memoize(calculate_size, _calculate_size, 1)

