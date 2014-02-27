# -*- coding: utf-8 -*-
import sys
try:
    from setuptools import setup
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup


__version__ = '0.1'


tests_require = ['nose == 1.3.0', 'pillow == 2.3.0', 'flask == 0.10.1']
if sys.version_info < (3,):
    tests_require.append('unittest2 == 0.5.1')
else:
    tests_require.append('unittest2py3k == 0.5.1')


setup(name='dom2img',
      version=__version__,
      packages=['dom2img'],
      description='Library/script for rendering html to images.',
      long_description='''This project is meant to be used as a helper
for web application's backend to render website screenshots.

On the frontend side, dom2img.js library grabs info about currently displayed
html and sends it to a backend server, which can call this python library
(or shell script) to render html to an image/screenshot approximation.
Currently only PhantomJS renderer is supported.
''',
      author=u'Bartek Ćwikłowski',
      author_email='paczesiowa@gmail.com',
      url='https://github.com/Paczesiowa/dom2img',
      download_url=
          'http://github.com/Paczesiowa/dom2img/tarball/v' + __version__,
      classifiers=
          ['Development Status :: 3 - Alpha',
           'Intended Audience :: Developers',
           'License :: Public Domain',
           'Operating System :: POSIX',
           'Programming Language :: Python :: 2',
           'Programming Language :: Python :: 2.6',
           'Programming Language :: Python :: 2.7',
           'Programming Language :: Python :: 3',
           'Programming Language :: Python :: 3.3',
           'Programming Language :: Python :: Implementation :: CPython',
           'Topic :: Internet :: WWW/HTTP :: Browsers',
           'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
           'Topic :: Multimedia :: Graphics :: Capture :: Screen Capture',
           'Topic :: Text Processing :: Markup :: HTML'],
      license='UNLICENSE/Public Domain',
      keywords=['html', 'screenshot', 'phantomjs'],
      platforms=['Linux'],
      package_data={'dom2img': ['render_file.phantom.js']},
      zip_safe=True,
      install_requires='BeautifulSoup4 == 4.3.2',
      entry_points={'console_scripts': 'dom2img = dom2img:main'},
      test_suite='nose.collector',
      tests_require=tests_require)
