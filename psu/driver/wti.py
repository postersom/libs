import time


class Driver(object):
    def __init__(self, connection):
        self._connection = connection
        self._prompt = 'NPS>'

    def on(self, port, timeout):
        self.power_control('on', port, timeout)

    def off(self, port, timeout):
        self.power_control('off', port, timeout)

    def cycle(self, port, timeout):
        self.power_control(['off', 'on'], port, timeout)

    def power_control(self, control, port, timeout):
        self._connection.open()
        for i in control if isinstance(control, list) else [control]:
            self._connection.send(f'/{i.upper()} {port},Y\r', expectphrase=self._prompt, timeout=timeout)
            time.sleep(5)
        self._connection.close()
