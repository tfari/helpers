""" Threading / multiprocessing worker dispatcher """
import threading
import multiprocessing
from typing import Callable, Optional

SPAWN, FORK, FORKSERVER = 'spawn', 'fork', 'forkserver'

class WorkerDispatcher:
    """
    Thread or multiprocessing worker dispatcher.
        - FORK and FORKSERVER multiprocessing context types only work on Unix
    """
    VALID_MP_TYPES = [SPAWN, FORK, FORKSERVER]

    def __init__(self, *, is_multiprocessing: bool = False, multiprocessing_context_type: str = ''):
        """
        :param is_multiprocessing:
        :param multiprocessing_context_type:
        :raises InvalidMultiprocessingType: if multiprocessing_type is not one of SPAWN, FORK, FORKSERVER
        """
        self.is_multiprocessing = is_multiprocessing
        self.multiprocessing_type = multiprocessing_context_type
        self.__mp_context = None

        if self.is_multiprocessing:
            if self.multiprocessing_type in WorkerDispatcher.VALID_MP_TYPES:
                self.__mp_context = multiprocessing.get_context(self.multiprocessing_type)
            else:
                raise self.InvalidMultiprocessingType(self.multiprocessing_type)

    def stub_target_threading_worker(self, work_list: list, *args) -> None:
        """ Stub for target threading workers """

    def stub_target_multiprocessing_worker(self, work_list: list, queues: dict, *args) -> None:
        """ Stub for target multiprocessing workers """

    def get_mp_context(self) -> Optional[multiprocessing.context.BaseContext]:
        """ Return using multiprocessing context, if any """
        return self.__mp_context

    def dispatch_threads(self, target: Callable, work_list: list, thread_num: int, *, common_args: tuple = ()) -> None:
        """
        Divide a list of work among a number of threads.

        :param target: worker target function
        :param work_list: list of work to divide among thread_num threads
        :param thread_num: number of threads to divide the work among
        :param common_args: any extra common arguments that might be required
        :raises WorkerDispatcherSetForMultiprocessing: if WorkerDispatcher was set to use multiprocessing
        """
        if self.is_multiprocessing:
            raise self.WorkerDispatcherSetForMultiprocessing()

        # Don't use more threads than there are work_list
        thread_num = len(work_list) if len(work_list) < thread_num else thread_num

        # Separate work in sub-lists
        k_lists = [[] for _ in range(thread_num)]
        [k_lists[(i % thread_num)].append(work_list[i]) for i in range(len(work_list))]

        # Fill in the threads
        threads = []
        for i in range(len(k_lists)):
            threads.append(threading.Thread(target=target, args=[k_lists[i], *common_args]))

        # Run the threads
        [thread.start() for thread in threads]
        [thread.join() for thread in threads]

    def dispatch_processes(self, target: Callable, work_list: list, proc_num: int, queue_names: tuple,
                           *, common_args: tuple = ()) -> dict[str: multiprocessing.Queue]:
        """
        Divide a list of work among a number of processes. Use queues to hold state between processes when the
        multiprocessing context type is spawn, or if the target platform is not known (Spawn is default for
        Windows/OSx, so the shared scope of Fork contexts only works on Unix)

        :param target: worker target function
        :param work_list: list of work to divide among proc_num processes
        :param proc_num: number of processes to divide the work among
        :param queue_names: names to use as keys for a dictionary of Queues
        :param common_args: any extra common arguments that might be required
        :raises WorkerDispatcherSetForThreading: if WorkerDispatcher was set to use threading
        :return: a dictionary of {queue_name: Queue} holding the results produced by the process targets
        """
        if not self.is_multiprocessing:
            raise self.WorkerDispatcherSetForThreading()
        queues = {q: multiprocessing.Manager().list() for q in queue_names}  # Make queues

        # Don't use more processes than there are work_list
        process_num = len(work_list) if len(work_list) < proc_num else proc_num

        # Separate work in sub-lists
        k_lists = [[] for _ in range(process_num)]
        [k_lists[(i % process_num)].append(work_list[i]) for i in range(len(work_list))]

        # Fill in the processes
        processes = []
        for i in range(len(k_lists)):
            processes.append(multiprocessing.Process(target=target, args=(k_lists[i], queues, *common_args)))

        # Run the threads
        [process.start() for process in processes]
        queues = {name: queue for name, queue in queues.items()}
        [process.join() for process in processes]
        return queues

    class WorkerDispatcherSetForMultiprocessing(Exception):
        """ WorkerDispatcher was set to use multiprocessing but was trying to use threading """

    class WorkerDispatcherSetForThreading(Exception):
        """ WorkerDispatcher was set to use threading but was trying to use multiprocessing """

    class InvalidMultiprocessingType(Exception):
        """ Invalid Multiprocessing Type passed into WorkerDispatcher initialization """
