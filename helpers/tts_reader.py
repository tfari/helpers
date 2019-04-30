import requests
import playsound
import os
import threading

"""
API Wrapper for downloading (and playing) text-to-speech results out of Voice RSS Api.
A valid api key (free to get) is needed.
There's a limit of 350 requests per day, and each request can only convert up to 100kb of text.  
This corresponds roughly to 25000 characters, depending encoding.

"""

API_KEY = None


def dl_tts(filename, index, text, language='en-us', api_key=API_KEY, fmt='16khz_16bit_stereo'):
    """
    Make an API request to TTS and save as filenameindex.wav

    :raises Connectivity Error
    :raises APIError

    :param filename: str, filename
    :param index: int, part index
    :param text: str, text to transform into speech
    :param language:str, language to use
    :param api_key:str, valid TTS Api Key
    :param fmt: str, format to download
    :return: None
    """
    possible_errors = ['The account is inactive!',
                       'The subscription is expired or requests count limitation is exceeded!',
                       'The request content length is too large!',
                       'The language does not support!',
                       'The language is not specified!',
                       'The text is not specified!',
                       'The API key is not available!',
                       'The API key is not specified!',
                       'The subscription does not support SSML!']

    # Make request
    data = {'key': api_key, 'src': text, 'hl': language, 'f': fmt}
    r = requests.post('http://api.voicerss.org', data=data)

    # Error checking
    if r.status_code != 200:
        raise ConnectivityError()

    for error in possible_errors:
        if r.text.find(error) != -1:
            raise APIError(error)

    # Save file
    with open('%s%s.wav' % (filename, index), 'wb') as f:
        f.write(r.content)
    f.close()


def _read_aloud(index):
    """
    Reads temporary files aloud

    :param index: int, index
    :return: None
    """
    playsound.playsound('tmp%s.wav' % index)


def read_tts_single(text, language='en-us', api_key=API_KEY, fmt='16khz_16bit_stereo'):
    """
    Gets a speech version of a text, then plays it

    :param text: str, text to transform into speech
    :param language: language:str, language to use
    :param api_key:str, valid TTS Api Key
    :param fmt: str, format to download
    :return: None
    """

    # Try to delete previous temp file
    try:
        os.remove('tmp0.wav')
    except FileNotFoundError:
        pass

    # Error Checking
    if not API_KEY:
        raise NoApiKey()
    if len(text) > 25000:
        raise TooLarge()

    #
    dl_tts('tmp', 0, text, language, api_key, fmt)
    _read_aloud(0)


def dl_tts_multiple(filename, pages, language='en-us', api_key=API_KEY, fmt='16khz_16bit_stereo'):
    """
    Download big, multi-file/page texts into speech

    :param filename: str, filename
    :param pages: list of str, texts to transform into speech, each str will be saved in a different part
    :param language: language:str, language to use
    :param api_key:str, valid TTS Api Key
    :param fmt: str, format to download
    :return: None
    """
    # Error checking
    if not API_KEY:
        raise NoApiKey()

    for page in pages:
        if len(page) > 25000:
            raise TooLarge()

    # Create a thread for each page
    threads = []
    count = 0
    for page in pages:
        t = threading.Thread(target=dl_tts, args=(filename, count, page, language, api_key, fmt))
        threads.append(t)
        count += 1

    # Deploy threads
    for t in threads:
        t.start()

    # Wait for them to return
    for t in threads:
        t.join()

    print("[*] Finished downloading %s" % filename)


# Exceptions


class NoApiKey(Exception):
    pass


class TooLarge(Exception):
    pass


class ConnectivityError(Exception):
    pass


class APIError(Exception):
    pass
