# helpers

Collection of useful reusable helper classes / functions

* [UniqueDictHandler](helpers/udh.py): Thread-locked dictionary handler that 
  does not allow, and records, repeated key assignations. Reads and writes data to JSON, and implements a CSV output 
  method. Can work with custom dataclasses as elements. [TESTS](tests/test_udh.py)

* [Logger](helpers/logger.py): Wrapper for stream and file handling Logger. In case of fatal errors call **sys.
  exit(1)** and exit process. [TESTS](tests/test_logger.py)

* [WorkerDispatcher](helpers/worker_dispatcher.py): Threading / multiprocessing worker dispatcher.
  [TESTS](tests/test_worker_dispatcher.py)

* [Notifier](helpers/notifier.py): Simple notification system using either [notify-send](https://vaskovsky.net/notify-send/) 
  or Tk. [TESTS](tests/test_notifier.py)