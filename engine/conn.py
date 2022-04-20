from engine import utils
from engine import constants
from engine.protocols import Client

CONTAINER = constants.CONTAINER
SYNC_GROUPS = constants.SYNC_GROUPS


class StationConfiguration(object):
    def __init__(self, name=None):
        self.container = name

    @staticmethod
    def add_container(name):
        CONTAINER[name] = {}
        return StationConfiguration(name)

    def add_connection(self, name, **kwargs):
        CONTAINER[self.container].update({name: kwargs})

    @staticmethod
    def add_sync_group(name, containers, timeout=60):
        containers = [cont.__dict__['container'] for cont in containers]
        [SYNC_GROUPS.update({container: {'name': name,
                                         'timeout': timeout,
                                         'containers': containers}}) for container in containers]


def connection_protocol():
    return dict([(k, Client(**v)) for k, v in CONTAINER[utils.get_container_info().container].items()])


