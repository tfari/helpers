import requests
import time
import sys


# v 0.0.1


def get_file(header, url, filename):
    """
    Implements a simple download bar for file downloads.

    :param header: A string to put in front of the filename when displaying the download status
    :param url: str, url to download
    :param filename: str, file path to save to
    :return: None
    """

    r = requests.get(url, stream=True)
    total_length = int(r.headers.get('content-length'))
    total_length_in_mbs = (total_length / 1000) / 1000

    with open(filename, 'wb') as f:  # Adapted from script found on stack overflow
        downloaded = 0
        downloaded_in_mbs = 0

        total_length = int(total_length)

        amt_in_range = 0
        secs_between_range = 0.25
        last_time_stamp = time.time()

        vel = 0
        estimated = 0

        for data in r.iter_content(chunk_size=1000):
            downloaded += len(data)
            downloaded_in_mbs = (downloaded/1000)/1000

            f.write(data)
            done = int(50 * downloaded / total_length)
            sys.stdout.write("\r%s%s - [%s%s] [%s Mb /%s Mb] [ %s Kbs | ETA: %s minutes.]" %
                             (header, filename, '=' * done, ' ' * (49 - done), '{:.2f}'.format(downloaded_in_mbs),
                              '{:.2f}'.format(total_length_in_mbs), '{:.2f}'.format(vel), '{:.2f}'.format(estimated)))

            sys.stdout.flush()

            # Download information
            if (time.time() - last_time_stamp) < secs_between_range:
                amt_in_range += 1
            else:
                vel = (amt_in_range * (1 / secs_between_range))
                vel = 0.001 if int(vel) == 0 else vel  # Do this to avoid ZeroDivisionError when connection drops
                last_time_stamp = time.time()
                amt_in_range = 0
                estimated = ((total_length/1000)/vel) / 60

    # New line
    print()
