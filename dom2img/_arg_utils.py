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


def non_negative_int(string, variable_name):
    '''
    Check if string is a unicode string that can be parsed
    as non-negative integer.
    variable_name is a unicode string used for exception message.

    >>> non_negative_int(u'7', 'x')
    7

    >>> non_negative_int(u'seven', 'x')
    Traceback (most recent call last):
    ...
    Dom2ImgArgumentException: x cannot be parsed as an int
    '''
    if type(string) != _compat.text:
        raise Dom2ImgArgumentException(
            variable_name + u' is not a unicode string')
    try:
        value = int(string)
    except ValueError:
        raise Dom2ImgArgumentException(
            variable_name + u' cannot be parsed as an int')
    else:
        if value < 0:
            raise Dom2ImgArgumentException(
                u'Unexpected negative integer for ' + variable_name)
        else:
            return value
