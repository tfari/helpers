""" Tests for Logger """
import os
from unittest import TestCase, mock
from helpers.logger import Logger


class TestLogger(TestCase):
    def tearDown(self) -> None:
        """ Clean up files """
        if os.path.exists('test.log'):
            os.remove('test.log')
        if os.path.exists('test_path'):
            os.remove('test_path/test.log')
            os.removedirs('test_path')

    def test__init__path_flag(self):
        Logger('test')  # No path
        self.assertTrue(os.path.exists('test.log'))

        os.makedirs('test_path')  # With path
        Logger('test', path='test_path')
        self.assertTrue(os.path.exists('test_path/test.log'))

    def test__init__debug_flag(self):
        logger = Logger('test')  # Debug flag is false
        logger.debug('abc')
        with open('test.log', 'r', encoding='utf-8') as r_file:
            self.assertEqual('', r_file.read())

        logger = Logger('test', debug_active=True)  # Debug flag is true
        logger.debug('abc')
        with open('test.log', 'r', encoding='utf-8') as r_file:
            self.assertEqual(2, len(r_file.read().split("\n")))

    def test__init__bad_filepath_raises_FileNotFoundError(self):
        self.assertRaises(FileNotFoundError, Logger, 'test', path='/666/')

    def test_info(self):
        logger = Logger('test')
        logger.info('abc')
        with open('test.log', 'r', encoding='utf-8') as r_file:
            self.assertEqual('INFO - abc', r_file.read().split('\n')[0].split('test - ')[1])

    def test_debug(self):
        logger = Logger('test', debug_active=True)
        logger.debug('abc')
        with open('test.log', 'r', encoding='utf-8') as r_file:
            self.assertEqual('DEBUG - abc', r_file.read().split('\n')[0].split('test - ')[1])

    def test_warn(self):
        logger = Logger('test')
        logger.warn('abc')
        with open('test.log', 'r', encoding='utf-8') as r_file:
            self.assertEqual('WARNING - abc', r_file.read().split('\n')[0].split('test - ')[1])

    def test_warn_w_exception(self):
        logger = Logger('test')
        try:
            a = []
            b = a[1]
        except IndexError as e:
            logger.warn(e)

        with open('test.log', 'r', encoding='utf-8') as r_file:
            self.assertEqual('WARNING - IndexError: list index out of range',
                             r_file.read().split('\n')[0].split('test - ')[1])

    @mock.patch("sys.exit")
    def test_err__init__w_false_use_fatal(self, mocked_fun):
        logger = Logger('test', use_fatal=False)
        logger.err('abc')
        with open('test.log', 'r', encoding='utf-8') as r_file:
            self.assertEqual('ERROR - abc', r_file.read().split('\n')[0].split('test - ')[1])

        mocked_fun.assert_not_called()

    @mock.patch("sys.exit")
    def test_err_non_fatal_str(self, mocked_fun):
        logger = Logger('test')
        logger.err('abc', non_fatal=True)
        with open('test.log', 'r', encoding='utf-8') as r_file:
            self.assertEqual('ERROR - abc', r_file.read().split('\n')[0].split('test - ')[1])
        mocked_fun.assert_not_called()

    @mock.patch("sys.exit")
    def test_err_non_fatal_w_exception(self, mocked_fun):
        logger = Logger('test')
        try:
            a = []
            b = a[1]
        except IndexError as e:
            logger.err(e, non_fatal=True)

        with open('test.log', 'r', encoding='utf-8') as r_file:
            self.assertEqual('ERROR - IndexError: list index out of range',
                             r_file.read().split('\n')[0].split('test - ')[1])
        mocked_fun.assert_not_called()

    @mock.patch("sys.exit")
    def test_fatal_err(self, mocked_fun):
        logger = Logger('test')
        logger.err('abc')

        mocked_fun.assert_called_with(1)  # sys.exit(1) was called

        with open('test.log', 'r', encoding='utf-8') as r_file:
            self.assertEqual('ERROR - abc', r_file.read().split('\n')[0].split('test - ')[1])
