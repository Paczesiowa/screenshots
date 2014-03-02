'''
Invalid argument value exception and validation utilities.
'''
from dom2img import _compat


class Dom2ImgArgumentException(ValueError):
    '''
    Exception class to be used when public dom2img
    function's argument has invalid value.
    '''
    pass


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
    Dom2ImgArgumentException: x cannot be parsed as an int
    '''
    if isinstance(val, _compat.text):
        try:
            val = val.encode('ascii')
        except UnicodeEncodeError:
            raise Dom2ImgArgumentException(
                variable_name + u' must be ascii-only unicode')
    if isinstance(val, _compat.byte_string):
        try:
            val = int(val)
        except ValueError:
            raise Dom2ImgArgumentException(
                variable_name + u' cannot be parsed as an int')
    if not isinstance(val, int):
        raise Dom2ImgArgumentException(
            variable_name + u' must be int or byte string or unicode')
    if val < 0:
        raise Dom2ImgArgumentException(
            u'Unexpected negative integer for ' + variable_name)
    return val
