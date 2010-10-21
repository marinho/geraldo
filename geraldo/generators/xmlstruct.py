from decimal import Decimal

try:
    # Using lxml
    from lxml import etree
except ImportError:
    etree = None

from geraldo.base import GeraldoObject, Report, ReportBand
from base import ReportGenerator

class XMLStructSerializer(object):
    """This is an **exporter** to output a XML format, with the goal to be
    used to import/export report classes. It ignores the queryset and just
    works with save/load the structure into a file.
    
    Would be nice use it also in a friendly JavaScript graphic tool to edit
    reports."""

    def __init__(self):
        if not etree:
            raise Exception('There is no lxml installed. This serializer needs it to (de)serialize data.')

    def serialize(self, object_tree, returns_string=True):
        """The argument 'object_tree' should receive a Python object or a list of them."""
        root = self._serialize_something(object_tree)

        if returns_string:
            return etree.tostring(root, pretty_print=True)
        else:
            return root

    def _serialize_something(self, obj, attrs=None):
        if isinstance(obj, (list, tuple)):
            return self._serialize_list(obj, attrs=attrs)
        elif hasattr(obj, '__mro__') and Report in obj.__mro__:
            return self._serialize_report(obj, attrs=attrs)
        elif isinstance(obj, (GeraldoObject, basestring, int, float, Decimal, bool)):
            return self._serialize_object(obj, attrs=attrs)
        elif issubclass(obj, GeraldoObject):
            return self._serialize_class(obj, attrs=attrs)
        else:
            raise Exception('Invalid object tree to serialize!')

    def _serialize_list(self, items, attrs=None):
        node = etree.Element('GeraldoObjects', attrib=(attrs or {})) # xmlns="http://www.geraldoreports.org/xml"

        for item in items:
            node.append(self._serialize_something(item))

        return node

    def _serialize_report(self, report, attrs=None):
        attrs = attrs or {}

        # Attributes
        for attr in dir(report):
            if attr in ('author','keywords','subject','title','first_page_number','print_if_empty',
                    'default_font_color','default_stroke_color','default_fill_color'):
                attrs[attr] = unicode(getattr(report, attr))

        # Root node
        node = etree.Element(report.get_name_to_serialize(), attrib=attrs)

        # Children attributes
        node.append(etree.Element('PageSize', attrib={
            'width': str(report.page_size[0]),
            'height': str(report.page_size[1]),
            }))
        node.append(etree.Element('MarginSet', attrib={
            'left': str(report.margin_left),
            'right': str(report.margin_right),
            'top': str(report.margin_top),
            'bottom': str(report.margin_bottom),
            }))
        if report.additional_fonts:
            for name, value in report.additional_fonts.items():
                attr_node = etree.Element('AdditionalFont', attrib={'name': name})

                if isinstance(value, basestring):
                    value = [value]

                if isinstance(value, (tuple,list)):
                    for font in value:
                        if isinstance(font, basestring):
                            attr_node.append(etree.Element('FontPath', attrib={'file': font}))
                        elif isinstance(font, dict):
                            attr_node.append(etree.Element('FontPath', attrib={
                                'name': font.get('name', None),
                                'file': font.get('file', None),
                                }))

                node.append(attr_node)
        if report.default_style:
            attr_node = etree.Element('DefaultStyle')

            for name, value in report.default_style.items():
                attr_node.append(etree.Element('StyleKey', attrib={'name': name, 'value': value}))

            node.append(attr_node)
        if report.borders:
            node.append(self._serialize_borders(report.borders))

        # Complex children
        for attr in ('band_begin','band_summary','band_page_header','band_page_footer','band_detail',
                'groups','subreports','cache_status','cache_prefix','cache_file_root'):
            value = getattr(report, attr, None)

            if value is None:
                continue

            attr_node = self._serialize_something(value, attrs={'name': attr})
            node.append(attr_node)

        return node

    def _serialize_class(self, cls, attrs=None):
        node = etree.Element(cls.get_name_to_serialize(), attrib=(attrs or {}))

        self._set_children(node, cls)

        return node

    def _serialize_object(self, obj, attrs=None):
        tag_name = hasattr(obj.__class__, 'get_name_to_serialize') and \
                   obj.__class__.get_name_to_serialize() or\
                   obj.__class__.__name__
        node = etree.Element(tag_name, attrib=(attrs or {}))

        self._set_children(node, obj)

        return node

    def _serialize_value(self, attr, value):
        node = etree.Element('GeraldoAttribute', attrib={
            'type': value.__class__.__name__,
            'name': attr,
            'value': unicode(value),
            })

        return node

    def _set_children(self, node, obj):
        if obj is None:
            return

        try:
            serializable_attrs = obj._serializable_attributes
        except AttributeError:
            serializable_attrs = [attr for attr in dir(obj) if not attr.startswith('_')]

        for attr in serializable_attrs:
            value = getattr(obj, attr)

            if isinstance(value, (basestring, int, float, Decimal, bool)):
                attr_node = self._serialize_value(attr, value)
            elif isinstance(value, (list, tuple)):
                attr_node = self._serialize_list(value, attrs={u'name': attr})
            elif isinstance(value, GeraldoObject):
                attr_node = self._serialize_object(value, attrs={u'name': attr})
            elif isinstance(obj, ReportBand) and attr == 'borders':
                attr_node = self._serialize_borders(report.borders)
            else:
                continue
            
            node.append(attr_node)

    def _serialize_borders(self, borders):
        node = etree.Element('Borders')

        for k in borders.keys():
            if isinstance(borders[k], (bool, int, basestring, float)):
                attr_node = self._serialize_value(k, borders[k])
            elif isinstance(borders[k], GeraldoObject):
                attr_node = self._serialize_object(borders[k], attrs={u'name': k})

            node.append(attr_node)

        return node

    def deserialize(self, data):
        """The argument 'data' should receive a string with serialized XML from Geraldo's
        Python objects."""
        pass


