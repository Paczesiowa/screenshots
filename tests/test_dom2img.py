# coding=utf-8
import os
import signal
import threading

from PIL import Image
from bs4 import BeautifulSoup

import tests.utils as utils
from dom2img import _compat, _dom2img, _exceptions


class CleanUpHTMLTest(utils.TestCase):

    FUN = lambda x: _dom2img._clean_up_html(x, u'http://example.com')

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
                                         u'http://example.com')
        self.assertTrue(isinstance(result, bytes))
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


class PhantomjsInvocationTest(utils.TestCase):

    def test(self):
        fun = _dom2img._phantomjs_invocation
        result = fun(width=800, height=600, top=50,
                     left=50, prefix=u'http://example.com/',
                     cookie_string=b'key1=val1;key2=val2')

        self.assertEqual(len(result), 8)
        for i in range(8):
            self.assertTrue(isinstance(result[i], _compat.text), i)

        phantomjs_path = result[0]
        self.assertTrue(phantomjs_path.endswith('phantomjs'))
        self.assertTrue(os.path.isabs(phantomjs_path))
        self.assertEqual(os.path.normpath(phantomjs_path), phantomjs_path)
        self.assertTrue(b'phantomjs' in utils.check_output(
            [phantomjs_path, '--help']))

        self.assertEqual(result[1],
                         os.path.join(os.path.dirname(_dom2img.__file__),
                                      'render_file.phantom.js'))
        self.assertEqual(result[2], '800')
        self.assertEqual(result[3], '600')
        self.assertEqual(result[4], '50')
        self.assertEqual(result[5], '50')
        self.assertEqual(result[6], 'example.com')
        self.assertEqual(result[7], 'key1=val1;key2=val2')


class RenderTest(utils.TestCase):

    FUN = _dom2img._render

    def test_render_size(self):
        content = b'<html></html>'
        output = _dom2img._render(content=content,
                                  width=100,
                                  height=200,
                                  top=0,
                                  left=0,
                                  prefix=u'',
                                  cookie_string=b'',
                                  timeout=30)
        image = utils.image_from_bytestring(output)
        self.assertEqual(image.size, (100, 200))

    def test_simple_render(self):
        output = _dom2img._render(content=utils.html_doc(),
                                  width=600,
                                  height=400,
                                  top=0,
                                  left=0,
                                  prefix=u'',
                                  cookie_string=b'',
                                  timeout=30)
        self._validate_render_pixels(output)

    def test_offset_render(self):
        output = _dom2img._render(content=utils.html_doc(),
                                  width=600,
                                  height=400,
                                  top=50,
                                  left=50,
                                  prefix=u'http://127.0.0.1',
                                  cookie_string=b'',
                                  timeout=30)
        self._validate_render_pixels(output, top=50, left=50)

    def test_cookie_render_with_wrong_cookie(self):
        with utils.FlaskApp() as app:
            prefix = u'http://127.0.0.1:' + str(app.port)
            output = _dom2img._render(content=utils.html_doc(app.port),
                                      width=600,
                                      height=400,
                                      top=0,
                                      left=0,
                                      prefix=prefix,
                                      cookie_string=b'key=val2',
                                      timeout=30)
            self._validate_render_pixels(output)

    def test_cookie_render(self):
        with utils.FlaskApp() as app:
            prefix = u'http://127.0.0.1:' + str(app.port)
            output = _dom2img._render(content=utils.html_doc(app.port),
                                      width=600,
                                      height=400,
                                      top=0,
                                      left=0,
                                      prefix=prefix,
                                      cookie_string=b'key=val',
                                      timeout=30)
            self._validate_render_pixels(output, div_color=(0, 0, 0))

    def test_cookie_render_wrong_cookie_domain(self):
        with utils.FlaskApp() as app:
            prefix = u'http://example.com/'
            output = _dom2img._render(content=utils.html_doc(app.port),
                                      width=600,
                                      height=400,
                                      top=0,
                                      left=0,
                                      prefix=prefix,
                                      cookie_string=b'key=val',
                                      timeout=30)
            self._validate_render_pixels(output)

    def test_crashy_render(self):
        killer_should_stop = [False]
        threading.Thread(target=utils.killer,
                         args=[os.getpid(), killer_should_stop]).start()

        err_msg = u'PhantomJS failed with status -' + \
            str(signal.SIGKILL) + '.*'
        try:
            kwargs = {'content': b'',
                      'width': 100,
                      'height': 200,
                      'top': 0,
                      'left': 0,
                      'prefix': u'',
                      'cookie_string': b'',
                      'timeout': 30}
            self.assertRaisesRegexp(_exceptions.PhantomJSFailure,
                                    err_msg, _dom2img._render,
                                    **kwargs)
        finally:
            killer_should_stop[0] = True

    def test_crash_collects_stderr(self):
        script = u'''
#!/bin/sh
echo ERRÖR 1>&2
exit 1
'''.encode('utf-8')
        with utils.mock_phantom_js_binary(script):
            kwargs = {'content': b'',
                      'width': 600,
                      'height': 400,
                      'top': 0,
                      'left': 0,
                      'prefix': u'http://127.0.0.1/',
                      'cookie_string': b'',
                      'timeout': 30}
            err_msg = \
                u'PhantomJS failed with status 1, and stderr output:\n' + \
                u'ERRR\n'
            self.assertRaisesRegexp(_exceptions.PhantomJSFailure,
                                    err_msg, _dom2img._render,
                                    **kwargs)

    def test_timeout(self):
        with utils.FlaskApp() as app:
            kwargs = {'content': utils.freezing_html_doc(app.port),
                      'width': 600,
                      'height': 400,
                      'top': 0,
                      'left': 0,
                      'prefix': u'http://127.0.0.1/',
                      'cookie_string': b'',
                      'timeout': 1}
            self.assertRaisesRegexp(_exceptions.PhantomJSTimeout,
                                    u'', _dom2img._render,
                                    **kwargs)


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


class Dom2ImgExceptionsMixin(object):

    def _make_kwargs(self, port):
        return {'content': utils.html_doc(port),
                'width': 200,
                'height': 200,
                'top': 0,
                'left': 0,
                'scale': 100,
                'prefix': u'http://example.com/',
                'cookies': 'key=val'}

    def _check_exception(self, err_msg, arg, val, exc=None):
        with utils.FlaskApp() as app:
            kwargs = self._make_kwargs(app.port)
            if arg is not None:
                kwargs[arg] = val
            if exc is not None:
                kwargs['exc'] = exc
            super(Dom2ImgExceptionsMixin, self)._check_exception(
                err_msg, **kwargs)

    def test_content_wrong_type(self):
        err_msg = u'content must be %s or %s, not []'
        err_msg = err_msg % (_compat.text.__name__, bytes.__name__)
        self._check_exception(err_msg, 'content', [], exc=TypeError)

    def test_width_wrong_type(self):
        err_msg = u'width must be %s, %s or int, not None'
        err_msg = err_msg % (_compat.text.__name__, bytes.__name__)
        self._check_exception(err_msg, 'width', None, exc=TypeError)

    def test_width_non_ascii_unicode(self):
        err_msg = u'invalid value for width: föö'
        self._check_exception(err_msg, 'width', u'föö')

    def test_width_unparseable(self):
        err_msg = u"invalid value for width: b'1.5'"
        self._check_exception(err_msg, 'width', b'1.5')

    def test_width_negative(self):
        err_msg = u'unexpected negative integer for width: -1'
        self._check_exception(err_msg, 'width', -1)

    def test_height_wrong_type(self):
        err_msg = u'height must be %s, %s or int, not None'
        err_msg = err_msg % (_compat.text.__name__, bytes.__name__)
        self._check_exception(err_msg, 'height', None, exc=TypeError)

    def test_height_non_ascii_unicode(self):
        err_msg = u'invalid value for height: föö'
        self._check_exception(err_msg, 'height', u'föö')

    def test_height_unparseable(self):
        err_msg = u"invalid value for height: b'1.5'"
        self._check_exception(err_msg, 'height', b'1.5')

    def test_height_negative(self):
        err_msg = u'unexpected negative integer for height: -1'
        self._check_exception(err_msg, 'height', -1)

    def test_top_wrong_type(self):
        err_msg = u'top must be %s, %s or int, not None'
        err_msg = err_msg % (_compat.text.__name__, bytes.__name__)
        self._check_exception(err_msg, 'top', None, exc=TypeError)

    def test_top_non_ascii_unicode(self):
        err_msg = u'invalid value for top: föö'
        self._check_exception(err_msg, 'top', u'föö')

    def test_top_unparseable(self):
        err_msg = u"invalid value for top: b'1.5'"
        self._check_exception(err_msg, 'top', b'1.5')

    def test_top_negative(self):
        err_msg = u'unexpected negative integer for top: -1'
        self._check_exception(err_msg, 'top', -1)

    def test_left_wrong_type(self):
        err_msg = u'left must be %s, %s or int, not None'
        err_msg = err_msg % (_compat.text.__name__, bytes.__name__)
        self._check_exception(err_msg, 'left', None, exc=TypeError)

    def test_left_non_ascii_unicode(self):
        err_msg = u'invalid value for left: föö'
        self._check_exception(err_msg, 'left', u'föö')

    def test_left_unparseable(self):
        err_msg = u"invalid value for left: b'1.5'"
        self._check_exception(err_msg, 'left', b'1.5')

    def test_left_negative(self):
        err_msg = u'unexpected negative integer for left: -1'
        self._check_exception(err_msg, 'left', -1)

    def test_scale_wrong_type(self):
        err_msg = u'scale must be %s, %s or int, not None'
        err_msg = err_msg % (_compat.text.__name__, bytes.__name__)
        self._check_exception(err_msg, 'scale', None, exc=TypeError)

    def test_scale_non_ascii_unicode(self):
        err_msg = u'invalid value for scale: föö'
        self._check_exception(err_msg, 'scale', u'föö')

    def test_scale_unparseable(self):
        err_msg = u"invalid value for scale: b'1.5'"
        self._check_exception(err_msg, 'scale', b'1.5')

    def test_scale_negative(self):
        err_msg = u'unexpected negative integer for scale: -1'
        self._check_exception(err_msg, 'scale', -1)

    def test_prefix_non_ascii_unicode(self):
        err_msg = u'invalid, non ascii-only value for prefix: ' + \
            u'http://example.com/föö'
        self._check_exception(err_msg, 'prefix', u'http://example.com/föö')

    def test_prefix_wrong_type(self):
        err_msg = u'prefix must be %s or %s, not None'
        err_msg = err_msg % (_compat.text.__name__, bytes.__name__)
        self._check_exception(err_msg, 'prefix', None, exc=TypeError)

    def test_prefix_non_absolute_url(self):
        err_msg = u'invalid, non-absolute URL value for prefix: example.com'
        self._check_exception(err_msg, 'prefix',
                              u'example.com', exc=ValueError)
        err_msg = u'invalid, non-absolute URL value for prefix: example.com/'
        self._check_exception(err_msg, 'prefix',
                              u'example.com/', exc=ValueError)
        err_msg = u'invalid, non-absolute URL value for prefix: //example.com'
        self._check_exception(err_msg, 'prefix',
                              u'//example.com', exc=ValueError)

    def test_cookies_wrong_type(self):
        err_msg = u'cookies must be %s, %s, %s or %s, not 7'
        err_msg = err_msg % (_compat.text.__name__, bytes.__name__,
                             type(None).__name__, dict.__name__)
        self._check_exception(err_msg, 'cookies', 7, exc=TypeError)

    def test_cookies_non_ascii_unicode(self):
        self._check_exception(u'unicode cookies must be ascii-only',
                              'cookies', u'föö')

    def test_cookies_key_values_non_ascii_unicode(self):
        self._check_exception(u'cookies keys/values must be ascii-only',
                              'cookies', {u'föö': u'bär'.encode('utf-8')})

    def test_cookies_key_values_wrong_type(self):
        self._check_exception(u'cookies key/values must be strings',
                              'cookies', {u'foo': []}, exc=TypeError)
        self._check_exception(u'cookies key/values must be strings',
                              'cookies', {3: b'bar'}, exc=TypeError)

    def test_cookies_key_with_equals_char(self):
        self._check_exception(u"cookies keys cannot use '=' character",
                              'cookies', {u'f=o': b'bar'})

    def test_cookies_key_values_with_semicolon(self):
        self._check_exception(u"cookies keys/values cannot use ';' character",
                              'cookies', {u'f;o': b'bar'})
        self._check_exception(u"cookies keys/values cannot use ';' character",
                              'cookies', {u'foo': b'b;r'})

    def test_phantomjs_not_in_path(self):
        old_path = os.environ['PATH']
        os.environ['PATH'] = ''
        try:
            self._check_exception(u"Couldn't find phantomjs binary in $PATH",
                                  None, None, _exceptions.PhantomJSNotInPath)
        finally:
            os.environ['PATH'] = old_path


class Dom2ImgTest(Dom2ImgExceptionsMixin, utils.TestCase):

    FUN = _dom2img.dom2img
    EXC = ValueError

    def test_complex(self):
        # override _resize to use 'nearest' resize filter
        # to make unit testing possible
        old_resize = _dom2img._resize

        def _new_resize(img_string, scale):
            return old_resize(img_string, scale, Image.NEAREST)

        with utils.MonkeyPatch(_dom2img, '_resize', _new_resize):
            with utils.FlaskApp() as app:
                port = app.port
                prefix = utils.prefix_for_port(port)
                output = _dom2img.dom2img(content=utils.html_doc(port),
                                          width=600,
                                          height=400,
                                          top=50,
                                          left=50,
                                          scale=50,
                                          prefix=prefix,
                                          cookies=b'key=val',
                                          timeout=30)
                self._validate_render_pixels(output, left=50, top=50, scale=.5,
                                             div_color=(0, 0, 0))

    def _check_images(self, arg, val1, val2):
        with utils.FlaskApp() as app:
            self._check_results(self._make_kwargs(app.port), arg, val1, val2)

    def test_content_gets_decoded_properly(self):
        content = u'<html>fööbär</html>'
        self._check_images('content', content, content.encode('utf-8'))

    def test_width_gets_parsed_properly(self):
        self._check_images('width', 100, b'100')
        self._check_images('width', 100, u'100')

    def test_height_gets_parsed_properly(self):
        self._check_images('height', 200, b'200')
        self._check_images('height', 200, u'200')

    def test_top_gets_parsed_properly(self):
        self._check_images('top', 30, b'30')
        self._check_images('top', 30, u'30')

    def test_left_gets_parsed_properly(self):
        self._check_images('left', 40, b'40')
        self._check_images('left', 40, u'40')

    def test_scale_gets_parsed_properly(self):
        self._check_images('scale', 50, b'50')
        self._check_images('scale', 50, u'50')

    def test_prefix_gets_parsed_properly(self):
        with utils.FlaskApp() as app:
            prefix1 = \
                b'http://127.0.0.1:' + str(app.port).encode('utf-8') + b'/'
            prefix2 = prefix1.decode('utf-8')
            self._check_results(self._make_kwargs(app.port),
                                'prefix', prefix1, prefix2)

    def test_empty_cookies_get_serialized_properly(self):
        self._check_images('cookies', b'', u'')
        self._check_images('cookies', b'', None)
        self._check_images('cookies', b'', {})

    def test_non_empty_cookies_get_serialized_properly(self):
        self._check_images('cookies', b'key=val', u'key=val')
        self._check_images('cookies', {b'key': b'val'}, {u'key': u'val'})
        self._check_images('cookies', {b'key': u'val'}, {u'key': b'val'})

    def test_crashy_phantomjs(self):
        killer_should_stop = [False]
        threading.Thread(target=utils.killer,
                         args=[os.getpid(), killer_should_stop]).start()

        err_msg = u'PhantomJS failed with status -' + \
            str(signal.SIGKILL) + '.*'
        try:
            kwargs = {'content': b'',
                      'width': 100,
                      'height': 200,
                      'prefix': b'http://example.com/',
                      'cookies': {}}
            self.assertRaisesRegexp(_exceptions.PhantomJSFailure,
                                    err_msg, _dom2img.dom2img,
                                    **kwargs)
        finally:
            killer_should_stop[0] = True

    def test_crash_collects_stderr(self):
        script = u'''
#!/bin/sh
echo ERRÖR 1>&2
exit 1
'''.encode('utf-8')
        with utils.mock_phantom_js_binary(script):
            kwargs = {'content': b'',
                      'width': 600,
                      'height': 400,
                      'prefix': b'http://example.com/',
                      'cookies': {}}
            err_msg = \
                u'PhantomJS failed with status 1, and stderr output:\n' + \
                u'ERRR\n'
            self.assertRaisesRegexp(_exceptions.PhantomJSFailure,
                                    err_msg, _dom2img.dom2img,
                                    **kwargs)

    def test_timeout(self):
        with utils.FlaskApp() as app:
            prefix = utils.prefix_for_port(app.port)
            kwargs = {'content': utils.freezing_html_doc(app.port),
                      'width': 600,
                      'height': 400,
                      'prefix': prefix,
                      'timeout': 1}
            self.assertRaisesRegexp(_exceptions.PhantomJSTimeout,
                                    u'', _dom2img.dom2img,
                                    **kwargs)


class Dom2ImgDebugTest(Dom2ImgExceptionsMixin, utils.TestCase):

    FUN = _dom2img.dom2img_debug
    EXC = ValueError

    def test(self):
        result = _dom2img.dom2img_debug(content=b'<html></html>',
                                        width=800,
                                        height=600,
                                        prefix=b'http://example.com/',
                                        top=50,
                                        left=25,
                                        scale=75,
                                        cookies=b'key1=val1;key2=val2')
        self.assertTrue(isinstance(result, _compat.text))

        content_path = result.split()[-1]
        with open(content_path, 'rb') as f:
            content = f.read()

        output = utils.read_process_until_line(
            result, b'Please follow the instructions:\n')

        os.remove(content_path)

        self.assertTrue(b'Viewport size: 800x600' in output)
        self.assertTrue(b'Scroll offsets (left:top): 25:50' in output)
        self.assertTrue(b'Cookie domain: example.com' in output)
        self.assertTrue(b'key1: val1' in output)
        self.assertTrue(b'key2: val2' in output)
        self.assertEqual(content, b'<html>\n</html>')
