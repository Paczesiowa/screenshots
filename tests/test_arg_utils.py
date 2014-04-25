# coding=utf-8
import tests.utils as utils
from dom2img import _arg_utils, _compat


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
