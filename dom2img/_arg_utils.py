'''
Invalid argument value exception and validation utilities.
'''
import functools

from dom2img import _compat, _url_utils, _inspect


def _concat_alternatives(alternatives):
    '''
    Return sentence with a list of alternatives.

    Args:
        alternatives: non-empty list of unicode texts.

    Returns:
        Unicode text with english sentence using the following format:
        "foo, bar or baz".

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
    '''
    Decorator factory for checking class of type-value unifier's value.

    Args:
        *possible_types: non-empty tuple of types, type-value unifier's value
            will be checked if it is an instance of these types.

    Returns:
        Function, that decorates type-value unifier, that works the same way,
        but it will throw a TypeError for values that aren't instance
        of one of possible_types.
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
    '''
    Decorator for setting default type-value unifier's variable name.

    Args:
        fun: type-value unifier to decorate.

    Returns:
        Function, type-value unifier that works the same way as fun, but makes
        the variable_name argument optional, by providing default value for it,
        e.g. "foo() argument".
    '''
    @functools.wraps(fun)
    def wrapper(val, variable_name=None):
        if variable_name is None:
            variable_name = fun.__name__ + u'() argument'
        return fun(val, variable_name)
    return wrapper


def _prettify_value_errors(fun):
    '''
    Type-value unifier decorator, that adds value info to thrown ValueErrors.

    Args:
        fun: Type-value unifier to decorate.

    Returns:
        Function, type-value unifier, that works the same way as fun, but adds
        information about value to all ValueError exceptions thrown during
        validation process.
    '''
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


def validate_and_unify(**arg_validators):
    '''
    Decorator factory for adding type-value unifiers to function arguments.

    Example usage:

    @validate_and_unify(x=some_type_value_unifier)
    def foo(x):
        ...

    Args:
        **arg_validators: Dict, that maps decorated function argument names
            to type-value unifiers. Decorated function will be called with
            unified arguments, or if they don't have the correct type,
            or fail the respective validation process an exception will
            be thrown instead.

    Returns:
        Function decorator; decorated function will work the same way, as long
        as call params will pass their respective type-value unifiers.
        Additionally, call params will be unified prior to being passed to
        decorated function. If they do not pass type checks or validation
        process, TypeError or ValueError will be raised instead of calling
        the decorated function.
    '''
    def wrapper(fun):
        @functools.wraps(fun)
        def inner_wrapper(*args, **kwargs):
            args_values = _inspect.getcallargs(fun, *args, **kwargs)
            for arg in args_values:
                try:
                    validator = arg_validators[arg]
                except KeyError:
                    pass
                else:
                    args_values[arg] = validator(args_values[arg], arg)
            return fun(**args_values)
        return inner_wrapper
    return wrapper


@_fix_variable_name
@_check_type(_compat.text, bytes, int)
@_prettify_value_errors
def non_negative_int(val, variable_name):
    '''
    Type-value unifier for non-negative integers.

    Values can be ints or [byte-]strings. Strings should be decimal
    representations of integers.

    Validation process checks if the value is greater, or equal to zero.

    Args:
        val: int, bytes or unicode text, containing value that should be
            unified to int and validated for being greater or equal to zero.
        variable_name: unicode text (optional, may be None), with variable
            name used for this value in the calling function. Used only
            for exception messages.

    Returns:
        int, that is greater or equal to zero.

    Raises:
        TypeError: val is not int, bytes or an unicode text.
        ValueError: val is a negative int or cannot be parsed as an int.

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
@_check_type(_compat.text, bytes)
@_prettify_value_errors
def absolute_url(val, variable_name):
    '''
    Type-value unifier for absolute URLs.

    Values can be bytes or an unicode text.

    Validation process checks if the string can be parsed as an absolute URL.

    Args:
        val: bytes or unicode text, containing ascii-only value, that must be
            an absolute URL.
        variable_name: unicode text (optional, may be None), with variable
            name used for this value in the calling function. Used only
            for exception messages.

    Returns:
        Unicode text, that is ascii-only and represents an absolute URL.

    Raises:
        TypeError: val is not bytes or an unicode text.
        ValueError: val is not ascii-only or it's not an absolute URL.
    '''
    try:
        if isinstance(val, bytes):
            val = val.decode('ascii')
        else:
            val.encode('ascii')  # check if it would work
    except (UnicodeDecodeError, UnicodeEncodeError):
        raise ValueError(u'invalid, non ascii-only value')

    if not _url_utils.is_absolute_url(val):
        raise ValueError(u'invalid, non-absolute URL value')

    return val


absolute_url.__name__ = 'absolute URL'


@_fix_variable_name
@_check_type(_compat.text, bytes)
def utf8_byte_string(val, variable_name):
    '''
    Type-value unifier for utf-8 strings.

    Values can be bytes or unicode texts.

    Validation process checks if the bytes object is properly utf-8 encoded.
    Unicode texts don't need any validation.

    Args:
        val: utf-8 encoded bytes or unicode text.
        variable_name: unicode text (optional, may be None), with variable
            name used for this value in the calling function. Used only
            for exception messages.

    Returns:
        bytes, utf-8 encoded.

    Raises:
        TypeError: val is not bytes or an unicode text.
        ValueError: val is bytes, but not properly utf-8 encoded.
    '''
    if isinstance(val, _compat.text):
        return val.encode('utf-8')
    try:
        val.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError(
            variable_name + u' byte string is not properly utf-8 encoded')
    return val
