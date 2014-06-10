import threading


def communicate_with_timeout(proc, timeout, input_=None):
    '''
    Interact with process with timeout.

    Communicates with subprocess for timeout seconds.
    If process fails to finish in that period, it gets killed
    using proc.kill() (so its children will not be killed).
    Process shouldn't be communicated with before calling this function.

    Args:
        proc: Popen object.
        timeout: int with number of seconds to wait for proc to finish.
        input_: bytes object with stdin to pipe into proc, or None.

    Returns:
        None if timeout seconds have passed, or result of proc.communicate().
    '''
    waker = threading.Event()
    proc_killed = [False]

    def killer():
        waker.wait(float(timeout))
        if proc.poll() is None:
            proc_killed[0] = True
            try:
                proc.kill()
            except OSError:
                pass

    t = threading.Thread(target=killer)
    t.start()
    result = proc.communicate(input=input_)
    waker.set()
    t.join()
    if proc_killed[0]:
        return None
    else:
        return result
