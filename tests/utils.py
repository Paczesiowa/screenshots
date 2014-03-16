import unittest2


class TestCase(unittest2.TestCase):

    def _check_result(self, output, *args, **kwargs):
        try:
            comparator = kwargs.pop('comparator')
        except KeyError:
            comparator = lambda x: x
        fun = self.FUN.__func__
        self.assertEqual(comparator(output), comparator(fun(*args, **kwargs)))

    def _check_result_true(self, *args, **kwargs):
        self._check_result(True, *args, **kwargs)

    def _check_result_false(self, *args, **kwargs):
        self._check_result(False, *args, **kwargs)

    def _check_exception(self, err_msg, *args, **kwargs):
        err_msg = err_msg.replace(u'(', u'\\(').replace(u')', u'\\)')
        try:
            exc = kwargs.pop('exc')
        except KeyError:
            exc = self.EXC
        fun = self.FUN.__func__
        self.assertRaisesRegexp(exc, err_msg, fun, *args, **kwargs)
