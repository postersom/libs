import re
from engine import conn
from engine import logger as log
from engine import sequence
from engine import sync_groups
from engine import initialize
from engine import questions
from engine import utils
from psu import power_control
from hipot import hipot


RDB = utils.RDB
apdicts = utils.APDicts()
get_variables = utils.get_variables()
PowerControlHandler = power_control.PowerControlHandler
HipotHandler = hipot.HipotHandler
TimeIt = utils.TimeIt


def ask_questions(question, picture_path, html, timeout=60):
    """
    :param question:
    :param picture_path:
    :param html:
    :param timeout:
    :return:
    """
    with TimeIt() as t:
        answer = questions.ask_questions(question=question,
                                         picture_path=picture_path,
                                         html=html,
                                         timeout=timeout)
    log.info(f'The user answered {answer} in {utils.formatted_seconds(t.duration)} seconds')
    return answer


def get_container_info():
    """
    - area: The test area for this container.
    - container: The name of this container
    - containers: The name of this containers
    - odc_family: The ODC family for this container.
    - test_mode: The test mode for this container.
    - serial_number: The serial number associated with this container.
    - username: The user name that started the test.
    :rtype: str
    """
    return utils.get_container_info()


def get_iss_mode():
    """
    :rtype: str
    :return: Production or Debug
    """
    return utils.get_iss_mode()


def getconnections():
    return conn.connection_protocol()


def strip_ansi_escape_chars(text):
    """Remove any ANSI escape characters found within the given text.

    :param str text: Text containing ANSI escape characters to be stripped.
    :return str: text with ANSI escape characters removed.
    """
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)


def add_sync_containers():
    sync_groups.add_sync_containers()


def sync_group(group_name, timeout=60):
    """Used to sync a group of containers

        This function will synchronize containers defined by group_name using:
            test_station.add_sync_group(group_name, list_of_containers_objects)
            in a _config file

        All containers set up to synchronize for this group will rendezvous at this function until all running
        containers are at this statement.

        The optional leader module/function will run by a random member container.  There is no way to enforce which
        container will run this function. Anything returned from the leader function will be returned by this function to
        all containers.

        The leader function must not call another sync with same containers, else a deadlock may occur.

        :param str group_name: The name (unique within a Test Station) of the group of containers to sync with.
        :param int timeout: Will raise timeout exception if synchronization takes longer than timeout (in seconds).
            this includes the time it takes the leader to do its option function, default is 1 minutes.
        :param dict kwargs: parameter/s to be passed to the leader function, optional.
        :return: the result of the leader function called or None if nothing.
        """

    return sync_groups.sync_group(group_name=group_name,
                                  timeout=timeout)


def get_sync_container():
    """
    Example 1:
        data = get_sync_container()
        data.name or data.timeout or data.containers

    Example 2:
        get_sync_container().name or get_sync_container().timeout or get_sync_container().containers
    """
    return sync_groups.get_sync_container()


def get_sync_container_name():
    """
    :return str: The container sync value name:
    """
    return sync_groups.get_sync_container_name()


def get_running_sync_containers():
    """
    :return str: The containers sync value in the group to run:
    """
    return sync_groups.get_running_sync_containers()


def cache_data(k: str, v: str):
    """Used to cache key/value pair information for persistence between process.

    Can be used to send data to another container
    The data saved can be read by any process in iss.
    Be careful of not writing from two place at once.
    :param str k: key
    :param str v: value
    """
    utils.cache_data(k, v)


def get_cached_data(k: str):
    """Returns the value of the data that was cached with cache_data.

    :param str k: Key to look for in the keyvaluestore
    :rtype: str
    :return: value associated with that key, None otherwise
    """
    return utils.get_cached_data(k)


def delete_cached_data(k: str):
    """Deletes the value and key that was cached with cache_data."""
    utils.delete_cached_data(k)


def get_station_configuration(**kwargs):
    return conn.StationConfiguration(**kwargs)


def iss(func):
    return sequence.checkstep(func)


def test_suite():
    initialize.test_suite()


def final_test_suite():
    initialize.final_test_suite()


def test_case():
    initialize.test_case()


def final_test_case():
    initialize.final_test_case()


def fail(msg=None):
    utils.fail(msg)


def fatal_error(msg=None):
    utils.fatal_error(msg)


def iss_service(func):
    return utils.iss_service(func)


def get_variable(key):
    return utils.get_variable(key)
