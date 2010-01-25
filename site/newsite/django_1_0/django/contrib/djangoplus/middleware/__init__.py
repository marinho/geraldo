import hmac, sha, base64, os

from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify

try:
    import Image, ImageDraw, ImageFont
except:
    from PIL import Image, ImageDraw, ImageFont

class FakeSessionCookieMiddleware(object):
    """
    Thanks to Dan Fairs
    The source post is available at:
    http://www.stereoplex.com/two-voices/cookieless-django-sessions-and-authentication-without-cookies
    """
    def process_request(self, request):
        if request.GET.has_key(settings.SESSION_COOKIE_NAME):
            request.COOKIES[settings.SESSION_COOKIE_NAME] = request.GET[settings.SESSION_COOKIE_NAME]
        elif request.POST.has_key(settings.SESSION_COOKIE_NAME):
            request.COOKIES[settings.SESSION_COOKIE_NAME] = request.POST[settings.SESSION_COOKIE_NAME]

class ProtectAntiRobotsMiddleware(object):
    def process_request(self, request):
        if request.get_full_path().startswith('/protectantirobots/'):
            path = request.GET.get('path', '') or request.POST.get('path', '')
            if request.path == '/protectantirobots/img/':
                s = base64.b64decode(request.COOKIES['protectantirobots_key_'+path])
                size = (100,30)
                img = Image.new("RGB", size, "white")

                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype(os.path.dirname(__file__)+"/FreeSansBold.ttf", 24)
                draw.text((2,2), s, fill="red", font=font)

                draw.line((0, 0) + img.size, fill=128)
                draw.line((0, img.size[1], img.size[0], 0), fill=128)
                del draw

                ret = HttpResponse(mimetype='image/gif')
                img.save(ret, "GIF")
            elif 'k' in request.GET:
                if request.POST:
                    n = request.POST['n']
                    sec = base64.b64decode(request.COOKIES['protectantirobots_key_'+path])
                    if n == sec:
                        ret = HttpResponseRedirect(request.COOKIES['protectantirobots_referer_'+path])
                        ret.set_cookie('protectantirobots_sec_'+str(path), sec)
                    else:
                        ret = render_to_response(
                            'djangoplus/protectantirobots.html',
                            {'msg': _('Invalid number!'), 'path': path},
                            context_instance=RequestContext(request),
                        )
                else:
                    ret = render_to_response(
                        'djangoplus/protectantirobots.html',
                        locals(),
                        context_instance=RequestContext(request),
                        )
                    ret.set_cookie('protectantirobots_key_'+str(path), request['k'])
                    ret.set_cookie('protectantirobots_referer_'+str(path), request.META.get('HTTP_REFERER', ''))

            return ret

