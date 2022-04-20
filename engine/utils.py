import time
import signal
import traceback
from robot.libraries.BuiltIn import BuiltIn
from engine import logger as log
from engine import conn
from engine import redis_lib
from engine import sync_groups


RDB = redis_lib.RDB


class APDicts:
    userdict = {}


class Structure:
    def __init__(self, **entries):
        self.__dict__.update(entries)


def get_variable(key):
    return BuiltIn().get_variable_value(key)


def get_variables():
    return BuiltIn().get_variables()


def get_container_info():
    info = Structure(area=BuiltIn().get_variable_value('${SUITE_NAME}'),
                     container=BuiltIn().get_variable_value('${slot_location}'),
                     containers=list(conn.CONTAINER.keys()),
                     odc_family=BuiltIn().get_variable_value('${odc_family}'),
                     test_mode=BuiltIn().get_variable_value('${test_mode}'),
                     serial_number=BuiltIn().get_variable_value('${serial_number}'),
                     username=BuiltIn().get_variable_value('${operation_id}'))
    return info


def get_iss_mode():
    return Structure(odc_family=BuiltIn().get_variable_value('${odc_family}'))


def fail(msg=None):
    msg = msg if msg else f"{BuiltIn().get_variable_value('${TEST NAME}')}: FAILED"
    log.error(msg)
    if conn.SYNC_GROUPS:
        RDB.hdel(sync_groups.get_sync_container_name(), BuiltIn().get_variable_value('${slot_location}'))
    BuiltIn().fail(msg=msg)


def fatal_error(msg=None):
    msg = msg if msg else f"{BuiltIn().get_variable_value('${TEST NAME}')}: FAILED"
    log.error(msg)
    BuiltIn().fatal_error(msg=msg)


def cache_data(k, v):
    RDB.set(f"{sync_groups.get_sync_container_name()}|{k}", v)


def get_cached_data(k):
    return RDB.get(f"{sync_groups.get_sync_container_name()}|{k}")


def delete_cached_data(k):
    RDB.delete(f"{sync_groups.get_sync_container_name()}|{k}")


def formatted_seconds(seconds):
    """Given number of seconds, return a string formatted in "hh:mm:ss"

    :param (float | int)  seconds: number of seconds to convert to a formatted string.
    :return: string
    """
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f'{h}:{m:02d}:{s:02d}'


class TimeIt(object):
    __slots__ = '_start_time', '_duration', '_running'

    def __init__(self):
        self._start_time = None
        self._duration = 0.0
        self._running = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self):
        self._start_time = time.time()
        self._running = True

    def stop(self):
        self._duration = time.time() - self._start_time
        self._running = False

    @property
    def running(self):
        return self._running

    @property
    def duration(self):
        if self._duration:
            return self._duration
        else:
            return time.time() - self._start_time


class Timeout(object):
    """Timeout class using Alarm signal

    Usage:

    with Timeout(3, 'do something within'):
        do something within 0:03:00, otherwise, failed
    """

    def __init__(self, timeout_secs, msg='Timeout after'):
        self._timeout_secs = int(timeout_secs)
        self.msg = msg
        self._start_time = None
        self._duration = 0.0
        self._running = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

    def _raise_timeout(self, *args):
        """Callback function that fail after the timer expires."""
        self._duration = time.time() - self._start_time
        self._running = False
        fail(f'{self.msg} ~ {formatted_seconds(self._timeout_secs)}')

    def start(self):
        """Starts the timer."""
        self._start_time = time.time()
        self._running = True
        signal.signal(signal.SIGALRM, self._raise_timeout)
        signal.alarm(self._timeout_secs)

    def stop(self):
        """Stops the timer."""
        signal.alarm(0)
        self._duration = time.time() - self._start_time
        self._running = False

    @property
    def timeout_secs(self):
        return self._timeout_secs

    @property
    def running(self):
        return self._running

    @property
    def duration(self):
        if self._duration:
            return self._duration
        else:
            return time.time() - self._start_time


def iss_service(func):
    def wrapper(*args, **kwargs):
        try:
            log.info(f'---> Starting Step "{BuiltIn().get_variable_value("${TEST NAME}")}" ({func.__module__}.{func.__name__})')
            return func(*args, **kwargs)
        except AssertionError:
            raise
        except:
            log.error(traceback.format_exc())
            fail(traceback.format_exc())
    return wrapper
