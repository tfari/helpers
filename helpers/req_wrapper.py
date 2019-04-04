import requests


# v 0.1


GET = 'get'
POST = 'post'


def request_wrapper(method, url, headers=None, cookies=None, data=None, proxies=None,
            expected_codes=None, expected_validation=None, expected_error=None):
    """
    Function that wraps an HTTP request with a layer of configurable validations.

    Raises BadMethodType, BadUrl, RequestConnectionError, UnexpectedCode, NotFoundExpectedValidation, FoundExpectedError


    :param method: can only use constants in this file (GET, POST, ...)
    :param url: string
    :param headers: header dictionary
    :param cookies: cookie dictionary
    :param data:  data dictionary
    :param proxies: proxy dictionary
    :param expected_codes: integer list, whitelist of acceptable http response codes
    :param expected_validation: string, a substring that validates we got the response we were looking for
    :param expected_error: string, a substring that confirms that we got to an error page

    :return: a request Response object.
    """
    # Method validation
    if (method is not GET) and (method is not POST):
        raise BadMethodType(method)

    # URL/Connection validation
    try:
        r = requests.request(method, url, headers=headers, cookies=cookies, data=data, proxies=proxies)
    except requests.exceptions.MissingSchema:
        raise BadUrl(url)
    except requests.exceptions.ConnectionError:
        raise RequestConnectionError(url)

    # Optional validations
    if expected_codes:
        if r.status_code not in expected_codes:
            raise UnexpectedCode(r.status_code, expected_codes, url, r)

    if expected_validation:
        if r.text.find(expected_validation) == -1:
            raise NotFoundExpectedValidation(r.text, expected_validation, url, r)

    if expected_error:
        if r.text.find(expected_error) != -1:
            raise FoundExpectedError(r.text, expected_error, url, r)

    return r


# EXCEPTIONS


class RequestWrapperError(Exception):
    pass


class BadMethodType(RequestWrapperError):
    pass


class BadUrl(RequestWrapperError):
    pass


class RequestConnectionError(RequestWrapperError):
    pass


class ExpectationError(RequestWrapperError):
    def __init__(self, value, expecting, url, response):
        self.value = value
        self.expecting = expecting
        self.url = url
        self.response = response
        Exception.__init__(self, value)

    def __str__(self, prev):
        return prev + ' (Check self.response for response object)'


class UnexpectedCode(ExpectationError):
    def __str__(self):
        return super().__str__(('Unexpected code: %s in url %s. Expecting: %s' % (self.value, self.url, self.expecting)))


class NotFoundExpectedValidation(ExpectationError):
    def __str__(self):
        return super().__str__(('Expected validation: "%s" not found in url %s' % (self.expecting, self.url)))


class FoundExpectedError(ExpectationError):
    def __str__(self):
        return super().__str__(('Expected error: "%s" found in url %s' % (self.expecting, self.url)))

