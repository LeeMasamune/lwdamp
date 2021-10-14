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

- This package requires no other third-party package and is envisioned to be 
OS-independent.

- End-user code is fully responsible for the methods that produce inputs and 
consume inputs. It is therefore recommended that the end-user code can monitor 
the progress of these actions.

- There is no automatic load balancing scheme in the implementation.

## Usage

> WIP


## License

[*Unlicense*](LICENSE).
