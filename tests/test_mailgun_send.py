""" Tests for MailgunSend. """
from unittest import TestCase, mock
from helpers.mailgun_send import MailgunSend

API_KEY = ''  # Set this before testing.
DOMAIN_NAME = ''  # Set this before testing.
RECIPIENT_LIST = ['']  # Set this before testing.

class TestMailgunSend(TestCase):
    def test__init__raises_InvalidToken(self):
        self.assertRaises(MailgunSend.InvalidToken, MailgunSend, '', '', '')

    def test__init__raises_InvalidDomain(self):
        self.assertRaises(MailgunSend.InvalidDomain, MailgunSend, API_KEY, '', '')

    def test_send_mail(self):
        MS = MailgunSend(API_KEY, DOMAIN_NAME, 'test')
        x = MS.send_mail(RECIPIENT_LIST, 'test_send_mail passed', 'test_send_mail passed')
        self.assertTrue('Queued. Thank you.' in x['message'])

    def test_send_mail_raises_APIError(self):
        MS = MailgunSend(API_KEY, DOMAIN_NAME, 'test')
        self.assertRaises(MailgunSend.APIError, MS.send_mail, [''], 'test', '666')
