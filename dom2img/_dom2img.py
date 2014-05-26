import os
import pipes
import subprocess
import sys
import tempfile
from distutils import spawn

import pkg_resources
from PIL import Image
from bs4 import BeautifulSoup

from dom2img import _cookies, _url_utils, _arg_utils, \
    _compat, _subprocess, _exceptions


def _clean_up_html(content, prefix):
    '''
    Clean up html by removing all script tags
    and making relative URLs absolute.
    content is an utf-8 encoded byte-string with html
    prefix is an ascii-only unicode URL that will be used to make absolute URL
    Returns cleaned up, utf-8 encoded html byte-string
    '''
    doc = BeautifulSoup(content)

    for tag in doc.findAll('script'):
        tag.decompose()

    _url_utils.absolutize_urls(doc, 'link', u'href', prefix)
    _url_utils.absolutize_urls(doc, 'a', u'href', prefix)
    _url_utils.absolutize_urls(doc, 'img', u'src', prefix)

    return doc.prettify().encode('utf-8')


def _phantomjs_invocation(width, height, top, left,
                          prefix, cookie_string):
    '''
    Returns command line arguments for running PhantomJS.

    width is an int with the width size of phantomjs viewport,
      and width of the resulting image
    height is an int with the height size of phantomjs viewport,
      and height of the resulting image
    top is an int with the pixel offset from the top/vertical scroll position
    left is an int with the pixel offset from the left/
      horizontal scroll position
    prefix is an ascii-only unicode containing absolute URL
    cookie_string is a byte-string containing cookies keys and values
      using format key1=val1;key2=val2

    Result is a list of text objects.

    Raises PhantomJSNotInPath if there's no phantomjs in $PATH
    '''
    cookie_domain = _cookies.get_cookie_domain(prefix)

    render_file_phantom_js_location = \
        os.path.realpath(pkg_resources.resource_filename(
            __name__, 'render_file.phantom.js'))
    phantomjs_binary = spawn.find_executable('phantomjs')
    if phantomjs_binary is None:
        raise _exceptions.PhantomJSNotInPath()

    if isinstance(render_file_phantom_js_location, bytes):
        render_file_phantom_js_location = \
            render_file_phantom_js_location.decode(sys.getfilesystemencoding())
        phantomjs_binary = phantomjs_binary.decode(sys.getfilesystemencoding())

    return [phantomjs_binary, render_file_phantom_js_location,
            _compat.text(width), _compat.text(height),
            _compat.text(top), _compat.text(left),
            cookie_domain.decode('ascii'),
            cookie_string.decode('ascii')]


def _render(content, width, height, top, left, prefix,
            cookie_string, timeout):
    '''
    Renders html content using PhantomJS
    content is an utf-8 encoded byte-string with html.
    width is an int with the width size of phantomjs viewport,
      and width of the resulting image
    height is an int with the height size of phantomjs viewport,
      and height of the resulting image
    top is an int with the pixel offset from the top/vertical scroll position
    left is an int with the pixel offset from the left/
      horizontal scroll position
    prefix is an ascii-only unicode containing absolute URL
    cookie_string is a byte-string containing cookies keys and values
      using format key1=val1;key2=val2
    timeout is an int with number of seconds after which PhantomJS
      will be killed and PhantomJSTimeout will be raised

    Raises:
    * PhantomJSFailure if PhantomJS process fails/crashes.
    * PhantomJSTimeout if PhantomJS takes more than timeout seconds to finish
    * PhantomJSNotInPath if there's no phantomjs in $PATH
    '''
    phantomjs_args = _phantomjs_invocation(width=width, height=height,
                                           top=top, left=left, prefix=prefix,
                                           cookie_string=cookie_string)
    proc = subprocess.Popen(phantomjs_args,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    result = _subprocess.communicate_with_timeout(proc, timeout, content)
    if result is None:
        raise _exceptions.PhantomJSTimeout(timeout)
    else:
        stdout, stderr = result
        if proc.returncode:
            stderr = stderr.decode('ascii', 'ignore') or None
            raise _exceptions.PhantomJSFailure(return_code=proc.returncode,
                                               stderr=stderr)
        else:
            return stdout


def _resize(img_string, scale, resize_filter=Image.ANTIALIAS):
    '''
    Resizes to <scale>% of original size the img_string
    img_string is a byte-string containing png image data
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


_dom2img_args_validator = \
    _arg_utils.validate_and_unify(content=_arg_utils.utf8_byte_string,
                                  height=_arg_utils.non_negative_int,
                                  width=_arg_utils.non_negative_int,
                                  top=_arg_utils.non_negative_int,
                                  left=_arg_utils.non_negative_int,
                                  scale=_arg_utils.non_negative_int,
                                  timeout=_arg_utils.non_negative_int,
                                  prefix=_arg_utils.absolute_url)


@_dom2img_args_validator
def dom2img(content, width, height, prefix, top=0,
            left=0, scale=100, cookies=None, timeout=30):
    '''
    Renders html using PhantomJS.

    Parameters:
    * content - html input (utf-8 encoded byte-string or unicode text)
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
    * timeout - non-negative int with number of seconds after which PhantomJS
                will be killed and PhantomJSTimeout will be raised

     height, width, top, left, timeout:
       int or byte-string/unicode text containing
       decimal representation of the integer number
    * prefix - absolute URL that will be used
               to resolve relative URLs in html (for images, css scripts)
               and to derive cookie domain for cookies
               can be byte-string or ascii-only unicode text.
    * cookies - cookies key and values that will be sent with all
                resource requests (images, css scripts)
      * None
      * byte-string (or ascii-only unicode text) using
        key1=val1;key2=val2 format
      * string dictionary with cookie keys and values.
        Neither keys nor values should contain semicolons.
        Keys cannot contain '=' character.
        Keys and values can be byte-strings or ascii-only unicode texts.

    Returns byte-string containing png image with the screenshot.

    Raises:
    * TypeError if arguments are not the right type
    * ValueError if arguments have invalid values
    * PhantomJSFailure if PhantomJS process fails/crashes.
    * PhantomJSTimeout if PhantomJS takes more than timeout seconds to finish
    * PhantomJSNotInPath if there's no phantomjs in $PATH
    '''
    cookie_string = _cookies.cookie_string(cookies, u'cookies')
    cleaned_up_content = _clean_up_html(content, prefix)
    img_string = _render(content=cleaned_up_content, width=width,
                         height=height, top=top, left=left, prefix=prefix,
                         cookie_string=cookie_string, timeout=timeout)
    return _resize(img_string, scale)


@_dom2img_args_validator
def dom2img_debug(content, width, height, prefix, timeout=30,
                  top=0, left=0, scale=100, cookies=None):
    '''
    Returns command to run PhantomJS renderer in debug mode.

    Parameters:
    * content - html input (utf-8 encoded byte-string or unicode text)
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
    * timeout - non-negative int (unused)

     height, width, top, left:
       int or byte-string/unicode text containing
       decimal representation of the integer number
    * prefix - absolute URL that will be used
               to resolve relative URLs in html (for images, css scripts)
               and to derive cookie domain for cookies
               can be byte-string or ascii-only unicode text.
    * cookies - cookies key and values that will be sent with all
                resource requests (images, css scripts)
      * None
      * byte-string (or ascii-only unicode text) using
        key1=val1;key2=val2 format
      * string dictionary with cookie keys and values.
        Neither keys nor values should contain semicolons.
        Keys cannot contain '=' character.
        Keys and values can be byte-strings or ascii-only unicode texts.

    Returns text string containing shell command,
    that runs PhantomJS renderer script in a debug mode.

    Raises:
    * TypeError if arguments are not the right type
    * ValueError if arguments have invalid values
    * PhantomJSNotInPath if there's no phantomjs in $PATH
    '''
    cookie_string = _cookies.cookie_string(cookies, u'cookies')

    (fd, content_path) = tempfile.mkstemp(suffix='.html',
                                          prefix='dom2img_input')
    os.close(fd)

    with open(content_path, 'wb') as f:
        f.write(_clean_up_html(content, prefix))

    phantomjs_args = \
        _phantomjs_invocation(width=width, height=height,
                              top=top, left=left, prefix=prefix,
                              cookie_string=cookie_string)

    command = list(map(pipes.quote, phantomjs_args)) + \
        [u'--debug', u'<', pipes.quote(content_path)]

    return u' '.join(command)
