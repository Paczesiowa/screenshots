'''
Utility functions for working with URLs.
'''
from dom2img import _compat


def is_absolute_url(url):
    '''
    Test if byte string can be parsed as an absolute URL

    >>> is_absolute_url(b'http://example.com/')
    True
    >>> is_absolute_url(b'dir/something')
    False
    '''
    return bool(_compat.urlparse(url).scheme)


def absolutize_urls(doc, tag_name, attr, prefix):
    '''
    Looks for specific tags in a document and tries to fix their attributes,
    if they contain relative URLs.
    doc is a BeautifulSoup document
    tag_name is a byte string of html tag to look for
    attr is a ascii-only unicode text of tag's attribute
      which value will be fixed
    prefix is an ascii-only unicode URL that will be used to make absolute URL
    doc is modified and also returned.

    >>> import bs4
    >>> absolutize_urls(bs4.BeautifulSoup('<a href="something"></a>'),\
                        b'a', u'href', u'http://127.0.0.1:8000/something')
    <a href="http://127.0.0.1:8000/something"></a>
    '''
    for tag in doc.findAll(tag_name):
        if tag.has_attr(attr) and not is_absolute_url(tag[attr]):
            tag[attr] = _compat.urljoin(prefix, tag[attr])
    return doc
