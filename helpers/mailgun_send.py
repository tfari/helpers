"""
API Wrapper to send emails via Mailgun. Requires an API key, but works for trial accounts (5k mails a month).
Requires:
    - requests
"""
import json
import time

import requests


class MailgunSend:
    """ Send emails via Mailgun API """
    _BASE_URL = 'https://api.mailgun.net/'
    _BASE_URL_EU = 'https://api.eu.mailgun.net'

    _VALIDATION_URL = 'v4/domains/{}'
    _EMAIL_SEND_URL = 'v3/{}/messages'

    def __init__(self, token: str, domain_name: str, sender_name: str, *, sleep_time_on_rate_limit: int = 1,
                 is_eu_domain: bool = False):
        """
        :param token: Valid mailgun token
        :param domain_name: Valid mailgun domain associated with the token
        :param sender_name: Sender's name
        :param sleep_time_on_rate_limit: Seconds to sleep if we are rate limited. Default: 1
        :param is_eu_domain: EU mailgun domains use a different URL structure (api.eu). Default: False
        """
        self._token = token
        self._domain_name = domain_name
        self._sender_name = sender_name
        self._sleep_time_on_rate_limit = sleep_time_on_rate_limit
        self._is_eu_domain = is_eu_domain

        base_url = MailgunSend._BASE_URL if not self._is_eu_domain else MailgunSend._BASE_URL_EU
        self._validate_url = base_url + MailgunSend._VALIDATION_URL
        self._send_url = base_url + MailgunSend._EMAIL_SEND_URL

        self._validate_token_and_domain()

    def send_mail(self, recipients: list[str], subject: str, message: str) -> dict:
        """
        Send email via Mailgun API

        :raise JSONErrorOn200Return: if the answer from the request was 200 but was not a JSON
        :raise HTTP Error: if the answer from the request was an error and not a JSON
        :raise APIError: on any other API error

        :return: dict, API response
        """
        data = {
            'from': f'{self._sender_name} <mailgun@{self._domain_name}>',
            'to': recipients,
            'subject': subject,
            'text': message
        }
        return self.__wrap_mailgun_api_request(self._send_url.format(self._domain_name), 'POST', data)

    def _validate_token_and_domain(self) -> None:
        """
        Validate token and domain

        :raise JSONErrorOn200Return: if the answer from the request was 200 but was not a JSON
        :raise InvalidToken: if the Mailgun token is invalid
        :raise InvalidDomain: if the Mailgun domain is invalid
        """
        try:
            self.__wrap_mailgun_api_request(self._validate_url.format(self._domain_name))
        except MailgunSend.InvalidToken as e:
            raise e
        except (MailgunSend.HTTPError, MailgunSend.APIError) as e:
            raise MailgunSend.InvalidDomain(f'Invalid domain_name: "{self._domain_name}" - {e}')

    def __wrap_mailgun_api_request(self, url, method='GET', data=None) -> dict:
        """
        Wrap a Mailgun request in order to handle rate-limiting and to catch JSON, HTTP and API errors.

        :param url: str, url to perform the HTTP request to
        :param method: GET/POST
        :param data: data for POST requests
        :return: dict, JSON, response of valid API call

        :raise JSONErrorOn200Return: if the answer from the request was 200 but was not a JSON
        :raise HTTP Error: if the answer from the request was an error and not a JSON
        :raise InvalidToken: if the Mailgun token is invalid
        :raise APIError: on any other API error
        """
        r = requests.request(method, url, data=data, auth=("api", self._token))
        if r.status_code != 200:
            if r.status_code == 429:   # Too many requests
                time.sleep(self._sleep_time_on_rate_limit)
                return self.__wrap_mailgun_api_request(url, method, data)
            else:
                try:
                    self.__handle_api_errors(r)
                except json.decoder.JSONDecodeError:
                    raise MailgunSend.HTTPError(f'HTTP Error: {url}, : {r}')
        else:
            try:
                return r.json()
            except json.decoder.JSONDecodeError:
                raise MailgunSend.JSONErrorOn200Return(f'JSONErrorOn200Return: {url}, : {r}')

    def __handle_api_errors(self, r: requests.Response) -> None:
        """
        Attempt to call r.json() and then raise according to the status_code and error contents.

        :raise InvalidToken: if the Mailgun token is invalid
        :raise APIError: on any other API error
        """
        response_json = r.json()
        if r.status_code == 401:
            raise MailgunSend.InvalidToken(f'Invalid Mailgun token: "{self._token}"')
        else:
            raise MailgunSend.APIError(f'Mailgun API Error: {r.status_code}, {response_json}')

    class MailgunSendError(Exception):
        """ Base error for MailgunSend """

    class JSONErrorOn200Return(MailgunSendError):
        """ JSON decoding failed on a 200 return error """

    class HTTPError(MailgunSendError):
        """ Answer from an HTTP request was an error and not a valid JSON API return"""

    class APIError(MailgunSendError):
        """ Unexpected Mailgun API Error """

    class InvalidToken(APIError):
        """ Invalid Mailgun Token """

    class InvalidDomain(APIError):
        """ Invalid Mailgun Token """
