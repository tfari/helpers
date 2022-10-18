""" Logger wrapper with "fatal error" functionality and stream / file handlers """
import sys
import logging
from typing import Union

class Logger:
    """
    Stream/File logger wrapper.
        - Logger format is: [time] - [logger_name] - [log level] - [message]
        - In the case of errors calls sys.exit(1) after logging the error by default.
    """
    def __init__(self, name: str, *, path: str = '', debug_active: bool = False, use_fatal: bool = True):
        """
        :param name: logger name and filename
        :param path: logger path. Defaults to current directory
        :param debug_active: if debug statements are active. Defaults to false
        :param use_fatal: if error logs should exit the script. Defaults to true
        :raises FileNotFoundError: if path is invalid
        """
        self._logger_name = name
        self._logger_path = path
        self._debug_active = debug_active
        self._use_fatal = use_fatal

        self._logger = self.__logger_setup()

    def info(self, msg: str) -> None:
        """ Log info message """
        self._logger.info(msg)

    def debug(self, msg: str) -> None:
        """ Log debug message """
        self._logger.debug(msg)

    def warn(self, warn_msg: Union[str, Exception]) -> None:
        """
        Log warning message
        :param warn_msg: str or Exception to log. If it is an exception, log its name and argument.
        """
        warn_msg = warn_msg if isinstance(warn_msg, str) else f'{warn_msg.__class__.__name__}: {warn_msg}'
        self._logger.warning(warn_msg)

    def err(self, err_msg: Union[str, Exception], *,  non_fatal: bool = False) -> None:
        """
        Log error message. Unless Logger was created with use_fatal=False, or non_fatal is passed in as True,
        calls sys.exit(1) after logging.

        :param err_msg: str or Exception to log. If it is an exception, log its name and argument.
        :param non_fatal: bool, default False. If true, do not quit application after logging.
        """
        err_msg = err_msg if isinstance(err_msg, str) else f'{err_msg.__class__.__name__}: {err_msg}'
        self._logger.error(err_msg)
        if self._use_fatal and not non_fatal:
            sys.exit(1)

    def __logger_setup(self) -> logging.Logger:
        """
        Setup a StreamHandler and FileHandler logger.
        :raises FileNotFoundError: if path is invalid
        """
        logger = logging.getLogger(self._logger_name)
        path = f'{self._logger_path}/{self._logger_name}.log' if self._logger_path else f'{self._logger_name}.log'

        sh, fh = logging.StreamHandler(), logging.FileHandler(path)  # Create handlers

        # Set level
        lvl = logging.INFO if not self._debug_active else logging.DEBUG
        logger.setLevel(lvl)
        sh.setLevel(lvl)
        fh.setLevel(lvl)

        # Set formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        sh.setFormatter(formatter)
        fh.setFormatter(formatter)

        # Add handlers
        logger.addHandler(sh)
        logger.addHandler(fh)

        return logger
