from __future__ import print_function

import sys
import os
import argparse
from dom2img import _cookies, _dom2img, _arg_utils
import dom2img


def foo(s):
    raise ValueError('dupa')


def main():
    prolog = '''Render html using PhantomJS.

UTF-8 encoded HTML is taken from stdin.

Returns on stdout string containing png image with the screenshot.

Return status can be:
0: success
2: if arguments are in improper format
'''
    formatter = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=prolog,
                                     formatter_class=formatter)

    parser.add_argument('--width', type=_arg_utils.non_negative_int,
                        required=True,
                        help='non-negative int with the width ' +
                        'of virtual render viewport (using pixels unit)')
    parser.add_argument('--height', type=_arg_utils.non_negative_int,
                        required=True,
                        help='non-negative int with the height ' +
                        'of virtual render viewport (using pixels unit)')
    parser.add_argument('--prefix', type=_arg_utils.absolute_url,
                        required=True,
                        help='absolute url that will be used to handle ' +
                        'relative urls in html (for images, css scripts) ' +
                        'and optionally for cookies')
    parser.add_argument('--top', type=_arg_utils.non_negative_int,
                        default='0',
                        help='non-negative int with offset from the top of ' +
                        'the page that should be rendered of virtual ' +
                        'render viewport (using pixels unit)')
    parser.add_argument('--left', type=_arg_utils.non_negative_int,
                        default='0',
                        help='non-negative int with offset from the left ' +
                        'border of the page that should be rendered ' +
                        'of virtual render viewport (using pixels unit)')
    parser.add_argument('--scale', type=_arg_utils.non_negative_int,
                        default='100',
                        help='non-negative int with percentage number ' +
                        'that the screenshot will be scaled to ' +
                        '(50 means half the original size)')
    parser.add_argument('--cookies', type=_cookies.parse_cookie_string,
                        default='',
                        help='semicolon-separated string containing ' +
                        'cookie elems using key=val format')
    parser.add_argument('-v', '-V', '--version', action='version',
                        version='%(prog)s ' + dom2img.__version__)

    args = vars(parser.parse_args())
    args['content'] = sys.stdin.read()

    result = _dom2img.dom2img(**args)
    os.write(sys.stdout.fileno(), result)

if __name__ == '__main__':
    main()
