"""
API Wrapper for downloading (and playing) text-to-speech results out of VoiceRSS API (https://www.voicerss.org/api/)
A valid api key (free to get) is needed.

There's a limit of 350 requests per day, and each request can only convert up to 100kb of text, which corresponds
roughly to 25000 characters (depending on the encoding).

Requirements: requests, playsound.
"""
import os

import requests
import playsound


class TTSReader:
    """ Download and play text-to-speech results out of VoiceRSS API (https://www.voicerss.org/api/). """
    _API_URL = 'https://api.voicerss.org'
    _POSSIBLE_ERRORS = [
        'The account is inactive!',
        'The subscription is expired or requests count limitation is exceeded!',
        'The request content length is too large!',
        'The language does not support!',
        'The language is not specified!',
        'The text is not specified!',
        'The API key is not available!',
        'The API key is not specified!',
        'The subscription does not support SSML!'
    ]

    def __init__(self, api_key: str, *, lang: str = 'en-us', fmt: str = '16khz_16bit_mono', txt_max_size: int = 25000):
        """
        :param api_key: Valid api key for VoiceRSS API
        :param lang: Valid language for text. Default: en-us (https://www.voicerss.org/api)
        :param fmt: Valid format for audio. Default: 16khz_16bit_mono (https://www.voicerss.org/api)
        :param txt_max_size: Max char length for text, should be roughly 100kb. Default: 25000
        """
        self._api_key = api_key
        self._lang = lang
        self._fmt = fmt
        self._txt_max_size = txt_max_size

    def download_and_read(self, text: str, *, filepath: str = '', delete_after_read: bool = True) -> None:
        """
        Call VoiceRSS API then use playsound to play output. Then delete file unless delete_after_read is passed in
        with False.

        :param text: Text for the API. Must be smaller than txt_max_size
        :param filepath: Filepath for the file. Default: temp.wav on cwd.
        :param delete_after_read: Delete file after reading. Default: True
        :raises TextTooLong: If text is bigger than self._txt_max_size
        :raises InvalidStatusCode: If site returns other than 200
        :raises APIError: If site returns an API Error in TTSReader._POSSIBLE_ERRORS
        """
        filepath = self.download(text, "temp" if not filepath else filepath)
        self.read_aloud(filepath)
        if delete_after_read and os.path.exists(filepath):
            os.remove(filepath)

    @staticmethod
    def read_aloud(filepath: str) -> None:
        """
        Use playsound to play filepath.
        :param filepath: Valid path for the .wav file. Adds .wav to ending if it is not passed in the filepath.
        """
        if not filepath.lower().endswith('.wav'):
            filepath += '.wav'

        playsound.playsound(filepath)

    def download(self, text: str, filepath: str) -> str:
        """
        Call VoiceRSS API and save output on disk.

        :param text: Text for the API
        :param filepath: Filepath for the .wav file
        :raises TextTooLong: If text is bigger than txt_max_size
        :raises InvalidStatusCode: If site returns other than 200
        :raises APIError: If site returns an API Error in TTSReader._POSSIBLE_ERRORS
        :returns filepath: Final filepath for .wav file
        """
        if len(text) > self._txt_max_size:
            raise TTSReader.TextTooLong(len(text))

        data = {'key': self._api_key, 'src': text, 'hl': self._lang, 'f': self._fmt}
        r = requests.post(TTSReader._API_URL, data=data)

        if r.status_code != 200:
            raise TTSReader.InvalidStatusCode(r.status_code)

        for error in TTSReader._POSSIBLE_ERRORS:
            if error in r.text:
                raise TTSReader.APIError(error)

        filepath = f'{filepath}.wav' if not filepath.endswith('.wav') else filepath
        with open(filepath, 'wb') as w_file:
            w_file.write(r.content)

        return filepath

    class TTSReaderError(Exception):
        """ Base TTSReader exception """

    class InvalidStatusCode(TTSReaderError):
        """ API returned other than 200 """

    class APIError(TTSReaderError):
        """ API returned an error """

    class TextTooLong(TTSReaderError):
        """ The text inputted to download is too large """
