import requests
import threading
import time


# v 0.0.1


VALID_METHODS = [GET, POST] = 'get', 'post'
TOO_MANY_REQUESTS = 429


class RequestData(object):
    """
    Class that holds arguments to pass to requests.request()
    """
    def __init__(self, method, data=None, json=None, headers=None, cookies=None,
                 files=None, auth=None, timeout=10, allow_redirects=True,
                 proxies=None, stream=None, cert=None):

        """
        Raises InvalidMethod

        :param method: GET or POST defined at the top of this file
        """
        self.method = method
        self.data = data
        self.json = json
        self.headers = headers
        self.cookies = cookies
        self.files = files
        self.auth = auth
        self.timeout = timeout
        self.allow_redirects = allow_redirects
        self.proxies = proxies
        self.stream = stream
        self.cert = cert

        # Validate method
        if self.method not in VALID_METHODS:
            raise InvalidMethod(self.method)


class RequestErrorData(object):
    """
    Class that holds information on the kind of error checking that RequestHandler should do
    """
    def __init__(self, allow_errors=True, error_connection_max_tries=10,
                 expected_status_codes=[200],
                 expected_validation_str=None,
                 expected_error_str=None):
        """
        :param allow_errors: boolean, if False, RequestHandler raises when there are errors
        :param error_connection_max_tries: integer, amount of times RequestHandler attempts the connection
        when it catches a ConnectionError
        :param expected_status_codes: list of integers, the expected valid status codes for the request
        :param expected_validation_str: string, a string to check against the response.text that validates the response
        :param expected_error_str: string, a string to check against the response.text that invalidates the response
        """

        self.allow_errors = allow_errors
        self.error_connection_max_tries = error_connection_max_tries

        self.expected_status_codes = expected_status_codes
        self.expected_validation_str = expected_validation_str
        self.expected_error_str = expected_error_str


class RequestHandler(object):
    """
    Class that executes a request over a list of links
    """
    def __init__(self, url_list, request_data, request_error_data):
        """
        :param url_list: list of strings
        :param request_data: RequestData object
        :param request_error_data: RequestErrorData object
        """
        self.url_list = url_list
        self.request_data = request_data
        self.request_error_data = request_error_data

        self.responses = []
        self.errors = []

    def run(self):
        """
        :return: None
        """
        for url in self.url_list:
            self._handle_url(url)

    def _request_wrapper(self, url):
        """
        Wraps the requests.request() function

        Raises InvalidURL and ConnectivityError

        :param url: string
        :return: request's ResponseObject instance
        """
        try:
            response_object = requests.request(self.request_data.method, url, data=self.request_data.data,
                                               json=self.request_data.json, headers=self.request_data.headers,
                                               cookies=self.request_data.cookies, files=self.request_data.files,
                                               auth=self.request_data.auth, timeout=self.request_data.timeout,
                                               allow_redirects=self.request_data.allow_redirects,
                                               proxies=self.request_data.proxies, stream=self.request_data.stream,
                                               cert=self.request_data.cert)
            return response_object

        except requests.exceptions.MissingSchema or requests.exceptions.InvalidSchema or requests.exceptions.InvalidURL:
            raise InvalidURL(url)
        except requests.exceptions.ConnectionError:
            raise ConnectivityError(url)

    def _handle_url(self, url, connectivity_n_try=0):
        """
        Performs a request, then error checks the response, and appends either the ResponseObject to self.responses, or
        a dictionary comprising of {'error':Exception, 'url':url, 'response':ResponseObject} to self.errors

        In case of ConnectivityError the function calls itself self.request_error_data.error_connection_max_tries times.

        Raise ConnectivityError, InvalidStatusCode, NoValidationString, ContainsErrorString

        :param url: string
        :param connectivity_n_try: integer, takes count of recursive calls
        :return: None
        """

        try:
            response_object = self._request_wrapper(url)

        except ConnectivityError:
            if self.request_error_data.allow_errors:
                if connectivity_n_try < self.request_error_data.error_connection_max_tries:
                    return self._handle_url(url, connectivity_n_try=connectivity_n_try + 1)
                else:
                    self.errors.append({'error': ConnectivityError, 'url': url, 'response': None})
                    return None
            else:
                raise ConnectivityError(url)

        # Validate by status_code
        if response_object.status_code not in self.request_error_data.expected_status_codes:
            if self.request_error_data.allow_errors:
                self.errors.append({'error': InvalidStatusCode, 'url': url, 'response': response_object})
                return None
            else:
                raise InvalidStatusCode(url)

        # Validate by expected validation str
        if self.request_error_data.expected_validation_str:
            if response_object.text.find(self.request_error_data.expected_validation_str) == -1:
                if self.request_error_data.allow_errors:
                    self.errors.append({'error': NoValidationString, 'url': url, 'response': response_object})
                    return None
                else:
                    raise NoValidationString(url)

        # Validate by expected error str
        if self.request_error_data.expected_error_str:
            if response_object.text.find(self.request_error_data.expected_error_str) != -1:
                if self.request_error_data.allow_errors:
                    self.errors.append({'error': ContainsErrorString, 'url': url, 'response': response_object})
                    return None

                else:
                    raise ContainsErrorString(url)

        self.responses.append(response_object)


class ThreadedRequestHandler(object):
    """
    Class that divides a big url_list around of number of threads.
    """
    def __init__(self, url_list, request_data, request_error_data, thread_num=1, max_passes=1, sleep_pass=0):
        """
        :param url_list: list of strings
        :param request_data: RequestData object
        :param request_error_data: RequestErrorData object
        :param thread_num: integer, the number of threads to use
        :param max_passes: integer, the number of passes over the url list before returning
        :param sleep_pass: integer, the time to sleep between passes, 0 by default.
        """
        self.url_list = url_list
        self.request_data = request_data
        self.request_error_data = request_error_data

        self.thread_num = thread_num
        self.max_passes = max_passes
        self.sleep_pass = sleep_pass

        self.responses = []
        self.errors = []

        self._init_threads(self.url_list)

    def _init_threads(self, url_list):
        """
        Creates the threads by dividing the url_list between self.thread_num. Fills self.threads and self.handlers.

        :param url_list: list of strings
        :return: None
        """
        self.threads = []
        self.handlers = []

        # Don't use more threads than urls
        self.thread_num = len(url_list) if len(url_list) < self.thread_num else self.thread_num

        t_lists = [[] for _ in range(self.thread_num)]

        count = 0
        for url in url_list:
            t_lists[(count % self.thread_num)].append(url)
            count += 1

        for thread_list in t_lists:
            rh = RequestHandler(thread_list, self.request_data, self.request_error_data)
            t = threading.Thread(target=rh.run)
            self.handlers.append(rh)
            self.threads.append(t)

    def do_threads(self, n_pass=0):
        """
        Start all threads, when they end recollect them and then call itself again but with the content of self.errors.

        :param n_pass: integer, takes count of recursive calls
        :return: None
        """
        self.errors = []

        for t in self.threads:
            t.start()

        for t in self.threads:  # TODO: We could repurpose threads as they become available
            t.join()

        for handler in self.handlers:
            self.responses += handler.responses
            self.errors += handler.errors

        print('[*] Pass n: %s, Responses: %s, Errors: %s' % (n_pass, len(self.responses), len(self.errors)))

        if len(self.errors) > 0:
            if n_pass < self.max_passes:
                url_list = [err['url'] for err in self.errors]
                self._init_threads(url_list)

                time.sleep(self.sleep_pass)

                return self.do_threads(n_pass=n_pass + 1)


# EXCEPTIONS


class InvalidMethod(Exception):
    pass


class InvalidURL(Exception):
    pass


class ConnectivityError(Exception):
    pass


class InvalidStatusCode(Exception):
    pass


class NoValidationString(Exception):
    pass


class ContainsErrorString(Exception):
    pass
