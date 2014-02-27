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


class Dom2ImgTest(unittest2.TestCase):

    def _image_from_bytestring(self, content):
        buff = StringIO.StringIO()
        buff.write(content)
        buff.seek(0)
        return Image.open(buff)

    def _validate_render_pixels(self, expected_pixel, *args):
        output = _dom2img._render(*args)
        with open('/tmp/test.png', 'w') as f:
            f.write(output)
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
