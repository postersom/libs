import re
import traceback
from engine import logger as log
from engine import utils


def checkstep(func):
    def inner(*args, **kwargs):
        name = utils.get_variable("${TEST NAME}")
        log.timestamp_log(f'---> Starting Step "{name}" ({func.__module__}.{func.__name__})')
        try:
            result = func(*args, **kwargs)
            if 'PASS' == result:
                return True
            elif 'FAIL' == result:
                utils.fail()
            else:
                log.error(f'Missing return statement. Please return "PASS" or "FAIL"')
        except:
            log.warning(traceback.format_exc())
        utils.fail()
    return inner
