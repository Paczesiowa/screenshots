# coding=utf-8
import unittest2

from dom2img import _arg_utils


class ArgUtilsTest(unittest2.TestCase):

    def test_non_negative_int(self):
        fun = _arg_utils.non_negative_int
        exc = _arg_utils.Dom2ImgArgumentException

        self.assertEqual(0, fun(u'0', u'x'))
        self.assertEqual(1, fun(u'1', u'x'))
        self.assertEqual(2, fun(b'2', u'x'))
        self.assertEqual(3, fun(b'3', u'x'))
        self.assertEqual(4, fun(4, u'x'))
        self.assertEqual(5, fun(5, u'x'))

        self.assertRaisesRegexp(exc,
                                u'x must be int or byte string or unicode',
                                fun, [], u'x')

        self.assertRaisesRegexp(exc,
                                u'x must be int or byte string or unicode',
                                fun, {}, u'x')

        self.assertRaisesRegexp(exc, u'y must be ascii-only unicode',
                                fun, u'ä', u'y')

        self.assertRaisesRegexp(exc, u'val cannot be parsed as an int',
                                fun, u'something', u'val')

        self.assertRaisesRegexp(exc, u'val cannot be parsed as an int',
                                fun, b'3.2', u'val')

        self.assertRaisesRegexp(exc, u'Unexpected negative integer for x',
                                fun, u'-2', u'x')
