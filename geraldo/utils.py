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
    parts = attr_path.split('.')

    val = getattr(obj, parts[0])

    if len(parts) > 1:
        val = get_attr_value(val, '.'.join(parts[1:]))

    if callable(val):
        val = val()
        
    return val

