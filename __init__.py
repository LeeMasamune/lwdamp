"""
Lightweight Wrapper for Distributed Asynchronous MultiProcessing

v0.2.0 b21288
"""

from typing import Any, Callable
from queue import Empty
from multiprocessing import Pool, Manager, Process, Queue
from multiprocessing.managers import BaseManager

################################################################################

class Configuration:

    def __init__(self):
        self.__server = "localhost"
        self.__port = 50286
        self.__authkey = b"lwdamp"
        self.__input_next : Callable[[], Any] = None
        self.__workload : Callable[[Any], Any] = None
        self.__workload_success : Callable[[Any], None] = None
        self.__workload_failure : Callable[[Any], None] = None

    #----------------------------------------------------------------------#
    # Common settings

    @property
    def server(self) -> str:
        return self.__server

    @server.setter
    def server(self, server: str) -> None:
        self.__server = server

    @property
    def port(self) -> int:
        return self.__port

    @port.setter
    def port(self, port: int) -> None:
        try:
            port = int(port)
        except Exception as ex:
            raise ValueError(f"21287.1009 Argument `port` must be a positive integer: {port}") from ex

        if port < 1:
            raise ValueError(f"21287.1010 Argument `port` must be a positive integer: {port}")

        self.__port = port

    @property
    def authkey(self) -> bytes:
        return self.__authkey

    @authkey.setter
    def authkey(self, authkey: bytes) -> None:
        if not isinstance(authkey, bytes):
            raise ValueError(f"21287.1015 Argument `authkey` must be a `bytes` instance")

        self.__authkey = authkey

    #----------------------------------------------------------------------#
    # Server-side settings

    @property
    def input_next(self) -> Callable[[], Any]:
        return self.__input_next

    @input_next.setter
    def input_next(self, func: Callable[[], Any]):
        if not callable(func):
            raise ValueError(f"21287.1117 Argument `func` must be callable: {type(func)=}")

        self.__input_next = func

    #----------------------------------------------------------------------#
    # Client-side options

    @property
    def workload(self) -> Callable[[Any], Any]:
        return self.__workload

    @workload.setter
    def workload(self, func: Callable[[Any], Any]):
        if not callable(func):
            raise ValueError(f"21287.1140 Argument `func` must be callable: {type(func)=}")

        self.__workload = func

    @property
    def workload_success(self) -> Callable[[Any], Any]:
        return self.__workload_success

    @workload_success.setter
    def workload_success(self, func: Callable[[Any], Any]):
        if not callable(func):
            raise ValueError(f"21287.1142 Argument `func` must be callable: {type(func)=}")

        self.__workload_success = func

    @property
    def workload_failure(self) -> Callable[[Any], Any]:
        return self.__workload_failure

    @workload_failure.setter
    def workload_failure(self, func: Callable[[Any], None]):
        if not callable(func):
            raise ValueError(f"21287.1143 Argument `func` must be callable: {type(func)=}")

        self.__workload_failure = func

################################################################################

class Handler:

    #----------------------------------------------------------------------#
    # Public members

    def __init__(self, cfg: Configuration):
        if not isinstance(cfg, Configuration):
            raise ValueError(f"21288.0028 Argument `cfg` must be a `Configuration` instance: {type(cfg).__name__}")

        self.__cfg = cfg

        self.__q_incoming : Queue = None # Must be initialized in server mode
        self.__q_outgoing : Queue = None # Must be initialized in server mode

    def start_server(self):
        """Starts the server."""

        if not callable(self.__cfg.input_next):
            raise ValueError(f"21288.0914 Configuration `input_next` must be set to a callable instance: type(input_next)={type(self.__cfg.input_next).__name__}")

        self._serve()

    def start_client(self, n_processes: int):
        """Starts the client with the specified pool size."""

        if not callable(self.__cfg.workload):
            raise ValueError(f"21288.0915 Configuration `workload` must be set to a callable instance: type(workload)={type(self.__cfg.workload).__name__}")

        self._client_loop(n_processes)

    #----------------------------------------------------------------------#
    # Protected members

    class _Master(BaseManager):
        # The defs in this class helps with intellisense
        def get_incoming_queue(self) -> Queue: ...
        def get_outgoing_queue(self) -> Queue: ...

    def _Master__init__(self, server) -> _Master:
        return self._Master(address=(server, self.__cfg.port), authkey=self.__cfg.authkey)

    def _Master_register_methods(self, register_with_callable: bool):

        #---------------------------------------------------------------#
        # Do not modify these queues directly outside of this class

        # get_incoming_queue
        if register_with_callable:
            self.__q_incoming = Queue() # XXX Can have maxsize
            self._Master.register("get_incoming_queue", callable=lambda: self.__q_incoming)
        else:
            self._Master.register("get_incoming_queue")

        # get_outgoing_queue
        if register_with_callable:
            self.__q_outgoing = Queue()
            self._Master.register("get_outgoing_queue", callable=lambda: self.__q_outgoing)
        else:
            self._Master.register("get_outgoing_queue")

        #---------------------------------------------------------------#

        pass

    def _serve(self):
        self._Master_register_methods(True)

        # Start message queue master
        Process(target=self._server_work,
                kwargs={

                    # These queues MUST be initialized at registration with callback
                    "q_incoming" : self.__q_incoming,
                    "q_outgoing" : self.__q_outgoing,

                    # "f_input_iter_next" : self.__cfg.input_iterable.__iter__().__next__
                    "f_input_iter_next" : self.__cfg.input_next
                }
            ).start()

        self._Master__init__("").get_server().serve_forever()

    def _connect(self):
        self._Master_register_methods(False)
        master = self._Master__init__(self.__cfg.server)
        master.connect()
        return master

    def _print_loop(self, print_queue: Queue):
        # print_queue must come from a multiprocessing.Manager so it can be shared
        from warnings import warn
        try:
            while True:
                d = print_queue.get(block=True)
                if len(d) == 0:
                    break

                args = d["args"]
                kwargs = d["kwargs"]
                kwargs["flush"] = True # Always flush
                print(*args, **kwargs)
        # except EOFError as ex:
            # warn(f"21287.1525 {type(ex).__name__} {str(ex)}")
            # pass
        except Exception as ex:
            warn(f"21287.1526 {type(ex).__name__} {str(ex)}")

    def _client_loop(self, n_processes: int):
        if not isinstance(n_processes, int) or n_processes < 1:
            raise ValueError(f"21287.1348 Argument `n_processes` must be a positive integer: {n_processes}")

        with Manager() as manager:

            # Used to block get_next_input_id, so that getting new input_id values
            #   are paused while the entire pool is busy
            input_bloq : Queue = manager.Queue(maxsize=n_processes)

            # Printing controls, allows non-overlapping printout across multiple processes
            print_queue : Queue = manager.Queue()
            print_loop = Process(target=self._print_loop, kwargs={ "print_queue" : print_queue })
            print_loop.start()

            remote_master = self._connect()

            # "Incoming" queue of server
            remote_q_incoming = remote_master.get_incoming_queue()

            # "Outgoing" queue of server
            remote_q_outgoing = remote_master.get_outgoing_queue()

            with Pool(processes=n_processes) as pool:

                while True:
                            # This object() is just a dummy value, it has no actual use
                    input_bloq.put(object(), block=True) # Blocks if queue is full

                    input_id = self._get_next_input_id(remote_q_incoming, remote_q_outgoing)
                    if input_id is None:
                        break

                    # Do workload on input, no use for returned AsyncResult
                    pool.apply_async(func=self._client_work,
                            # args=...,
                            kwds={ "input_bloq" : input_bloq,
                                    "input_id" : input_id,
                                    "print_queue" : print_queue,
                                    "workload" : self.__cfg.workload },
                            callback=self.__cfg.workload_success,
                            error_callback=self.__cfg.workload_failure
                        )

                pool.close()
                pool.join() # Wait for remaining processes to exit

            print_queue.put(dict()) # Empty dict means stop
            print_loop.join()

    def _get_next_input_id(self, remote_q_incoming: Queue, remote_q_outgoing: Queue):
        try:
            try: # Try to get a value immediately
                return remote_q_outgoing.get(block=False)
            except Empty:
                pass # Ignore empty
            except Exception as ex:
                if __debug__: breakpoint()
                raise

            # Request for an input
            remote_q_incoming.put(object(), block=True) # Allow block so server.py can have client.py wait

            # Wait for a response, return response immediately when available
            return remote_q_outgoing.get(block=True)

        except Exception as ex:
            if __debug__: breakpoint()
            raise

    def _client_work(self, input_bloq: Queue, input_id, print_queue: Queue, workload: Callable[[Any], Any]):
        try:
            def print_enqueue(*args, **kwargs):
                try:
                    print_queue.put({ "args" : args, "kwargs" : kwargs })
                except:
                    print(*args, **kwargs)

            return workload(input_id, print_enqueue)

        finally:
            try: input_bloq.get_nowait() # Unblock get_input only on workload end
            except Empty: pass # Ignore exception when input_bloq is empty

    def _server_work(self, q_incoming: Queue, q_outgoing: Queue, f_input_iter_next: Callable[[], None]):
        """Looks for a message from the `incoming` pile,
        gets an input, puts the input into the `outgoing` pile."""

        while True:
            print(".", end="", flush=True) # status: Waiting for messages
            q_incoming.get(block=True) # Wait for incoming message

            print(":", end="", flush=True) # status: Got new message, ready to get input
            input = f_input_iter_next() # Run user-set function to get next input
            print("+", end="", flush=True) # status: Input collected

            q_outgoing.put(input, block=True) # Add input to outgoing messages
            if input is None:
                print("_", end="", flush=True) # status: `None` sent to outgoing
            else:
                print("#", end="", flush=True) # status: Input sent to outgoing

################################################################################
