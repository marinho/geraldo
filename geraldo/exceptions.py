class EmptyQueryset(Exception):
    pass

class ObjectNotFound(Exception):
    pass

class ManyObjectsFound(Exception):
    pass

class AttributeNotFound(Exception):
    pass

class NotYetImplemented(Exception):
    pass

class AbortEvent(Exception):
    """Exception class used inside event methods to abort that printing/rendering"""
    pass

