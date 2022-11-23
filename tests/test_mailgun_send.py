""" Tests for MailgunSend. """
import os
import json
from unittest import TestCase
from helpers.mailgun_send import MailgunSend

# Set these before testing, or use a _keys_for_test.json file: {"test_mailgun_send": {"api_key": API_KEY,
# "domain_name": DOMAIN_NAME, "recipient_list": RECIPIENT_LIST}}
API_KEY = ''
DOMAIN_NAME = ''
RECIPIENT_LIST = ['']

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(f'{SCRIPT_PATH}/_keys_for_tests.json'):
    with open(f'{SCRIPT_PATH}/_keys_for_tests.json', 'r', encoding='utf-8') as r_file:
        jsoned = json.load(r_file)['test_mailgun_send']
        API_KEY = jsoned['api_key']
        DOMAIN_NAME = jsoned["domain_name"]
        RECIPIENT_LIST = jsoned["recipient_list"]


class TestMailgunSend(TestCase):
    def test__init__raises_InvalidToken(self):
        self.assertRaises(MailgunSend.InvalidToken, MailgunSend, '', '', '')

    def test__init__raises_InvalidDomain(self):
        self.assertRaises(MailgunSend.InvalidDomain, MailgunSend, API_KEY, '', '')

    def test_send_mail(self):
        MS = MailgunSend(API_KEY, DOMAIN_NAME, 'TestMailgunSend')
        x = MS.send_mail(RECIPIENT_LIST, 'test_send_mail passed', 'test_send_mail passed')
        self.assertTrue('Queued. Thank you.' in x['message'])

    def test_send_mail_raises_APIError(self):
        MS = MailgunSend(API_KEY, DOMAIN_NAME, 'test')
        self.assertRaises(MailgunSend.APIError, MS.send_mail, [''], 'test', '666')
