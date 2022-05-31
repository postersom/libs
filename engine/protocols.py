import os
import re
import time
import sys
import getpass
import paramiko
import codecs
import hashlib
import multiprocessing as mp
from engine import utils
from engine import conn
from engine import redis_lib
from engine import sync_groups as sync
from engine import logger as log


RDB = redis_lib.RDB


def strip_ansi_codes(s):
    return re.sub(r'\x1b\[([0-9,A-Z]{1,2}[mKH]?(;[0-9]{1,2})?(;[0-9]{3})?)?[mKH]?', '', s)


def write_to_file(path, msg):
    os.makedirs(f'{path}') if not os.path.isdir(f'{path}') else None
    for i in [utils.get_variable("${TEST NAME}"), 'buffer_logs']:
        with open(f'{path}/{i}.raw', 'a+', encoding="utf-8") as f:
            f.write(msg)


def save_log(msg, shared):
    if shared:
        for path in RDB.hvals(sync.get_sync_container_name()):
            process = mp.Process(target=write_to_file, args=(path, msg))
            process.start()
    else:
        write_to_file(utils.get_variable('${Raw_logs_path}'), msg)


def get_master_container():
    return utils.get_variable('${slot_location}') == sync.get_running_sync_containers()[0]


class Client(object):
    def __init__(self, protocol, host=None, shared_conn=False, user=None, password=None, timeout=30, port=None,
                 baudrate=9600, bytesize=8, stopbits=1, local_prompt=None, encoding='ISO-8859-1',
                 display=False, *args, **kwargs):
        self.protocol = protocol.lower()
        self.shared_conn = shared_conn
        self.host = host
        self.user = user
        self.password = password
        self.timeout = timeout
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.stopbits = stopbits
        self.local_prompt = local_prompt if local_prompt else user
        self.display = display
        self.decoder = codecs.getincrementaldecoder(encoding)()
        self.client = paramiko.SSHClient()
        self.channel = None
        self.last_match = None
        self.recbuf = None
        self.sync_id = '6adf97f83acf6453d4a6a4b1070f3754'
        self.__dict__.update(kwargs)

    def __del__(self):
        self.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.protocol not in ['ssh', 'telnet', 'serial']:
            utils.fail(f'No config protocol {self.protocol}, Please config protocol ["telnet", "serial", "ssh"]')

        if self.protocol == 'ssh':
            os.system(f'ssh-keygen -R {self.host}')
            time.sleep(.1)
            self.client.connect(hostname=self.host, username=self.user, password=self.password, timeout=self.timeout)
            self.channel = self.client.invoke_shell(width=120, height=48)
            self.expectphrase(self.local_prompt)

        elif self.protocol in ['telnet', 'serial']:
            self.client.connect(hostname='127.0.0.1', username=getpass.getuser(), password='Minipackadmin', timeout=self.timeout)
            self.channel = self.client.invoke_shell(width=120, height=48)

        if not self.shared_conn or self.shared_conn and get_master_container():
            if self.protocol == 'ssh':
                self.display = True
                self.channel.send('\r'.encode())
                self.expectphrase(self.local_prompt, timeout=self.timeout)
            elif self.protocol in ['telnet', 'serial']:
                self.expectphrase(getpass.getuser(), timeout=self.timeout)
                if self.protocol == 'telnet':
                    self.channel.send(f"kill -9 `ps -ef | grep '{self.host} {self.port}' | grep -v grep | awk '{{print $2}}'`\r".encode())
                    self.expectphrase(getpass.getuser(), timeout=self.timeout)
                    time.sleep(.1)
                    if self.user:
                        self.channel.send(f'telnet {self.host}\r'.encode())
                        self.expectphrase(r'[Ll]ogin:', timeout=self.timeout)
                        self.channel.send(f'{self.user}\r'.encode())
                        self.expectphrase(r'[Pp]assword:', timeout=self.timeout)
                        self.channel.send(f'{self.password}\r'.encode())
                        self.expectphrase(self.local_prompt, timeout=self.timeout)
                    else:
                        self.channel.send(f'telnet {self.host} {self.port}\r'.encode())
                        self.expectphrase('Escape character', timeout=self.timeout)
                else:
                    self.channel.send(f"kill -9 `ps -ef | grep '{self.port}' | grep -v grep | awk '{{print $2}}'`\r".encode())
                    self.expectphrase(getpass.getuser(), timeout=self.timeout)
                    self.channel.send(f'tio -b {self.baudrate} -d {self.bytesize} -f none -s {self.stopbits} -p none {self.port}\r'.encode())
                    self.expectphrase('Connected.', timeout=self.timeout)
        self.display = True

    def send(self, command, expectphrase='', timeout=30, wait_before_send=None, check_received_string=None,
             check_not_received_string=None, strip_ansi=True, retry=1):
        if wait_before_send:
            log.info(f'Wait Before Send: {wait_before_send} second')
            time.sleep(wait_before_send)
        timeout = timeout if timeout else self.timeout
        _cmd = command.replace('\n', '\\n').replace('\r', '')
        if isinstance(expectphrase, list):
            _expect = [i.replace('\n', '\\n').replace('\r', '') for i in expectphrase]
        else:
            _expect = expectphrase.replace('\n', '\\n').replace('\r', '')
        for i in range(1, retry+1):
            status = []
            status.append(True) if not (check_received_string and check_not_received_string) else None
            log.info(f"Send: '{_cmd}' | Expect Phrase: '{_expect}' | Timeout: {timeout}")
            self.sync_id = hashlib.md5(f'{command}|{i}'.encode()).hexdigest()
            log.info(f'Shared Connection ID: {self.sync_id}') if self.shared_conn else None
            if not self.shared_conn or self.shared_conn and get_master_container():
                utils.delete_cached_data(self.sync_id) if self.shared_conn else None
                while not self.channel.send_ready():
                    time.sleep(.009)
                self.channel.send(command)
            else:
                time.sleep(3)
            self.expectphrase(expectphrase, timeout=timeout, strip_ansi=strip_ansi) if expectphrase else None
            if check_received_string:
                status.append(self.check_received_string(check_received_string))
            if check_not_received_string:
                status.append(self.check_not_received_string(check_not_received_string))
            if all(status):
                return True
            log.warning(f"Try sending the command '{_cmd}' for the {i}th time.") if i != retry else None
        utils.fail()

    def expectphrase(self, expect='', timeout=None, strip_ansi=True):
        if isinstance(expect, str) and len(expect) != 0:
            expect = [expect]
        time.sleep(.01)
        response = ''
        with utils.Timeout(timeout if timeout else self.timeout, f'Timeout Expect Phrase'):
            while len(expect) == 0 or not [s for s in expect if s in response or re.search(s, response, re.DOTALL)]:
                if not self.shared_conn or self.shared_conn and get_master_container():
                    while not self.channel.recv_ready():
                        time.sleep(.009)
                    buffer = self.channel.recv(1024)
                    if len(buffer) == 0:
                        break
                    buffer_decoded = self.decoder.decode(buffer).replace('\r', '')
                    buffer_decoded = strip_ansi_codes(buffer_decoded) if strip_ansi else buffer_decoded
                    if self.display:
                        sys.stdout.write(buffer_decoded)
                        sys.stdout.flush()
                        save_log(buffer_decoded, shared=self.shared_conn)
                    response += buffer_decoded
                    utils.cache_data(self.sync_id, response) if self.shared_conn else None
                else:
                    get_cached = utils.get_cached_data(self.sync_id)
                    response = get_cached if get_cached else ''
                time.sleep(.01)
        found_pattern = ''
        if len(expect) != 0:
            found_pattern = [(i, s) for i, s in enumerate(expect) if s in response or re.search(s, response, re.DOTALL)]
        self.recbuf = response
        if len(expect) != 0 and len(found_pattern) != 0:
            self.recbuf = re.sub(fr'{found_pattern[0][1]}$', '', self.recbuf)
            self.last_match = found_pattern[0][1]
            return found_pattern[0][0]
        return -1

    def close(self):
        try:
            self.client.close()
        except:
            pass

    def check_received_string(self, msg):
        userdict = utils.APDicts.userdict
        results = []
        for i in msg if isinstance(msg, list) else [msg]:
            for key in re.findall(r'[^.]?\$\{(.+?)\}', i):
                i = i.replace(f'${{{key}}}', str(userdict[key]))
            s = i if i in self.recbuf else None
            if not s:
                s = re.search(i, self.recbuf)
                s = s.group(0) if s else ''
            log.debug(f"Check Received String: Expect: '{i}', Actual: '{s}' ---> {'PASS' if s else 'FAIL'}")
            results.append(bool(s))
        return all(results)

    def check_not_received_string(self, msg):
        userdict = utils.APDicts.userdict
        results = []
        for i in msg if isinstance(msg, list) else [msg]:
            for key in re.findall(r'[^.]?\$\{(.+?)\}', i):
                i = i.replace(f'${{{key}}}', str(userdict[key]))
            s = i if i in self.recbuf else None
            if not s:
                s = re.search(i, self.recbuf)
                s = s.group(0) if s else ''
            log.debug(f"Check Not Received String: Dis Not Expect: '{i}', Actual: '{s}' ---> {'FAIL' if s else 'PASS'}")
            results.append(not bool(s))
        return all(results)
