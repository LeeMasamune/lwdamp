# Example of how to setup and run a server that serves numbers

from __init__ import Configuration, Handler
# Replace `from __init__` with `from lwdamp` in end-user code

cfg = Configuration()

ct_count = 0
max_count = 20 # Only serve this many numbers

def get_next_number(): # Must return None if there are no more inputs
    global ct_count, max_count # Globals does work
    ct_count += 1
    if ct_count > max_count:
        # Return None to tell any client to stop
        return None
    from random import randint
    return ct_count * 100 + randint(1, 99)

cfg.input_next = get_next_number

if __name__ == "__main__":
    # .start_server must be in __main__
    Handler(cfg).start_server()
