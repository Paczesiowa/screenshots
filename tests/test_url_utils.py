import bs4

from dom2img import _url_utils

import tests.utils as utils


class NonNegativeIntTest(utils.TestCase):

    FUN = _url_utils.is_absolute_url

    def test_simple(self):
        self._check_result_true(b'http://example.com/')

    def test_url_with_path(self):
        self._check_result_true(
            b'https://example.com/something/something_else.txt')

    def test_url_with_path_using_parent_references(self):
        self._check_result_true(
            b'http://example.com/something/../something.txt')

    def test_url_without_scheme(self):
        self._check_result_false(b'/something.txt')

    def test_url_without_scheme_using_parent_references(self):
        self._check_result_false(b'/../something.txt')

    def test_url_with_protocol_relative_scheme(self):
        self._check_result_false(b'//something/something.txt')


class AbsolutizeURLsTest(utils.TestCase):

    def _check(self, html_in, html_out, tag, attribute):
        bs = bs4.BeautifulSoup
        prefix = 'http://example.com/something'
        doc_in = bs(html_in)
        doc_out = bs(html_out)
        result = _url_utils.absolutize_urls(doc_in, tag, attribute, prefix)
        self.assertEqual(str(doc_out), str(result))
        self.assertEqual(str(doc_in), str(doc_out))

    def test_simple(self):
        self._check(b'<a href="something"></a>',
                    b'<a href="http://example.com/something"></a>',
                    b'a', u'href')

    def test_other_tags_are_not_changed(self):
        self._check(b'<a href="something"></a>',
                    b'<a href="something"></a>',
                    b'b', u'href')

    def test_other_attributes_are_not_changed(self):
        self._check(b'<a href="something"></a>',
                    b'<a href="something"></a>',
                    b'a', u'src')

    def test_absolute_urls_are_not_changed(self):
        self._check(b'<a href="http://example.com/"></a>',
                    b'<a href="http://example.com/"></a>',
                    b'a', u'href')
