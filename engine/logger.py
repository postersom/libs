import os
from datetime import datetime
from engine import utils


def message(msg):
    raw_path = utils.get_variable("${Raw_logs_path}")
    test_name = utils.get_variable("${TEST NAME}")
    os.makedirs(f'{raw_path}') if not os.path.isdir(f'{raw_path}') else None
    for i in [test_name, 'sequences_logs']:
        with open(f'{raw_path}/{i}.txt', 'a+', encoding="utf-8") as f:
            f.write(f'{msg}\r')


def timestamp_log(msg):
    raw_path = utils.get_variable("${Raw_logs_path}")
    test_name = utils.get_variable("${TEST NAME}")
    test_mode = utils.get_variable('${test_mode}')
    os.makedirs(f'{raw_path}') if not os.path.isdir(f'{raw_path}') else None
    for i in [test_name, 'sequences_logs']:
        with open(f'{raw_path}/{i}.txt', 'a+', encoding="utf-8") as f:
            if i == 'sequences_logs':
                f.write(f'[{datetime.now().isoformat()[:-3]}]|{test_mode}|{test_name}|: {msg}\r')
            else:
                f.write(f'[{datetime.now().isoformat()[:-3]}]: {msg}\r')


def info(msg):
    timestamp_log(msg=f'{"INFO":<8}: {msg}')


def debug(msg):
    timestamp_log(msg=f'{"DEBUG":<8}: {msg}')


def warning(msg):
    timestamp_log(msg=f'{"WARNING":<8}: {msg}')


def error(msg):
    timestamp_log(msg=f'{"ERROR":<8}: {msg}')
