""" Logger wrapper with fatal error functionality and stream and file handlers """
import sys
import logging
from typing import Union

class Logger:
    """
    Stream/File logger wrapper.
        - Logger format is: [time] - [logger_name] - [log level] - [message]
        - In the case of errors, allows to pass in a flag to call sys.exit(1) after logging the error.
    """
    def __init__(self, name: str, *, path: str = '', debug_active: bool = False):
        """
        :param name: logger name and filename
        :param path: logger path. Defaults to current directory
        :param debug_active: if debug statements are active. Defaults to false
        :raises FileNotFoundError: if path is invalid
        """
        self._logger_name = name
        self._logger_path = path
        self._debug_active = debug_active

        self._logger = self.__logger_setup()

    def info(self, msg: str) -> None:
        """ Log info message """
        self._logger.info(msg)

    def debug(self, msg: str) -> None:
        """ Log debug message """
        self._logger.debug(msg)

    def err(self, err_msg: Union[str, Exception], *,  fatal: bool = False) -> None:
        """
        Log an error or warning message. If it is an error call sys.exit(1)

        :param err_msg: str or exception to log. If it is an exception, log its name and argument.
        :param fatal: bool, default False. If true, log as error and then call sys.exit(1)
        """
        err_msg = err_msg if isinstance(err_msg, str) else f'{err_msg.__class__.__name__}: {err_msg}'
        if fatal:
            self._logger.error(err_msg)
            sys.exit(1)
        else:
            self._logger.warning(err_msg)

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
