def serialize(objects, fields=None):
    xml_tpl = r"""<?xml version="1.0" encoding="utf-8"?>
    <entities>
    %s
    </entities>
    """
    ret = []

    for obj in objects:
        ret.append(obj.to_xml())

    return xml_tpl%'\n'.join(ret)

