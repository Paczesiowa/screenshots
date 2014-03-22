# coding=utf-8
import StringIO
import multiprocessing
import os
import socket
from subprocess import Popen, PIPE

import flask
import unittest2
from PIL import Image

from dom2img import _dom2img


def image_from_bytestring(content):
    return Image.open(StringIO.StringIO(content))


class TestCase(unittest2.TestCase):

    _multiprocess_can_split_ = True

    def _check_result(self, output, *args, **kwargs):
        try:
            comparator = kwargs.pop('comparator')
        except KeyError:
            comparator = lambda x: x
        fun = self.FUN.__func__
        self.assertEqual(comparator(output), comparator(fun(*args, **kwargs)))

    def _check_results(self, kwargs, arg, val1, val2):
        fun = self.FUN.__func__
        kwargs1 = kwargs.copy()
        kwargs1[arg] = val1
        kwargs2 = kwargs.copy()
        kwargs2[arg] = val2
        self.assertEqual(fun(**kwargs1), fun(**kwargs2))

    def _check_result_true(self, *args, **kwargs):
        self._check_result(True, *args, **kwargs)

    def _check_result_false(self, *args, **kwargs):
        self._check_result(False, *args, **kwargs)

    def _check_exception(self, err_msg, *args, **kwargs):
        err_msg = err_msg.replace(u'(', u'\\(').replace(u')', u'\\)')
        try:
            exc = kwargs.pop('exc')
        except KeyError:
            exc = self.EXC
        fun = self.FUN.__func__
        self.assertRaisesRegexp(exc, err_msg, fun, *args, **kwargs)

    def _validate_render_pixels(self, png_data, left=0, top=0, scale=1,
                                div_color=(255, 0, 0)):
        image = image_from_bytestring(png_data)
        width, height = image.size
        for i in range(width):
            for j in range(height):
                if (scale * (100 - left) <= i < scale * (500 - left)) \
                        and (scale * (100 - top) <= j < scale * (300 - top)):
                    expected_pixel = div_color + (255,)
                else:
                    expected_pixel = (255, 255, 255, 255)
                self.assertEqual(image.getpixel((i, j)), expected_pixel,
                                 msg=str((i, j)))

dirty_html_doc = u'''
<!DOCTYPE html>
<html>
  <head>
    <link rel="stylesheet" href="div_bg_color.css">
    <link rel="stylesheet" type="text/css" href="http://example.com/test.css">
    <script src="test.js"></script>
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
    <script src="http://example.com/test.js"></script>
    <script type="text/javascript">
      var x = 'hello';
      alert(x);
    </script>
  </head>
  <body>
    <div>
    </div>
    <script type="text/javascript">
      var x = 'hello';
      alert(x);
    </script>
    <div style="display: none;">
      föö=bär
      <img src="test.png" />
      <a href="test.html">
        <img src="http://sample.com/test.jpg" />
      </a>
    </div>
  </body>
</html>
'''.encode('utf-8')


def html_doc(port=8000):
    prefix = 'http://127.0.0.1:' + str(port) + '/'
    return _dom2img._clean_up_html(dirty_html_doc, prefix)


class FlaskApp(object):

    def __init__(self):
        self._app = flask.Flask('test')

        # test.css overrides div bgcolor to black
        # if cookie key=val is present
        @self._app.route('/div_bg_color.css', methods=['GET'])
        def div_bg_color_css():
            if flask.request.cookies.get('key') == 'val':
                css = 'div { background-color: black !important; }'
            else:
                css = ''
            return flask.Response(css, mimetype='text/css')

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
        sock.close()
        kwargs = {'port': port, 'threaded': True}
        self._app.port = port
        self._server = multiprocessing.Process(target=self._app.run,
                                               kwargs=kwargs)

    def __enter__(self):
        self._server.start()
        return self._app

    def __exit__(self, type, value, traceback):
        self._server.terminate()
        self._server.join()


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


def call_script(args, stdin):
    new_env = os.environ.copy()
    new_env['PYTHONPATH'] = '.'
    proc = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE, env=new_env)
    result = proc.communicate(stdin)
    return result[0], result[1], proc.returncode
