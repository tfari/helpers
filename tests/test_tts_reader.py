""" Tests for TTSReader. Some tests should be checked by hand (the ones that check reading). """
import os
from unittest import TestCase, mock
from helpers.tts_reader import TTSReader

API_KEY = ''  # Set this before testing.

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
        t.download_and_read('Test download and read.', filepath='test')
        self.assertFalse(os.path.exists('test.wav'))

    def test_download_and_read_non_delete_after_read(self):
        t = TTSReader(api_key=API_KEY)
        t.download_and_read('Test download and read non-delete after read.', filepath='test', delete_after_read=False)
        self.assertTrue(os.path.exists('test.wav'))
        os.remove('test.wav')
