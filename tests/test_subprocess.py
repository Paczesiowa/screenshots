import tests.utils as utils
import time

from dom2img import _subprocess

import subprocess


class SubprocessTest(utils.TestCase):

    FUN = _subprocess.communicate_with_timeout

    def _popen(self, *args):
        python_with_args = ('python', '-c') + args
        return subprocess.Popen(python_with_args,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

    def _sleep_prog(self):
        prog = b'''
import os
import sys
import time
time.sleep(2)
os.write(sys.stdout.fileno(), b'good sleep')
'''
        return self._popen(prog)

    def test_stdout(self):
        proc = self._popen('''
import os
import sys
os.write(sys.stdout.fileno(), b'hello')
''')
        self._check_result((b'hello', b''), proc, 30)

    def test_stderr(self):
        proc = self._popen('''
import os
import sys
os.write(sys.stderr.fileno(), b':-(')
''')
        self._check_result((b'', b':-('), proc, 30)

    def test_timeout_kill(self):
        self._check_result(None, self._sleep_prog(), 1)

    def test_timeout_kill_elapsed_time(self):
        proc = self._sleep_prog()

        start = time.time()
        _subprocess.communicate_with_timeout(proc, 1)
        stop = time.time()
        elapsed_time = int(round(stop - start))
        self.assertEqual(elapsed_time, 1)

    def test_timeout_no_kill_elapsed_time(self):
        proc = self._sleep_prog()

        start = time.time()
        _subprocess.communicate_with_timeout(proc, 3)
        stop = time.time()
        elapsed_time = int(round(stop - start))
        self.assertEqual(elapsed_time, 2)
