""" Handler for Mailgun API interaction """
import json.decoder
import time
import requests

GET, POST = 'GET', 'POST'  # Handy constants


class MailgunHandler:
    """
    Handler for Mailgun API interaction
    """
    _BASE_URL = 'https://api.mailgun.net/'  # Careful with EU domains
    _VALIDATION_URL = _BASE_URL + 'v4/domains/%s'
    _EMAIL_SEND_URL = _BASE_URL + 'v3/%s/messages'

    def __init__(self, mailgun_token: str, domain_name: str, mailgun_sender_name: str, sleep_time_on_rate_limit: int):
        self.mailgun_token = mailgun_token
        self.domain_name = domain_name
        self.mailgun_sender_name = mailgun_sender_name
        self.sleep_time_on_rate_limit = sleep_time_on_rate_limit

        self._validate_token_and_domain()

    def _wrap_mailgun_api_request(self, url, method=GET, data=None) -> dict:
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
        r = requests.request(method, url, data=data, auth=("api", self.mailgun_token))
        if r.status_code != 200:
            if r.status_code == 429:   # Too many requests
                time.sleep(self.sleep_time_on_rate_limit)
                return self._wrap_mailgun_api_request(url, method, data)
            else:
                try:
                    self._handle_api_errors(r)
                except json.decoder.JSONDecodeError:
                    raise self.HTTPError(f'HTTP Error: {url}, : {r}')
        else:
            try:
                return r.json()
            except json.decoder.JSONDecodeError:
                raise self.JSONErrorOn200Return(f'JSONErrorOn200Return: {url}, : {r}')

        pass

    def _handle_api_errors(self, r: requests.Response) -> None:
        """
        Attempt to call r.json() and then raise according to the status_code and error contents.

        :param r: requests.Response object
        :raise InvalidToken: if the Mailgun token is invalid
        :raise APIError: on any other API error
        """
        response_json = r.json()
        if r.status_code == 401:
            raise self.InvalidToken(f'Invalid Mailgun token: "{self.mailgun_token}"')
        else:
            raise self.APIError(f'Mailgun API Error: {r.status_code}, {response_json}')

    def _validate_token_and_domain(self) -> None:
        """
        Validate token and domain
        :raise InvalidToken: if the Mailgun token is invalid
        :raise InvalidDomain: if the Mailgun domain is invalid
        """
        try:
            self._wrap_mailgun_api_request(self._VALIDATION_URL % self.domain_name)
        except (self.HTTPError, self.APIError) as e:
            raise self.InvalidDomain(f'Invalid domain_name: "{self.domain_name}" - {e}')

    def send_mail(self, recipients: list[str], subject: str, message: str):
        """
        Email recipients

        :raise JSONErrorOn200Return: if the answer from the request was 200 but was not a JSON
        :raise HTTP Error: if the answer from the request was an error and not a JSON
        :raise APIError: on any other API error
        """
        data = {
            "from": f"{self.mailgun_sender_name} <mailgun@{self.domain_name}>",
            "to": recipients,
            "subject": subject,
            "text": message
        }
        self._wrap_mailgun_api_request(self._EMAIL_SEND_URL % self.domain_name, POST, data)

    class JSONErrorOn200Return(Exception):
        """ .json() failed on a 200 return error """

    class HTTPError(Exception):
        """ Answer from an HTTP request was an error and not a valid JSON API return"""

    class APIError(Exception):
        """ Unexpected Mailgun API Error """

    class InvalidToken(APIError):
        """ Invalid Mailgun Token """

    class InvalidDomain(APIError):
        """ Invalid Mailgun Token """
