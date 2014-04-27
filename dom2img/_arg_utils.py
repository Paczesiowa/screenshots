'''
Invalid argument value exception and validation utilities.
'''
from dom2img import _compat, _url_utils
import functools


def _concat_alternatives(alternatives):
    '''
    Return sentence with a list of alternatives

    >>> _concat_alternatives([u'foo']) == u'foo'
    True

    >>> _concat_alternatives([u'foo', u'bar']) == u'foo or bar'
    True

    >>> _concat_alternatives([u'foo', u'bar', u'baz']) == u'foo, bar or baz'
    True
    '''
    if not alternatives:
        return u''
    elif len(alternatives) == 1:
        return alternatives[0]
    else:
        return u', '.join(alternatives[:-1]) + u' or ' + alternatives[-1]


def _check_type(*possible_types):
    '''Type-value unifier decorator, that checks if value
    is instance of one of the specified types
    '''
    def wrapper(fun):
        @functools.wraps(fun)
        def inner_wrapper(val, variable_name):
            if isinstance(val, possible_types):
                return fun(val, variable_name)

            possible_types_string = \
                _concat_alternatives([type_.__name__
                                      for type_ in possible_types])

            err_msg = u'%s must be %s, not %s'
            err_msg = _compat.clean_exc_message(
                err_msg % (variable_name, possible_types_string,
                           _compat.make_text(val)))
            raise TypeError(err_msg)
        return inner_wrapper
    return wrapper


def _fix_variable_name(fun):
    'Type-value unifier decorator, that sets default variable_name'
    @functools.wraps(fun)
    def wrapper(val, variable_name=None):
        if variable_name is None:
            variable_name = fun.__name__ + u'() argument'
        return fun(val, variable_name)
    return wrapper


def _prettify_value_errors(fun):
    'Type-value unifier decorator, that value adds info to thrown ValueErrors'
    @functools.wraps(fun)
    def wrapper(val, variable_name):
        try:
            return fun(val, variable_name)
        except ValueError as e:
            (err_msg,) = e.args
            err_msg += u' for %s: %s' % (variable_name,
                                         _compat.make_text(val))
            e.args = (_compat.clean_exc_message(err_msg),)
            raise e
    return wrapper


@_fix_variable_name
@_check_type(_compat.text, _compat.byte_string, int)
@_prettify_value_errors
def non_negative_int(val, variable_name):
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
    try:
        val = int(val)
    except (ValueError, UnicodeEncodeError):
        raise ValueError(u'invalid value')

    if val < 0:
        raise ValueError(u'unexpected negative integer')

    return val

non_negative_int.__name__ = 'non-negative integer'


@_fix_variable_name
@_check_type(_compat.text, _compat.byte_string)
@_prettify_value_errors
def absolute_url(val, variable_name):
    '''
    Parse absolute URL.

    val is a ascii-only byte-string or unicode text containing absolute URL.

    variable_name is a unicode string used for exception message (or None).

    Returns ascii-only unicode text containing absolute URL.

    Raises:
    * TypeError if val is not a byte-string or unicode text
    * ValueError if val is not an ascii-only string
    * ValueError if val is not an absolute URL
    '''
    try:
        if isinstance(val, _compat.byte_string):
            val = val.decode('ascii')
        else:
            val.encode('ascii')  # check if it would work
    except (UnicodeDecodeError, UnicodeEncodeError):
        raise ValueError(u'invalid, non ascii-only value')

    if not _url_utils.is_absolute_url(val):
        raise ValueError(u'invalid, non-absolute URL value')

    return val


absolute_url.__name__ = 'absolute URL'
