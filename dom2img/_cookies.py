import re

from dom2img import _arg_utils, _compat


def serialize_cookies(cookies):
    '''
    Serializes cookie dictionary to cookie string.
    cookies must be a dict mapping byte string cookie keys
    to byte string cookie values. Neither keys nor values should
    contain semicolons. Keys cannot contain '=' character.
    Result is a semicolon-separated byte string with cookie elems
    in key=value format.

    >>> serialize_cookies({b'key1': b'val1', b'key2': b'val2'}) == \
        b'key2=val2;key1=val1'
    True
    '''
    return ';'.join(map('='.join, cookies.items()))


def parse_cookie_string(cookie_string):
    '''
    Parse cookie dictionary from a unicode text string,
    containing only ascii characters, using format key1=val1;key2=val2.
    Returns dictionary mapping byte string cookie keys to byte string
    cookie values.

    Raises exception if cookie_string is not an unicode text string,
    or if it contains non-ascii characters.

    >>> parse_cookie_string(u'key1=val1;key2=val2') == \
        {b'key1': b'val1', b'key2': b'val2'}
    True
    '''
    if type(cookie_string) is not _compat.text:
        raise _arg_utils.Dom2ImgArgumentException(
            'cookie_string must be an ascii-only unicode text string')
    if u'=' not in cookie_string:
        return {}
    cookies = {}
    cookie_elems = cookie_string.split(u';')
    try:
        for cookie_elem in cookie_elems:
            cookie = cookie_elem.split(u'=')
            cookie_key = cookie.pop(0).encode('ascii')
            cookie_value = '='.join(cookie).encode('ascii')
            cookies[cookie_key] = cookie_value
        return cookies
    except UnicodeEncodeError:
        raise _arg_utils.Dom2ImgArgumentException(
            'cookie_string must be an ascii-only unicode text string')


def validate_cookies(cookies):
    '''
    Check if cookies is a dict:
    * dict keys can be byte strings or ascii-only unicode text strings,
      they cannot contain ';' and '=' characters.
    * dict values can be byte strings or ascii-only unicode text strings,
      they cannot contain ';'.
    Returns validated dict, where keys and values are byte strings.
    Raises exception if cookie keys/values contain illegal characters,
    or if they contain non-ascii characters.

    >>> validate_cookies({u'key1': u'val1', u'key2': u'val2'}) == \
        {b'key1': b'val1', b'key2': b'val2'}
    True
    '''
    if type(cookies) is not dict:
        raise _arg_utils.Dom2ImgArgumentException(
            'cookies must be a dict')

    def validate_cookie_string(s):
        if type(s) not in [_compat.byte_string, _compat.text]:
            raise _arg_utils.Dom2ImgArgumentException(
                'cookies key/values must be strings')
        if type(s) is _compat.text:
            try:
                s = s.encode('ascii')
            except UnicodeEncodeError:
                raise _arg_utils.Dom2ImgArgumentException(
                    'cookies keys/values must be ascii-only')
        if b';' in s:
            raise _arg_utils.Dom2ImgArgumentException(
                "cookies keys/values cannot use ';' character")
        return s

    result = {}
    for key, val in cookies.items():
        new_key = validate_cookie_string(key)
        if b'=' in new_key:
            raise _arg_utils.Dom2ImgArgumentException(
                "cookies keys cannot use '=' character")
        new_val = validate_cookie_string(val)
        result[new_key] = new_val
    return result


def get_cookie_domain(url):
    '''
    Returns server domain that can be used as a cookie domain.
    Port number is stripped from the url.
    url must be an byte string with absolute URL containing scheme.
    Result is a byte string.

    >>> get_cookie_domain(b'http://google.com:7000/path/' + \
                           b'something?key=val&key2=val2') == \
        b'google.com'
    True
    '''
    parsed_prefix = _compat.urlparse(url)
    if parsed_prefix.port is not None:
        return re.search('([^:]+)(:[0-9]+)?', parsed_prefix.netloc).group(1)
    else:
        return parsed_prefix.netloc
