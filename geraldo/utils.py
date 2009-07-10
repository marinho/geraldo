from reportlab.lib.units import * # Check this - is the source of units
from reportlab.lib.pagesizes import * # Check this - is the source of page sizes

from exceptions import AttributeNotFound

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
        return eval(size)
    
    return size

