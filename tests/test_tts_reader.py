""" Tests for TTSReader. Some tests should be checked by hand (the ones that check reading). """
import os
import json
from unittest import TestCase
from helpers.tts_reader import TTSReader

# Set this before testing, or use a _keys_for_test.json file: {"test_tts_reader": {"api_key": API_KEY}}
API_KEY = ''

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(f'{SCRIPT_PATH}/_keys_for_tests.json'):
    with open(f'{SCRIPT_PATH}/_keys_for_tests.json', 'r', encoding='utf-8') as r_file:
        API_KEY = json.load(r_file)['test_tts_reader']['api_key']

class TestTTSReader(TestCase):
    def test_download_raises_TextTooLong(self):
        t = TTSReader(api_key=API_KEY, txt_max_size=1)
        self.assertRaises(TTSReader.TextTooLong, t.download, 'Test', filepath='Test')

    def test_download_raises_InvalidStatusCode(self):
        t = TTSReader(api_key=API_KEY)
        temp = TTSReader._API_URL
        TTSReader._API_URL = 'http://example.org/doesnt_exit'
        self.assertRaises(TTSReader.InvalidStatusCode, t.download, 'Test', filepath='Test')
        TTSReader._API_URL = temp

    def test_download_raises_APIError(self):
        t = TTSReader(api_key='666')
        self.assertRaises(TTSReader.APIError, t.download, 'Test', filepath='Test')

    def test_download(self):
        t = TTSReader(api_key=API_KEY)
        t.download('Test', filepath='test')
        self.assertTrue(os.path.exists('test.wav'))
        os.remove('test.wav')

    def test_read_aloud(self):
        t = TTSReader(api_key=API_KEY)
        t.download('Test read aloud passed.', filepath='test')
        t.read_aloud('test')
        os.remove('test.wav')

    def test_download_and_read(self):
        t = TTSReader(api_key=API_KEY)
        t.download_and_read('Test download and read passed.', filepath='test')
        self.assertFalse(os.path.exists('test.wav'))

    def test_download_and_read_non_delete_after_read(self):
        t = TTSReader(api_key=API_KEY)
        t.download_and_read('Test download and read non-delete after read.', filepath='test', delete_after_read=False)
        self.assertTrue(os.path.exists('test.wav'))
        os.remove('test.wav')
