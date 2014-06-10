'''
Utility functions for working with URLs.
'''
from dom2img import _compat


def is_absolute_url(url):
    '''
    Test if bytes object can be parsed as an absolute URL.

    Args:
        url: bytes object that will be checked if it could be parsed as an
            absolute URL.

    Returns:
        A bool value indicating if the url argument could be parsed as an
        absolute URL.

    >>> is_absolute_url(b'http://example.com/')
    True
    >>> is_absolute_url(b'dir/something')
    False
    '''
    return bool(_compat.urlparse(url).scheme)


def absolutize_urls(doc, tag_name, attr, prefix):
    '''
    Turns relative URLs in a HTML document into absolute URLs.

    Looks for specific tags in a document and if they contain relative URLs
    tries to fix their attributes, by making them absolute URLs.

    Input document is modified and also returned.

    Args:
        doc: BeautifulSoup document.
        tag_name: bytes object with HTML tag to look for.
        attr: Ascii-only unicode text of tag's attribute
            which value will be fixed.
        prefix: Ascii-only unicode URL that will be used to make absolute URLs.
    Returns:
        BeautifulSoup document that was passed as doc argument, but all
        URLs are absolute (for specified tag and attribute).

    >>> import bs4
    >>> absolutize_urls(bs4.BeautifulSoup('<a href="something"></a>'),\
                        b'a', u'href', u'http://127.0.0.1:8000/something')
    <a href="http://127.0.0.1:8000/something"></a>
    '''
    for tag in doc.findAll(tag_name):
        if tag.has_attr(attr) and not is_absolute_url(tag[attr]):
            tag[attr] = _compat.urljoin(prefix, tag[attr])
    return doc
