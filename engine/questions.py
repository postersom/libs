import time
import requests
import json
from engine import utils
from engine import logger as log


def ask_questions(question, picture_path, html, timeout=60):
    url = 'http://localhost:8080/api/user_interaction'
    slot = utils.get_variable("${slot_location}")
    data = {'slot_location_no': slot,
            'message': question,
            'timeout': timeout,
            'picture': picture_path,
            'html': html,
            'title': ''}
    header = {'Content-Type': 'application/json',
              'Data-Type': 'application/json'}
    log.warning(question)
    requests.post(url, data=json.dumps(data), headers=header)
    with utils.Timeout(timeout, 'The users do not answer questions within'):
        while True:
            response = requests.get(url, params={'slot_location_no': slot}, headers=header).json()
            response = response.get("data")
            if isinstance(response, dict):
                status = response.get("answer")
                reason = response.get("reason")
                log.error(reason) if '-' != reason else None
                if status:
                    return status
            time.sleep(1)
