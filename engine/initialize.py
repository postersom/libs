import time
from datetime import datetime
from datetime import timedelta
from timeit import default_timer as timer
from engine import utils
from engine import constants
from engine import logger as log


RUNTIME = constants.RUNTIME


def test_suite():
    pass


def final_test_suite():
    pass


def test_case():
    RUNTIME['start_time'] = timer()
    log.message('-' * 100)
    log.message(f'SERIAL NUMBER:  {utils.get_variable("${serial_number}")}')
    log.message(f'FAMILY:         {utils.get_variable("${odc_family}").upper()}')
    log.message(f'TEST MODE:      {utils.get_variable("${test_mode}").upper()}')
    log.message(f'SLOT TEST:      {utils.get_variable("${slot_location}")}')
    log.message(f'SCRIPT VERSION: {utils.get_variable("${script_version}")}')
    log.message(f'STEP TEST NAME: {utils.get_variable("${TEST NAME}")}')
    log.message(f'START TIME:     {datetime.now().isoformat()[:-3]} ({time.strftime("%Z")})')
    log.message('-'*100)
    if str(utils.get_variable("${PREV TEST STATUS}")) == 'FAIL':
        utils.fail('Skipping Testcase because the status of the previous test case is FAILED.')


def final_test_case():
    log.message('-'*100)
    log.message(f"END TIME: {datetime.utcnow().isoformat()[:-3]}")
    log.message(f"RUN TIME: {str(timedelta(seconds=timer() - RUNTIME['start_time']))[:-3]}")
    log.message('-'*100)
