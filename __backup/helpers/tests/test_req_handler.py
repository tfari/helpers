from unittest import TestCase
from backup.helpers.helpers.req_handler import GET, VALID_METHODS, RequestData, RequestErrorData, RequestHandler, \
    ThreadedRequestHandler, InvalidMethod, InvalidURL, ConnectivityError, InvalidStatusCode, NoValidationString, \
    ContainsErrorString


class TestRequestSess(TestCase):
    def test___init__(self):
        # Test nothing else raises
        for method in VALID_METHODS:
            RequestData(method)

        # Test exceptions
        self.assertRaises(InvalidMethod, RequestData, 'a')


class TestRequestHandler(TestCase):
    def test__request_wrapper(self):
        with open('test_expected_request_response', 'r') as f:
            expected = f.read()

        test_url = 'http://example.org'
        invalid_err_url = 'asaff'
        connect_err_url = 'http://examasfafgple.org'

        # Test nothing else raises
        rh = RequestHandler([], RequestData(GET), RequestErrorData())
        rh._request_wrapper(test_url)

        # Test exceptions
        self.assertRaises(InvalidURL, rh._request_wrapper, invalid_err_url)
        self.assertRaises(ConnectivityError, rh._request_wrapper, connect_err_url)

        # Test it works as it should
        response = rh._request_wrapper(test_url)
        self.assertEqual(expected, response.text)

    def test__handle_url(self):
        with open('test_expected_request_response', 'r') as f:
            expected = f.read()

        test_url = 'http://example.org'
        connect_err_url = 'http://examasfafgple.org'

        # Test nothing else raises
        rh = RequestHandler([test_url, test_url, test_url], RequestData(GET), RequestErrorData())
        rh.run()

        # Test exceptions
        connectivity_raise = RequestHandler([connect_err_url], RequestData(GET),
                                            RequestErrorData(allow_errors=False))
        status_code_raise = RequestHandler([test_url], RequestData(GET),
                                           RequestErrorData(allow_errors=False, expected_status_codes=[400]))
        validation_str_raise = RequestHandler([test_url], RequestData(GET),
                                              RequestErrorData(allow_errors=False, expected_validation_str='afafplfa'))
        error_str_raise = RequestHandler([test_url], RequestData(GET),
                                         RequestErrorData(allow_errors=False, expected_error_str=expected[0:5]))

        self.assertRaises(ConnectivityError, connectivity_raise.run)
        self.assertRaises(InvalidStatusCode, status_code_raise.run)
        self.assertRaises(NoValidationString, validation_str_raise.run)
        self.assertRaises(ContainsErrorString, error_str_raise.run)

        # Test it works as it should

        # # With one
        rh = RequestHandler([test_url], RequestData(GET), RequestErrorData())
        rh.run()
        self.assertEqual(1, len(rh.responses))
        self.assertEqual(0, len(rh.errors))

        # # With many
        rh = RequestHandler([test_url, test_url, test_url, test_url, connect_err_url, connect_err_url, test_url],
                            RequestData(GET), RequestErrorData())
        rh.run()
        self.assertEqual(5, len(rh.responses))
        self.assertEqual(2, len(rh.errors))
        self.assertEqual(ConnectivityError, rh.errors[0]['error'])
        self.assertEqual(ConnectivityError, rh.errors[1]['error'])

        # # Status code error check
        rh = RequestHandler([test_url], RequestData(GET), RequestErrorData(expected_status_codes=[1900]))
        rh.run()
        self.assertEqual(1, len(rh.errors))
        self.assertEqual(InvalidStatusCode, rh.errors[0]['error'])

        # # Validation Str error check
        rh = RequestHandler([test_url], RequestData(GET), RequestErrorData(expected_validation_str=expected[0:5]))
        rh.run()
        self.assertEqual(0, len(rh.errors))

        rh = RequestHandler([test_url], RequestData(GET), RequestErrorData(expected_validation_str='alf'))
        rh.run()
        self.assertEqual(1, len(rh.errors))
        self.assertEqual(NoValidationString, rh.errors[0]['error'])

        # # Error Str error check
        rh = RequestHandler([test_url], RequestData(GET), RequestErrorData(expected_error_str='aogfka'))
        rh.run()
        self.assertEqual(0, len(rh.errors))

        rh = RequestHandler([test_url], RequestData(GET), RequestErrorData(expected_error_str=expected[0:5]))
        rh.run()
        self.assertEqual(1, len(rh.errors))
        self.assertEqual(ContainsErrorString, rh.errors[0]['error'])


class TestThreadedRequestHandler(TestCase):
    def test__init_threads(self):
        test_url = 'http://example.org'

        # Test nothing else raises
        tr = ThreadedRequestHandler([test_url] * 5, RequestData(GET),
                                    RequestErrorData(), 5)
        self.assertEqual(tr.thread_num, len(tr.threads))
        self.assertEqual(5, len(tr.handlers))

        # Test exceptions

        # Test it works as it should
        tr = ThreadedRequestHandler([test_url, test_url, test_url], RequestData(GET), RequestErrorData(), 5)
        self.assertEqual(3, tr.thread_num)
        self.assertEqual(1, len(tr.handlers[0].url_list))

        tr = ThreadedRequestHandler([test_url, test_url, test_url], RequestData(GET), RequestErrorData(), 2)
        self.assertEqual(2, tr.thread_num)
        self.assertEqual(2, len(tr.handlers[0].url_list))

        tr = ThreadedRequestHandler([test_url] * 148, RequestData(GET), RequestErrorData(), 10)
        self.assertEqual(10, tr.thread_num)
        self.assertEqual(15, len(tr.handlers[0].url_list))

    def test_do_threads(self):
        test_url = 'http://example.org'
        error_url = 'http://examasfafgple.org'
        with open('test_expected_request_response', 'r') as f:
            expected = f.read()

        # Test nothing else raises
        tr = ThreadedRequestHandler([test_url, test_url, test_url, test_url, test_url, test_url, error_url], RequestData(GET),
                                    RequestErrorData(), 5)

        tr.do_threads()

        # Test exceptions

        # Test it works as it should
        for response in tr.responses:
            self.assertEqual(expected, response.text)

        self.assertEqual(1, len(tr.errors))
