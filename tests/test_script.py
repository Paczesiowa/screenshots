# coding=utf-8
import itertools
import os
import random
import signal
import threading

import tests.utils as utils


def serialize_args_for_dom2img_script(kwargs_list):
    args = ['python', 'dom2img/_script.py']
    for key, val in kwargs_list:
        if val and isinstance(val, bytes):
            val = val.decode('ascii')
        args.append('--' + key + ('=' + str(val) if val else ''))
    return args


def dom2img_script(input_, kwargs_list):
    args = serialize_args_for_dom2img_script(kwargs_list)
    return utils.call_script(args, input_)


class ScriptTest(utils.TestCase):

    ARGS = [('width', 600),
            ('height', 400),
            ('top', 50),
            ('left', 50),
            ('scale', 100),
            ('prefix', b'http://example.com/'),
            ('timeout', b'30'),
            ('cookies', b'key=val')]

    def _test_with_args(self, port, args):
        for i, (key, val) in enumerate(args):
            if key == 'prefix':
                args[i] = (key, utils.prefix_for_port(port))
        return dom2img_script(utils.html_doc(port), args)

    def _check_output(self, port, args, div_color=(0, 0, 0)):
        output = self._test_with_args(port, args)[0]
        self._validate_render_pixels(output, left=50, top=50,
                                     div_color=div_color)

    def test_complex(self):
        with utils.FlaskApp() as app:
            self._check_output(app.port, list(self.ARGS))

    def test_permuted_args(self):
        all_permutations = list(itertools.permutations(self.ARGS))
        random.shuffle(all_permutations)
        with utils.FlaskApp() as app:
            for permuted_args in all_permutations[:2]:
                self._check_output(app.port, list(permuted_args))

    def test_script_usage(self):
        result = dom2img_script('', [('help', None)])
        self.assertTrue(b'usage' in result[0])
        self.assertEqual(result[1], b'')
        self.assertEqual(result[2], 0)

    def test_script_missing_arg(self):
        for arg_to_skip in ['height', 'width', 'prefix']:
            args = list(self.ARGS)
            for i, (arg, _) in enumerate(args):
                if arg == arg_to_skip:
                    args.pop(i)
            result = dom2img_script('', args)
            self.assertTrue(b'usage' in result[1])
            self.assertEqual(result[0], b'')
            self.assertEqual(result[2], 1)

    def test_optional_cookies_param(self):
        args = list(self.ARGS)
        for i, (arg, _) in enumerate(args):
            if arg == 'cookies':
                args.pop(i)
        with utils.FlaskApp() as app:
            self._check_output(app.port, args, div_color=(255, 0, 0))

    def test_crash(self):
        args = serialize_args_for_dom2img_script(self.ARGS)
        proc = utils.start_script(args)

        killer_should_stop = [False]
        threading.Thread(target=utils.killer,
                         args=[proc.pid, killer_should_stop]).start()

        stdout, stderr = proc.communicate(b'')
        try:
            self.assertEqual(stdout, b'')
            self.assertEqual(stderr,
                             b'PhantomJS failed with status -' +
                             str(signal.SIGKILL).encode('ascii') + b'\n')
            self.assertEqual(proc.returncode, 2)
        finally:
            killer_should_stop[0] = True

    def test_crash2(self):
        script = u'''
#!/bin/sh
echo -n ERRÖR 1>&2
exit 1
'''.encode('utf-8')
        with utils.mock_phantom_js_binary(script):
            args = list(self.ARGS)
            result = dom2img_script('', args)
            err_msg = \
                b'PhantomJS failed with status 1, and stderr output:\n' + \
                b'ERRR\n'
            self.assertEqual(result[1], err_msg)
            self.assertEqual(result[0], b'')
            self.assertEqual(result[2], 2)

    def test_timeout(self):
        with utils.FlaskApp() as app:
            args = dict(self.ARGS)
            args['prefix'] = utils.prefix_for_port(app.port)
            args['timeout'] = b'1'
            result = dom2img_script(utils.freezing_html_doc(app.port),
                                    args.items())
            err_msg = b'PhantomJS process has been killed, ' + \
                b'because it took longer than 1 seconds to finish\n'
            self.assertEqual(result[1], err_msg)
            self.assertEqual(result[0], b'')
            self.assertEqual(result[2], 3)

    def test_debug(self):
        args = list(self.ARGS) + [('debug', None)]
        stdout, stderr, retcode = dom2img_script(b'<html></html>', args)
        self.assertEqual(stderr, b'')
        self.assertEqual(retcode, 0)

        self.assertTrue(isinstance(stdout, bytes))

        content_path = stdout.split()[-1]
        with open(content_path, 'rb') as f:
            content = f.read()

        output = utils.read_process_until_line(
            stdout, b'Please follow the instructions:\n')

        os.remove(content_path)

        self.assertTrue(b'Viewport size: 600x400' in output)
        self.assertTrue(b'Scroll offsets (left:top): 50:50' in output)
        self.assertTrue(b'Cookie domain: example.com' in output)
        self.assertTrue(b'key: val' in output)
        self.assertEqual(content, b'<html>\n</html>')
