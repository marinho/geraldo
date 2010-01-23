"""Caching functions file. You can use this stuff to store generated reports in a file
system cache, and save time and performance."""

import os

from utils import memoize, get_attr_value

try:
    set
except:
    from sets import Set as set

CACHE_DISABLED = 0
CACHE_BY_QUERYSET = 1
CACHE_BY_RENDER = 2
DEFAULT_CACHE_STATUS = CACHE_DISABLED

CACHE_BACKEND = 'geraldo.cache.FileCacheBackend'
CACHE_FILE_ROOT = '/tmp/'

class BaseCacheBackend(object):
    """This is the base class (and abstract too) to be inherited by any cache backend
    to store and restore reports from a cache."""

    def get(self, hash_key):
        pass

    def set(self, hash_key, content):
        pass

    def exists(self, hash_key):
        pass

class FileCacheBackend(BaseCacheBackend):
    """This cache backend is able to store and restore using a path on the file system."""

    cache_file_root = '/tmp/'

    def __init__(self, cache_file_root=None):
        self.cache_file_root = cache_file_root or self.cache_file_root

        # Creates the directory if doesn't exists
        if not os.path.exists(self.cache_file_root):
            os.makedirs(self.cache_file_root)

    def get(self, hash_key):
        # Returns None if doesn't exists
        if not self.exists(hash_key):
            return None

        # Returns the file content
        fp = file(os.path.join(self.cache_file_root, hash_key), 'rb')
        content = fp.read()
        fp.close()

        return content

    def set(self, hash_key, content):
        # Writes the content in the file
        fp = file(os.path.join(self.cache_file_root, hash_key), 'wb')
        fp.write(content)
        fp.close()

    def exists(self, hash_key):
        return os.path.exists(os.path.join(self.cache_file_root, hash_key))

@memoize
def get_report_cache_attributes(report):
    from widgets import ObjectValue

    # Find widgets attributes
    widgets = [widget.attribute_name for widget in report.find_by_type(ObjectValue)]

    # Find grouppers attributes
    groups = [group.attribute_name for group in report.groups]

    return list(set(widgets + groups))

try:
    # Python 2.5 or higher
    from hashlib import sha512 as hash_constructor
except ImportError:
    # Python 2.4
    import sha
    hash_constructor = sha.new

def make_hash_key(report, objects_list):
    """This function make a hash key from a list of objects.
    
    Situation 1
    -----------

    If the objects have an method 'repr_for_cache_hash_key', it is called to get their
    string repr value. This is the default way to get repr strings from rendered pages
    and objects.
    
    Situation 2
    -----------

    Otherwise, if exists, the method 'get_cache_relevant_attributes' from report will be
    called to request what attributes have to be used from the object list to make the
    string.
    
    If the method above does't exists, then all attributes explicitly found in report
    elements will be used.
    
    The result list will be transformed to a long concatenated string and a hash key
    will be generated from it."""

    global get_report_cache_attributes

    result = []

    # Get attributes for cache from report
    if hasattr(report, 'get_cache_relevant_attributes'):
        report_attrs = report.get_cache_relevant_attributes
    else:
        report_attrs = lambda: get_report_cache_attributes(report)

    for obj in objects_list:
        # Situation 1 - mostly report pages and geraldo objects
        if hasattr(obj, 'repr_for_cache_hash_key'):
            result.append(obj.repr_for_cache_hash_key())

        # Situation 2 - mostly queryset objects list
        else:
            result.append(u'/'.join([unicode(get_attr_value(obj, attr)) for attr in report_attrs()]))

    # Makes the hash key
    m = hash_constructor()
    m.update(u'\n'.join(result))

    return '%s-%s'%(report.cache_prefix, m.hexdigest())

def get_cache_backend(class_path, **kwargs):
    """This method initializes the cache backend from string path informed."""
    parts = class_path.split('.')
    module = __import__('.'.join(parts[:-1]), fromlist=[parts[-1]])
    cls = getattr(module, parts[-1])

    return cls(**kwargs)

