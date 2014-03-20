# coding=utf-8
import argparse
import StringIO
import unittest2

from PIL import Image
from bs4 import BeautifulSoup

from dom2img import _dom2img

import tests.utils as utils


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

        buff = StringIO.StringIO()
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


class Dom2ImgTest(unittest2.TestCase):

    def test_dom2img_wrapper(self):
        fun = _dom2img.dom2img
        exc = argparse.ArgumentTypeError

        worker_args = {}

        def grab_worker_args(**kwargs):
            worker_args.clear()
            for key, val in kwargs.items():
                worker_args[key] = val

        with utils.MonkeyPatch(_dom2img, '_dom2img', grab_worker_args):
            fun(b'content', 100, 100, b'http://example.com/', 0, 0, 100, None)
            self.assertEqual(worker_args['content'], b'content')

            fun(u'fööbär', 100, 100, b'http://example.com/', 0, 0, 100, None)
            self.assertEqual(worker_args['content'], u'fööbär'.encode('utf-8'))

            fun(b'', 100, 100, b'http://example.com/', 0, 0, 100, None)
            self.assertEqual(worker_args['width'], 100)

            fun(b'', b'200', 100, b'http://example.com/', 0, 0, 100, None)
            self.assertEqual(worker_args['width'], 200)

            fun(b'', u'300', 100, b'http://example.com/', 0, 0, 100, None)
            self.assertEqual(worker_args['width'], 300)

            fun(b'', 100, 100, b'http://example.com/', 0, 0, 100, None)
            self.assertEqual(worker_args['height'], 100)

            fun(b'', 100, b'200', b'http://example.com/', 0, 0, 100, None)
            self.assertEqual(worker_args['height'], 200)

            fun(b'', 100, u'300', b'http://example.com/', 0, 0, 100, None)
            self.assertEqual(worker_args['height'], 300)

            fun(b'', 100, 100, b'http://example.com/', 100, 0, 100, None)
            self.assertEqual(worker_args['top'], 100)

            fun(b'', 100, 100, b'http://example.com/', b'200', 0, 100, None)
            self.assertEqual(worker_args['top'], 200)

            fun(b'', 100, 100, b'http://example.com/', u'300', 0, 100, None)
            self.assertEqual(worker_args['top'], 300)

            fun(b'', 100, 100, b'http://example.com/', 0, 100, 100, None)
            self.assertEqual(worker_args['left'], 100)

            fun(b'', 100, 100, b'http://example.com/', 0, b'200', 100, None)
            self.assertEqual(worker_args['left'], 200)

            fun(b'', 100, 100, b'http://example.com/', 0, u'300', 100, None)
            self.assertEqual(worker_args['left'], 300)

            fun(b'', 100, 100, b'http://example.com/', 0, 0, 100, None)
            self.assertEqual(worker_args['scale'], 100)

            fun(b'', 100, 100, b'http://example.com/', 0, 0, b'200', None)
            self.assertEqual(worker_args['scale'], 200)

            fun(b'', 100, 100, b'http://example.com/', 0, 0, u'300', None)
            self.assertEqual(worker_args['scale'], 300)

            fun(b'', 100, 100, b'http://example.com/', 0, 0, 100, None)
            self.assertEqual(worker_args['prefix'], b'http://example.com/')

            fun(b'', 100, 100, u'http://example.com/', 0, 0, 100, None)
            self.assertEqual(worker_args['prefix'], b'http://example.com/')

            fun(b'', 100, 100, b'http://example.com/', 0, 0, 100, None)
            self.assertEqual(worker_args['cookie_string'], b'')

            fun(b'', 100, 100, b'http://example.com/', 0, 0, 100, {})
            self.assertEqual(worker_args['cookie_string'], b'')

            fun(b'', 100, 100, b'http://example.com/', 0, 0, 100, b'')
            self.assertEqual(worker_args['cookie_string'], b'')

            fun(b'', 100, 100, b'http://example.com/', 0, 0, 100, u'')
            self.assertEqual(worker_args['cookie_string'], b'')

            fun(b'', 100, 100, b'http://example.com/',
                0, 0, 100, b'key1=val1;key2=val2')
            self.assertEqual(worker_args['cookie_string'],
                             b'key1=val1;key2=val2')

            fun(b'', 100, 100, b'http://example.com/',
                0, 0, 100, u'key1=val1;key2=val2')
            self.assertEqual(worker_args['cookie_string'],
                             b'key1=val1;key2=val2')

            fun(b'', 100, 100, b'http://example.com/',
                0, 0, 100, {b'key1': b'val1', b'key2': b'val2'})
            self.assertEqual(worker_args['cookie_string'],
                             b'key2=val2;key1=val1')

            fun(b'', 100, 100, b'http://example.com/',
                0, 0, 100, {u'key1': u'val1', u'key2': u'val2'})
            self.assertEqual(worker_args['cookie_string'],
                             b'key2=val2;key1=val1')

            self.assertRaisesRegexp(
                exc, u'content must be utf-8 encoded byte string or unicode',
                fun, [], 0, 0, b'http://example.com/', 0, 0, 0, {})

            self.assertRaisesRegexp(
                exc, u'width must be int/byte string/unicode',
                fun, b'', None, 0, b'http://example.com/', 0, 0, 0, {})

            self.assertRaisesRegexp(
                exc, u'width must be ascii-only unicode',
                fun, b'', u'föö', 0, b'http://example.com/', 0, 0, 0, {})

            self.assertRaisesRegexp(
                exc, u'width cannot be parsed as an int',
                fun, b'', b'1.5', 0, b'http://example.com/', 0, 0, 0, {})

            self.assertRaisesRegexp(
                exc, u'Unexpected negative integer for width',
                fun, b'', -1, 0, b'http://example.com/', 0, 0, 0, {})

            self.assertRaisesRegexp(
                exc, u'height must be int/byte string/unicode',
                fun, b'', 0, None, b'http://example.com/', 0, 0, 0, {})

            self.assertRaisesRegexp(
                exc, u'height must be ascii-only unicode',
                fun, b'', 0, u'föö', b'http://example.com/', 0, 0, 0, {})

            self.assertRaisesRegexp(
                exc, u'height cannot be parsed as an int',
                fun, b'', 0, b'1.5', b'http://example.com/', 0, 0, 0, {})

            self.assertRaisesRegexp(
                exc, u'Unexpected negative integer for height',
                fun, b'', 0, -1, b'http://example.com/', 0, 0, 0, {})

            self.assertRaisesRegexp(
                exc, u'top must be int/byte string/unicode',
                fun, b'', 0, 0, b'http://example.com/', None, 0, 0, {})

            self.assertRaisesRegexp(
                exc, u'top must be ascii-only unicode',
                fun, b'', 0, 0, b'http://example.com/', u'föö', 0, 0, {})

            self.assertRaisesRegexp(
                exc, u'top cannot be parsed as an int',
                fun, b'', 0, 0, b'http://example.com/', b'1.5', 0, 0, {})

            self.assertRaisesRegexp(
                exc, u'Unexpected negative integer for top',
                fun, b'', 0, 0, b'http://example.com/', -1, 0, 0, {})

            self.assertRaisesRegexp(
                exc, u'left must be int/byte string/unicode',
                fun, b'', 0, 0, b'http://example.com/', 0, None, 0, {})

            self.assertRaisesRegexp(
                exc, u'left must be ascii-only unicode',
                fun, b'', 0, 0, b'http://example.com/', 0, u'föö', 0, {})

            self.assertRaisesRegexp(
                exc, u'left cannot be parsed as an int',
                fun, b'', 0, 0, b'http://example.com/', 0, b'1.5', 0, {})

            self.assertRaisesRegexp(
                exc, u'Unexpected negative integer for left',
                fun, b'', 0, 0, b'http://example.com/', 0, -1, 0, {})

            self.assertRaisesRegexp(
                exc, u'scale must be int/byte string/unicode',
                fun, b'', 0, 0, b'http://example.com/', 0, 0, None, {})

            self.assertRaisesRegexp(
                exc, u'scale must be ascii-only unicode',
                fun, b'', 0, 0, b'http://example.com/', 0, 0, u'föö', {})

            self.assertRaisesRegexp(
                exc, u'scale cannot be parsed as an int',
                fun, b'', 0, 0, b'http://example.com/', 0, 0, b'1.5', {})

            self.assertRaisesRegexp(
                exc, u'Unexpected negative integer for scale',
                fun, b'', 0, 0, b'http://example.com/', 0, 0, -1, {})

            self.assertRaisesRegexp(
                ValueError, u'unicode prefix must be ascii-only',
                fun, b'', 0, 0, u'http://example.com/föö', 0, 0, 0, {})

            self.assertRaisesRegexp(
                TypeError, u'prefix must be a byte-string or an unicode text',
                fun, b'', 0, 0, None, 0, 0, 0, {})

            self.assertRaisesRegexp(
                ValueError, u'prefix must be an absolute url',
                fun, b'', 0, 0, b'example.com', 0, 0, 0, {})

            self.assertRaisesRegexp(
                ValueError, u'prefix must be an absolute url',
                fun, b'', 0, 0, b'example.com/', 0, 0, 0, {})

            self.assertRaisesRegexp(
                ValueError, u'prefix must be an absolute url',
                fun, b'', 0, 0, b'//example.com', 0, 0, 0, {})

            self.assertRaisesRegexp(
                ValueError, u'prefix must be an absolute url',
                fun, b'', 0, 0, b'//example.com/', 0, 0, 0, {})

            self.assertRaisesRegexp(
                exc, u'cookies must be None/string/dict',
                fun, b'', 0, 0, b'http://example.com/', 0, 0, 0, 7)

            self.assertRaisesRegexp(
                exc, u'unicode cookies must be ascii-only',
                fun, b'', 0, 0, b'http://example.com/', 0, 0, 0, u'föö')

            self.assertRaisesRegexp(
                exc, u'cookies keys/values must be ascii-only',
                fun, b'', 0, 0, b'http://example.com/', 0, 0, 0,
                {u'föö': b'bär'})

            self.assertRaisesRegexp(
                exc, u'cookies key/values must be strings',
                fun, b'', 0, 0, b'http://example.com/', 0, 0, 0,
                {u'foo': []})

            self.assertRaisesRegexp(
                exc, u'cookies key/values must be strings',
                fun, b'', 0, 0, b'http://example.com/', 0, 0, 0,
                {3: b'bar'})

            self.assertRaisesRegexp(
                exc, u"cookies keys cannot use '=' character",
                fun, b'', 0, 0, b'http://example.com/', 0, 0, 0,
                {u'f=o': b'bar'})

            self.assertRaisesRegexp(
                exc, u"cookies keys/values cannot use ';' character",
                fun, b'', 0, 0, b'http://example.com/', 0, 0, 0,
                {u'f;o': b'bar'})

            self.assertRaisesRegexp(
                exc, u"cookies keys/values cannot use ';' character",
                fun, b'', 0, 0, b'http://example.com/', 0, 0, 0,
                {u'foo': b'b;r'})
