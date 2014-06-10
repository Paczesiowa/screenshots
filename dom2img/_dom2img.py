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
    Remove all script tags and make relative URLs absolute.

    Args:
        content: Utf-8 encoded bytes with HTML.
        prefix: Ascii-only unicode URL, that will be used to make
            absolute URLs.

    Returns:
        Utf-8 encoded bytes with HTML that doesn't contain any script tags,
        and all relative URLs were made absolute.
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
    Prepare command line arguments for running PhantomJS renderer.

    Args:
        width: int, non-negative width of PhantomJS viewport in pixels.
        height: int, non-negative height of PhantomJS viewport in pixels.
        top: int, pixel offset from the top/vertical scroll position.
        left: int, pixel offset from the left/horizontal scroll position.
        prefix: Ascii-only unicode text containing absolute URL
            with origin of the HTML.
        cookie_string: bytes containing cookies using "key1=val1;key2=val2"
            format.

    Returns:
        list of unicode text objects that contains cli args for running
        PhantomJS renderer.

    Raises:
        PhantomJSNotInPath: There's no phantomjs in $PATH.
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
    Renders HTML content using PhantomJS.

    Args:
        content: Utf-8 encoded bytes with HTML.
        width: int, non-negative width of PhantomJS viewport in pixels.
        height: int, non-negative height of PhantomJS viewport in pixels.
        top: int, pixel offset from the top/vertical scroll position.
        left: int, pixel offset from the left/horizontal scroll position.
        prefix: Ascii-only unicode text containing absolute URL
            with origin of the HTML.
        cookie_string: bytes containing cookies using "key1=val1;key2=val2"
            format.
        timeout: int, number of seconds after which PhantomJS will be killed.

    Returns:
        bytes with PNG data of the render.

    Raises:
        PhantomJSFailure: PhantomJS process failed/crashed.
        PhantomJSTimeout: PhantomJS took more than timeout seconds to finish.
        PhantomJSNotInPath: There's no PhantomJS in $PATH.
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
    Resize an image.

    Args:
        img_string: bytes containing PNG image data.
        scale: int with percentage number of the resize, 50 (percent)
            means 2 times smaller image.
        resize_filter: Pillow resize filter, abstracted for tests.

    Returns:
        bytes containing PNG image data of the resized image.
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
    Renders HTML using PhantomJS.

    Args:
        content: Utf-8 encoded bytes or unicode text with HTML input.
        width: int, bytes or unicode text containing integer, or decimal
            representation of an integer, that is greater or equal to zero,
            and represents the width of the virtual render viewport, using
            pixels unit.
        height: int, bytes or unicode text containing integer, or decimal
            representation of an integer, that is greater or equal to zero,
            and represents the height of the virtual render viewport, using
            pixels unit.
        top: int, bytes or unicode text containing integer, or decimal
            representation of an integer, that is greater or equal to zero,
            and represents the vertical offset, using pixels unit, from the top
            of the page, where rendering should start.
        left: int, bytes or unicode text containing integer, or decimal
            representation of an integer, that is greater or equal to zero,
            and represents the horizontal offset, using pixels unit, from the
            left border of the page, where rendering should start.
        scale: int, bytes or unicode text containing integer, or decimal
            representation of an integer, that is greater or equal to zero,
            and represents the percentage number of the desired resize,
            50 (percent) means 2 times smaller image.
        timeout: int, bytes or unicode text containing integer, or decimal
            representation of an integer, that is greater or equal to zero,
            and represents the number of seconds after which PhantomJS will
            be killed.
        prefix: Ascii-only bytes or unicode text containing absolute URL,
            that will be used to resolve relative URLs in HTML
            (e.g. for images, css scripts) and to derive cookie domain for
            cookies.
        cookies: Cookies keys and values that will be sent with all
            resource requests (e.g. images, css scripts). Cookies can be:
                * None
                * bytes or ascii-only unicode text using "key1=val1;key2=val2"
                    format.
                * dict with cookie bytes/unicode text keys and values.
                    Neither keys nor values should contain semicolons.
                    Keys cannot contain '=' character.

    Returns:
        bytes containing PNG image data with the render.

    Raises:
        TypeError: arguments are not the right type.
        ValueError: arguments have invalid values.
        PhantomJSFailure: PhantomJS process failed/crashed.
        PhantomJSTimeout: PhantomJS took too long to finish.
        PhantomJSNotInPath: There's no PhantomJS in $PATH.
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
    Build a command to run PhantomJS renderer in debug mode.

    Args:
        The same as for dom2img().

    Returns:
        Unicode text with a command to run PhantomJS renderer script
        in a debug mode.

    Raises:
        TypeError: arguments are not the right type.
        ValueError: arguments have invalid values.
        PhantomJSNotInPath: There's no PhantomJS in $PATH.
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
