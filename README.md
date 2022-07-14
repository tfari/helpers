# helpers

Collection of useful reusable helper classes / functions

* [UniqueDictHandler](helpers/udh.py): Thread-locked dictionary handler that 
  does not allow, and records, repeated key assignations. Reads and writes data to JSON, and implements a CSV output 
  method. Can work with custom dataclasses as elements. [TESTS](tests/test_udh.py)