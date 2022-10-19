""" Tests for notifier. Some of these tests will send notifications, and should be checked by user preferably one at a
time. """
from unittest import TestCase
from helpers.notifier import Notifier, Icon

class TestNotifier(TestCase):
    def test_init_raises_UnexpectedNotifySendInitError(self):
        temp = Notifier._EXPECTED_NOTIFY_SEND_ERR
        Notifier._EXPECTED_NOTIFY_SEND_ERR = '666'
        self.assertRaises(Notifier.UnexpectedNotifySendInitError, Notifier)
        # clean up monkey patching
        Notifier._EXPECTED_NOTIFY_SEND_ERR = temp

    def test_notify_notify_send(self):
        n = Notifier()
        n.notify('Test', 'testing with info icon')
        n.notify('Test', 'testing with important icon', icon=Icon.IMPORTANT)
        n.notify('Test', 'testing with error icon', icon=Icon.ERROR)

    def test_notify_notify_send_raises_NotifySendError(self):
        n = Notifier()
        self.assertRaises(Notifier.NotifySendError, n.notify, '', '')

    def test_notify_notify_tk_temporal(self):
        n = Notifier(force_tk=True)
        n.notify('Test', 'testing temporal 1 ', temporal=True)
        n.notify('Test', 'testing temporal 2 ', temporal=True)
        n.notify('Test', 'testing temporal 3 ', temporal=True)

    def test_notify_notify_tk__notif_queue_temporal(self):
        n = Notifier(force_tk=True)
        for i in range(11):
            n.notify('Test', f'testing temporal {i} w queue', temporal=True)

    def test_notify_notify_tk_non_temporal(self):
        n = Notifier(force_tk=True)
        n.notify('Test', 'testing non temporal 1 ')
        n.notify('Test', 'testing non temporal 2 ')
        n.notify('Test', 'testing non temporal 3 ')

    def test_notify_notify_tk__notif_queue_non_temporal(self):
        n = Notifier(force_tk=True)
        for i in range(11):
            n.notify('Test', f'testing non temporal {i} w queue')
