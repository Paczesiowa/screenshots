import re

from dom2img import _compat, _arg_utils


def serialize_cookies(cookies):
    '''
    Serializes cookie dictionary to cookie string.

    Args:
        cookies: dict mapping byte-string cookie keys to byte-string
            cookie values. Neither keys nor values should contain semicolons.
            Keys cannot contain '=' character.

    Returns:
        Semicolon-separated bytes object with cookie elems in key=value format.
    '''
    return b';'.join(map(b'='.join, cookies.items()))


def parse_cookie_string(cookie_string):
    '''
    Parse cookie dictionary from a string using "key1=val1;key2=val2" format.

    Args:
        cookie_string: Ascii-only bytes or unicode text with cookies, using
            "key1=val1;key2=val2" format.

    Returns:
        dict mapping bytes cookie keys to bytes cookie values.

    Raises:
        TypeError: cookie_string is not bytes or unicode text.
        ValueError: cookie_string contains non-ascii characters.

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
    Validates cookies dict for illegal characters and types.

    Check if cookies is a dict:
        dict keys can be ascii-only bytes or unicode text strings,
            they cannot contain ';' and '=' characters.
        dict values can be ascii-only bytes or unicode text strings,
            they cannot contain ';'.

    Args:
        cookies: dict with cookies.

    Returns:
        dict with validated cookies. all keys and values are bytes.

    Raises:
        TypeError: cookies keys or values are not bytes or unicode texts.
        ValueError: cookies keys or values are not ascii-only, or
            contain illegal characters.

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
    Extract server domain that can be used as a cookie domain.

    Port number is stripped from the URL.

    Args:
        url: Ascii-only unicode text with absolute URL containing scheme.

    Returns:
        bytes with hostname that can be used as a cookie domain.

    >>> get_cookie_domain(u'http://example.com:7000/path/' + \
                           u'something?key=val&key2=val2') == \
        b'example.com'
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
    Type-value unifier for cookie strings.

    Args:
        val:
            * None
            * bytes or ascii-only unicode text using "key1=val1;key2=val2"
                format.
            * dict with cookie bytes/unicode text keys and values.
                Neither keys nor values should contain semicolons.
                Keys cannot contain '=' character.
        variable_name: unicode text (optional, may be None), with variable
            name used for this value in the calling function. Used only
            for exception messages.

    Returns:
        bytes with cookie string using "key1=val1;key2=val2" format.

    Raises:
        TypeError: val is not None, bytes, unicode text or dict, or contains
            keys or values that are not bytes or unicode texts.
        ValueError: cookies or its keys/values is not ascii-only, or
            contain illegal characters.
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
