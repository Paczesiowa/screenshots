# coding=utf-8
import pkg_resources

from dom2img import _dom2img, _exceptions


try:
    __version__ = pkg_resources.require('dom2img')[0].version
except pkg_resources.DistributionNotFound:
    __version__ = 'dev'


__author__ = 'Bartek Ćwikłowski <paczesiowa@gmail.com>'


dom2img = _dom2img.dom2img
dom2img_debug = _dom2img.dom2img_debug
Dom2ImgError = _exceptions.Dom2ImgError
PhantomJSFailure = _exceptions.PhantomJSFailure
PhantomJSTimeout = _exceptions.PhantomJSTimeout
__all__ = ['dom2img', 'dom2img_debug', 'Dom2ImgError',
           'PhantomJSFailure', 'PhantomJSTimeout']
