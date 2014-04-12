import sys


try:
    import urlparse as urllib
except ImportError:
    import urllib.parse as urllib

try:
    import StringIO
    BytesIO = StringIO.StringIO
except ImportError:
    import io
    BytesIO = io.BytesIO


urlparse = urllib.urlparse
urljoin = urllib.urljoin

if sys.version_info < (3,):
    text = unicode
    byte_string = str
else:
    text = str
    byte_string = bytes

if sys.version_info < (3,):
    # exceptions in python2, cannot contain unicode chars
    # or they will error when being printed
    # replace all characters with ascii-safe equivalents
    def clean_exc_message(msg):
        return msg.encode('ascii', 'replace').decode('ascii')
else:
    def clean_exc_message(msg):
        return msg

if sys.version_info < (3,):
    def make_text(val):
        if isinstance(val, str):
            return u"b'" + unicode(val) + u"'"
        else:
            return unicode(val)
else:
    make_text = str
