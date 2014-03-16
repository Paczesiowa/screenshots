import unittest2

import bs4

from dom2img import _url_utils


class IsAbsoluteURLTest(unittest2.TestCase):

    def is_abs(self, url):
        self.assertTrue(_url_utils.is_absolute_url(url))

    def is_not_abs(self, url):
        self.assertFalse(_url_utils.is_absolute_url(url))

    def test_simple(self):
        self.is_abs(b'http://example.com/')

    def test_url_with_path(self):
        self.is_abs(b'https://example.com/something/something_else.txt')

    def test_url_with_path_using_parent_references(self):
        self.is_abs(b'http://example.com/something/../something.txt')

    def test_url_without_scheme(self):
        self.is_not_abs(b'/something.txt')

    def test_url_without_scheme_using_parent_references(self):
        self.is_not_abs(b'/../something.txt')

    def test_url_with_protocol_relative_scheme(self):
        self.is_not_abs(b'//something/something.txt')


class AbsolutizeURLsTest(unittest2.TestCase):

    def check(self, html_in, html_out, tag, attribute):
        bs = bs4.BeautifulSoup
        prefix = 'http://example.com/something'
        doc_in = bs(html_in)
        doc_out = bs(html_out)
        result = _url_utils.absolutize_urls(doc_in, tag, attribute, prefix)
        self.assertEqual(str(doc_out), str(result))
        self.assertEqual(str(doc_in), str(doc_out))

    def test_simple(self):
        self.check(b'<a href="something"></a>',
                   b'<a href="http://example.com/something"></a>',
                   b'a', b'href')

    def test_other_tags_are_not_changed(self):
        self.check(b'<a href="something"></a>',
                   b'<a href="something"></a>',
                   b'b', b'href')

    def test_other_attributes_are_not_changed(self):
        self.check(b'<a href="something"></a>',
                   b'<a href="something"></a>',
                   b'a', b'src')

    def test_absolute_urls_are_not_changed(self):
        self.check(b'<a href="http://example.com/"></a>',
                   b'<a href="http://example.com/"></a>',
                   b'a', b'href')
