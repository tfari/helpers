"""
Thread-locked dictionary handler that does not allow, and records, repeated key assignations.
Reads and writes data to JSON. Implements CSV output method. Can work with custom dataclasses as elements.
"""
import csv
import json
from threading import Lock
from typing import Callable

IGNORE, NOTIFY, BREAK = 'ignore', 'notify', 'break'


class UniqueDictHandler(object):
    """
    Thread-locked dictionary handler that does not allow, and records, repeated key assignations.
    Implements all dict functionality, except that iterates over items, instead of keys.

    Repetitions are saved, and the behaviour on repetitions can be one of the following, set via the
    on_repetition_action keyword argument on instantiation:

    - IGNORE/"ignore" : Ignores repetitions, saves them.
    - NOTIFY/"notify" : Notifies when repetitions happen, saves them.
    - BREAK/"break" : Raises UniqueDictHandler.RepetitionHappened when repetitions happen, saves them.

    During instantiation, the keyword argument data_type can be used to set an element's type other than
    dictionaries, specifically to use with dataclasses. This type is checked on setting new items.

    Reads and writes data to JSON. When using a special data_type, __dict__ will be used to serialize it as JSON.

    Implements a CSV output method that inputs a csv_filepath, a tuple of column header strings, and either a tuple
    of keys to grab values from the dictionary, or to use with getattrs() to grab values if a special dataclass is
    used, or a function to assemble each row that accepts an element as only argument, and returns a list of data to
    use as row values.

    """
    def __init__(self, filepath: str = '', *, on_repetition_action: str = IGNORE, data_type=dict):
        """
        :param filepath: Path to use for json reading/writing
        :param on_repetition_action: How to handle repeated keys: "ignore", "notify": print a message,
            "break": raise UniqueDictHandler.RepetitionHappened
        :param data_type: Type the elements will be, dict by default.
        """
        self.filepath = filepath

        # Check on_repetition_action is either IGNORE, NOTIFY or BREAK
        if on_repetition_action not in (IGNORE, NOTIFY, BREAK):
            raise UniqueDictHandler.InvalidValue(f'"{on_repetition_action}"')
        else:
            self.on_repetition_action = on_repetition_action

        self.data_type = data_type

        self.lock = Lock()
        self.repeated_elements: dict[str, list] = {}
        self.elements: dict[str, object] = {}

    def __setitem__(self, key, item):
        with self.lock:
            if type(item) != self.data_type:
                raise UniqueDictHandler.InvalidValue(f'Expected: {self.data_type}, got: {type(item)} -> {repr(item)}')

            if self.elements.get(key):
                repeated_msg = f'Repeated key: "{key}", new item: {item}, old item: {self.elements.get(key)}'
                self._add_repeated(key, item)
                if self.on_repetition_action is BREAK:
                    raise UniqueDictHandler.RepetitionHappened(repeated_msg)
                elif self.on_repetition_action is NOTIFY:
                    print(f'<UniqueDictHandler> {repeated_msg}')
            else:
                self.elements[key] = item

    def __getitem__(self, key):
        return self.elements[key]

    def __repr__(self):
        return f'<UniqueDictHandler> Repeated count: {self.len_repeated()}\n{repr(self.elements)}'

    def __len__(self):
        return len(self.elements)

    def __delitem__(self, key):
        del self.elements[key]

    def keys(self):
        """ Get keys """
        return self.elements.keys()

    def values(self):
        """ Get values """
        return self.elements.values()

    def items(self):
        """ Get items """
        return self.elements.items()

    def pop(self, *args):
        """ Pop """
        return self.elements.pop(*args)

    def __contains__(self, item):
        return item in self.elements

    def __iter__(self):
        return iter(list(self.elements.values()))

    def _add_repeated(self, key, item) -> None:
        """ Add a new item to the repeated_elements dict.
        If it is the first repetition assign it a list with the first
        element being the already existing one in elements dict. """
        if self.repeated_elements.get(key):
            self.repeated_elements[key].append(item)
        else:
            self.repeated_elements[key] = [self.elements.get(key), item]

    def get_repeated(self) -> dict:
        """ Get the repeated elements """
        return self.repeated_elements

    def len_repeated(self) -> int:
        """ Get the amount of repeated elements """
        return len(self.repeated_elements)

    def json_read(self, *, filepath: str = '') -> None:
        """
        Read elements from JSON
        :param filepath: filepath to use instead of self.filepath
        """
        with open(filepath if filepath else self.filepath, 'r', encoding='utf-8') as rf:
            json_from_file = json.load(rf)
        for key, value in json_from_file.items():
            if self.data_type is dict:
                self[key] = value
            else:
                self[key] = self.data_type(**value)

    def json_write(self, *, filepath: str = '') -> None:
        """
        Write elements to JSON
        :param filepath: filepath to use instead of self.filepath
        """
        with open(filepath if filepath else self.filepath, 'w', encoding='utf-8') as wf:
            if self.data_type is dict:
                elements = self.elements
            else:
                elements = {k: self[k].__dict__ for k in self.keys()}
            json.dump(elements, wf, indent=4)

    def csv_output(self, csv_filepath, headers: tuple, *, key_order: tuple = ('',),
                   row_fun: Callable = None) -> None:
        """
        Output data into a CSV file. Pass either key_order or row_fun.

        If row_fun is passed, row_fun is called for each element, and expects a list return to use as row data.

        If key_order is passed instead, the strings will be used as keys (if data_type is dict, or has not been
        passed), or as instance variable names if data_type is a dataclass.

        :param csv_filepath: path for the CSV
        :param headers: column headers
        :param key_order: if this is passed, use these key/variable names of dict/dataclass elements to fill in the
        respective columns of each row
        :param row_fun: (function) if this is passed, call this function with the element for each row, expects a list
        return to write as row
        """

        with open(csv_filepath, 'w', encoding='utf-8', newline='') as wf:
            csv_writer = csv.writer(wf, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
            csv_writer.writerow(headers)

            for element in self:
                if row_fun:
                    row = row_fun(element)
                else:
                    if self.data_type is dict:
                        row = [element[k] for k in key_order]
                    else:
                        row = [element.__getattribute__(k) for k in key_order]

                csv_writer.writerow(row)

    class InvalidValue(Exception):
        """ Invalid Value """

    class RepetitionHappened(Exception):
        """ Repetition Happened """
