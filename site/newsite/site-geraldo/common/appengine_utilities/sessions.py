"""
Copyright (c) 2008, appengine-utilities project
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
- Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.
- Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
- Neither the name of the appengine-utilities project nor the names of its
  contributors may be used to endorse or promote products derived from this
  software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# main python imports
import os
import time
import datetime
import random
import sha
import Cookie
import pickle
import __main__

# google appengine imports
from google.appengine.ext import db
from google.appengine.api import memcache

# settings, if you have these set elsewhere, such as your django settings file,
# you'll need to adjust the values to pull from there.

COOKIE_NAME = 'appengine-utilities-session-sid'
DEFAULT_COOKIE_PATH = '/'
SESSION_EXPIRE_TIME = 7200 # sessions are valid for 7200 seconds (2 hours)
CLEAN_CHECK_PERCENT = 15 # 15% of all requests will clean the database
INTEGRATE_FLASH = True # integrate functionality from flash module?
CHECK_IP = True # validate sessions by IP
CHECK_USER_AGENT = True # validate sessions by user agent
SET_COOKIE_EXPIRES = True # Set to True to add expiration field to cookie
SESSION_TOKEN_TTL = 5 # Number of seconds a session token is valid for.


class _AppEngineUtilities_Session(db.Model):
    """
    Model for the sessions in the datastore. This contains the identifier and
    validation information for the session.
    """

    sid = db.StringListProperty()
    ip = db.StringProperty()
    ua = db.StringProperty()
    last_activity = db.DateTimeProperty(auto_now=True)


class _AppEngineUtilities_SessionData(db.Model):
    """
    Model for the session data in the datastore.
    """

    session = db.ReferenceProperty(_AppEngineUtilities_Session)
    keyname = db.StringProperty()
    content = db.BlobProperty()


class Session(object):
    """
    Sessions used to maintain user presence between requests.

    Sessions store a unique id as a cookie in the browser and
    referenced in a datastore object. This maintains user presence
    by validating requests as visits from the same browser.

    You can add extra data to the session object by using it
    as a dictionary object. Values can be any python object that
    can be pickled.

    For extra performance, session objects are also store in
    memcache and kept consistent with the datastore. This
    increases the performance of read requests to session
    data.
    """

    def __init__(self, cookie_path=DEFAULT_COOKIE_PATH,
            cookie_name=COOKIE_NAME, session_expire_time=SESSION_EXPIRE_TIME,
            clean_check_percent=CLEAN_CHECK_PERCENT,
            integrate_flash=INTEGRATE_FLASH, check_ip=CHECK_IP,
            check_user_agent=CHECK_USER_AGENT,
            set_cookie_expires=SET_COOKIE_EXPIRES,
            session_token_ttl=SESSION_TOKEN_TTL):
        """
        Initializer

        Args:
          cookie_name: The name for the session cookie stored in the browser.
          session_expire_time: The amount of time between requests before the
              session expires.
          clean_check_percent: The percentage of requests the will fire off a
              cleaning routine that deletes stale session data.
          integrate_flash: If appengine-utilities flash utility should be
              integrated into the session object.
          check_ip: If browser IP should be used for session validation
          check_user_agent: If the browser user agent should be used for
              sessoin validation.
          set_cookie_expires: True adds an expires field to the cookie so
              it saves even if the browser is closed.
          session_token_ttl: Number of sessions a session token is valid
              for before it should be regenerated.
        """

        self.cookie_path = cookie_path
        self.cookie_name = cookie_name
        self.session_expire_time = session_expire_time
        self.clean_check_percent = clean_check_percent
        self.integrate_flash = integrate_flash
        self.check_user_agent = check_user_agent
        self.check_ip = check_ip
        self.set_cookie_expires = set_cookie_expires
        self.session_token_ttl = session_token_ttl

        """
        Check the cookie and, if necessary, create a new one.
        """
        self.cache = {}
        self.sid = None
        string_cookie = os.environ.get('HTTP_COOKIE', '')
        self.cookie = Cookie.SimpleCookie()
        self.cookie.load(string_cookie)
        # check for existing cookie
        if self.cookie.get(cookie_name):
            self.sid = self.cookie[cookie_name].value
            # If there isn't a valid session for the cookie sid,
            # start a new session.
            self.session = self._get_session()
            if self.session is None:
                self.sid = self.new_sid()
                self.session = _AppEngineUtilities_Session()
                self.session.ua = os.environ['HTTP_USER_AGENT']
                self.session.ip = os.environ['REMOTE_ADDR']
                self.session.sid = [self.sid]
                self.cookie[cookie_name] = self.sid
                self.cookie[cookie_name]['path'] = cookie_path
                if set_cookie_expires:
                    self.cookie[cookie_name]['expires'] = \
                        self.session_expire_time
            else:
                # check the age of the token to determine if a new one
                # is required
                duration = datetime.timedelta(seconds=self.session_token_ttl)
                session_age_limit = datetime.datetime.now() - duration
                if self.session.last_activity < session_age_limit:
                    self.sid = self.new_sid()
                    if len(self.session.sid) > 2:
                        self.session.sid.remove(self.session.sid[0])
                    self.session.sid.append(self.sid)
                else:
                    self.sid = self.session.sid[-1]
                self.cookie[cookie_name] = self.sid
                self.cookie[cookie_name]['path'] = cookie_path
                if set_cookie_expires:
                    self.cookie[cookie_name]['expires'] = \
                        self.session_expire_time
        else:
            self.sid = self.new_sid()
            self.session = _AppEngineUtilities_Session()
            self.session.ua = os.environ['HTTP_USER_AGENT']
            self.session.ip = os.environ['REMOTE_ADDR']
            self.session.sid = [self.sid]
            self.cookie[cookie_name] = self.sid
            self.cookie[cookie_name]['path'] = cookie_path
            if set_cookie_expires:
                self.cookie[cookie_name]['expires'] = self.session_expire_time

        self.cache['sid'] = pickle.dumps(self.sid)

        # update the last_activity field in the datastore every time that
        # the session is accessed. This also handles the write for all
        # session data above.
        self.session.put()
        print self.cookie

        # fire up a Flash object if integration is enabled
        if self.integrate_flash:
            import flash
            self.flash = flash.Flash(cookie=self.cookie)

        # randomly delete old stale sessions in the datastore (see
        # CLEAN_CHECK_PERCENT variable)
        if random.randint(1, 100) < CLEAN_CHECK_PERCENT:
            self._clean_old_sessions()

    def new_sid(self):
        """
        Create a new session id.
        """
        sid = sha.new(repr(time.time()) + os.environ['REMOTE_ADDR'] + \
                str(random.random())).hexdigest()
        return sid

    def _get_session(self):
        """
        Get the user's session from the datastore
        """
        query = _AppEngineUtilities_Session.all()
        query.filter('sid', self.sid)
        if self.check_user_agent:
            query.filter('ua', os.environ['HTTP_USER_AGENT'])
        if self.check_ip:
            query.filter('ip', os.environ['REMOTE_ADDR'])
        results = query.fetch(1)
        if len(results) is 0:
            return None
        else:
            sessionAge = datetime.datetime.now() - results[0].last_activity
            if sessionAge.seconds > self.session_expire_time:
                results[0].delete()
                return None
            return results[0]

    def _get(self, keyname=None):
        """
        Return all of the SessionData object unless keyname is specified, in
        which case only that instance of SessionData is returned.
        Important: This does not interact with memcache and pulls directly
        from the datastore.

        Args:
            keyname: The keyname of the value you are trying to retrieve.
        """
        query = _AppEngineUtilities_SessionData.all()
        query.filter('session', self.session)
        if keyname != None:
            query.filter('keyname =', keyname)
        results = query.fetch(1000)

        if len(results) is 0:
            return None
        if keyname != None:
            return results[0]
        return results

    def _validate_key(self, keyname):
        """
        Validate the keyname, making sure it is set and not a reserved name.
        """
        if keyname is None:
            raise ValueError('You must pass a keyname for the session' + \
                ' data content.')
        elif keyname in ('sid', 'flash'):
            raise ValueError(keyname + ' is a reserved keyname.')

        if type(keyname) != type([str, unicode]):
            return str(keyname)
        return keyname

    def _put(self, keyname, value):
        """
        Insert a keyname/value pair into the datastore for the session.

        Args:
            keyname: The keyname of the mapping.
            value: The value of the mapping.
        """
        keyname = self._validate_key(keyname)
 
        if value is None:
            raise ValueError('You must pass a value to put.')
        sessdata = self._get(keyname=keyname)
        if sessdata is None:
            sessdata = _AppEngineUtilities_SessionData()
            sessdata.session = self.session
            sessdata.keyname = keyname
        sessdata.content = pickle.dumps(value)
        self.cache[keyname] = pickle.dumps(value)
        sessdata.put()
        self._set_memcache()

    def _delete_session(self):
        """
        Delete the session and all session data for the sid passed.
        """
        sessiondata = self._get()
        # delete from datastore
        if sessiondata is not None:
            for sd in sessiondata:
                sd.delete()
        # delete from memcache
        memcache.delete('sid-'+str(self.session.key()))
        # delete the session now that all items that reference it are deleted.
        self.session.delete()
        # if the event class has been loaded, fire off the sessionDeleted event
        if 'AEU_Events' in __main__.__dict__:
            __main__.AEU_Events.fire_event('sessionDelete')

    def delete(self):
        """
        Delete the current session and start a new one.

        This is useful for when you need to get rid of all data tied to a
        current session, such as when you are logging out a user.
        """
        self._delete_session()

    def delete_all_sessions(self):
        """
        Deletes all sessions and session data from the data store and memcache.
        """
        all_sessions_deleted = False
        all_data_deleted = False

        while not all_sessions_deleted:
            query = _AppEngineUtilities_Session.all()
            results = query.fetch(1000)
            if len(results) is 0:
                all_sessions_deleted = True
            else:
                for result in results:
                    result.delete()

        while not all_data_deleted:
            query = _AppEngineUtilities_SessionData.all()
            results = query.fetch(1000)
            if len(results) is 0:
                all_data_deleted = True
            else:
                for result in results:
                    result.delete()

    def _clean_old_sessions(self):
        """
        Delete expired sessions from the datastore.

        This is only called for CLEAN_CHECK_PERCENT percent of requests because
        it could be rather intensive.
        """
        duration = datetime.timedelta(seconds=self.session_expire_time)
        session_age = datetime.datetime.now() - duration
        query = _AppEngineUtilities_Session.all()
        query.filter('last_activity <', session_age)
        results = query.fetch(1000)
        for result in results:
            data_query = _AppEngineUtilities_SessionData.all()
            query.filter('session', result)
            data_results = data_query.fetch(1000)
            for data_result in data_results:
                data_result.delete()
            memcache.delete('sid-'+str(result.key()))
            result.delete()

    # Implement Python container methods

    def __getitem__(self, keyname):
        """
        Get item from session data.

        keyname: The keyname of the mapping.
        """
        # flash messages don't go in the datastore

        if self.integrate_flash and (keyname == 'flash'):
            return self.flash.msg
        if keyname in self.cache:
            return pickle.loads(str(self.cache[keyname]))
        mc = memcache.get('sid-'+str(self.session.key()))
        if mc is not None:
            if keyname in mc:
                return mc[keyname]
        data = self._get(keyname)
        if data:
            self.cache[keyname] = data.content
            self._set_memcache()
            return pickle.loads(data.content)
        else:
            raise KeyError(str(keyname))

    def __setitem__(self, keyname, value):
        """
        Set item in session data.

        Args:
            keyname: They keyname of the mapping.
            value: The value of mapping.
        """
 #       if type(keyname) is type(''):
            # flash messages don't go in the datastore

        if self.integrate_flash and (keyname == 'flash'):
            self.flash.msg = value
        else:
            keyname = self._validate_key(keyname)
            self.cache[keyname] = value
            self._set_memcache()
            return self._put(keyname, value)
#        else:
#            raise TypeError('Session data objects are only accessible by' + \
#                ' string keys, not numerical indexes.')

    def __delitem__(self, keyname):
        """
        Delete item from session data.

        Args:
            keyname: The keyname of the object to delete.
        """
        sessdata = self._get(keyname = keyname)
        if sessdata is None:
            raise KeyError(str(keyname))
        sessdata.delete()
        if keyname in self.cache:
            del self.cache[keyname]
        self._set_memcache()

    def __len__(self):
        """
        Return size of session.
        """
        # check memcache first
        mc = memcache.get('sid-'+str(self.session.key()))
        if mc is not None:
            return len(mc)
        results = self._get()
        return len(results)

    def __contains__(self, keyname):
        """
        Check if an item is in the session data.

        Args:
            keyname: The keyname being searched.
        """
        try:
            r = self.__getitem__(keyname)
        except KeyError:
            return False
        return True

    def __iter__(self):
        """
        Iterate over the keys in the session data.
        """
        # try memcache first
        mc = memcache.get('sid-'+str(self.session.key()))
        if mc is not None:
            for k in mc:
                yield k
        else:
            for k in self._get():
                yield k.keyname

    def __str__(self):
        """
        Return string representation.
        """
        return ', '.join(['("%s" = "%s")' % (k, self[k]) for k in self])

    def _set_memcache(self):
        """
        Set a memcache object with all the session date. Optionally you can
        add a key and value to the memcache for put operations.
        """
        # Pull directly from the datastore in order to ensure that the
        # information is as up to date as possible.
        data = {}
        sessiondata = self._get()
        if sessiondata is not None:
            for sd in sessiondata:
                data[sd.keyname] = pickle.loads(sd.content)

        memcache.set('sid-'+str(self.session.key()), data, \
            self.session_expire_time)
