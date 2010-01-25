from django.http import Http404

def get_object_or_404(cls, **kwargs):
    field, value = kwargs.items()[0]

    obj = cls.get_by_field(field, value)

    if not obj:
        raise Http404

    return obj
