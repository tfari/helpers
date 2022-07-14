import time
import threading
import datetime

from tkinter import Tk, Label, NW


# v 0.0.1

"""
Tk-based graphical notification system

Usage:
    NOTIFYSERVER.notify(message, title)
"""
# TODO: Turn this into an actual daemon/server so that many processes/tasks running on other machines can notify to the
#  machine running the tk_notify server.
# TODO: Add some backlog in case notifications show when the user isn't in front of the computer
# TODO: Make the tk_notify server run on systray
# TODO: Make appearance user-defined via a settings.json file


class NotifyServer(object):
    """
    Base class for creating notifications
    """
    def __init__(self):
        self.notifications = 0
        root = Tk()  # We do this for the line below
        self.notification_list = [None] * int(root.winfo_screenheight() / 140)  # TODO: Implement this (how many fit?)
        root.destroy()  # We do this for the line above

    def notify(self, msg, title=None):
        """
        Create and display a notification

        :param msg: str
        :param title: str
        :return: None
        """
        print(datetime.datetime.now(), title, '->', msg)  # TODO: VERBOSE setting

        # We call notificate() on a separate thread
        t = threading.Thread(target=self.notificate, args=(msg, title, self.notifications))
        t.start()
        self.notifications += 1

    def notificate(self, msg, title, n=0):
        """

        :param msg:
        :param title:
        :param n:
        :return:
        """

        # Create a Tk() instance
        root = Tk()
        root.config(bg='#28292b')
        root.overrideredirect(1)
        root.attributes('-alpha', 0.5)
        root.attributes('-topmost', True)

        # Constrain the title and msg so that they fit in the alloted space
        if title:
            title = title
            title_txt = Label(root, text=title, bg='#28292b', fg='#f7f7f7', anchor=NW,
                              font=('Helvetica', 9, "bold underline"))
            title_txt.pack(padx=5, pady=5)
            msg = msg[:314]
        else:
            msg = msg[:450]

        msg_txt = Label(root, text=msg, bg='#28292b', fg='#f7f7f7', anchor=NW, wraplength=380)
        msg_txt.pack(padx=5)

        # Animate

        width, height = root.winfo_screenwidth(), root.winfo_screenheight()

        # Bring up
        x = 0
        alpha = 0.0
        for i in range(100):
            x += 4.1
            alpha += 0.008
            root.geometry('%dx%d+%d+%d' % (400, 120, width-x, (height-160) - (140 * n)))
            root.attributes('-alpha', alpha)
            root.update_idletasks()
            root.update()

        # Stay for 5 secs
        for i in range(5):
            time.sleep(1)
            root.update_idletasks()
            root.update()

        # Go down
        for i in range(100):
            x -= 6.1
            alpha -= 0.008
            root.geometry('%dx%d+%d+%d' % (400, 120, width-x, (height-160) - (140 * n)))
            root.attributes('-alpha', alpha)
            root.update_idletasks()
            root.update()

        # Destroy notification
        self.notifications -= 1
        root.destroy()


NOTIFYSERVER = NotifyServer()
