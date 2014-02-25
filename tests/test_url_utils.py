import unittest

import bs4

from dom2img import _url_utils


class UrlUtilsTest(unittest.TestCase):

    def assertEqualStr(self, a, b):
        return self.assertEqual(str(a), str(b))

    def test_is_absolute_url(self):
        self.assertTrue(_url_utils.is_absolute_url(
            b'http://example.com/something'))
        self.assertTrue(_url_utils.is_absolute_url(
            b'https://example.com/something/something_else.txt'))
        self.assertTrue(_url_utils.is_absolute_url(
            b'http://example.com/something/../something.txt'))

        self.assertFalse(_url_utils.is_absolute_url(
            b'/something.txt'))
        self.assertFalse(_url_utils.is_absolute_url(
            b'/../something.txt'))
        self.assertFalse(_url_utils.is_absolute_url(
            b'//something/../something.txt'))

    def test_absolutize_urls(self):
        bs = bs4.BeautifulSoup
        prefix = 'http://127.0.0.1:8000/something'

        # make sure we return and modify in place
        doc = bs('<a href="something"></a>')
        self.assertEqualStr(
            doc, _url_utils.absolutize_urls(doc, b'a', b'href', prefix))

        # make sure we don't touch other tags
        doc = bs('<a href="something"></a>')
        self.assertEqualStr(bs('<a href="something"></a>'),
                            _url_utils.absolutize_urls(doc, b'b',
                                                       b'href', prefix))

        # make sure we don't touch other attributes
        doc = bs('<a href="something"></a>')
        self.assertEqualStr(bs('<a href="something"></a>'),
                            _url_utils.absolutize_urls(doc, b'a',
                                                       b'src', prefix))

        # make sure we don't touch absolute urls
        doc = bs('<a href="http://example.com/"></a>')
        self.assertEqualStr(bs('<a href="http://example.com/"></a>'),
                            _url_utils.absolutize_urls(doc, b'a',
                                                       b'href', prefix))

        # make sure it works
        doc = bs('<a href="test"></a>')
        self.assertEqualStr(bs('<a href="http://127.0.0.1:8000/test"></a>'),
                            _url_utils.absolutize_urls(doc, b'a',
                                                       b'href', prefix))
