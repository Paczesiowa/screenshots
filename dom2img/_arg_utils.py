'''
Invalid argument value exception and validation utilities.
'''
import argparse

from dom2img import _compat


def non_negative_int(val, variable_name):
    '''
    Check if val can be used as an non-negative integer value. it can be:
    * non-negative int
    * byte string containing decimal representation of non-negative-int
    * unicode text containing decimal representation of non-negative-int

    variable_name is a unicode string used for exception message.

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
            raise exc(variable_name + u' must be ascii-only unicode')
    if isinstance(val, _compat.byte_string):
        try:
            val = int(val)
        except ValueError:
            raise exc(variable_name + u' cannot be parsed as an int')
    if not isinstance(val, int):
        raise exc(variable_name + u' must be int or byte string or unicode')
    if val < 0:
        raise exc(u'Unexpected negative integer for ' + variable_name)
    return val
