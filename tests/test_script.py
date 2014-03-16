# coding=utf-8
import StringIO
import multiprocessing
import unittest2
import os

from PIL import Image
from flask import Flask, request, Response
from subprocess import Popen, PIPE


def call_script(args, stdin):
    new_env = os.environ.copy()
    new_env['PYTHONPATH'] = '.'
    proc = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=new_env)
    result = proc.communicate(stdin)
    return result[0], result[1], proc.returncode


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

    def test_script(self):
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

        # result is empty if there's no cookie key=val
        # test.css overrides body bgcolor to white
        # body_margin.css sets body margin to 0
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

        with Process(app.run, port=1111):
            output = call_script(['python',
                                  'dom2img/_script.py',
                                  '--width=500',
                                  '--height=300',
                                  '--top=50',
                                  '--left=50',
                                  '--scale=100',
                                  '--prefix=http://127.0.0.1:1111/',
                                  '--cookies=key=val'],
                                 content)[0]
            image = self._image_from_bytestring(output)
            self.assertEqual(image.size, (500, 300))
            for i in range(500):
                for j in range(300):
                    if (50 <= i < 450) and (50 <= j < 250):
                        expected_pixel = (255, 0, 0, 255)
                    else:
                        expected_pixel = (255, 255, 255, 255)
                    self.assertEqual(image.getpixel((i, j)),
                                     expected_pixel, str((i, j)))

    def test_script_permuted_args(self):
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

        # result is empty if there's no cookie key=val
        # test.css overrides body bgcolor to white
        # body_margin.css sets body margin to 0
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

        with Process(app.run, port=1111):
            output = call_script(['python',
                                  'dom2img/_script.py',
                                  '--height=300',
                                  '--scale=100',
                                  '--width=500',
                                  '--top=50',
                                  '--cookies=key=val',
                                  '--prefix=http://127.0.0.1:1111/',
                                  '--left=50'],
                                 content)[0]
            image = self._image_from_bytestring(output)
            self.assertEqual(image.size, (500, 300))
            for i in range(500):
                for j in range(300):
                    if (50 <= i < 450) and (50 <= j < 250):
                        expected_pixel = (255, 0, 0, 255)
                    else:
                        expected_pixel = (255, 255, 255, 255)
                    self.assertEqual(image.getpixel((i, j)),
                                     expected_pixel, str((i, j)))

    def test_script_usage(self):
        '''
        Test all the features!
        '''
        result = call_script(['python', 'dom2img/_script.py', '--help'], '')
        self.assertTrue(b'usage' in result[0])
        self.assertEqual(result[1], '')
        self.assertEqual(result[2], 0)

    def test_script_missing_arg(self):
        base_args = ['python', 'dom2img/_script.py', '--cookies=key=val']
        extra_args = ['--height=300', '--width=500',
                      '--prefix=http://127.0.0.1:1111/']
        for i in range(len(extra_args)):
            args = list(extra_args)
            args.pop(i)
            result = call_script(base_args + args, '')
            self.assertTrue(b'usage' in result[1])
            self.assertEqual(b'', result[0])
            self.assertEqual(2, result[2])

    def test_script_optional_cookie_string(self):
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
        margin: 0;
        background-color: black !important;
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

        # result is empty if there's no cookie key=val
        # test.css overrides body bgcolor to white
        # body_margin.css sets body margin to 0
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

        with Process(app.run, port=1111):
            output = call_script(['python',
                                  'dom2img/_script.py',
                                  '--height=300',
                                  '--scale=100',
                                  '--width=500',
                                  '--top=50',
                                  '--prefix=http://127.0.0.1:1111/',
                                  '--left=50'],
                                 content)[0]
            image = self._image_from_bytestring(output)
            self.assertEqual(image.size, (500, 300))
            for i in range(500):
                for j in range(300):
                    if (50 <= i < 450) and (50 <= j < 250):
                        expected_pixel = (255, 0, 0, 255)
                    else:
                        expected_pixel = (0, 0, 0, 255)
                    self.assertEqual(image.getpixel((i, j)),
                                     expected_pixel, str((i, j)))
