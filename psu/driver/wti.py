import time


class Driver(object):
    def __init__(self, connection):
        self._connection = connection
        self._prompt = 'NPS>'

    def on(self, port, timeout):
        self.power_control('on', port, timeout)

    def off(self, port, timeout):
        self.power_control('off', port, timeout)

    def cycle(self, port, timeout, time_sleep):
        self.power_control(['off', 'on'], port, timeout, time_sleep)

    def power_control(self, control, port, timeout, time_sleep=0):
        self._connection.open()
        for i in control if isinstance(control, list) else [control]:
            self._connection.send(f'/{i.upper()} {port},Y\r', expectphrase=self._prompt, timeout=timeout)
            time.sleep(time_sleep)
        self._connection.close()
