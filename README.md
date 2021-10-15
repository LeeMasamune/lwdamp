# lwdamp

*Lightweight Wrapper for Distributed Asynchronous MultiProcessing*

## Purpose

The goal of this package is to be able to *quickly* and *easily* setup and
deploy the processing a large number of inputs by distributing the inputs
accross multiple parallel worker subprocesses and accross multiple machines.

## Features and Limitations

- The implementation leverages the features of the Python built-in
[`multiprocessing`](https://docs.python.org/3.9/library/multiprocessing.html)
module. As such, any limitation of the said package is assumed to be inherited.

- This package requires no other third-party package and is expected to be
OS-independent.

- End-user code is fully responsible for the methods that produce inputs and
consume inputs. It is therefore recommended that the end-user code can monitor
the progress of these actions.

- There is no automatic load balancing scheme in the implementation. End-user
code may set the maximum number of local subprocesses to maintain, but this
maximum will not dynamically change during the lifetime of the parent process
running the subprocess pool.

- This package is not meant for fast communication between processes.

## Usage

> WIP

## Changelog

### v0.2.0

- **Usage**
    - Upd: Second parameter of `Configuration.workload` (`print` proxy) utilizes parameters of the Python built-in `print(...)`
    - Upd: Handler.start_client now requires `n_processes` argument
- **Internal**
    - Fix: `Handler.start_client` now ends gracefully
    - Upd: Default port and authkey
    - Upd: Additional checking for required functions related to Handler.start_* methods
    - Ren: `mmpp.py` to `__init__.py`, repo dir is now package dir
- **Others**
    - Add: demo scripts

### v0.1.4
- Initial version (package was then named mmpp.py).

## License

[*Unlicense*](LICENSE).
