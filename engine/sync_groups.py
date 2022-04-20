import os
import re
import time
from engine import logger as log
from engine import utils
from engine import conn
from engine import redis_lib


RDB = redis_lib.RDB


class Structure:
    def __init__(self, **entries):
        self.__dict__.update(entries)


def sync_group(group_name, timeout=60):
    sync = get_sync_container()
    group = f"{sync.name}::{group_name}"
    log.info(f"Sync Group Name      = {group}")
    log.info(f"Sync Containers List = {list(RDB.hkeys(sync.name))}")
    RDB.sadd(group, utils.get_variable('${slot_location}'))
    with utils.Timeout(timeout, 'Timeout Sync Group'):
        while True:
            if RDB.scard(group) <= 0 or RDB.scard(group) == len(RDB.hkeys(sync.name)):
                break
            time.sleep(.009)
    RDB.delete(group)
    return True


def add_sync_containers():
    slot = utils.get_variable('${slot_location}')
    sync = get_sync_container()
    log.info(f"Sync Group Name      = {sync.name}")
    [RDB.delete(key) for key in RDB.keys('*') if sync.name in key]
    time.sleep(sync.timeout)
    RDB.hset(sync.name, slot, utils.get_variable('${Raw_logs_path}'))
    start_time = time.time()+sync.timeout
    while time.time() <= start_time:
        if len(RDB.hgetall(sync.name)) == len(sync.containers):
            break
    log.info(f"Sync Containers List = {RDB.hkeys(sync.name)}")
    log.info(f"Sync Containers Path = {RDB.hvals(sync.name)}")
    log.info(f"Sync Group Time Out  = {sync.timeout}")


def get_sync_container():
    sync = conn.SYNC_GROUPS[utils.get_variable('${slot_location}')]
    return Structure(**sync)


def get_sync_container_name():
    return get_sync_container().name


def get_running_sync_containers():
    return RDB.hkeys(get_sync_container().name)
