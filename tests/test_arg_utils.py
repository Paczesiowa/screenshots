# coding=utf-8
import argparse
import unittest2

from dom2img import _arg_utils


class NonNegativeIntTest(unittest2.TestCase):

    def check_result(self, inp, out, var=None):
        fun = _arg_utils.non_negative_int
        self.assertEqual(out, fun(inp, variable_name=var))

    def check_exception(self, inp, exc_msg, var=None):
        fun = _arg_utils.non_negative_int
        exc = argparse.ArgumentTypeError
        self.assertRaisesRegexp(exc, exc_msg, fun, inp, var)

    def test_unicode(self):
        self.check_result(u'0', 0, u'x')

    def test_byte_string(self):
        self.check_result(b'1', 1, u'x')

    def test_int(self):
        self.check_result(2, 2, u'x')

    def test_without_variable_name(self):
        self.check_result(3, 3)

    def test_wrong_type(self):
        self.check_exception([], u'x must be int/byte string/unicode', u'x')

    def test_wrong_type_without_variable_name(self):
        err_msg = u'non_negative_int arg must be int/byte string/unicode'
        self.check_exception({}, err_msg)

    def test_non_ascii_unicode_input(self):
        self.check_exception(u'ä', u'y must be ascii-only unicode', u'y')

    def test_non_ascii_unicode_input_without_variable_name(self):
        self.check_exception(u'ä', u'non_negative_int arg must be ascii-only')

    def test_unparsable_garbage(self):
        self.check_exception(u'something', u'val cannot be parsed as an int',
                             u'val')

    def test_unparsable_float_byte_string(self):
        self.check_exception(b'3.2', u'val cannot be parsed as an int',
                             u'val')

    def test_unparsable_float_byte_string_without_variable_name(self):
        self.check_exception(b'3.2', u'cannot parse as an int')

    def test_negative_byte_string(self):
        self.check_exception(b'-1', u'Unexpected negative integer for x', u'x')

    def test_negative_unicode(self):
        self.check_exception(u'-2', u'Unexpected negative integer for x', u'x')

    def test_negative_int(self):
        self.check_exception(-3, u'Unexpected negative integer for x', u'x')

    def test_negative_without_variable_name(self):
        self.check_exception(b'-4', u'Unexpected negative integer')


class AbsoluteURLTest(unittest2.TestCase):

    def _check_result(self, inp, out):
        fun = _arg_utils.absolute_url
        self.assertEqual(out, fun(inp))

    def _check_exception(self, inp, exc_msg, exc_type=ValueError):
        fun = _arg_utils.absolute_url
        self.assertRaisesRegexp(exc_type, exc_msg, fun, inp)

    def test_simple_byte_string(self):
        self._check_result(b'http://example.com/', b'http://example.com/')

    def test_simple_unicode(self):
        self._check_result(u'http://example.com/', b'http://example.com/')

    def test_url_with_path_byte_string(self):
        self._check_result(b'http://example.com/foo/bar',
                           b'http://example.com/foo/bar')

    def test_url_with_path_unicode(self):
        self._check_result(u'http://example.com/foo/bar',
                           b'http://example.com/foo/bar')

    def test_wrong_type(self):
        err_msg = u'absolute_url\\(\\) argument must be ' + \
            u'a byte string or unicode text'
        self._check_exception(None, err_msg, TypeError)

    def test_non_ascii_unicode(self):
        err_msg = \
            u'absolute_url\\(\\) unicode text argument must be ascii-only'
        self._check_exception(u'http://exämple.com/', err_msg)

    def test_simple_relative_url(self):
        err_msg = u'absolute_url\\(\\) argument must be an absolute url'
        self._check_exception(b'something', err_msg)

    def test_complex_relative_url(self):
        err_msg = u'absolute_url\\(\\) argument must be an absolute url'
        self._check_exception(b'path/something', err_msg)

    def test_scheme_less_url(self):
        err_msg = u'absolute_url\\(\\) argument must be an absolute url'
        self._check_exception(b'example.com/', err_msg)

    def test_protocol_relative_url(self):
        err_msg = u'absolute_url\\(\\) argument must be an absolute url'
        self._check_exception(u'//example.com/', err_msg)
