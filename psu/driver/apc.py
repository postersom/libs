import time


class Driver(object):
    def __init__(self, connection):
        self._connection = connection
        self._prompt = '#'

    def on(self, port, timeout):
        self.power_control('on', port, timeout)

    def off(self, port, timeout):
        self.power_control('off', port, timeout)

    def cycle(self, port, timeout, time_sleep):
        self.power_control(['off', 'on'], port, timeout, time_sleep)

    def power_control(self, control, port, timeout, time_sleep=0):
        self._connection.open()
        for i in control if isinstance(control, list) else [control]:
            self._connection.send(f'psu_manager psu{port} {i}\r', expectphrase=self._prompt, timeout=timeout)
            time.sleep(3)
            self._connection.send(f'psu_manager psu{port} status\r', expectphrase=self._prompt, timeout=timeout)
            time.sleep(time_sleep)
        self._connection.close()
