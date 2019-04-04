from unittest import TestCase
from helpers.req_wrapper import GET, request_wrapper, BadMethodType, BadUrl, RequestConnectionError, UnexpectedCode, \
    NotFoundExpectedValidation, FoundExpectedError


class TestRequestWrapper(TestCase):
    def test_request(self):
        with open('test_expected_request_response', 'r') as f:
            expected_response = f.read()

        # NO INTERNET self.assertRaises(RequestConnectionError, r.request, GET, 'https://example.org')

        # Tests function doesnt raise extra thing
        request_wrapper(GET, 'http://example.org', expected_codes=[200])

        # Tests exceptions
        self.assertRaises(BadMethodType, request_wrapper, 0, '')
        self.assertRaises(BadUrl, request_wrapper, GET, '')
        self.assertRaises(RequestConnectionError, request_wrapper, GET, 'http://ajsfa')
        self.assertRaises(UnexpectedCode, request_wrapper, GET, 'http://example.org', expected_codes=[404])
        self.assertRaises(UnexpectedCode, request_wrapper, GET, 'http://example.org', expected_codes=['200'])
        self.assertRaises(NotFoundExpectedValidation, request_wrapper, GET, 'http://example.org', expected_codes=[200],
                          expected_validation='asfokag4494')
        self.assertRaises(FoundExpectedError, request_wrapper, GET, 'http://example.org', expected_codes=[200],
                          expected_error='Example Domain')

        # Tests function does what it has to do
        response = request_wrapper(GET, 'http://example.org', expected_codes=[200])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, expected_response)

