# coding=utf-8
import argparse
import unittest2

from dom2img import _arg_utils


class ArgUtilsTest(unittest2.TestCase):

    def test_non_negative_int(self):
        fun = _arg_utils.non_negative_int
        exc = argparse.ArgumentTypeError

        self.assertEqual(0, fun(u'0', u'x'))
        self.assertEqual(1, fun(u'1', u'x'))
        self.assertEqual(2, fun(b'2', u'x'))
        self.assertEqual(3, fun(b'3', u'x'))
        self.assertEqual(4, fun(4, u'x'))
        self.assertEqual(5, fun(5, u'x'))

        self.assertEqual(0, fun(u'0'))
        self.assertEqual(1, fun(b'1'))

        self.assertRaisesRegexp(exc,
                                u'x must be int/byte string/unicode',
                                fun, [], u'x')

        self.assertRaisesRegexp(exc, u'non_negative_int arg must be ' +
                                'int/byte string/unicode',
                                fun, {})

        self.assertRaisesRegexp(exc, u'y must be ascii-only unicode',
                                fun, u'ä', u'y')

        self.assertRaisesRegexp(exc,
                                u'non_negative_int arg must be ascii-only',
                                fun, u'ä')

        self.assertRaisesRegexp(exc, u'val cannot be parsed as an int',
                                fun, u'something', u'val')

        self.assertRaisesRegexp(exc, u'val cannot be parsed as an int',
                                fun, b'3.2', u'val')

        self.assertRaisesRegexp(exc, u'cannot parse as an int',
                                fun, b'3.2')

        self.assertRaisesRegexp(exc, u'Unexpected negative integer for x',
                                fun, u'-2', u'x')

        self.assertRaisesRegexp(exc, u'Unexpected negative integer',
                                fun, u'-2')

    def test_absolute_url(self):
        fun = _arg_utils.absolute_url

        self.assertEqual(b'http://example.com/',
                         fun(b'http://example.com/'))

        self.assertEqual(u'http://example.com/',
                         fun(b'http://example.com/'))

        self.assertEqual(b'http://example.com/foo/bar',
                         fun(b'http://example.com/foo/bar'))

        self.assertEqual(u'http://example.com/foo/bar/',
                         fun(b'http://example.com/foo/bar/'))

        self.assertRaisesRegexp(TypeError,
                                u'absolute_url\\(\\) argument must be ' +
                                u'a byte string or unicode text',
                                fun, None)

        self.assertRaisesRegexp(ValueError,
                                u'absolute_url\\(\\) unicode text argument ' +
                                u'must be ascii-only',
                                fun, u'http://exämple.com/')

        self.assertRaisesRegexp(ValueError,
                                u'absolute_url\\(\\) argument must be ' +
                                u'an absolute url',
                                fun, b'example.com/')

        self.assertRaisesRegexp(ValueError,
                                u'absolute_url\\(\\) argument must be ' +
                                u'an absolute url',
                                fun, u'//example.com/')
