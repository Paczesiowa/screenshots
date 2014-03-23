import sys

try:
    import urlparse as urllib
except ImportError:
    import urllib.parse as urllib


urlparse = urllib.urlparse
urljoin = urllib.urljoin

if sys.version_info < (3,):
    text = unicode
    byte_string = str
else:
    text = str
    byte_string = bytes
