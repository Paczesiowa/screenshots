# coding=utf-8
import sys

import tests.utils as utils
from dom2img import _arg_utils, _compat


class CheckTypeTest(utils.TestCase):

    def test_single(self):
        @_arg_utils._check_type(int)
        def foo(val, variable_name):
            return variable_name
        self.assertEqual(u'x', foo(2, u'x'))
        self.assertRaisesRegexp(TypeError, u'x must be int, not None',
                                foo, None, u'x')

    def test_double(self):
        @_arg_utils._check_type(int, float)
        def foo(val, variable_name):
            return variable_name
        self.assertEqual(u'x', foo(2, u'x'))
        self.assertEqual(u'x', foo(2., u'x'))
        self.assertRaisesRegexp(TypeError, u'x must be int or float, not None',
                                foo, None, u'x')

    def test_triple(self):
        @_arg_utils._check_type(int, dict, list)
        def foo(val, variable_name):
            return variable_name
        self.assertEqual(u'x', foo(2, u'x'))
        self.assertEqual(u'x', foo({}, u'x'))
        self.assertEqual(u'x', foo([], u'x'))
        self.assertRaisesRegexp(TypeError,
                                u'x must be int, dict or list, not None',
                                foo, None, u'x')

    def test_byte_string_value(self):
        @_arg_utils._check_type(int)
        def foo(val, variable_name):
            return variable_name
        self.assertRaisesRegexp(TypeError, u"x must be int, not b'bar'",
                                foo, b'bar', u'x')

    def test_byte_string_unicode_value(self):
        @_arg_utils._check_type(int)
        def foo(val, variable_name):
            return variable_name
        if sys.version_info < (3,):
            err_msg = u"x must be int, not b'b\\?\\?r'"  # escape ? for regexp
        else:
            # escape \ for regexp
            err_msg = u"x must be int, not b'b\\\\xc3\\\\xa4r'"
        self.assertRaisesRegexp(TypeError, err_msg,
                                foo, u'bär'.encode('utf-8'), u'x')

    def test_unicode_error_message(self):
        @_arg_utils._check_type(int)
        def foo(val, variable_name):
            return variable_name
        err_msg = u'bär must be int, not föö'
        self.assertRaisesExcStr(TypeError, err_msg,
                                foo, u'föö', u'bär')


class FixVariableNameTest(utils.TestCase):

    def test_no_override(self):
        @_arg_utils._fix_variable_name
        def foo(val, variable_name):
            return variable_name
        self.assertEqual(u'x', foo(2, u'x'))

    def test_override_on_none(self):
        @_arg_utils._fix_variable_name
        def foo(val, variable_name):
            return variable_name
        self.assertEqual(u'foo() argument', foo(2))
        self.assertEqual(u'foo() argument', foo(2, None))


class PrettifyValueErrorsTest(utils.TestCase):

    def test_return_works(self):
        @_arg_utils._prettify_value_errors
        def foo(val, variable_name):
            return val
        self.assertEqual(2, foo(2, u'x'))

    def test_other_exceptions_pass_through(self):
        @_arg_utils._prettify_value_errors
        def foo(val, variable_name):
            raise TypeError(u'bar')
        self.assertRaisesRegexp(TypeError, u'bar', foo, 2, u'x')

    def test_simple_value_error(self):
        @_arg_utils._prettify_value_errors
        def foo(val, variable_name):
            raise ValueError(u'invalid value')
        self.assertRaisesRegexp(ValueError, u'invalid value for x: 2',
                                foo, 2, u'x')

    def test_byte_string_value(self):
        @_arg_utils._prettify_value_errors
        def foo(val, variable_name):
            raise ValueError(u'error')
        self.assertRaisesRegexp(ValueError, u"error for x: b'bar'",
                                foo, b'bar', u'x')

    def test_byte_string_unicode_value(self):
        @_arg_utils._prettify_value_errors
        def foo(val, variable_name):
            raise ValueError(u'error')
        if sys.version_info < (3,):
            err_msg = u"error for x: b'b\\?\\?r'"  # escape ? for regexp
        else:
            # escape \ for regexp
            err_msg = u"error for x: b'b\\\\xc3\\\\xa4r'"
        self.assertRaisesRegexp(ValueError, err_msg,
                                foo, u'bär'.encode('utf-8'), u'x')

    def test_unicode_error_message(self):
        @_arg_utils._prettify_value_errors
        def foo(val, variable_name):
            raise ValueError(u'errör')
        if sys.version_info < (3,):
            err_msg = u'err\\?r for x: 2'  # escape ? for regexp
        else:
            err_msg = u'errör for x: 2'
        self.assertRaisesRegexp(ValueError, err_msg,
                                foo, 2, u'x')


class NonNegativeIntTest(utils.TestCase):

    FUN = _arg_utils.non_negative_int
    EXC = ValueError

    def test_unicode(self):
        self._check_result(0, u'0', u'x')

    def test_byte_string(self):
        self._check_result(1, b'1', u'x')

    def test_int(self):
        self._check_result(2, 2, u'x')

    def test_without_variable_name(self):
        self._check_result(3, 3)

    def test_wrong_type(self):
        err_msg = u'x must be %s, %s or int, not []'
        err_msg = err_msg % (_compat.text.__name__,
                             _compat.byte_string.__name__)
        self._check_exception(err_msg, [], u'x', exc=TypeError)

    def test_wrong_type_without_variable_name(self):
        err_msg = u'non_negative_int() argument must be %s, ' + \
            u'%s or int, not {}'
        err_msg = err_msg % (_compat.text.__name__,
                             _compat.byte_string.__name__)
        self._check_exception(err_msg, {}, exc=TypeError)

    def test_non_ascii_unicode_input(self):
        err_msg = u'invalid value for y: bär'
        self._check_exception(err_msg, u'bär', u'y')

    def test_non_ascii_unicode_input_without_variable_name(self):
        err_msg = u'invalid value for non_negative_int() argument: bär'
        self._check_exception(err_msg, u'bär')

    def test_unparsable_garbage(self):
        err_msg = u'invalid value for val: something'
        self._check_exception(err_msg, u'something', u'val')

    def test_unparsable_float_byte_string(self):
        err_msg = u"invalid value for val: b'3.2'"
        self._check_exception(err_msg, b'3.2', u'val')

    def test_unparsable_float_byte_string_without_variable_name(self):
        err_msg = u"invalid value for non_negative_int() argument: b'3.2'"
        self._check_exception(err_msg, b'3.2')

    def test_negative_byte_string(self):
        err_msg = u"unexpected negative integer for x: b'-1'"
        self._check_exception(err_msg, b'-1', u'x')

    def test_negative_unicode(self):
        err_msg = u'unexpected negative integer for x: -2'
        self._check_exception(err_msg, u'-2', u'x')

    def test_negative_int(self):
        err_msg = u'unexpected negative integer for x: -3'
        self._check_exception(err_msg, -3, u'x')

    def test_negative_without_variable_name(self):
        err_msg = u'unexpected negative integer ' + \
            u"for non_negative_int() argument: b'-4'"
        self._check_exception(err_msg, b'-4')


class AbsoluteURLTest(utils.TestCase):

    FUN = _arg_utils.absolute_url
    EXC = ValueError

    def test_simple_byte_string(self):
        self._check_result(u'http://example.com/', b'http://example.com/')

    def test_simple_unicode(self):
        self._check_result(u'http://example.com/', u'http://example.com/')

    def test_url_with_path_byte_string(self):
        self._check_result(u'http://example.com/foo/bar',
                           b'http://example.com/foo/bar')

    def test_url_with_path_unicode(self):
        self._check_result(u'http://example.com/foo/bar',
                           u'http://example.com/foo/bar')

    def test_wrong_type(self):
        err_msg = u'absolute_url() argument must be ' + \
            u'%s or %s, not None'
        err_msg = err_msg % (_compat.text.__name__,
                             _compat.byte_string.__name__)
        self._check_exception(err_msg, None, exc=TypeError)

    def test_non_ascii_unicode(self):
        err_msg = u'invalid, non ascii-only value for absolute_url() ' + \
            u'argument: http://exämple.com/'
        self._check_exception(err_msg, u'http://exämple.com/')

    def test_non_ascii_byte_string(self):
        byte_string = u'http://exämple.com/'.encode('utf-8')
        err_msg = u'invalid, non ascii-only value for absolute_url() ' + \
            u'argument: ' + _compat.make_text(byte_string)
        self._check_exception(err_msg, byte_string)

    def test_simple_relative_url(self):
        err_msg = u'invalid, non-absolute URL value for ' + \
            u"absolute_url() argument: b'something'"
        self._check_exception(err_msg, b'something')

    def test_complex_relative_url(self):
        err_msg = u'invalid, non-absolute URL value for absolute_url() ' + \
            u"argument: b'path/something'"
        self._check_exception(err_msg, b'path/something')

    def test_scheme_less_url(self):
        err_msg = u'invalid, non-absolute URL value for absolute_url() ' + \
            u"argument: b'example.com/'"
        self._check_exception(err_msg, b'example.com/')

    def test_protocol_relative_url(self):
        err_msg = u'invalid, non-absolute URL value for absolute_url() ' + \
            u'argument: //example.com/'
        self._check_exception(err_msg, u'//example.com/')


class UTF8ByteStringTest(utils.TestCase):

    FUN = _arg_utils.utf8_byte_string
    EXC = ValueError

    def test_text(self):
        self._check_result(b'foo', u'foo', u'content')
        self._check_result(u'bär'.encode('utf-8'), u'bär', u'content')

    def test_byte_string(self):
        self._check_result(b'foo', b'foo', u'content')
        bar_bs = u'bär'.encode('utf-8')
        self._check_result(bar_bs, bar_bs, u'content')

    def test_without_variable_name(self):
        self._check_result(b'bar', b'bar')

    def test_wrong_type(self):
        err_msg = u'x must be %s or %s, not []'
        err_msg = err_msg % (_compat.text.__name__,
                             _compat.byte_string.__name__)
        self._check_exception(err_msg, [], u'x', exc=TypeError)

    def test_wrong_type_without_variable_name(self):
        err_msg = u'utf8_byte_string() argument must be %s or ' + \
            u'%s, not {}'
        err_msg = err_msg % (_compat.text.__name__,
                             _compat.byte_string.__name__)
        self._check_exception(err_msg, {}, exc=TypeError)

    def test_byte_string_not_utf8(self):
        bar_bs_16 = u'bär'.encode('utf-16')
        err_msg = u'content byte string ' + \
            u'is not properly utf-8 encoded'
        self._check_exception(err_msg, bar_bs_16, u'content')

    def test_byte_string_not_utf8_without_variable_name(self):
        bar_bs_16 = u'bär'.encode('utf-16')
        err_msg = u'utf8_byte_string() argument byte string ' + \
            u'is not properly utf-8 encoded'
        self._check_exception(err_msg, bar_bs_16)
