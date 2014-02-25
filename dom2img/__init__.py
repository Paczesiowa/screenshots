import pkg_resources

try:
    __version__ = pkg_resources.require('dom2img')[0].version
except pkg_resources.DistributionNotFound:
    __version__ = 'dev'
