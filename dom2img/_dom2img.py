import argparse
import sys
from subprocess import Popen, PIPE
from dom2img import _cookies, _url_utils, _arg_utils, _compat
from PIL import Image
import pkg_resources
from bs4 import BeautifulSoup


def _clean_up_html(content, prefix):
    '''
    Clean up html by removing all script tags
    and making relative urls absolute.
    content is an utf-8 encoded byte string with html
    prefix is an ascii-only unicode url that will be used to make absolute url
    Returns cleaned up, utf-8 encoded html byte string
    '''
    doc = BeautifulSoup(content)

    for tag in doc.findAll('script'):
        tag.decompose()

    _url_utils.absolutize_urls(doc, 'link', u'href', prefix)
    _url_utils.absolutize_urls(doc, 'a', u'href', prefix)
    _url_utils.absolutize_urls(doc, 'img', u'src', prefix)

    return doc.prettify().encode('utf-8')


def _render(content, width, height, top, left, cookie_domain, cookie_string):
    '''
    Renders html content using PhantomJS
    content is an utf-8 encoded byte string with html.
    width is an int with the width size of phantomjs viewport,
      and width of the resulting image
    height is an int with the height size of phantomjs viewport,
      and height of the resulting image
    top is an int with the pixel offset from the top/vertical scroll position
    left is an int with the pixel offset from the left/
      horizontal scroll position
    cookie_domain is a byte string containing url (just the host part)
    cookie_string is a byte string containing cookies keys and values
    using format key1=val1;key2=val2
    '''
    render_file_phantom_js_location = \
        pkg_resources.resource_filename(__name__, 'render_file.phantom.js')
    phantomjs_args = ['phantomjs', render_file_phantom_js_location,
                      str(width), str(height), str(top),
                      str(left), cookie_domain, cookie_string]
    proc = Popen(phantomjs_args, stdin=PIPE, stdout=PIPE)
    return proc.communicate(content)[0]


def _resize(img_string, scale, resize_filter=Image.ANTIALIAS):
    '''
    Resizes to <scale>% of original size the img_string
    img_string is a bytestring containing png image data
    scale is an integer percentage number (50 means 2 times smaller image)
    resize_filter is a PIL filter used for resizing
    '''
    if scale != 100:  # no point in resizing to 100%
        img = Image.open(_compat.BytesIO(img_string))
        width, height = img.size
        new_width = int(round(width * (scale / 100.)))
        new_height = int(round(height * (scale / 100.)))
        result = img.resize((new_width, new_height), resize_filter)
        buff = _compat.BytesIO()
        result.save(buff, format='PNG')
        return buff.getvalue()
    else:
        return img_string


def _dom2img(content, width, height, top, left, scale, prefix, cookie_string):
    '''
    Renders html using PhantomJS.

    Parameters:
    * content - utf-8 encoded byte string containing html input
    * width - non-negative int with the width of virtual render viewport
              (using pixels unit)
    * height - non-negative int with the height of virtual render viewport
               (using pixels unit)
    * top - non-negative int with offset from the top of the page,
            that should be rendered (using pixels unit)
    * left - non-negative int with offset from the left border of the page,
             that should be rendered (using pixels unit)
    * scale - non-negative int with percentage number,
              that the screenshot will be scaled to (50 means half the
              original size)
    * prefix - ascii-only unicode containing absolute url that will be used
               to handle relative urls in html (for images, css scripts)
               and optionally for cookies
    * cookie_string - byte string containing cookies keys and values
                      using format key1=val1;key2=val2

    Returns string containing png image with the screenshot.
    '''
    cookie_domain = _cookies.get_cookie_domain(prefix)
    cleaned_up_content = _clean_up_html(content, prefix)
    img_string = _render(cleaned_up_content, width, height, top,
                         left, cookie_domain, cookie_string)

    return _resize(img_string, scale)


def dom2img(content, width, height, prefix,
            top=0, left=0, scale=100, cookies=None):
    '''
    Renders html using PhantomJS.

    Parameters:
    * content - html input (utf-8 encoded byte string or unicode text)
    * width - non-negative int with the width of virtual
              render viewport (using pixels unit)
    * height - non-negative int with the height of virtual
               render viewport (using pixels unit).
    * top - non-negative int with offset from the top of the page
            where rendering should start (using pixels unit)
    * left - non-negative int with offset from the left border of the page
             where rendering should start (using pixels unit)
    * scale - non-negative int with percentage number
              that the screenshot will be scaled to (50 means half the
              original size)

     height, width, top, left: int or byte string/unicode text containing
                               decimal representation of the integer number
    * prefix - absolute url that will be used
               to resolve relative urls in html (for images, css scripts)
               and to derive cookie domain for cookies
               can be byte string or ascii-only unicode text.
    * cookies - cookies key and values that will be sent with all
                resource requests (images, css scripts)
      * None
      * byte string (or ascii-only unicode text) using
        key1=val1;key2=val2 format
      * string dictionary with cookie keys and values.
        Neither keys nor values should contain semicolons.
        Keys cannot contain '=' character.
        Keys and values can be byte strings or ascii-only unicode texts.

    Returns byte string containing png image with the screenshot.

    Raises:
    * Dom2ImgArgumentException (subclass of ValueError) if arguments are
      in improper format
    '''
    if isinstance(content, _compat.text):
        content = content.encode('utf-8')
    if not isinstance(content, _compat.byte_string):
        raise argparse.ArgumentTypeError(
            'content must be utf-8 encoded byte string or unicode')
    height = _arg_utils.non_negative_int(height, u'height')
    width = _arg_utils.non_negative_int(width, u'width')
    top = _arg_utils.non_negative_int(top, u'top')
    left = _arg_utils.non_negative_int(left, u'left')
    scale = _arg_utils.non_negative_int(scale, u'scale')
    prefix = _arg_utils.absolute_url(prefix, u'prefix')
    if cookies is None:
        cookies = {}
    if isinstance(cookies, dict):
        cookies = _cookies.validate_cookies(cookies)
        cookie_string = _cookies.serialize_cookies(cookies)
    elif isinstance(cookies, _compat.text):
        try:
            cookie_string = cookies.encode('ascii')
        except UnicodeEncodeError:
            raise argparse.ArgumentTypeError(
                'unicode cookies must be ascii-only')
    elif isinstance(cookies, _compat.byte_string):
        cookie_string = cookies
    else:
        raise argparse.ArgumentTypeError(
            'cookies must be None/string/dict')

    return _dom2img(content=content, width=width, height=height,
                    prefix=prefix, top=top, left=left, scale=scale,
                    cookie_string=cookie_string)
