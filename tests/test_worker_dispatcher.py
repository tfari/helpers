""" Tests for WorkerDispatcher """
import multiprocessing
from unittest import TestCase
from helpers.worker_dispatcher import WorkerDispatcher, SPAWN, FORK, FORKSERVER


class TestWorkerDispatcher(TestCase):

    def test__init__multiprocessing_wrong_type_raises_InvalidMultiProcessingType(self):
        self.assertRaises(WorkerDispatcher.InvalidMultiprocessingType,
                          WorkerDispatcher, is_multiprocessing=True, multiprocessing_context_type='666')

    def test__init__multiprocessing_right_start_method(self):
        wd = WorkerDispatcher()
        self.assertIsNone(wd.get_mp_context())

        wd = WorkerDispatcher(is_multiprocessing=True, multiprocessing_context_type=SPAWN)
        self.assertIsInstance(wd.get_mp_context(), multiprocessing.context.SpawnContext)

        # These two will only work on Unix
        wd = WorkerDispatcher(is_multiprocessing=True, multiprocessing_context_type=FORK)
        self.assertIsInstance(wd.get_mp_context(), multiprocessing.context.ForkContext)

        wd = WorkerDispatcher(is_multiprocessing=True, multiprocessing_context_type=FORKSERVER)
        self.assertIsInstance(wd.get_mp_context(), multiprocessing.context.ForkServerContext)

    def test_dispatch_threads_raises_WorkerDispatcherSetForMultiprocessing(self):
        wd = WorkerDispatcher(is_multiprocessing=True, multiprocessing_context_type=SPAWN)
        self.assertRaises(WorkerDispatcher.WorkerDispatcherSetForMultiprocessing,
                          wd.dispatch_threads, wd.stub_target_threading_worker, [], 1)

    def test_dispatch_processes_raises_WorkerDispatcherSetForThreading(self):
        wd = WorkerDispatcher()
        self.assertRaises(WorkerDispatcher.WorkerDispatcherSetForThreading,
                          wd.dispatch_processes, wd.stub_target_multiprocessing_worker, [], 1, ('Test',))

    def test_dispatch_threads(self):
        def __target(work_list, output_var):
            for wl in work_list:
                output_var.append(wl)

        result_var = []
        wd = WorkerDispatcher()
        wd.dispatch_threads(__target, [1, 2, 3, 4, 5, 6], 2, common_args=(result_var,))

        self.assertEqual(6, len(result_var))
        self.assertEqual(21, sum(result_var))

    def test_dispatch_processes(self):
        def __target(work_list, queues):
            for wl in work_list:
                queues['test'].append(wl)

        wd = WorkerDispatcher(is_multiprocessing=True, multiprocessing_context_type=FORK)  # Cope out for pickling error
        queues_returned = wd.dispatch_processes(__target, [1, 2, 3, 4, 5, 6], 2, ('test',))
        self.assertEqual(6, len(queues_returned['test']))
        self.assertEqual(21, sum(queues_returned['test']))
