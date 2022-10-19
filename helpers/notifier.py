""" Simple Notification system using either notify-send (https://vaskovsky.net/notify-send/) or Tk. If notifying
    via Tk and notifications exceed the screen's space, they get added into a queue until there is space. """

import time
import math
import threading
import subprocess

from enum import Enum
from tkinter import Button, Label, Tk, BOTTOM, NW, SE

class Icon(Enum):
    """ Icons for notify-send """
    INFO = 'info'
    IMPORTANT = 'important'
    ERROR = 'error'


class Notifier:
    """ Simple Notification system using either notify-send (https://vaskovsky.net/notify-send/) or Tk. If notifying
    via Tk and notifications exceed the screen's space, they get added into a queue until there is space. """

    # notify-send constants
    _NOTIFY_SEND_COMMAND = 'notify-send'
    _EXPECTED_NOTIFY_SEND_ERR = b'No summary specified.\n'

    # tkinter constants
    _DEFAULT_DISPLAY_SECONDS = 5
    _TK_BG_COLOR = '#28292b'
    _TK_FG_COLOR = '#f7f7f7'
    _TK_ALPHA_LVL = 0.5
    _TK_TOPMOST = True
    _TK_WIDTH = 400
    _TK_HEIGHT = 120
    _TK_MARGIN_HORIZONTAL = 10
    _TK_MARGIN_VERTICAL = 20

    def __init__(self, *, force_tk: bool = False):
        """
        :param force_tk: force usage of Tk even if notify-send is available
        :raises UnexpectedNotifySendInitError: If notify-send check returns an error other than the expected.
        """
        # Check if notify-send is available
        self.__using_notify_send = False if force_tk else self.__check_notify_send()
        self.__displayed_notifications = 0
        if not self.__using_notify_send:
            root = Tk()
            width, height = root.winfo_screenwidth(), root.winfo_screenheight()
            self.__max_display_notifications = math.floor(height / (Notifier._TK_HEIGHT + Notifier._TK_MARGIN_VERTICAL))
            self.__notif_queue = []
            root.destroy()

    @staticmethod
    def __check_notify_send() -> bool:
        """
        Check if notify-send can be used
        :raises UnexpectedNotifySendInitError: If notify-send check returns an error other than the expected.
        """
        try:
            x = subprocess.run(Notifier._NOTIFY_SEND_COMMAND, capture_output=True)
            if x.returncode == 1 and x.stderr == Notifier._EXPECTED_NOTIFY_SEND_ERR:
                return True
            else:
                raise Notifier.UnexpectedNotifySendInitError(x.stderr)
        except FileNotFoundError:
            return False

    def notify(self, title: str, msg: str,
               *, icon: Icon = Icon.INFO, display_time: int = 0, temporal: bool = False) -> None:
        """
        Send a notification
        :param title: Notification's title
        :param msg: Notification's message
        :param icon: Notification's icon (for notify-send only)
        :param display_time: Notification's display time (Tk only). Default to 5 seconds
        :param temporal: If a notification should be deleted after display time (Tk only) . Default to false
        :raises NotifySendError: If using notify-send, and it returns an error
        """
        if self.__using_notify_send:
            self.__notify_notify_send(title, msg, icon)
        else:
            self.__notify_tk(title, msg, display_time if display_time > 0 else Notifier._DEFAULT_DISPLAY_SECONDS,
                             temporal)

    @staticmethod
    def __notify_notify_send(title: str, msg: str, icon: Icon) -> None:
        """
        Use notify-send to display a notification.
        :raises NotifySendError: in case of errors.
        """
        x = subprocess.run([Notifier._NOTIFY_SEND_COMMAND, title, msg, '-i', icon.value], capture_output=True)
        if x.returncode == 1:
            raise Notifier.NotifySendError(x.stderr)

    def __notify_tk(self, title: str, msg: str, display_time: int, temporal: bool) -> None:
        """ Use Tk to display a notification. """
        if self.__displayed_notifications < self.__max_display_notifications:
            t = threading.Thread(target=self.__notify_tk_thread_target,
                                 args=(self.__displayed_notifications, title, msg, display_time, temporal))
            t.start()
            self.__displayed_notifications += 1
        else:
            self.__notif_queue.append((title, msg, display_time, temporal))

    def __notify_tk_thread_target(self, notif_n: int, title: str, msg: str, display_time: int, temporal: bool) -> None:
        """
        Threading target for displaying notifications via Tk.

        :param notif_n: Number of notification displayed, to correct for height.
        :param title: Notification's title
        :param msg: Notification's message
        :param display_time: Seconds to display the notification if temporal is True
        :param temporal: If notification should auto-destroy after display_time seconds
        """
        # Create a Tk() instance
        root = Tk()
        root.config(bg=Notifier._TK_BG_COLOR)
        root.overrideredirect(True)
        root.attributes('-alpha', Notifier._TK_ALPHA_LVL)
        root.attributes('-topmost', Notifier._TK_TOPMOST)

        # Constrain the title and msg so that they fit in the allotted space
        if title:
            title_txt = Label(root, text=title, bg=Notifier._TK_BG_COLOR, fg=Notifier._TK_FG_COLOR, anchor=NW,
                              font=('Helvetica', 9, "bold underline"))
            title_txt.pack(padx=5, pady=5)
            msg = msg[:314]
        else:
            msg = msg[:450]

        # Pack and display message
        msg_txt = Label(root, text=msg, bg=Notifier._TK_BG_COLOR, fg=Notifier._TK_FG_COLOR, anchor=NW, wraplength=380)
        msg_txt.pack(padx=5)

        if not temporal:  # pack close button if it is not  a temporal notification
            exit_button = Button(root, text='Exit', bg=Notifier._TK_BG_COLOR, fg=Notifier._TK_FG_COLOR, anchor=SE,
                                 command=lambda: self.__destroy_notification(root, notif_n))
            exit_button.pack(side=BOTTOM, anchor=SE)

        # Resize and place window on lower right corner
        width, height = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry('%dx%d+%d+%d' % (Notifier._TK_WIDTH, Notifier._TK_HEIGHT,
                                       width - (Notifier._TK_WIDTH + Notifier._TK_MARGIN_HORIZONTAL),
                                       (height - (Notifier._TK_HEIGHT + Notifier._TK_MARGIN_VERTICAL))
                                       - ((Notifier._TK_HEIGHT + Notifier._TK_MARGIN_VERTICAL) * notif_n)))
        root.update()

        if temporal:  # Wait before destroying if it is a temporal notification
            time.sleep(display_time)
            self.__destroy_notification(root, notif_n)
        root.mainloop()

    def __destroy_notification(self, root: Tk, notif_n: int) -> None:
        """ Destroy notification """
        self.__displayed_notifications -= 1
        root.destroy()
        if self.__notif_queue:
            # Ugly, but it works better than calling __notify_tk inside the thread, as threads step on each other's
            # position more easily that way.
            t = threading.Thread(target=self.__notify_tk_thread_target,
                                 args=(notif_n, *self.__notif_queue.pop(0)))
            t.start()

    class UnexpectedNotifySendInitError(Exception):
        """ Notify send did not return the expected error on init check"""

    class NotifySendError(Exception):
        """ Notify send returned an error when attempting to notify """
