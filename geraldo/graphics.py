from reportlab.lib.colors import black
from reportlab.lib.units import cm

class Graphic(object):
    """Base graphic class"""
    stroke = True
    stroke_color = black
    stroke_width = 1

    fill = False
    fill_color = black

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

class Rect(Graphic):
    """A simple rectangle"""
    left = None
    top = None
    width = None
    height = None

class RoundRect(Rect):
    """A rectangle graphic element that is possible set its radius and have
    round corners"""
    radius = 0.5

class Line(Graphic):
    """A simple line"""
    left = None
    top = None
    right = None
    bottom = None

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

class Arc(Graphic):
    """A simple circle"""
    left = None
    top = None
    right = None
    bottom = None
    start_angle = 0
    extent = 90

class Ellipse(Graphic):
    """A simple circle"""
    left = None
    top = None
    right = None
    bottom = None

class Image(Graphic):
    """A image"""
    left = None
    top = None
    _width = None
    _height = None
    filename = None
    _image = None # PIL image object is stored here

    def _get_image(self):
        """Uses Python Imaging Library to load an image and get its informations"""
        if not self._image:
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
        ret = self._height or self.image.size[1]
        return ret * 0.02*cm

    def _set_height(self, value):
        self._height = value

    height = property(_get_height, _set_height)

    def _get_width(self):
        ret = self._width or self.image.size[0]
        return ret * 0.02*cm

    def _set_width(self, value):
        self._width = value

    width = property(_get_width, _set_width)

