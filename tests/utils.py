# coding=utf-8
import contextlib
import multiprocessing
import os
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time

import flask
import unittest2
from PIL import Image

from dom2img import _dom2img, _compat


try:
    import urllib2 as urllib
except ImportError:
    import urllib.request as urllib


def image_from_bytestring(content):
    return Image.open(_compat.BytesIO(content))


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

    def assertRaisesExcStr(self, excClass, excMsg,
                           callableObj, *args, **kwargs):
        try:
            callableObj(*args, **kwargs)
        except excClass as e:
            if sys.version_info < (3,):
                excMsg = excMsg.encode('ascii', 'replace').decode('ascii')
            self.assertEqual(str(e), excMsg)

    def _check_exception(self, err_msg, *args, **kwargs):
        try:
            exc = kwargs.pop('exc')
        except KeyError:
            exc = self.EXC
        fun = self.FUN.__func__
        self.assertRaisesExcStr(exc, err_msg, fun, *args, **kwargs)

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


def prefix_for_port(port):
    return u'http://127.0.0.1:' + str(port) + u'/'


def html_doc(port=8000):
    prefix = prefix_for_port(port)
    return _dom2img._clean_up_html(dirty_html_doc, prefix)


def freezing_html_doc(port=8000):
    content = b'''
<!DOCTYPE html>
<html>
  <head>
    <link rel="stylesheet" href="%dfreeze.css">
  </had>
  <body>
  </body>
</html>
'''
    prefix = prefix_for_port(port)
    return content.replace(b'%d', prefix.encode('ascii'))


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

        # freeze.css requests freezes
        @self._app.route('/freeze.css', methods=['GET'])
        def freeze_css():
            time.sleep(60)

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
        server_started = False
        while not server_started:
            try:
                conn = urllib.urlopen('http://127.0.0.1:' + str(self._app.port)
                                      + '/div_bg_color.css')
                conn.close()
                server_started = True
            except urllib.URLError:
                time.sleep(.1)
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


def start_script(args):
    new_env = os.environ.copy()
    new_env['PYTHONPATH'] = ':'.join(sys.path)
    pipe = subprocess.PIPE
    return subprocess.Popen(args, stdin=pipe, stdout=pipe,
                            stderr=pipe, env=new_env)


def call_script(args, stdin):
    proc = start_script(args)
    result = proc.communicate(stdin)
    return result[0], result[1], proc.returncode


def check_output(*popenargs, **kwargs):
    '''
    copy of subprocess.check_output, which is not present in python-2.6
    '''
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd)
    return output


def read_process_until_line(cmd, line):
    '''
    Run shell command, read all the output lines until line encountered.
    Kill it.
    '''
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True,
                               preexec_fn=os.setpgrp)
    result = b''
    while True:
        output_line = process.stdout.readline()
        result += output_line
        if output_line == line:
            break
    os.killpg(process.pid, signal.SIGTERM)
    return result


def killer(parent_pid, killer_should_stop):
    output = b''
    while not killer_should_stop[0] and b'phantomjs ' not in output:
        time.sleep(.01)
        try:
            output = check_output(
                ['ps', '--ppid', str(parent_pid), '-o', 'pid,cmd'])
        except subprocess.CalledProcessError:
            pass
    if killer_should_stop[0]:
        return
    output = output.split(b'\n')[1:]  # skip header line
    line = list(filter(lambda l: b'phantomjs ' in l, output))[0]
    pid = int(line.split()[0])
    os.kill(pid, signal.SIGKILL)


@contextlib.contextmanager
def mock_phantom_js_binary(script):
    script = script.lstrip()
    tmp_dir = tempfile.mkdtemp()
    tmp_phantomjs_path = os.path.join(tmp_dir, 'phantomjs')
    with open(tmp_phantomjs_path, 'wb') as f:
        f.write(script)
    st = os.stat(tmp_phantomjs_path)
    os.chmod(tmp_phantomjs_path, st.st_mode | stat.S_IEXEC)
    old_path = os.environ['PATH']
    os.environ['PATH'] = tmp_dir + ':' + old_path
    try:
        yield
    finally:
        os.environ['PATH'] = old_path
        shutil.rmtree(tmp_dir)
