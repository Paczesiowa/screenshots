# coding=utf-8
import StringIO
import multiprocessing
import unittest2

from PIL import Image
from bs4 import BeautifulSoup
from flask import Flask, request, Response

from dom2img import _dom2img


class Process(object):

    def __init__(self, fun, *args, **kwargs):
        self.server = multiprocessing.Process(target=fun, args=args,
                                              kwargs=kwargs)

    def __enter__(self):
        self.server.start()

    def __exit__(self, type, value, traceback):
        self.server.terminate()
        self.server.join()


class MonkeyPatch(object):

    def __init__(self, obj, attr, new_attr):
        self._obj = obj
        self._attr = attr
        self._new_attr = new_attr

    def __enter__(self):
        self._old = getattr(self._obj, self._attr)
        setattr(self._obj, self._attr, self._new_attr)

    def __exit__(self, type, value, traceback):
        setattr(self._obj, self._attr, self._old)


class Dom2ImgTest(unittest2.TestCase):

    def _image_from_bytestring(self, content):
        return Image.open(StringIO.StringIO(content))

    def _validate_render_pixels(self, expected_pixel, *args):
        output = _dom2img._render(*args)
        image = self._image_from_bytestring(output)
        width, height = image.size
        for i in range(width):
            for j in range(height):
                self.assertEqual(image.getpixel((i, j)),
                                 expected_pixel(i, j),
                                 msg=str((i, j)))

    def test_clean_up_html(self):
        prefix = b'http://example.com'
        fun = lambda x: _dom2img._clean_up_html(x, prefix)
        bs = BeautifulSoup

        self.assertEqual(fun(b'<script src="test.js"></script>'),
                         b'')
        self.assertEqual(fun(b'<script src="test.js">'),
                         b'')
        self.assertEqual(fun(b'<script src="test.js" />'),
                         b'')
        self.assertEqual(fun(b'<script>alert("test");</script>'),
                         b'')

        content = u'''
<!DOCTYPE html>
<html>
  <head>
    <link rel="stylesheet" type="text/css" href="test.css">
    <link rel="stylesheet" type="text/css" href="http://sample.com/test.css">
    <script src="test.js"></script>
    <script src="test.js" />
    <style></style>
    <style>
      p {
        color: #ff0000;
      }
    </style>
    <script src="http://example.com/test.js"></script>
    <script type="text/javascript">
      var x = 'hello';
      alert(x);
    </script>
  </head>
  <body>
    <script type="text/javascript">
      var x = 'hello';
      alert(x);
    </script>
    <p>
      föö=bär
      <img src="test.png" />
    </p>
    <a href="test.html">
      <img src="http://sample.com/test.jpg" />
    </a>
  </body>
</html>
'''
        content2 = u'''
<!DOCTYPE html>
<html>
  <head>
    <link rel="stylesheet" type="text/css" href="http://example.com/test.css">
    <link rel="stylesheet" type="text/css" href="http://sample.com/test.css">
    <style></style>
    <style>
      p {
        color: #ff0000;
      }
    </style>
  </head>
  <body>
    <p>
      föö=bär
      <img src="http://example.com/test.png" />
    </p>
    <a href="http://example.com/test.html">
      <img src="http://sample.com/test.jpg" />
    </a>
  </body>
</html>
'''
        self.assertEqual(bs(fun(content.encode('utf-8'))).prettify(),
                         bs(content2).prettify())

    def test_render_size(self):
        content = b'<html></html>'
        output = _dom2img._render(content, 100, 200, 0, 0, '', '')
        image = self._image_from_bytestring(output)
        self.assertEqual(image.size, (100, 200))

    def test_simple_render(self):
        '''
        Test that rendering works
        '''
        content = b'''
<!DOCTYPE html>
<html>
  <body style="margin: 0;
               background-color: white;">
    <div style="width: 200px;
                height: 100px;
                background-color: red;
                margin: 50px;">
    </div>
  </body>
</html>
'''

        def expected_pixel(i, j):
            if (50 <= i < 250) and (50 <= j < 150):
                return (255, 0, 0, 255)
            else:
                return (255, 255, 255, 255)

        self._validate_render_pixels(expected_pixel, content,
                                     300, 200, 0, 0, '', '')

    def test_offset_render(self):
        '''
        Test that scrolled (with offsets) rendering works
        '''
        content = b'''
<!DOCTYPE html>
<html>
  <body style="margin: 0;
               background-color: white;
               width: 600px;
               height: 800px;">
    <div style="width: 200px;
                height: 100px;
                background-color: red;
                margin: 50px;">
    </div>
  </body>
</html>
'''

        def expected_pixel(i, j):
            if (i < 200) and (25 <= j < 125):
                return (255, 0, 0, 255)
            else:
                return (255, 255, 255, 255)

        self._validate_render_pixels(expected_pixel, content,
                                     250, 150, 25, 50, '', '')

    def test_cookie_render(self):
        '''
        Test that cookies are correctly passed to referenced resources
        '''
        content = b'''
<!DOCTYPE html>
<html>
  <head>
    <link rel="stylesheet" href="http://127.0.0.1:1111/test.css">
    <style>
      body {
        margin: 0px;
        background-color: white;
      }
      div {
        width: 200px;
        height: 100px;
        background-color: red;
        margin: 50px;
      }
    </style>
  </head>
  <body>
    <div>
    </div>
  </body>
</html>
'''
        app = Flask('test')

        # test.css overrides body bgcolor to black
        # if cookie key=val is present
        @app.route('/test.css', methods=['GET'])
        def test_css():
            if request.cookies.get('key') == 'val':
                css = 'body { background-color: black !important; }'
            else:
                css = ''
            return Response(css, mimetype='text/css')

        # pixels inside div are red, rest are of color
        def expected_pixel_for_bgcolor(*color):
            def aux(i, j):
                if (50 <= i < 250) and (50 <= j < 150):
                    return (255, 0, 0, 255)
                else:
                    return tuple(color)
            return aux

        # bg is not changed if /test.css is empty (because no cookie)
        with Process(app.run, port=1111):
            self._validate_render_pixels(
                expected_pixel_for_bgcolor(255, 255, 255, 255),
                content, 300, 200, 0, 0, '', '')

        # bg is changed with correct cookie passed to /test.css
        with Process(app.run, port=1111):
            self._validate_render_pixels(
                expected_pixel_for_bgcolor(0, 0, 0, 255),
                content, 300, 200, 0, 0, '127.0.0.1', 'key=val')

        # bg is not changed with correct cookie passed, but wrong domain
        with Process(app.run, port=1111):
            self._validate_render_pixels(
                expected_pixel_for_bgcolor(255, 255, 255, 255),
                content, 300, 200, 0, 0, 'example.com', 'key=val')

    def test_resize(self):
        img = Image.new('RGBA', (80, 40))

        def pixel_color(i, j):
            if (20 <= i < 60) and (10 <= j < 30):
                return (255, 0, 0, 255)
            else:
                return (255, 255, 255, 255)

        for i in range(80):
            for j in range(40):
                img.putpixel((i, j), pixel_color(i, j))

        buff = StringIO.StringIO()
        img.save(buff, format='PNG')
        img_string = buff.getvalue()

        # default antialias filter looks better, but the result
        # is hard to unittest
        result_string = _dom2img._resize(img_string, 50, Image.NEAREST)

        result = Image.open(StringIO.StringIO(result_string))
        self.assertEqual(result.size, (40, 20))
        for i in range(40):
            for j in range(20):
                self.assertEqual(result.getpixel((i, j)),
                                 pixel_color(2 * i, 2 * j))

    def test_dom2img(self):
        '''
        Test all the features!
        '''
        content = b'''
<!DOCTYPE html>
<html>
  <head>
    <link rel="stylesheet" href="http://127.0.0.1:1111/test.css">
    <link rel="stylesheet" href="body_margin.css">
    <style>
      body {
        width: 800px;
        height: 800px;
      }
      div {
        width: 400px;
        height: 200px;
        background-color: red;
        margin: 100px;
      }
    </style>
    <script src="http://code.jquery.com/jquery-1.10.1.min.js"></script>
    <script>
      $(document).ready(function() {
        $('div').remove();
      });
    </script>
  </head>
  <body>
    <div>
    </div>
  </body>
</html>
'''
        app = Flask('test')

        # test.css overrides body bgcolor to black
        # if cookie key=val is present
        @app.route('/<path>', methods=['GET'])
        def test_css(path):
            if request.cookies.get('key') == 'val':
                if path == 'test.css':
                    css = 'body { background-color: white;}'
                elif path == 'body_margin.css':
                    css = 'body { margin: 0;}'
                else:
                    css = ''
            else:
                css = ''
            return Response(css, mimetype='text/css')

        # override _resize to use 'nearest' resize filter
        # to make unit testing possible
        old_resize = _dom2img._resize

        def _new_resize(img_string, scale):
            return old_resize(img_string, scale, Image.NEAREST)

        with MonkeyPatch(_dom2img, '_resize', _new_resize):
            with Process(app.run, port=1111):
                output = _dom2img._dom2img(content, 500, 300, 50, 50, 50,
                                           'http://127.0.0.1:1111/', 'key=val')
                image = self._image_from_bytestring(output)
                self.assertEqual(image.size, (250, 150))
                for i in range(250):
                    for j in range(150):
                        if (25 <= i < 225) and (25 <= j < 125):
                            expected_pixel = (255, 0, 0, 255)
                        else:
                            expected_pixel = (255, 255, 255, 255)
                        self.assertEqual(image.getpixel((i, j)),
                                         expected_pixel, str((i, j)))
