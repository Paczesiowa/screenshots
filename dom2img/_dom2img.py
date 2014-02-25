import sys
from subprocess import Popen, PIPE

from dom2img import _cookies, _url_utils
import pkg_resources
from bs4 import BeautifulSoup


def _clean_up_html(content, prefix):
    '''
    Clean up html by removing all script tags
    and making relative urls absolute.
    content is a utf-8 encoded byte string with html
    prefix is a url byte string that will be user to make absolute url.
    Returns cleaned up html string
    '''
    doc = BeautifulSoup(content)

    for tag in doc.findAll('script'):
        tag.decompose()

    _url_utils.absolutize_urls(doc, 'link', 'href', prefix)
    _url_utils.absolutize_urls(doc, 'a', 'href', prefix)
    _url_utils.absolutize_urls(doc, 'img', 'src', prefix)

    return doc.prettify()


def _render(content, width, height, top, left, cookie_domain, cookie_string):
    '''
    Renders html content using PhantomJS
    '''
    render_file_phantom_js_location = \
        pkg_resources.resource_filename(__name__, 'render_file.phantom.js')
    phantomjs_args = ['phantomjs', render_file_phantom_js_location,
                      str(width), str(height), str(top),
                      str(left), cookie_domain, cookie_string]
    proc = Popen(phantomjs_args, stdin=PIPE, stdout=PIPE)
    if sys.version > '3':
        if type(content) == str:
            content = content.encode('utf-8')
    else:
        if type(content) == unicode:
            content = content.encode('utf-8')
    return proc.communicate(content)[0]


def _resize(img_string, scale):
    '''
    Resizes to <scale>% of original size the img_string
    using convert tool from imagemagick
    '''
    if scale != 100:  # no point in resizing to 100%
        convert_args = ['convert', '-', '-resize', str(scale) + '%', '-']
        proc = Popen(convert_args, stdin=PIPE, stdout=PIPE)
        return proc.communicate(img_string)[0]
    else:
        return img_string


def dom2img(content, height, width, top, left, scale, prefix, cookies=None):
    '''
    Renders html using PhantomJS.

    Parameters:
    * content - string containing html input
    * height - string containing non-negative int with
               the height of virtual render viewport (using pixels unit)
    * width - string containing non-negative int with
              the width of virtual render viewport (using pixels unit)
    * top - string containing non-negative int with
            offset from the top of the page that should be rendered
            (using pixels unit)
    * left - string containing non-negative int with
             offset from the left border of the page that should be rendered
             (using pixels unit)
    * scale - string containing non-negative int with percentage number
              that the screenshot will be scaled to (50 means half the
              original size)
    * prefix - string containing absolute urls that will be used
               to handle relative urls in html (for images, css scripts)
               and optionally for cookies
    * cookies - string-to-string dictionary (or None) containing
                cookie keys and values. ";=" are invalid characters

    Returns string containing png image with the screenshot.

    Raises:
    * Dom2ImgArgumentException (subclass of ValueError) if arguments are
      in improper format
    '''
    if type(content) != str and type(content) != unicode:
        raise _utils.Dom2ImgArgumentException('content is not a string')
    height = _utils.non_negative_int(height, 'height')
    width = _utils.non_negative_int(width, 'width')
    top = _utils.non_negative_int(top, 'top')
    left = _utils.non_negative_int(left, 'left')
    scale = _utils.non_negative_int(scale, 'scale')
    if not _utils.is_absolute_url(prefix):
        raise _utils.Dom2ImgArgumentException('prefix must be an absolute URL')
    _cookies.validate_cookies(cookies)

    cookie_string = _utils.serialize_cookies(cookies)
    cookie_domain = _utils.get_cookie_domain(prefix)
    cleaned_up_content = _clean_up_html(content, prefix)
    img_string = _render(cleaned_up_content, width, height, top,
                         left, cookie_domain, cookie_string)

    return _resize(img_string, scale)
