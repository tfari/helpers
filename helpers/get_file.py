""" Download a file using requests. Display a download bar on stdout unless told otherwise. """
import sys
import time
import requests


def get_file(prefix: str, filepath: str, url: str, *, chunk_size: int = 1000, show_bar: bool = True,
             secs_between_range: float = 0.25, bar_size: int = 50, dl_char: str = '#', empty_char: str = '-') -> None:
    """
    Use requests to download a file. Display a download bar unless show_bar is False.
    Download bar scheme ex:
    prefix : filename - [####--------------] [ current mbs / total mbs  ] [ velocity kbs | ETA: estimated minutes ]

    :param prefix: Prefix for the download bar
    :param filepath: Filepath for the download
    :param url: Url to download
    :param chunk_size: Size of the chunks to write. Default: 1000
    :param show_bar: Show the download bar?. Default: True
    :param secs_between_range: Seconds between estimated/velocity calculations. Default: 0.25
    :param bar_size: Size of the download bar. Default: 50
    :param dl_char: Char to use for the downloaded portion of the bar. Default: "#"
    :param empty_char: Char to use for the empty portion of the bar. Default: "-"
    """
    def __format(n: float) -> str:
        return '{:.2f}'.format(n)

    def __in_mbs(n: int) -> str:
        return __format((n / 1000) / 1000)

    # Start get
    r = requests.get(url, stream=True)
    total_length = int(r.headers.get('content-length'))

    with open(filepath, 'wb') as f:  # Adapted from script found on stack overflow
        amt_in_range = 0
        last_time_stamp = time.time()

        vel = 0
        estimated_minutes = 0
        already_downloaded = 0

        for data in r.iter_content(chunk_size=chunk_size):
            f.write(data)

            if show_bar:
                already_downloaded += len(data)

                prcnt_done = int(bar_size * already_downloaded / total_length)
                msg = f'\r{prefix} : {filepath} - [{dl_char * prcnt_done}{empty_char * (bar_size - 1 - prcnt_done)}] ' \
                      f'[ {__in_mbs(already_downloaded)} mbs / {__in_mbs(total_length)} mbs] ' \
                      f'[ {__format(vel)} kbs | ETA: {__format(estimated_minutes)} minutes ]'
                sys.stdout.write(msg)
                sys.stdout.flush()

                # Download information
                if (time.time() - last_time_stamp) < secs_between_range:
                    amt_in_range += 1
                else:
                    vel = (amt_in_range * (1 / secs_between_range))
                    vel = 0.001 if int(vel) == 0 else vel  # Do this to avoid ZeroDivisionError when connection drops
                    last_time_stamp = time.time()
                    amt_in_range = 0
                    estimated_minutes = ((total_length/chunk_size)/vel) / 60
