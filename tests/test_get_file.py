""" Tests for get_file """
import os
import requests
from unittest import TestCase, mock
from helpers.get_file import get_file


class TestGetFile(TestCase):
    def test_get_file(self):
        r = requests.get('http://example.org')
        get_file('', 'test.html', 'http://example.org')
        with open('test.html', 'r', encoding='utf-8') as r_file:
            self.assertEqual(r.text, r_file.read())

        os.remove('test.html')
