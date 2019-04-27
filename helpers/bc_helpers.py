import requests
import re
from bs4 import BeautifulSoup


# v 0.0.1


"""
Bandcamp related helper functions. 
"""


def is_valid_bandcamp_url(url):
    """
    :param url: str
    :return: True/False depending on if url is a valid Bandcamp URL
    """
    r = requests.get(url, allow_redirects=False)
    if r.status_code == 200:
        return True
    return False


def is_valid_username(username):
    """
    :param username: str
    :return: True/False depending on if url is a valid Bandcamp username
    """
    return is_valid_bandcamp_url('https://%s.bandcamp.com' % username)


def get_all_info(username):
    """
    Gets a list of relative links to all albums and tracks in username's Bandcamp profile
    :param username:
    :return:
    """
    r = requests.get('https://%s.bandcamp.com/music' % username)
    bs = BeautifulSoup(r.text, 'html.parser')
    regex = re.compile('.*music-grid-item .*')
    urls = []
    for a in bs.find_all("li", {"class": regex}):
            urls.append(a.find('a').get('href'))

    return urls


def get_album_info(username, album_relative_url):
    """
    :param username: str
    :param album_relative_url: str
    :return: dict. representation of album information
    """
    response = {}
    r = requests.get('https://%s.bandcamp.com%s' % (username, album_relative_url))
    bs = BeautifulSoup(r.text, 'html.parser')
    scripts = bs.findAll('script')
    for s in scripts:
        if str(s).find('var TralbumData') != -1:
            response['artist'] = re.findall('artist: ".*"', str(s))[0].split('"')[1]
            response['artist_avatar'] = re.findall('image_id: .*', str(s))[0].split(': ')[1]
            response['album_title'] = re.findall('album_title: ".*"', str(s))[0].split('"')[1]
            response['album_cover'] = re.findall('art_id: .*,', str(s))[0].split(': ')[1][:-1]
            response['track_info'] = eval(re.findall('trackinfo: .*', str(s))[0].split(': ')[1][:-1].
                                          replace('null', 'None').replace('false', 'False').replace('true', 'True'))
            try:
                response['album_release'] = eval(re.findall('current: .*', str(s))[0].split(': ')[1][:-1].
                                             replace('null', 'None').replace('false', 'False').
                                             replace('true', 'True'))['publish_date'].split(' ')[2]
            except SyntaxError:
                response['album_release'] = None

    return response


def get_track_info(username, track_relative_url):
    """
    :param username: str
    :param track_relative_url: str
    :return: dict. representation of track information
    """
    response = {}
    r = requests.get('https://%s.bandcamp.com%s' % (username, track_relative_url))
    bs = BeautifulSoup(r.text, 'html.parser')
    scripts = bs.findAll('script')
    for s in scripts:
        if str(s).find('var TralbumData') != -1:
            response['artist'] = re.findall('artist : ".*"', str(s))[0].split('"')[1]
            response['artist_avatar'] = re.findall('image_id: .*', str(s))[0].split(': ')[1]
            response['album_cover'] = re.findall('art_id: .*', str(s))[0].split(': ')[1][:-1]
            try:
                response['album_url'] = re.findall('album_url: .*', str(s))[0].split('"')[1]
            except IndexError:
                response['album_url'] = None

            response['track_info'] = eval(re.findall('trackinfo: .*', str(s))[0].split(': ')[1][:-1].
                                          replace('null', 'None').replace('false', 'False').replace('true', 'True'))[0]

    return response
