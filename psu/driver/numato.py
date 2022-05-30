import time


class Driver(object):
    def __init__(self, connection):
        self._connection = connection
        self._prompt = '>'

    def on(self, port, timeout):
        self.power_control('on', port, timeout)

    def off(self, port, timeout):
        self.power_control('off', port, timeout)

    def cycle(self, port, timeout, time_sleep):
        self.power_control(['off', 'on'], port, timeout, time_sleep)

    def power_control(self, control, port, timeout, time_sleep=0):
        self._connection.open()
        for i in control if isinstance(control, list) else [control]:
            for p in port.split(' '):
                self._connection.send(f'relay {p} {i}\r', expectphrase=self._prompt, timeout=timeout)
                time.sleep(.009)
            time.sleep(time_sleep)
        self._connection.close()
