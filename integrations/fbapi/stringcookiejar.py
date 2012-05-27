from cookielib import CookieJar
import cPickle as pickle

class StringCookieJar(CookieJar):
    def __init__(self, string=None, policy=None):
        CookieJar.__init__(self, policy)
        if string:
            self._cookies = pickle.loads(string)

    def dump(self):
        return pickle.dumps(self._cookies)
