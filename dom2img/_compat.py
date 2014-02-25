try:
    import urlparse as urllib
except ImportError:
    import urllib.parse as urllib


urlparse = urllib.urlparse
urljoin = urllib.urljoin
text = unicode
byte_string = str
