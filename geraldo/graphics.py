from reportlab.lib.colors import black
from reportlab.lib.units import cm

from base import BAND_WIDTH, BAND_HEIGHT, Element

class Graphic(Element):
    """Base graphic class"""
    visible = True

    stroke = True
    stroke_color = black
    stroke_width = 1

    fill = False
    fill_color = black

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

class Rect(Graphic):
    """A simple rectangle"""
    pass

class RoundRect(Rect):
    """A rectangle graphic element that is possible set its radius and have
    round corners"""
    radius = 0.5

class Fixed(Graphic):
    """A fixed graphic is base on right and bottom coordinates instead of width
    and height.
    
    It is just a reference class and shouldn't be used directly in reports."""
    left = None
    top = None
    right = None
    bottom = None

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

class Line(Fixed):
    """A simple line"""

    @property
    def height(self):
        return self.bottom - self.top

    @property
    def width(self):
        return self.right - self.left

class Circle(Graphic):
    """A simple circle"""
    left_center = None
    top_center = None
    radius = None

class Arc(Fixed):
    """A simple circle"""
    start_angle = 0
    extent = 90

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

