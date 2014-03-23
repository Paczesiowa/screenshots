import pkg_resources
from dom2img import _dom2img

try:
    __version__ = pkg_resources.require('dom2img')[0].version
except pkg_resources.DistributionNotFound:
    __version__ = 'dev'


dom2img = _dom2img.dom2img
__all__ = ['dom2img']
