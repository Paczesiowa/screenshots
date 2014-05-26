import re

from dom2img import _compat, _arg_utils


def serialize_cookies(cookies):
    '''
    Serializes cookie dictionary to cookie string.
    cookies must be a dict mapping byte-string cookie keys
    to byte-string cookie values. Neither keys nor values should
    contain semicolons. Keys cannot contain '=' character.
    Result is a semicolon-separated byte-string with cookie elems
    in key=value format.
    '''
    return b';'.join(map(b'='.join, cookies.items()))


def parse_cookie_string(cookie_string):
    '''
    Parse cookie dictionary from a byte-string or ascii-only unicode text,
    using format key1=val1;key2=val2.
    Returns dictionary mapping byte-string cookie keys to byte string
    cookie values.

    Raises:
    * TypeError if cookie_string is not a string
    * ValueError if cookie_string is an unicode text
      and it contains non-ascii characters.

    >>> parse_cookie_string(u'key1=val1;key2=val2') == \
        {b'key1': b'val1', b'key2': b'val2'}
    True
    '''
    if isinstance(cookie_string, _compat.text):
        try:
            cookie_string = cookie_string.encode('ascii')
        except UnicodeEncodeError:
            err_msg = u'unicode cookie_string must be ascii-only'
            raise ValueError(err_msg)
    if not isinstance(cookie_string, bytes):
        err_msg = u'cookie_string must be an ascii-only ' +\
            u'unicode text or a byte-string'
        raise TypeError(err_msg)
    if b'=' not in cookie_string:
        return {}
    cookies = {}
    cookie_elems = cookie_string.split(b';')
    for cookie_elem in cookie_elems:
        cookie = cookie_elem.split(b'=')
        cookie_key = cookie.pop(0)
        cookie_value = b'='.join(cookie)
        cookies[cookie_key] = cookie_value
    return cookies


parse_cookie_string.__name__ = 'cookie string'


def validate_cookies(cookies):
    '''
    Check if cookies is a dict:
    * dict keys can be byte-strings or ascii-only unicode text strings,
      they cannot contain ';' and '=' characters.
    * dict values can be byte-strings or ascii-only unicode text strings,
      they cannot contain ';'.
    Returns validated dict, where keys and values are byte-strings.
    Raises exception if cookie keys/values contain illegal characters,
    or if they contain non-ascii characters.

    >>> validate_cookies({u'key1': u'val1', u'key2': u'val2'}) == \
        {b'key1': b'val1', b'key2': b'val2'}
    True
    '''
    if not isinstance(cookies, dict):
        raise TypeError(u'cookies must be a dict')

    def validate_cookie_string(s):
        if not isinstance(s, bytes) and \
                not isinstance(s, _compat.text):
            raise TypeError(u'cookies key/values must be strings')
        if isinstance(s, _compat.text):
            try:
                s = s.encode('ascii')
            except UnicodeEncodeError:
                raise ValueError(u'cookies keys/values must be ascii-only')
        if b';' in s:
            raise ValueError(u"cookies keys/values cannot use ';' character")
        return s

    result = {}
    for key, val in cookies.items():
        new_key = validate_cookie_string(key)
        if b'=' in new_key:
            raise ValueError(u"cookies keys cannot use '=' character")
        new_val = validate_cookie_string(val)
        result[new_key] = new_val
    return result


def get_cookie_domain(url):
    '''
    Returns server domain that can be used as a cookie domain.
    Port number is stripped from the URL.
    url bust be an ascii-only unicode with absolute URL containing scheme
    Result is a byte-string.

    >>> get_cookie_domain(u'http://google.com:7000/path/' + \
                           u'something?key=val&key2=val2') == \
        b'google.com'
    True
    '''
    parsed_prefix = _compat.urlparse(url)
    if parsed_prefix.port is not None:
        result = re.search(u'([^:]+)(:[0-9]+)?', parsed_prefix.netloc).group(1)
    else:
        result = parsed_prefix.netloc
    return result.encode('utf-8')


@_arg_utils._fix_variable_name
@_arg_utils._check_type(_compat.text, bytes, type(None), dict)
def cookie_string(val, variable_name):
    '''
    Returns byte-string with cookies using key1=val1;key2=val2 format

    val can be:
      * None
      * byte-string (or ascii-only unicode text) using
        key1=val1;key2=val2 format
      * string dictionary with cookie keys and values.
        Neither keys nor values should contain semicolons.
        Keys cannot contain '=' character.
        Keys and values can be byte-strings or ascii-only unicode texts.

    variable_name is a unicode string used for exception message (or None).
    '''
    if val is None:
        return b''
    if isinstance(val, dict):
        return serialize_cookies(validate_cookies(val))
    if isinstance(val, _compat.text):
        try:
            return val.encode('ascii')
        except UnicodeEncodeError:
            err_msg = u'unicode ' + variable_name + u' must be ascii-only'
            raise ValueError(err_msg)
    return val
