""" Tests for UniqueDictHandler """
import os
from unittest import TestCase, mock
from helpers.udh import UniqueDictHandler, IGNORE, NOTIFY, BREAK


class TestUniqueDictHandler(TestCase):
    class DC:
        """ Mock dataclass """

        def __init__(self, a, b, c, d):
            self.a, self.b, self.c, self.d = a, b, c, d

        def __eq__(self, other):
            return self.a == other.a \
                   and self.b == other.b \
                   and self.c == other.c \
                   and self.d == other.d

    def test__init__on_repetition_action(self):
        # Check nothing breaks on __init__ with expected on_repetition_action constants
        UniqueDictHandler(on_repetition_action='ignore')
        UniqueDictHandler(on_repetition_action=IGNORE)
        UniqueDictHandler(on_repetition_action='notify')
        UniqueDictHandler(on_repetition_action=NOTIFY)
        UniqueDictHandler(on_repetition_action='break')
        UniqueDictHandler(on_repetition_action=BREAK)

    def test__init__raises_InvalidValue_on_bad_on_repetition_action(self):
        self.assertRaises(UniqueDictHandler.InvalidValue, UniqueDictHandler, on_repetition_action='666')

    def test__setitem__(self):
        udh = UniqueDictHandler(data_type=int)
        udh['a'] = 1
        self.assertEqual(1, udh.elements['a'])

    def test__setitem__raises_InvalidValue_on_wrong_item_type(self):
        udh = UniqueDictHandler()
        self.assertRaises(UniqueDictHandler.InvalidValue, udh.__setitem__, 'a', 1)

    @mock.patch.object(UniqueDictHandler, "_add_repeated")
    def test__setitem__calls___add_repeated_on_repetition(self, mocked_fun):
        udh = UniqueDictHandler(data_type=int)
        udh['a'], udh['a'] = 1, 2
        mocked_fun.assert_called()

    def test__setitem__raises_RepetitionHappened_on_BREAK_on_repetition_action(self):
        udh = UniqueDictHandler(on_repetition_action=BREAK, data_type=int)
        udh['a'] = 1
        self.assertRaises(UniqueDictHandler.RepetitionHappened, udh.__setitem__, 'a', 2)

    @mock.patch("builtins.print")
    def test__setitem__prints_message_on_NOTIFY_on_repetition_action(self, mocked_fun):
        udh = UniqueDictHandler(on_repetition_action=NOTIFY, data_type=int)
        udh['a'], udh['a'] = 1, 2
        mocked_fun.assert_called()

    def test__getitem__(self):
        udh = UniqueDictHandler(data_type=int)
        udh['a'] = 1
        self.assertEqual(1, udh['a'])

    def test__repr__(self):
        udh = UniqueDictHandler(data_type=int)
        udh['a'], udh['a'] = 1, 2
        self.assertEqual("<UniqueDictHandler> Repeated count: 1\n{'a': 1}", repr(udh))

    def test__len__(self):
        udh = UniqueDictHandler(data_type=int)
        self.assertEqual(0, len(udh))
        udh['test'], udh['test2'], udh['test3'] = 1, 2, 3
        self.assertEqual(3, len(udh))

    def test__delitem__(self):
        udh = UniqueDictHandler(data_type=int)
        udh['a'] = 1
        del udh['a']
        self.assertRaises(KeyError, udh.__getitem__, 'a')

    def test_keys(self):
        udh = UniqueDictHandler(data_type=int)
        udh['a'], udh['b'], udh['c'] = 1, 2, 3
        self.assertEqual(['a', 'b', 'c'], list(udh.keys()))

    def test_values(self):
        udh = UniqueDictHandler(data_type=int)
        udh['a'], udh['b'], udh['c'] = 1, 2, 3
        self.assertEqual([1, 2, 3], list(udh.values()))

    def test_items(self):
        udh = UniqueDictHandler(data_type=int)
        udh['a'], udh['b'], udh['c'] = 1, 2, 3
        self.assertEqual([('a', 1), ('b', 2), ('c', 3)], list(udh.items()))

    def test_pop(self):
        udh = UniqueDictHandler(data_type=int)
        udh['a'] = 1
        udh.pop('a')
        self.assertRaises(KeyError, udh.__getitem__, 'a')

    def test__contains__(self):
        udh = UniqueDictHandler(data_type=int)
        udh['a'] = 1
        self.assertEqual(True, 'a' in udh)
        self.assertEqual(False, 'b' in udh)

    def test__iter__(self):
        udh = UniqueDictHandler(data_type=int)
        udh['a'], udh['b'], udh['c'] = 1, 2, 3
        self.assertEqual([1, 2, 3], [x for x in udh])

    def test__add_repeated(self):
        udh = UniqueDictHandler(data_type=int)
        udh['a'] = 0
        udh._add_repeated('a', 1)
        self.assertEqual({'a': [0, 1]}, udh.get_repeated())
        udh._add_repeated('a', 2)
        udh._add_repeated('a', 3)
        self.assertEqual({'a': [0, 1, 2, 3]}, udh.get_repeated())

    def test_get_repeated(self):
        udh = UniqueDictHandler(data_type=int)
        udh['a'], udh['a'] = 1, 2
        self.assertEqual({'a': [1, 2]}, udh.get_repeated())

    def test_len_repeated(self):
        udh = UniqueDictHandler(data_type=int)
        self.assertEqual(0, udh.len_repeated())
        udh['a'], udh['a'], udh['a'], udh['b'], udh['b'], udh['c'] = 1, 2, 3, 4, 5, 6
        self.assertEqual(2, udh.len_repeated())

    def test_clear(self):
        udh = UniqueDictHandler(data_type=int)
        udh['a'] = 1
        udh.clear()
        self.assertEqual([], list(udh.keys()))

    def test_json_read(self):
        udh = UniqueDictHandler(filepath='json_test')
        with open('json_test', 'w', encoding='utf-8') as w_file:
            w_file.write('{"a": {"a": 1}, "b": {"a": 2}}')
        udh.json_read()
        self.assertEqual([{"a": 1}, {"a": 2}], [x for x in udh])
        os.remove('json_test')

    def test_json_read_dataclass(self):
        udh = UniqueDictHandler(filepath='json_test', data_type=TestUniqueDictHandler.DC)
        with open('json_test', 'w', encoding='utf-8') as w_file:
            w_file.write('{"a": {"a": 1, "b": 2, "c": 3, "d": 4}, '
                         '"b": {"a": 1, "b": 2, "c": 3, "d": 4}}')
        udh.json_read()
        self.assertEqual([TestUniqueDictHandler.DC(1, 2, 3, 4),
                          TestUniqueDictHandler.DC(1, 2, 3, 4)], [x for x in udh])
        os.remove('json_test')

    def test_json_write(self):
        udh = UniqueDictHandler(filepath='json_test')
        udh['a'], udh['b'] = {"a": 1}, {"a": 2}
        udh.json_write()
        with open('json_test', 'r', encoding='utf-8') as r_file:
            j_file = r_file.read()
        self.assertEqual('{\n    "a": {\n        "a": 1\n    },\n    "b": {\n        "a": 2\n    }\n}', j_file)
        os.remove('json_test')

    def test_json_write_dataclass(self):
        udh = UniqueDictHandler(filepath='json_test', data_type=TestUniqueDictHandler.DC)
        udh['a'] = TestUniqueDictHandler.DC(1, 2, 3, 4)
        udh.json_write()
        with open('json_test', 'r', encoding='utf-8') as r_file:
            j_file = r_file.read()
        self.assertEqual('{\n    "a": {\n        "a": 1,\n        '
                         '"b": 2,\n        "c": 3,\n        "d": 4\n    }\n}', j_file)
        os.remove('json_test')

    def test_csv_output_dict_key_order(self):
        udh = UniqueDictHandler()
        udh['a'], udh['b'], udh['c'], udh['a'] = {'a': 1, 'b': 2, 'c': 3, 'd': 4},\
                                                 {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5},\
                                                 {'a': 1, 'b': 2, 'c': 3, 'd': 4}, \
                                                 {'a': 1}
        udh.csv_output('csv_output', ('A', 'B', 'C', 'D'), key_order=('a', 'c', 'b', 'd'))

        with open('csv_output', 'r', encoding='utf-8') as r_file:
            csv_file = r_file.read()

        self.assertEqual('"A","B","C","D"\n"1","3","2","4"\n"1","3","2","4"\n"1","3","2","4"\n', csv_file)
        os.remove('csv_output')

    def test_csv_output_dict_row_func(self):
        udh = UniqueDictHandler()
        udh['a'], udh['b'], udh['c'], udh['a'] = {'a': 1, 'b': 2, 'c': 3, 'd': 4},\
                                                 {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5},\
                                                 {'a': 1, 'b': 2, 'c': 3, 'd': 4}, \
                                                 {'a': 1}
        udh.csv_output('csv_output', ('A', 'B', 'C', 'D'),
                       row_fun=lambda e: [e['a']**2, e['b']**2, e['c']**2, e['d']**2])

        with open('csv_output', 'r', encoding='utf-8') as r_file:
            csv_file = r_file.read()

        self.assertEqual('"A","B","C","D"\n"1","4","9","16"\n"1","4","9","16"\n"1","4","9","16"\n', csv_file)
        os.remove('csv_output')

    def test_csv_output_dataclass_key_order(self):
        udh = UniqueDictHandler(data_type=TestUniqueDictHandler.DC)
        udh['a1'], udh['a2'], udh['a3'] = TestUniqueDictHandler.DC(1, 2, 3, 4),\
                                          TestUniqueDictHandler.DC(1, 2, 3, 4),\
                                          TestUniqueDictHandler.DC(1, 2, 3, 4)
        udh.csv_output('csv_output', ('A', 'B', 'C', 'D'), key_order=('a', 'c', 'b', 'd'))

        with open('csv_output', 'r', encoding='utf-8') as r_file:
            csv_file = r_file.read()

        self.assertEqual('"A","B","C","D"\n"1","3","2","4"\n"1","3","2","4"\n"1","3","2","4"\n', csv_file)
        os.remove('csv_output')

    def test_csv_output_dataclass_row_func(self):
        udh = UniqueDictHandler(data_type=TestUniqueDictHandler.DC)
        udh['a1'], udh['a2'], udh['a3'] = TestUniqueDictHandler.DC(1, 2, 3, 4), \
                                          TestUniqueDictHandler.DC(1, 2, 3, 4), \
                                          TestUniqueDictHandler.DC(1, 2, 3, 4)
        udh.csv_output('csv_output', ('A', 'B', 'C', 'D'),
                       row_fun=lambda e: [e.a**2, e.b**2, e.c**2, e.d**2])

        with open('csv_output', 'r', encoding='utf-8') as r_file:
            csv_file = r_file.read()

        self.assertEqual('"A","B","C","D"\n"1","4","9","16"\n"1","4","9","16"\n"1","4","9","16"\n', csv_file)
        os.remove('csv_output')
