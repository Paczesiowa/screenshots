import unittest

from dom2img import _arg_utils


class ArgUtilsTest(unittest.TestCase):

    def test_non_negative_int(self):
        fun = _arg_utils.non_negative_int
        exc = _arg_utils.Dom2ImgArgumentException

        self.assertEqual(3, fun(u'3', 'x'))

        self.assertEqual(0, fun(u'0', 'x'))

        self.assertRaisesRegexp(exc, 'x is not a unicode string',
                                fun, '3', 'x')

        self.assertRaisesRegexp(exc, 'x cannot be parsed as an int',
                                fun, u'3.2', 'x')

        self.assertRaisesRegexp(exc, 'x cannot be parsed as an int',
                                fun, u'something', 'x')

        self.assertRaisesRegexp(exc, 'Unexpected negative integer for x',
                                fun, u'-2', 'x')
