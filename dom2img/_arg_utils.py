'''
Invalid argument value exception and validation utilities.
'''
from dom2img import _compat, _url_utils


def non_negative_int(val, variable_name=None):
    '''
    Check if val can be used as an non-negative integer value. it can be:
    * non-negative int
    * byte-string containing decimal representation of non-negative-int
    * unicode text containing decimal representation of non-negative-int

    variable_name is a unicode string used for exception message (or None).

    Raises:
    * TypeError if val is not int or string
    * ValueError if val is negative or cannot be parsed

    >>> non_negative_int(u'7', 'x')
    7
    '''
    if variable_name is None:
        variable_name = u'non_negative_int() argument'

    if not isinstance(val, _compat.text) and \
       not isinstance(val, _compat.byte_string) and \
       not isinstance(val, int):
        err_msg = u"%s must be an int or a string, not '%s'"
        err_msg = _compat.clean_exc_message(
            err_msg % (variable_name, _compat.make_text(val)))
        raise TypeError(err_msg)

    try:
        val = int(val)
    except (ValueError, UnicodeEncodeError):
        err_msg = u"invalid value for %s: '%s'"
        err_msg = _compat.clean_exc_message(
            err_msg % (variable_name, _compat.make_text(val)))
        raise ValueError(err_msg)

    if val < 0:
        err_msg = u'Unexpected negative integer for %s: %d'
        raise ValueError(err_msg % (variable_name, val))

    return val

non_negative_int.__name__ = 'non-negative integer'


def absolute_url(val, variable_name=None):
    '''
    Parse absolute URL.

    val is a byte-string or ascii-only unicode text containing
    absolute URL.

    variable_name is a unicode string used for exception message (or None).

    Returns ascii-only unicode text containing absolute URL.

    Raises:
    * TypeError if val is not a byte-string or unicode text
    * ValueError if val is a non ascii-only unicode text
    * ValueError if val is not an absolute URL
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
                u'a byte-string or unicode text'
        else:
            err_msg = \
                variable_name + u' must be a byte-string or an unicode text'
        raise TypeError(err_msg)
    if not _url_utils.is_absolute_url(val):
        if variable_name is None:
            err_msg = u'absolute_url() argument must be an absolute URL'
        else:
            err_msg = variable_name + u' must be an absolute URL'
        raise ValueError(err_msg)

    return val


absolute_url.__name__ = 'absolute URL'
