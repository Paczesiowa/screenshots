# coding=utf-8
import unittest2

from dom2img import _cookies, _arg_utils


class CookiesTest(unittest2.TestCase):

    def test_serialize_cookies(self):
        fun = _cookies.serialize_cookies
        self.assertEqual(fun({}), b'')
        self.assertEqual(fun(None), b'')

        self.assertEqual(fun({b'foo': b'bar'}), b'foo=bar')

        self.assertEqual(fun({b'foo': b'bar', b'baz': b'quux'}),
                         b'foo=bar;baz=quux')

    def test_parse_cookie_string(self):
        fun = _cookies.parse_cookie_string
        exc = _arg_utils.Dom2ImgArgumentException

        self.assertEqual(fun(u''), {})
        self.assertEqual(fun(u'test'), {})
        self.assertEqual(fun(u'='), {b'': b''})
        self.assertEqual(fun(u'foo=bar'), {b'foo': b'bar'})
        self.assertEqual(fun(u'foo=bar=baz'), {b'foo': b'bar=baz'})
        self.assertEqual(fun(u'foo=bar=baz===;quux=plonk'),
                         {b'foo': b'bar=baz===', b'quux': b'plonk'})

        self.assertRaisesRegexp(exc, 'cookie_string must be an ascii-only ' +
                                'unicode text string', fun, 'foo')

        self.assertRaisesRegexp(exc, 'cookie_string must be an ascii-only ' +
                                'unicode text string', fun, u'föö=bär')

    def test_parse_serialize_cookies(self):
        fun1 = _cookies.serialize_cookies
        fun2 = _cookies.parse_cookie_string

        self.assertEqual(b'foo=bar',
                         fun1(fun2(u'foo=bar')))

        self.assertEqual(b'foo=bar&baz=quux',
                         fun1(fun2(u'foo=bar&baz=quux')))

        self.assertEqual(b'foo=bar=quux==',
                         fun1(fun2(u'foo=bar=quux==')))

    def test_validate_cookies(self):
        fun = _cookies.validate_cookies
        exc = _arg_utils.Dom2ImgArgumentException

        self.assertEqual(fun({}), {})
        self.assertEqual(fun(None), {})
        self.assertEqual(fun({b'foo': b'bar'}), {b'foo': b'bar'})
        self.assertEqual(fun({u'foo': u'bar'}), {b'foo': b'bar'})
        self.assertEqual(fun({b'foo': b'bar', u'baz': u'quux'}),
                         {b'foo': b'bar', b'baz': b'quux'})

        self.assertRaisesRegexp(exc, 'cookies must be a dict or None',
                                fun, [])
        self.assertRaisesRegexp(exc, 'cookies key/values must be strings',
                                fun, {u'foo': []})
        self.assertRaisesRegexp(exc, 'cookies key/values must be strings',
                                fun, {3: b'bar'})
        self.assertRaisesRegexp(exc, 'cookies keys/values must be ascii-only',
                                fun, {u'föö': u'bar'})
        self.assertRaisesRegexp(exc, 'cookies keys/values must be ascii-only',
                                fun, {u'foo': u'bär'})
        self.assertRaisesRegexp(exc, "cookies keys cannot use '=' character",
                                fun, {u'f=o': b'bar'})
        self.assertRaisesRegexp(exc,
                                "cookies keys/values cannot use ';' character",
                                fun, {u'f;o': b'bar'})
        self.assertRaisesRegexp(exc,
                                "cookies keys/values cannot use ';' character",
                                fun, {u'foo': b'b;r'})

    def test_get_cookie_domain(self):
        fun = _cookies.get_cookie_domain
        self.assertEqual(b'google.com', fun(b'http://google.com'))
        self.assertEqual(b'google.com', fun(b'http://google.com/'))
        self.assertEqual(b'google.com', fun(b'http://google.com/something'))
        self.assertEqual(b'google.com', fun(b'http://google.com/?key=val'))
        self.assertEqual(b'google.com', fun(b'http://google.com:8000'))
        result = fun(
            b'http://google.com:7000/path/something?key=val&key2=val2')
        self.assertEqual(result, b'google.com')
