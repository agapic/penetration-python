import string
import hashlib
from itertools import product

CHARSET = string.ascii_lowercase +  string.digits
MAX_LENGTH = 5
NUM_PROCESSES = None # defaults to all available cores

HASHALG = "md5"
HASH = "5a105e8b9d40e1329780d62ea2265d8a"

PAIRS = ["".join(t) for t in product(CHARSET, repeat=2)]

def make_bases(count):
    bases = [PAIRS] * (count // 2)
    if count & 1:
        bases.insert(0, CHARSET)
    return bases

# string_gen is what the workers run.  Everything else
# runs in the main program.
def string_gen(prefix, suffix_len, length):
    # Generate all strings of length `length` starting with `prefix`.
    # If length > suffix_len, only the last suffix_len characters
    # need to be generated.
    if length <= suffix_len:
        assert prefix == ""
        bases = make_bases(length)
    else:
        assert len(prefix) + suffix_len == length
        bases = make_bases(suffix_len)
    for t in product(*bases):
        result = prefix + "".join(t)
        # do something with result
        if hashlib.new(HASHALG, result).hexdigest() == HASH:
            return result

def record_done(result):
    global all_done, the_secret
    print ".",
    if result is not None:
        print
        the_secret = result
        all_done = True
        pool.close()
        pool.terminate() # stop all workers! we're done

def do_work(pool, strings_per_chunk=1000000):
    global all_done, the_secret
    all_done = False
    the_secret = None
    # What's the most chars we can cycle through without
    # exceeding strings_per_chunk?
    N = len(CHARSET)
    suffix_len = 1
    while N**suffix_len <= strings_per_chunk:
        suffix_len += 1
    suffix_len -= 1
    print "workers will cycle through the last", suffix_len, "chars"

    # There's no point to splitting up very short strings.
    max_short_len = min(suffix_len, MAX_LENGTH)
    for length in range(1, max_short_len + 1):
        pool.apply_async(string_gen, args=("", suffix_len, length),
                         callback=record_done)
        if all_done:
            return
    # And now the longer strings.
    for length in range(max_short_len + 1, MAX_LENGTH + 1):
        for t in product(*make_bases(length - suffix_len)):
            prefix = "".join(t)
            pool.apply_async(string_gen, args=(prefix, suffix_len, length),
                             callback=record_done)
            if all_done:
                return

if __name__ == "__main__":
    import multiprocessing
    pool = multiprocessing.Pool(NUM_PROCESSES)
    do_work(pool)
    pool.close()
    pool.join()
    if the_secret is None:
        print "didn't crack it!"
    else:
        print "the plaintext is", repr(the_secret)