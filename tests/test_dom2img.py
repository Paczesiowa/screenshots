# coding=utf-8
import argparse

from PIL import Image
from bs4 import BeautifulSoup

import tests.utils as utils
from dom2img import _compat, _dom2img


class CleanUpHTMLTest(utils.TestCase):

    FUN = lambda x: _dom2img._clean_up_html(x, b'http://example.com')

    def test_script_tag_removal(self):
        self._check_result(b'', b'<script src="test.js"></script>')

    def test_script_tag_removal_without_closing_tag(self):
        self._check_result(b'', b'<script src="test.js">')

    def test_script_tag_removal_with_implicit_closing_tag(self):
        self._check_result(b'', b'<script src="test.js" />')

    def test_script_tag_removal_with_inline_js(self):
        self._check_result(b'', b'<script>alert("test");</script>')

    def test_result_is_utf8_byte_string(self):
        result = _dom2img._clean_up_html(utils.dirty_html_doc,
                                         b'http://example.com')
        self.assertTrue(isinstance(result, _compat.byte_string))
        result.decode('utf-8')

    def test_complex(self):
        content = u'''
<!DOCTYPE html>
<html>
  <head>
    <link rel="stylesheet" href="http://example.com/div_bg_color.css">
    <link rel="stylesheet" type="text/css" href="http://example.com/test.css">
    <style></style>
    <style>
      body {
        width: 800px;
        height: 800px;
        margin: 0;
        background-color: white;
      }
      div {
        width: 400px;
        height: 200px;
        background-color: red;
        margin: 100px;
      }
    </style>
  </head>
  <body>
    <div>
    </div>
    <div style="display: none;">
      föö=bär
      <img src="http://example.com/test.png" />
      <a href="http://example.com/test.html">
        <img src="http://sample.com/test.jpg" />
      </a>
    </div>
  </body>
</html>

'''
        self._check_result(content, utils.dirty_html_doc,
                           comparator=lambda c: BeautifulSoup(c).prettify())


class RenderTest(utils.TestCase):

    FUN = _dom2img._render

    def test_render_size(self):
        content = b'<html></html>'
        output = _dom2img._render(content=content,
                                  width=100,
                                  height=200,
                                  top=0,
                                  left=0,
                                  cookie_domain=b'',
                                  cookie_string=b'')
        image = utils.image_from_bytestring(output)
        self.assertEqual(image.size, (100, 200))

    def test_simple_render(self):
        output = _dom2img._render(content=utils.html_doc(),
                                  width=600,
                                  height=400,
                                  top=0,
                                  left=0,
                                  cookie_domain='',
                                  cookie_string='')
        self._validate_render_pixels(output)

    def test_offset_render(self):
        output = _dom2img._render(content=utils.html_doc(),
                                  width=600,
                                  height=400,
                                  top=50,
                                  left=50,
                                  cookie_domain='',
                                  cookie_string='')
        self._validate_render_pixels(output, top=50, left=50)

    def test_cookie_render_with_wrong_cookie(self):
        with utils.FlaskApp() as app:
            output = _dom2img._render(content=utils.html_doc(app.port),
                                      width=600,
                                      height=400,
                                      top=0,
                                      left=0,
                                      cookie_domain='127.0.0.1',
                                      cookie_string='key=val2')
            self._validate_render_pixels(output)

    def test_cookie_render(self):
        with utils.FlaskApp() as app:
            output = _dom2img._render(content=utils.html_doc(app.port),
                                      width=600,
                                      height=400,
                                      top=0,
                                      left=0,
                                      cookie_domain='127.0.0.1',
                                      cookie_string='key=val')
            self._validate_render_pixels(output, div_color=(0, 0, 0))

    def test_cookie_render_wrong_cookie_domain(self):
        with utils.FlaskApp() as app:
            output = _dom2img._render(content=utils.html_doc(app.port),
                                      width=600,
                                      height=400,
                                      top=0,
                                      left=0,
                                      cookie_domain='example.com',
                                      cookie_string='key=val')
            self._validate_render_pixels(output)


class ResizeTest(utils.TestCase):

    def test_resize(self):
        img = Image.new('RGBA', (600, 400))

        for i in range(600):
            for j in range(400):
                if (100 <= i < 500) and (100 <= j < 300):
                    color = (255, 0, 0, 255)
                else:
                    color = (255, 255, 255, 255)
                img.putpixel((i, j), color)

        buff = _compat.BytesIO()
        img.save(buff, format='PNG')
        img_string = buff.getvalue()

        # default antialias filter looks better, but the result
        # is hard to unittest
        result_string = _dom2img._resize(img_string, 50, Image.NEAREST)
        self._validate_render_pixels(result_string, scale=.5)

        result_img = utils.image_from_bytestring(result_string)
        self.assertEqual((300, 200), result_img.size)


class Dom2ImgWorkerTest(utils.TestCase):

    def test_complex(self):
        # override _resize to use 'nearest' resize filter
        # to make unit testing possible
        old_resize = _dom2img._resize

        def _new_resize(img_string, scale):
            return old_resize(img_string, scale, Image.NEAREST)

        with utils.MonkeyPatch(_dom2img, '_resize', _new_resize):
            with utils.FlaskApp() as app:
                port = app.port
                prefix = b'http://127.0.0.1:' + str(port) + b'/'
                output = _dom2img._dom2img(content=utils.html_doc(port),
                                           width=600,
                                           height=400,
                                           top=50,
                                           left=50,
                                           scale=50,
                                           prefix=prefix,
                                           cookie_string=b'key=val')
                self._validate_render_pixels(output, left=50, top=50, scale=.5,
                                             div_color=(0, 0, 0))


class Dom2ImgTest(utils.TestCase):

    FUN = _dom2img.dom2img
    EXC = argparse.ArgumentTypeError

    def _make_kwargs(self, port):
        return {b'content': utils.html_doc(port),
                b'width': 200,
                b'height': 200,
                b'top': 0,
                b'left': 0,
                b'scale': 100,
                b'prefix': b'http://example.com/',
                b'cookies': 'key=val'}

    def _check_images(self, arg, val1, val2):
        with utils.FlaskApp() as app:
            self._check_results(self._make_kwargs(app.port), arg, val1, val2)

    def _check_exception(self, err_msg, arg, val, exc=None):
        with utils.FlaskApp() as app:
            kwargs = self._make_kwargs(app.port)
            kwargs[arg] = val
            if exc is not None:
                kwargs['exc'] = exc
            super(Dom2ImgTest, self)._check_exception(err_msg, **kwargs)

    def test_content_gets_decoded_properly(self):
        content = u'<html>fööbär</html>'
        self._check_images(b'content',
                           content,
                           content.encode('utf-8'))

    def test_width_gets_parsed_properly(self):
        self._check_images(b'width', 100, b'100')
        self._check_images(b'width', 100, u'100')

    def test_height_gets_parsed_properly(self):
        self._check_images(b'height', 200, b'200')
        self._check_images(b'height', 200, u'200')

    def test_top_gets_parsed_properly(self):
        self._check_images(b'top', 30, b'30')
        self._check_images(b'top', 30, u'30')

    def test_left_gets_parsed_properly(self):
        self._check_images(b'left', 40, b'40')
        self._check_images(b'left', 40, u'40')

    def test_scale_gets_parsed_properly(self):
        self._check_images(b'scale', 50, b'50')
        self._check_images(b'scale', 50, u'50')

    def test_prefix_gets_parsed_properly(self):
        with utils.FlaskApp() as app:
            prefix1 = b'http://127.0.0.1:' + str(app.port) + b'/'
            prefix2 = prefix1.decode('utf-8')
            self._check_results(self._make_kwargs(app.port),
                                b'prefix', prefix1, prefix2)

    def test_empty_cookies_get_serialized_properly(self):
        self._check_images(b'cookies', b'', u'')
        self._check_images(b'cookies', b'', None)
        self._check_images(b'cookies', b'', {})

    def test_non_empty_cookies_get_serialized_properly(self):
        self._check_images(b'cookies', b'key=val', u'key=val')
        self._check_images(b'cookies', {b'key': b'val'}, {u'key': u'val'})
        self._check_images(b'cookies', {b'key': u'val'}, {u'key': b'val'})

    def test_content_wrong_type(self):
        self._check_exception(
            u'content must be utf-8 encoded byte string or unicode',
            b'content', [])

    def test_width_wrong_type(self):
        self._check_exception(u'width must be int/byte string/unicode',
                              b'width', None)

    def test_width_non_ascii_unicode(self):
        self._check_exception(u'width must be ascii-only unicode',
                              b'width', u'föö')

    def test_width_unparseable(self):
        self._check_exception(u'width cannot be parsed as an int',
                              b'width', b'1.5')

    def test_width_negative(self):
        self._check_exception(u'Unexpected negative integer for width',
                              b'width', -1)

    def test_height_wrong_type(self):
        self._check_exception(u'height must be int/byte string/unicode',
                              b'height', None)

    def test_height_non_ascii_unicode(self):
        self._check_exception(u'height must be ascii-only unicode',
                              b'height', u'föö')

    def test_height_unparseable(self):
        self._check_exception(u'height cannot be parsed as an int',
                              b'height', b'1.5')

    def test_height_negative(self):
        self._check_exception(u'Unexpected negative integer for height',
                              b'height', -1)

    def test_top_wrong_type(self):
        self._check_exception(u'top must be int/byte string/unicode',
                              b'top', None)

    def test_top_non_ascii_unicode(self):
        self._check_exception(u'top must be ascii-only unicode',
                              b'top', u'föö')

    def test_top_unparseable(self):
        self._check_exception(u'top cannot be parsed as an int',
                              b'top', b'1.5')

    def test_top_negative(self):
        self._check_exception(u'Unexpected negative integer for top',
                              b'top', -1)

    def test_left_wrong_type(self):
        self._check_exception(u'left must be int/byte string/unicode',
                              b'left', None)

    def test_left_non_ascii_unicode(self):
        self._check_exception(u'left must be ascii-only unicode',
                              b'left', u'föö')

    def test_left_unparseable(self):
        self._check_exception(u'left cannot be parsed as an int',
                              b'left', b'1.5')

    def test_left_negative(self):
        self._check_exception(u'Unexpected negative integer for left',
                              b'left', -1)

    def test_scale_wrong_type(self):
        self._check_exception(u'scale must be int/byte string/unicode',
                              b'scale', None)

    def test_scale_non_ascii_unicode(self):
        self._check_exception(u'scale must be ascii-only unicode',
                              b'scale', u'föö')

    def test_scale_unparseable(self):
        self._check_exception(u'scale cannot be parsed as an int',
                              b'scale', b'1.5')

    def test_scale_negative(self):
        self._check_exception(u'Unexpected negative integer for scale',
                              b'scale', -1)

    def test_prefix_non_ascii_unicode(self):
        self._check_exception(u'unicode prefix must be ascii-only',
                              b'prefix', u'http://example.com/föö',
                              exc=ValueError)

    def test_prefix_wrong_type(self):
        self._check_exception(
            u'prefix must be a byte-string or an unicode text',
            b'prefix', None, exc=TypeError)

    def test_prefix_non_absolute_url(self):
        self._check_exception(u'prefix must be an absolute url',
                              b'prefix', b'example.com', exc=ValueError)
        self._check_exception(u'prefix must be an absolute url',
                              b'prefix', b'example.com/', exc=ValueError)
        self._check_exception(u'prefix must be an absolute url',
                              b'prefix', b'//example.com', exc=ValueError)

    def test_cookies_wrong_type(self):
        self._check_exception(u'cookies must be None/string/dict',
                              b'cookies', 7)

    def test_cookies_non_ascii_unicode(self):
        self._check_exception(u'unicode cookies must be ascii-only',
                              b'cookies', u'föö')

    def test_cookies_key_values_non_ascii_unicode(self):
        self._check_exception(u'cookies keys/values must be ascii-only',
                              b'cookies', {u'föö': u'bär'.encode('utf-8')})

    def test_cookies_key_values_wrong_type(self):
        self._check_exception(u'cookies key/values must be strings',
                              b'cookies', {u'foo': []})
        self._check_exception(u'cookies key/values must be strings',
                              b'cookies', {3: b'bar'})

    def test_cookies_key_with_equals_char(self):
        self._check_exception(u"cookies keys cannot use '=' character",
                              b'cookies', {u'f=o': b'bar'})

    def test_cookies_key_values_with_semicolon(self):
        self._check_exception(u"cookies keys/values cannot use ';' character",
                              b'cookies', {u'f;o': b'bar'})
        self._check_exception(u"cookies keys/values cannot use ';' character",
                              b'cookies', {u'foo': b'b;r'})
