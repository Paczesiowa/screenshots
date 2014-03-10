# coding=utf-8
import StringIO
import multiprocessing
import unittest2

from PIL import Image
from bs4 import BeautifulSoup
from flask import Flask, request, Response

from dom2img import _script


class Dom2ImgTest(unittest2.TestCase):

    def test_script(self):
        pass
