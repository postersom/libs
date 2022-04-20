import logging
import importlib

log = logging.getLogger(__name__)


class HipotHandler(object):

    def __init__(self, driver, connection):
        """
        HipotHandler initialization imports a particular instrument driver and opens
        a telnet connection

        :param driver: is the hipot driver module name to be imported
        :param connection: is the hipot telnet connection created in the station config
        :return None

        Example:
        driver_instance = HipotHandler(hipot_model,hipot_connection_object)
        """
        self.__connection = connection
        self.__connection.open()
        self.__hipot_type = driver
        log.info('Hipot handler is connected')
        module = importlib.import_module(f"{__name__.rsplit('.', 1)[0]}.driver.{driver}")
        self.driver = module.Driver(self.__connection)
        log.info('Module imported')

    def close(self):
        """
        Close the hipot instrument telnet connection
        :return None
        """
        self.__connection.close()

    def reset_instrument(self):
        """
        Reset the instrument to original power on configuration
        """
        self.driver.reset_instrument()

    def check_interlock(self):
        """
        Reset the instrument to original power on configuration
        """
        return self.driver.check_interlock()

    def check_cal_due(self):
        """
        This function will check when will expired the calibration in hipot equipment
        """
        return self.driver.check_cal_due()

    def continuity_test(self, current=25, voltage=8, hi_limit=100, lo_limit=0, dwell=1, offset=0, frequency=60,
                        margin_test=False):
        """
        Configures and executes continuity test
        :param current: (str):
        :param voltage: (str):
        :param hi_limit: (str):
        :param lo_limit: (str):
        :param dwell: (str):
        :param offset: (str):
        :param frequency: (str):
        :param margin_test: (str)

        Example:

        """

        return self.driver.continuity_test(current, voltage, hi_limit, lo_limit, dwell, offset, frequency, margin_test)

    def ac_hipot_test(self, voltage=1200, hi_limit_t=10, lo_limit_t=0, ramp_up=1, dwell=1, arc_sense=5, frequency=60,
                      ramp_down=None, hi_limit_r=None, lo_limit_r=None, arc_detect=None, continuity=None,
                      arc_fail=None, margin_test=False):
        """
        Configures and executes AC hipot test
        :param voltage: (str)
        :param hi_limit_t: (str)
        :param lo_limit_t: (str)
        :param ramp_up: (str)
        :param dwell: (str)
        :param arc_sense: (str)
        :param frequency: (str)
        :param ramp_down: (str)
        :param hi_limit_r: (str)
        :param lo_limit_r: (str)
        :param arc_detect: (str)
        :param continuity: (str)
        :param arc_fail: (str)
        :param margin_test: (str)

        Omnia exlusive params:
        ramp_down (str) hi_limit_r (str) lo_limit_r (str) arc_detect (str) continuity (str)
        QuadCheck exclusive params
        arc_fail (str)

        Example:
        """
        log.info(self.__hipot_type)
        if self.__hipot_type in ['omnia', 'omnia2']:
            return self.driver.ac_hipot_test(voltage, hi_limit_t, lo_limit_t, ramp_up, dwell, arc_sense, frequency,
                                             ramp_down, hi_limit_r, lo_limit_r, arc_detect, continuity, margin_test)
        else:
            return self.driver.ac_hipot_test(voltage, hi_limit_t, lo_limit_t, ramp_up, dwell, arc_sense, frequency,
                                             arc_fail)

    def dc_hipot_test(self, voltage=1200, hi_limit=10000, lo_limit=0, ramp_up=1, dwell=1, charge_lo=0, arc_sense=5,
                      ramp_hi='OFF', arc_detect='OFF', ramp_down=None, continuity=None, margin_test=False):
        """
        Configures and executes DC hipot test
        :param voltage: (str)
        :param hi_limit: (str)
        :param lo_limit: (str)
        :param ramp_up: (str)
        :param dwell: (str)
        :param charge_lo: (str)
        :param arc_sense: (str)
        :param ramp_hi: (str)
        :param arc_detect: (str)
        :param ramp_down: (str)
        :param continuity: (str)
        :param margin_test: (str)

        Omnia exclusive params:
        ramp_down (str) continuity (str)

        Example:
        """
        if ramp_down is None and continuity is None:
            return self.driver.dc_hipot_test(voltage, hi_limit, lo_limit, ramp_up, dwell, charge_lo, arc_sense, ramp_hi,
                                             arc_detect, margin_test)
        else:
            return self.driver.dc_hipot_test(voltage, hi_limit, lo_limit, ramp_up, dwell, charge_lo, arc_sense, ramp_hi,
                                             arc_detect, ramp_down, continuity, margin_test)

    def stop_test(self):
        """
        Resets the instrument. If a failure condition occurs during a test, pressing this button will reset the
        system, shut off the alarm and clear the failure condition. The Reset button must be pressed before
        performing another test or changing any of the setup parameters. This button also serves as an abort signal
        to stop any test in progress.

        :return:
        """

        self.driver.stop_test()
