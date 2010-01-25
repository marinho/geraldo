import Cookie
import os

from common.appengine_utilities import sessions


class SessionMiddleware(object):
    TEST_COOKIE_NAME = 'testcookie'
    TEST_COOKIE_VALUE = 'worked'

    def process_request(self, request):
        request.session = sessions.Session()
        request.session.set_test_cookie = self.set_test_cookie
        request.session.test_cookie_worked = self.test_cookie_worked
        request.session.delete_test_cookie = self.delete_test_cookie

    def set_test_cookie(self):
        string_cookie = os.environ.get('HTTP_COOKIE', '')

        self.cookie = Cookie.SimpleCookie()
        self.cookie.load(string_cookie)
        self.cookie[self.TEST_COOKIE_NAME] = self.TEST_COOKIE_VALUE
        print self.cookie

    def test_cookie_worked(self):
        string_cookie = os.environ.get('HTTP_COOKIE', '')

        self.cookie = Cookie.SimpleCookie()
        self.cookie.load(string_cookie)

        return self.cookie.get(self.TEST_COOKIE_NAME)

    def delete_test_cookie(self):
        string_cookie = os.environ.get('HTTP_COOKIE', '')

        self.cookie = Cookie.SimpleCookie()
        self.cookie.load(string_cookie)
        self.cookie[self.TEST_COOKIE_NAME] = ''
        self.cookie[self.TEST_COOKIE_NAME]['path'] = '/'
        self.cookie[self.TEST_COOKIE_NAME]['expires'] = 0
