'''
Invalid argument value exception and validation utilities.
'''
import argparse

from dom2img import _compat, _url_utils


def non_negative_int(val, variable_name=None):
    '''
    Check if val can be used as an non-negative integer value. it can be:
    * non-negative int
    * byte string containing decimal representation of non-negative-int
    * unicode text containing decimal representation of non-negative-int

    variable_name is a unicode string used for exception message (or None).

    >>> non_negative_int(u'7', 'x')
    7

    >>> non_negative_int(u'seven', 'x')
    Traceback (most recent call last):
    ...
    ArgumentTypeError: x cannot be parsed as an int
    '''
    exc = argparse.ArgumentTypeError
    if isinstance(val, _compat.text):
        try:
            val = val.encode('ascii')
        except UnicodeEncodeError:
            if variable_name is None:
                err_msg = u'non_negative_int arg must be ascii-only'
            else:
                err_msg = variable_name + u' must be ascii-only unicode'
            raise exc(err_msg)
    if isinstance(val, _compat.byte_string):
        try:
            val = int(val)
        except ValueError:
            if variable_name is None:
                err_msg = u'cannot parse as an int'
            else:
                err_msg = variable_name + u' cannot be parsed as an int'
            raise exc(err_msg)
    if not isinstance(val, int):
        if variable_name is None:
            err_msg = u'non_negative_int arg must be int/byte string/unicode'
        else:
            err_msg = variable_name + u' must be int/byte string/unicode'
        raise exc(err_msg)
    if val < 0:
        if variable_name is None:
            err_msg = u'Unexpected negative integer'
        else:
            err_msg = u'Unexpected negative integer for ' + variable_name
        raise exc(err_msg)
    return val


non_negative_int.__name__ = 'non-negative integer'


def absolute_url(val, variable_name=None):
    '''
    Parse absolute url.

    val is a byte string or ascii-only unicode text containing
    absolute url.

    variable_name is a unicode string used for exception message (or None).

    Returns ascii-only unicode text containing absolute url.

    Raises:
    * TypeError if val is not a byte-string or unicode text
    * ValueError if val is a non ascii-only unicode text
    * ValueError if val is not an absolute url
    '''
    if isinstance(val, _compat.byte_string):
        val = val.decode('ascii')
    if isinstance(val, _compat.text):
        try:
            val.encode('ascii')
        except UnicodeEncodeError:
            if variable_name is None:
                err_msg = u'absolute_url() unicode text argument ' + \
                    u'must be ascii-only'
            else:
                err_msg = u'unicode ' + variable_name + u' must be ascii-only'
            raise ValueError(err_msg)
    if not isinstance(val, _compat.text):
        if variable_name is None:
            err_msg = u'absolute_url() argument must be ' + \
                u'a byte string or unicode text'
        else:
            err_msg = \
                variable_name + u' must be a byte-string or an unicode text'
        raise TypeError(err_msg)
    if not _url_utils.is_absolute_url(val):
        if variable_name is None:
            err_msg = u'absolute_url() argument must be an absolute url'
        else:
            err_msg = variable_name + u' must be an absolute url'
        raise ValueError(err_msg)

    return val


absolute_url.__name__ = 'absolute url'
