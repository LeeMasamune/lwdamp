# Example of how to setup and run a client that processes numbers

from __init__ import Configuration, Handler
# Replace `from __init__` with `from lwdamp` in end-user code

cfg = Configuration()

cfg.server = "localhost"

# Use additional parameter as hostname or address
from sys import argv
if len(argv) > 1:
    cfg.server = argv[1]

def compute_something(input, print): # Must have two parameters

    # The `print` parameter can be used instead of built-in print to ensure
    #   no two prinntouts will overlap
    print(f"{input=}", "started", end=" :: ")

    # Simulate a lengthy process
    from time import sleep
    from random import randint
    sleep(randint(4, 10))

    print(f"{input=}", "finished", end=" :: ")

cfg.workload = compute_something

if __name__ == "__main__":
    # .start_client must be in __main__
    Handler(cfg).start_client(4) # Only run 4 processes in parallel
