'''
Invalid argument value exception and validation utilities.
'''
import argparse

from dom2img import _compat


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
