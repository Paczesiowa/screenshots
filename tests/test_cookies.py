# coding=utf-8
import tests.utils as utils
from dom2img import _cookies, _compat


class SerializeCookiesTest(utils.TestCase):

    FUN = _cookies.serialize_cookies

    def test_empty(self):
        self._check_result(b'', {})

    def test_simple(self):
        self._check_result(b'foo=bar', {b'foo': b'bar'})

    def test_complex(self):
        result = _cookies.serialize_cookies({b'foo': b'bar', b'baz': b'quux'})
        self.assertTrue(b'foo=bar' in result)
        self.assertTrue(b'baz=quux' in result)
        self.assertTrue(b';' in result)
        self.assertEqual(16, len(result))


class ParseCookieStringTest(utils.TestCase):

    FUN = _cookies.parse_cookie_string
    EXC = ValueError

    def test_empty(self):
        self._check_result({}, b'')

    def test_no_equals_char(self):
        self._check_result({}, u'test')

    def test_single_equals_char(self):
        self._check_result({b'': b''}, u'=')

    def test_simple_byte_string(self):
        self._check_result({b'foo': b'bar'}, b'foo=bar')

    def test_simple_unicode(self):
        self._check_result({b'foo': b'bar'}, u'foo=bar')

    def test_cookie_value_with_equals_char(self):
        self._check_result({b'foo': b'bar=baz'}, u'foo=bar=baz')

    def test_complex_unicode(self):
        self._check_result({b'foo': b'bar=baz===', b'quux': b'plonk'},
                           u'foo=bar=baz===;quux=plonk')

    def test_complex_byte_string(self):
        self._check_result({b'foo': b'bar=baz===', b'quux': b'plonk'},
                           b'foo=bar=baz===;quux=plonk')

    def test_non_ascii_unicode(self):
        self._check_exception(u'unicode cookie_string must be ascii-only',
                              u'föö=bär')

    def test_wrong_type(self):
        err_msg = u'cookie_string must be an ascii-only ' + \
            u'unicode text or a byte-string'
        self._check_exception(err_msg, None, exc=TypeError)


def parse_and_serialize_cookies(input_):
    return _cookies.serialize_cookies(_cookies.parse_cookie_string(input_))


class ParseAndSerializeCookiesTest(utils.TestCase):

    FUN = parse_and_serialize_cookies

    def test_simple_byte_string(self):
        self._check_result(b'foo=bar', b'foo=bar')

    def test_simple_unicode(self):
        self._check_result(b'foo=bar', u'foo=bar')

    def test_complex_byte_string(self):
        self._check_result(b'foo=bar&baz=quux', b'foo=bar&baz=quux')

    def test_complex_unicode(self):
        self._check_result(b'foo=bar&baz=quux', u'foo=bar&baz=quux')

    def test_multiple_equals_characters_in_value(self):
        self._check_result(b'foo=bar=quux==', b'foo=bar=quux==')


class ValidateCookiesTest(utils.TestCase):

    FUN = _cookies.validate_cookies
    EXC = ValueError

    def test_empty(self):
        self._check_result({}, {})

    def test_simple_byte_string(self):
        self._check_result({b'foo': b'bar'}, {b'foo': b'bar'})

    def test_simple_unicode(self):
        self._check_result({b'foo': b'bar'}, {u'foo': u'bar'})

    def test_complex(self):
        self._check_result({b'foo': b'bar', b'baz': b'quux'},
                           {b'foo': b'bar', u'baz': u'quux'})

    def test_wrong_type(self):
        self._check_exception(u'cookies must be a dict', [], exc=TypeError)

    def test_wrong_type_of_values(self):
        self._check_exception(u'cookies key/values must be strings',
                              {u'foo': []}, exc=TypeError)

    def test_wrong_type_of_keys(self):
        self._check_exception(u'cookies key/values must be strings',
                              {3: u'bar'}, exc=TypeError)

    def test_non_ascii_unicode_keys(self):
        self._check_exception(u'cookies keys/values must be ascii-only',
                              {u'föö': u'bar'})

    def test_non_ascii_unicode_values(self):
        self._check_exception(u'cookies keys/values must be ascii-only',
                              {u'foo': u'bär'})

    def test_keys_with_equals_char(self):
        self._check_exception(u"cookies keys cannot use '=' character",
                              {u'f=o': b'bar'})

    def test_keys_with_semicolon(self):
        self._check_exception(u"cookies keys/values cannot use ';' character",
                              {u'f;o': b'bar'})

    def test_values_with_semicolon(self):
        self._check_exception(u"cookies keys/values cannot use ';' character",
                              {u'foo': b'b;r'})


class GetCookieDomainTest(utils.TestCase):
    FUN = _cookies.get_cookie_domain

    def test_simple(self):
        self._check_result(b'example.com', u'http://example.com')

    def test_with_ending_slash(self):
        self._check_result(b'example.com', u'http://example.com/')

    def test_with_path(self):
        self._check_result(b'example.com', u'http://example.com/something')

    def test_with_query_part(self):
        self._check_result(b'example.com', u'http://example.com/?key=val')

    def test_with_port(self):
        self._check_result(b'example.com', u'http://example.com:8000')

    def test_complex(self):
        input_ = u'http://example.com:7000/path/something?key=val&key2=val2'
        self._check_result(b'example.com', input_)


class CookieStringTest(utils.TestCase):

    FUN = _cookies.cookie_string
    EXC = ValueError

    def _check_result(self, output, *args, **kwargs):
        args = list(args)
        args.insert(1, u'cookies')
        super(CookieStringTest, self)._check_result(output, *args, **kwargs)

    def _check_exception(self, err_msg, *args, **kwargs):
        args = list(args)
        args.insert(1, u'cookies')
        super(CookieStringTest, self)._check_exception(err_msg, *args,
                                                       **kwargs)

    def test_empty(self):
        self._check_result(b'', None)
        self._check_result(b'', b'')
        self._check_result(b'', u'')
        self._check_result(b'', {})

    def test_non_empty(self):
        self._check_result(b'key=val', b'key=val')
        self._check_result(b'key=val', u'key=val')
        self._check_result(b'key=val', {u'key': u'val'})
        self._check_result(b'key=val', {u'key': b'val'})
        self._check_result(b'key=val', {b'key': b'val'})
        self._check_result(b'key=val', {b'key': u'val'})

    def test_two_keys(self):
        def comparator(cookie_string):
            return sorted(cookie_string.split(b';'))

        self._check_result(b'key1=val1;key2=val2', b'key1=val1;key2=val2',
                           comparator=comparator)
        self._check_result(b'key1=val1;key2=val2', u'key1=val1;key2=val2',
                           comparator=comparator)
        self._check_result(b'key1=val1;key2=val2', {b'key1': b'val1',
                                                    b'key2': b'val2'},
                           comparator=comparator)
        self._check_result(b'key1=val1;key2=val2', {u'key1': u'val1',
                                                    u'key2': u'val2'},
                           comparator=comparator)

    def test_wrong_type(self):
        err_msg = u'cookies must be %s, %s, %s or %s, not 7'
        err_msg = err_msg % (_compat.text.__name__, bytes.__name__,
                             type(None).__name__, dict.__name__)
        self._check_exception(err_msg, 7, exc=TypeError)

    def test_non_ascii_unicode(self):
        self._check_exception(u'unicode cookies must be ascii-only', u'föö')

    def test_key_values_non_ascii_unicode(self):
        self._check_exception(u'cookies keys/values must be ascii-only',
                              {u'föö': u'bär'.encode('utf-8')})

    def test_key_values_wrong_type(self):
        self._check_exception(u'cookies key/values must be strings',
                              {u'foo': []}, exc=TypeError)
        self._check_exception(u'cookies key/values must be strings',
                              {3: b'bar'}, exc=TypeError)

    def test_key_with_equals_char(self):
        self._check_exception(u"cookies keys cannot use '=' character",
                              {u'f=o': b'bar'})

    def test_key_values_with_semicolon(self):
        self._check_exception(u"cookies keys/values cannot use ';' character",
                              {u'f;o': b'bar'})
        self._check_exception(u"cookies keys/values cannot use ';' character",
                              {u'foo': b'b;r'})
