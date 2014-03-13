from __future__ import print_function

import sys
import os
import argparse
from dom2img import _cookies, _dom2img, _arg_utils


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--width', type=int,
                        help='non-negative int with the width ' +
                        'of virtual render viewport (using pixels unit)')
    args = parser.parse_args()
    print(args)
    sys.exit(0)
    if len(sys.argv) < 7 or len(sys.argv) > 8 or '--help' in sys.argv:
        print('Render html using PhantomJS.')
        print('usage:', sys.argv[0], 'height width top left scale prefix',
              end='')
        print('[cookie_string] < file.html')
        print('''
Parameters:
* width - string containing non-negative int with
          the width of virtual render viewport (using pixels unit)
* height - string containing non-negative int with
           the height of virtual render viewport (using pixels unit)
* top - string containing non-negative int with
        offset from the top of the page that should be rendered
        (using pixels unit)
* left - string containing non-negative int with
         offset from the left border of the page that should be rendered
         (using pixels unit)
* scale - string containing non-negative int with percentage number
          that the screenshot will be scaled to (50 means half the
          original size)
* prefix - string containing absolute urls that will be used
           to handle relative urls in html (for images, css scripts)
           and optionally for cookies
* cookie_string - semicolon-separated string containing cookie elems
                  using key=val format

Returns on stdout string containing png image with the screenshot.

Return status can be:
0: success
1: if arguments are in improper format''')
        sys.exit(1)

    content = sys.stdin.read()
    width = sys.argv[1]
    height = sys.argv[2]
    top = sys.argv[3]
    left = sys.argv[4]
    scale = sys.argv[5]
    prefix = sys.argv[6]
    if len(sys.argv) == 8:
        cookie_string = sys.argv[7]
        cookies = _cookies.parse_cookie_string(cookie_string)
    else:
        cookies = None

    try:
        result = _dom2img.dom2img(content=content,
                                  width=width,
                                  height=height,
                                  top=top,
                                  left=left,
                                  scale=scale,
                                  prefix=prefix,
                                  cookies=cookies)
        os.write(sys.stdout.fileno(), result)
    except _arg_utils.Dom2ImgArgumentException as e:
        print(e, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
