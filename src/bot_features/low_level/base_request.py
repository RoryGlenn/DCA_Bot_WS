import base64
import hashlib
import hmac
import time
import urllib.parse
import requests

from bot_features.low_level.kraken_enums import *


class BaseRequest():
    def __init__(self, api_key: str, api_secret: str) -> None:
        """ Create an object with authentication information. """
        self.key           = api_key
        self.secret        = api_secret
        self.uri           = 'https://api.kraken.com'
        self.apiversion    = '0'
        self.session       = requests.Session()
        self.response      = None
        self._json_options = {}
        return

    def json_options(self, **kwargs):
        """ Set keyword arguments to be passed to JSON deserialization. """
        self._json_options = kwargs
        return self

    def close(self) -> None:
        """ Close this session."""
        self.session.close()
        return

    def load_key(self, key: str, secret: str) -> None:
        """ Load kraken key and kraken secret. """
        self.key    = key
        self.secret = secret
        return

    def query(self, urlpath: str, data: dict, headers: dict = None, timeout: int = None):
        """ Low-level query handling. """
        if data is None:
            data = {}
        if headers is None:
            headers = {}
            
        url           = self.uri + urlpath
        self.response = self.session.post(url, data=data, headers=headers, timeout=timeout)

        if self.response.status_code not in (200, 201, 202):
            self.response.raise_for_status()
        return self.response.json(**self._json_options)

    def query_public(self, method: str, data: dict = None, timeout: int = None):
        """ Performs an API query that does not require a valid key/secret pair. """
        if data is None:
            data = {}
        urlpath = '/' + self.apiversion + '/public/' + method
        return self.query(urlpath, data, timeout = timeout)

    def query_private(self, method: str, data=None, timeout=None):
        """ Performs an API query that requires a valid key/secret pair. """
        if data is None:
            data = {}

        if not self.key or not self.secret:
            raise Exception('Either key or secret is not set! (Use `load_key()`.')

        data['nonce'] = self.nonce()
        urlpath       = '/' + self.apiversion + '/private/' + method
        headers       = { 'API-Key': self.key, 'API-Sign': self.sign(data, urlpath) }
        return self.query(urlpath, data, headers, timeout = timeout)

    def nonce(self) -> int:
        """ An always-increasing unsigned integer (up to 64 bits wide) """
        return int(1000*time.time())

    def sign(self, data: dict, urlpath: str) -> str:
        """ Sign request data according to Kraken's scheme. """
        postdata  = urllib.parse.urlencode(data)
        # Unicode-objects must be encoded before hashing
        encoded   = (str(data['nonce']) + postdata).encode()
        message   = urlpath.encode() + hashlib.sha256(encoded).digest()
        signature = hmac.new(base64.b64decode(self.secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(signature.digest())
        return sigdigest.decode()
