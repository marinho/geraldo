from base import BAND_WIDTH, BAND_HEIGHT, Element
from utils import cm, black

class Graphic(Element):
    """Base graphic class"""
    stroke = True
    stroke_color = black
    stroke_width = 1

    fill = False
    fill_color = black

    _repr_for_cache_attrs = ('left','top','height','width','visible','stroke',
            'stroke_color','stroke_width','fill','fill_color')

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    def set_rect(self, **kwargs):
        """This method will adapt the graphic element in a rect."""
        self.left = kwargs.get('left', self.left)
        self.top = kwargs.get('top', self.top)

        if 'width' in kwargs:
            self.width = kwargs['width']
        elif 'right' in kwargs:
            self.width = kwargs['right'] - self.left

        if 'height' in kwargs:
            self.height = kwargs['height']
        elif 'bottom' in kwargs:
            self.height = kwargs['bottom'] - self.top

    def clone(self):
        new = super(Graphic, self).clone()
        new.stroke = self.stroke
        new.stroke_color = self.stroke_color
        new.stroke_width = self.stroke_width

        new.fill = self.fill
        new.fill_color = self.fill_color

        return new

class Rect(Graphic):
    """A simple rectangle"""
    pass

class RoundRect(Rect):
    """A rectangle graphic element that is possible set its radius and have
    round corners"""
    radius = 0.5

    _repr_for_cache_attrs = ('left','top','height','width','visible','stroke',
                'stroke_color','stroke_width','fill','fill_color','radius')

    def clone(self):
        new = super(RoundRect, self).clone()
        new.radius = self.radius

        return new

class Fixed(Graphic):
    """A fixed graphic is base on right and bottom coordinates instead of width
    and height.
    
    It is just a reference class and shouldn't be used directly in reports."""
    left = None
    top = None
    right = None
    bottom = None

    _repr_for_cache_attrs = ('left','top','height','width','visible','stroke',
            'stroke_color','stroke_width','fill','fill_color','right','bottom')

    def set_rect(self, **kwargs):
        self.left = kwargs.get('left', self.left)
        self.top = kwargs.get('top', self.top)

        if 'right' in kwargs:
            self.right = kwargs['right']
        elif 'width' in kwargs:
            self.right = kwargs['width'] + self.left

        if 'bottom' in kwargs:
            self.bottom = kwargs['bottom']
        elif 'height' in kwargs:
            self.bottom = kwargs['height'] + self.top

    def clone(self):
        new = super(Fixed, self).clone()
        new.left = self.left
        new.top = self.top
        new.right = self.right
        new.bottom = self.bottom

        return new

class Line(Fixed):
    """A simple line"""

    def height(self):
        return self.bottom - self.top
    height = property(height)

    def width(self):
        return self.right - self.left
    width = property(width)

class Circle(Graphic):
    """A simple circle"""
    left_center = None
    top_center = None
    radius = None

    _repr_for_cache_attrs = ('left','top','height','width','visible','stroke',
            'stroke_color','stroke_width','fill','fill_color','left_center',
            'top_center','radius')

    def clone(self):
        new = super(Circle, self).clone()
        new.left_center = self.left_center
        new.top_center = self.top_center
        new.radius = self.radius

        return new

class Arc(Fixed):
    """A simple circle"""
    start_angle = 0
    extent = 90

    _repr_for_cache_attrs = ('left','top','height','width','visible','stroke',
            'stroke_color','stroke_width','fill','fill_color','start_angle','extent')

    def clone(self):
        new = super(Arc, self).clone()
        new.start_angle = self.start_angle
        new.extent = self.extent

        return new

class Ellipse(Fixed):
    """A simple circle"""
    pass

class Image(Graphic):
    """A image"""
    left = None
    top = None
    _width = None
    _height = None
    filename = None
    _image = None # PIL image object is stored here
    get_image = None # To be overrided
    stretch = False

    _repr_for_cache_attrs = ('left','top','height','width','visible','stroke',
            'stroke_color','stroke_width','fill','fill_color','filename')

    def clone(self):
        new = super(Image, self).clone()
        new.left = self.left
        new.top = self.top
        new._width = self._width
        new._height = self._height
        new.filename = self.filename
        new._image = self._image
        new.get_image = self.get_image

        return new

    def _get_image(self):
        """Uses Python Imaging Library to load an image and get its
        informations"""
        if self.get_image:
            self._image = self.get_image(self)

        if not self._image and self.filename:
            try:
                import Image as PILImage
            except ImportError:
                from PIL import Image as PILImage

            self._image = PILImage.open(self.filename)

        return self._image

    def _set_image(self, value):
        self._image = value

    image = property(_get_image, _set_image)

    def _get_height(self):
        ret = self._height or (self.image and self.image.size[1] or 0)
        return ret * 0.02*cm

    def _set_height(self, value):
        self._height = value

    height = property(_get_height, _set_height)

    def _get_width(self):
        ret = self._width or (self.image and self.image.size[0] or 0)
        return ret * 0.02*cm

    def _set_width(self, value):
        self._width = value

    width = property(_get_width, _set_width)

