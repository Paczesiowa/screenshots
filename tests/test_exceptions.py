import tests.utils as utils
from dom2img import _exceptions


class PhantomJSFailureTest(utils.TestCase):

    def test_string_empty(self):
        exc_inst = _exceptions.PhantomJSFailure(return_code=1)
        self.assertEqual(str(exc_inst),
                         u'PhantomJS failed with status 1')

    def test_string(self):
        exc_inst = _exceptions.PhantomJSFailure(return_code=1,
                                                stderr='some output')
        err_msg = u'PhantomJS failed with status 1, and stderr output:\n'
        err_msg += u'some output'
        self.assertEqual(str(exc_inst), err_msg)


class PhantomJSTimeoutTest(utils.TestCase):

    def test_string(self):
        exc_inst = _exceptions.PhantomJSTimeout(30)
        err_msg = u'PhantomJS process has been killed, ' + \
            u'because it took longer than 30 seconds to finish'
        self.assertEqual(str(exc_inst), err_msg)
