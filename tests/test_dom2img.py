# coding=utf-8
import StringIO
import unittest

from PIL import Image
from bs4 import BeautifulSoup

from dom2img import _dom2img


class Dom2ImgTest(unittest.TestCase):

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

    def test_render(self):
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
        output = _dom2img._render(content, 300, 200, 0, 0, '', '')
        buff = StringIO.StringIO()
        buff.write(output)
        buff.seek(0)
        image = Image.open(buff)
        self.assertEqual(image.size, (300, 200))
        for i in range(300):
            for j in range(200):
                pixel = image.getpixel((i, j))
                if (50 <= i < 250) and (50 <= j < 150):
                    self.assertEqual(pixel, (255, 0, 0, 255))
                else:
                    self.assertEqual(pixel, (255, 255, 255, 255))
