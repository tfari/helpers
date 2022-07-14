import os
from unittest import TestCase
from backup.helpers.helpers.excel_writer import ExcelWriter, BadKey, DifferentNumberOfKeys, UnexpectedHeadersInFile, NonExistentHeaderName


class TestExcelWriter(TestCase):
    def test_add(self):
        x = ExcelWriter('aa', ['a', 'b'])
        ok_keys = {'a': 1, 'b': 2}
        extra_keys = {'a': 0, 'b': 1, 'c': 2}
        missing_keys = {'a': 0}
        bad_keys = {'a': 0, 'd': 1}

        # Tests function doesnt raise extra thing
        self.assertEqual(None, x.add(ok_keys))

        # Tests exceptions
        self.assertRaises(DifferentNumberOfKeys, x.add, extra_keys)
        self.assertRaises(DifferentNumberOfKeys, x.add, missing_keys)
        self.assertRaises(BadKey, x.add, bad_keys)

        # Tests function does what it has to do
        self.assertEqual([ok_keys], x.data)

    def test_order_by(self):
        x = ExcelWriter('a', ['a', 'b'])
        data_1 = {'a': 0, 'b': 1}
        data_2 = {'a': 1, 'b': 0}
        x.add(data_1)
        x.add(data_2)

        # Tests function doesnt raise extra thing
        self.assertEqual(None, x.order_by('a'))

        # Test exceptions
        self.assertRaises(NonExistentHeaderName, x.order_by, 'c')

        # Test function does what it has to do
        x.order_by('b')
        self.assertEqual([data_2, data_1], x.data)
        x.order_by('a')
        self.assertEqual([data_1, data_2], x.data)

    def test__check_file_headers(self):
        good_headers = ExcelWriter('test_clean', ['a', 'b'])
        bad_headers = ExcelWriter('test_check_file_headers', ['a', 'b', 'c'])

        # Tests function doesnt raise extra thing
        self.assertEqual(None, good_headers.write())

        os.remove('test_clean.xlsx')  # Clean up

        # Tests exceptions
        self.assertRaises(UnexpectedHeadersInFile, bad_headers.write)

