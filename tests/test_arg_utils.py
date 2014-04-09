# coding=utf-8
import argparse

import tests.utils as utils
from dom2img import _arg_utils


class NonNegativeIntTest(utils.TestCase):

    FUN = _arg_utils.non_negative_int
    EXC = argparse.ArgumentTypeError

    def test_unicode(self):
        self._check_result(0, u'0', u'x')

    def test_byte_string(self):
        self._check_result(1, b'1', u'x')

    def test_int(self):
        self._check_result(2, 2, u'x')

    def test_without_variable_name(self):
        self._check_result(3, 3)

    def test_wrong_type(self):
        self._check_exception(u'x must be int/byte-string/unicode', [], u'x')

    def test_wrong_type_without_variable_name(self):
        err_msg = u'non_negative_int arg must be int/byte-string/unicode'
        self._check_exception(err_msg, {})

    def test_non_ascii_unicode_input(self):
        self._check_exception(u'y must be ascii-only unicode', u'ä', u'y')

    def test_non_ascii_unicode_input_without_variable_name(self):
        self._check_exception(u'non_negative_int arg must be ascii-only', u'ä')

    def test_unparsable_garbage(self):
        self._check_exception(u'val cannot be parsed as an int',
                              u'something', u'val')

    def test_unparsable_float_byte_string(self):
        self._check_exception(u'val cannot be parsed as an int',
                              b'3.2', u'val')

    def test_unparsable_float_byte_string_without_variable_name(self):
        self._check_exception(u'cannot parse as an int', b'3.2')

    def test_negative_byte_string(self):
        self._check_exception(u'Unexpected negative integer for x',
                              b'-1', u'x')

    def test_negative_unicode(self):
        self._check_exception(u'Unexpected negative integer for x',
                              u'-2', u'x')

    def test_negative_int(self):
        self._check_exception(u'Unexpected negative integer for x', -3, u'x')

    def test_negative_without_variable_name(self):
        self._check_exception(u'Unexpected negative integer', b'-4')


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
            u'a byte-string or unicode text'
        self._check_exception(err_msg, None, exc=TypeError)

    def test_non_ascii_unicode(self):
        err_msg = u'absolute_url() unicode text argument must be ascii-only'
        self._check_exception(err_msg, u'http://exämple.com/')

    def test_simple_relative_url(self):
        err_msg = u'absolute_url() argument must be an absolute URL'
        self._check_exception(err_msg, b'something')

    def test_complex_relative_url(self):
        err_msg = u'absolute_url() argument must be an absolute URL'
        self._check_exception(err_msg, b'path/something')

    def test_scheme_less_url(self):
        err_msg = u'absolute_url() argument must be an absolute URL'
        self._check_exception(err_msg, b'example.com/')

    def test_protocol_relative_url(self):
        err_msg = u'absolute_url() argument must be an absolute URL'
        self._check_exception(err_msg, u'//example.com/')
