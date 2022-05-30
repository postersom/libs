from importlib import import_module


class PowerControlHandler(object):
    def __init__(self, driver, connection, port=None, timeout=30, time_sleep=5):
        """
        :param driver - is the power control driver module name to be imported:
        :param connection - is the power control ssh or telnet connection created in the station config:
        :param port - port: (str)
        :param timeout - timeout: (int)
        :param time_sleep - time_sleep: (int)
        :return None
        Example:
            p = lib.PowerControlHandler(driver='wti', connection=lib.getconnections()['WTI'], port='A1 A2', timeout=10)
            p.on()
            p.off()
            or
            p = lib.PowerControlHandler(driver='wti', connection=lib.getconnections()['WTI'])
            p.on(port='A1 A2')
            p.off(port='A1 A2')
        """
        self._connection = connection
        self._port = port
        self._timeout = timeout
        self.time_sleep = time_sleep
        module = import_module(f"{__name__.rsplit('.', 1)[0]}.driver.{driver}")
        self.driver = module.Driver(connection=self._connection)

    def on(self, port=None, timeout=None):
        """
        :param port - port: (str)
        :param timeout - timeout: (int)
        :return:
        """
        port = port if port else self._port
        timeout = timeout if timeout else self._timeout
        return self.driver.on(port, timeout)

    def off(self, port=None, timeout=None):
        """
        :param port - port: (str)
        :param timeout - timeout: (int)
        :return:
        """
        port = port if port else self._port
        timeout = timeout if timeout else self._timeout
        return self.driver.off(port, timeout)

    def cycle(self, port=None, timeout=None, time_sleep=None):
        """
        :param port - port: (str)
        :param timeout - timeout: (int)
        :param time_sleep - time_sleep: (int)
        :return:
        """
        port = port if port else self._port
        timeout = timeout if timeout else self._timeout
        time_sleep = time_sleep if time_sleep else self.time_sleep
        return self.driver.cycle(port, timeout, time_sleep)
