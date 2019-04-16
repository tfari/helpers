from helpers.req_handler import GET, RequestData, RequestErrorData, RequestHandler


# v 0.0.1


"""
Soundcloud related helper functions. Some implement the Soundcloud API, others use selenium and other approaches to 
get data (mostly identifiers) from Soundcloud.
"""


def get_client_id():
    """
    We get the client_id either from client_id in PATH or we generate one and save it there.

    :return: string, a valid client_id for using the Soundcloud API.
    """

    # Check if file already exists.
    try:
        client_id = open('client_id', 'r').read()
        print('[*] Loaded client_id')

    # File does not exist: generate a client_id and save it.
    except FileNotFoundError:
        print('[!] client_id does not exist')

        client_id = _generate_client_id()
        with open('client_id', 'w') as f:
            f.write(str(client_id))
        print('[*] Saved client_id: %s' % client_id)

    return client_id


def _generate_client_id():
    """
    Generates a client_id by using a headless Selenium instance to visit Soundcloud.
    We use seleniumwire to grab an api-v2 request, and we extract client_id from the url.

    :return: string, a valid client_id for using the Soundcloud API.
    """

    # USES HEADLESS SELENIUM INSTANCE FOR GENERATING A CLIENT_ID
    print('[*] Fetching client_id.')

    from seleniumwire import webdriver
    from selenium.webdriver.firefox.options import Options

    options = Options()
    options.headless = True

    url = 'http://soundcloud.com/nasa'  # We visit an account because we need the page to generate an api-v2 request.

    driver = webdriver.Firefox(options=options)
    driver.get(url)

    print('[*][*] WebDriver up')
    driver.close()

    # GETS CLIENT_ID FROM THE REQUEST URL MADE TO api-v2
    url_to_api_v2 = ''
    for request in driver.requests:
        if request.response:
            if request.path.find('api-v2') != -1:
                url_to_api_v2 = request.path
                break

    # EXTRACT USER_ID FROM URL
    url_to_api_v2 = url_to_api_v2.split('?')[1].split('&')

    dict_response = {}
    for part in url_to_api_v2:
        s = part.split('=')
        dict_response[s[0]] = s[1]

    return dict_response['client_id']


def _resolve(resolve_url, client_id):
    """
    Make resolve requests.

    :param resolve_url: string, what to resolve
    :param client_id: string, a valid client_id
    :return: dict, the .json response to the resolve request
    """
    url = 'http://api.soundcloud.com/resolve?url=%s&client_id=%s' % (resolve_url, client_id)
    rh = RequestHandler([url], RequestData(GET), RequestErrorData(allow_errors=False))
    rh.run()
    response = rh.responses[0].json()
    return response


def get_user_id(user_name, client_id):
    """
    Get user_id of user_name.

    :param user_name: string, a valid user_name
    :param client_id: string, a valid client_id
    :return: string, user_id of user_name
    """
    return _resolve('http://soundcloud.com/%s' % user_name, client_id)['id']


def get_track_id(track_url, client_id):
    """
    Get track_id from track_url

    :param track_url: string, a valid track's url
    :param client_id: string, a valid client_id
    :return: string, track_id from track_url
    """
    return _resolve(track_url, client_id)['id']
