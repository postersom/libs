import time
import logging
from datetime import datetime

log = logging.getLogger(__name__)


class Driver(object):

    def __init__(self, connection):
        """
        Driver init receives an instrument telnet connection from the handler to reset the instrument
        and verify if the correct driver has been initialized
        :param connection: telnet connection
        :return:
        """
        log.info('Initializing HypotULTRAM Driver...')
        time.sleep(3)
        self.file_number = 0
        self.__connection = connection
        # Removed RST since is causing some instrument to hang and fail to init
        # self.__connection.send('*RST\n')
        # time.sleep(7)
        self.__connection.send('*IDN?\n', expectphrase='ASSOCIATED RESEARCH', timeout=3)
        response = self.__connection.recbuf.split(',')
        hipot_model = response[1]
        hipot_serial = response[2]
        self.model = hipot_model
        self.serial = hipot_serial

        if hipot_model not in ['7854', '8204', '7704']:
            log.info('Expected hipot was not found')
            raise Exception('Incorrect Hipot model [{}]'.format(hipot_model))
        """
        if (hipot_model in '8204') and (hipot_fw >= 9650315):
            log.info('Expected hipot FW not found this HypotULTRAM equipment behaves like HypotULTRAM2')
            raise Exception('Incorrect Hipot FW [{}] version, should have a smaller version'.format(hipot_fw))
        """

        self.file_total_qty(3)

    def reset_instrument(self):
        """
        Command: *RST
        Reset the instrument to original power on configuration.
        Does not clear Enable register for Standard Summary
        Status or Standard Event Registers. Does not clear the
        output queue. Does not clear the power-on-status-clear
        flag.
        """
        log.info('Send *RST')
        self.__connection.send('*RST\n')
        time.sleep(5)

    def check_interlock(self):
        """
        Command: RI?
        This function checks that interlock switch is active before starting test.
        """
        log.info('Send RI?...')
        self.__connection.send('RI?\n', expectphrase='\n', timeout=2)
        result = self.__connection.recbuf

        return result

    def check_cal_due(self):
        """
        Command: SCDU?
        This function will check the date calibration for the equipment

        """

        log.debug('Send SCDU?\n')
        self.__connection.send('SCDU?\n', expectphrase=['0', ','], timeout=3)
        date_cal = self.__connection.recbuf
        time_const = '00:00:00.000000 '
        response = str(date_cal).replace('\n', '')
        response = time_const + response.replace(',', '-')
        hipot_cal_due = datetime.strptime(response, '%H:%M:%S.%f %m-%d-%y')
        log.debug('Date of calibration is {}'.format(hipot_cal_due))

        return hipot_cal_due

    def file_total_qty(self, qty):
        """
        :param qty:
        Verifies that GND, ACW and DCW settings files are created, if not creates them
        """

        self.__connection.send('LF 1?\n', expectphrase='\n', timeout=3)
        if '01,GND' not in self.__connection.recbuf:
            self.__connection.send('FD 1\n', expectphrase='\n', timeout=3)
            self.__connection.send('FN 1,GND\n', expectphrase='\n', timeout=3)

        self.__connection.send('LF 2?\n', expectphrase='\n', timeout=3)
        if '02,ACW' not in self.__connection.recbuf:
            self.__connection.send('FD 2\n', expectphrase='\n', timeout=3)
            self.__connection.send('FN 2,ACW\n', expectphrase='\n', timeout=3)

        self.__connection.send('LF 3?\n', expectphrase='\n', timeout=3)
        if '03,DCW' not in self.__connection.recbuf:
            self.__connection.send('FD 3\n', expectphrase='\n', timeout=3)
            self.__connection.send('FN 3,DCW\n', expectphrase='\n', timeout=3)

        log.info('Send FT?')
        self.__connection.send('FT?\n', expectphrase='\n', timeout=1)
        # # total_files = int(self.__connection.foundphrase[0])
        # total_files = int(self.__connection.recbuf)
        # log.info('Total files: {}'.format(total_files))
        #
        # if qty < total_files:
        #     for x in xrange(total_files, qty, -1):
        #         log.info('Send FD {}'.format(x))
        #         self.__connection.send('FD {}\n'.format(x), expectphrase='\n', timeout=3)

    def file_load(self, file_name):
        """
        :param file_name:
        FL <file number>
        Load a file from non-volatile memory into random access
        memory RAM.
        """
        if file_name == 'GND':
            self.file_number = 1
        elif file_name == 'ACW':
            self.file_number = 2
        elif file_name == 'DCW':
            self.file_number = 3
        else:
            log.info('invalid file_name')
        self.__connection.send(f'FL {self.file_number}\n', expectphrase='\n', timeout=3)

    def select_step(self):
        """
        SS <step number>
        Selects the active selected step to load into RAM.
        The step must first be selected before any specific
        parameters can be edited.
        """

        log.info('Send SS 1')
        self.__connection.send('SS 1\n', expectphrase='\n', timeout=3)

    def test_data_result(self):
        """
        command: TD?
        Read the active data being displayed on the LCD display
        while the test is in process. Will also read the last
        data taken when the test sequence has completed.
        """
        time.sleep(2)
        for retries in range(1, 11):
            time.sleep(1)
            self.__connection.send('TD?\n', expectphrase='\n', timeout=3)
            response = self.__connection.recbuf.split(',')
            if self.__connection.recbuf.split(',')[2] in ['Pass', 'PASS']:
                response = self.__connection.recbuf.split(',')
                log.info(response)
                return response
            elif retries == 10:
                raise Exception('hipot {} Failure: {} test_status'.format(response[1], response[2]))

    def margin_test_data_result(self):
        """
        command: TD?
        Read the active data being displayed on the LCD display
        while the test is in process. Will also read the last
        data taken when the test sequence has completed.
        """
        time.sleep(2)
        for retries in range(1, 11):
            time.sleep(1)
            self.__connection.send('TD?\n', expectphrase='\n', timeout=3)
            response = self.__connection.recbuf.split(',')
            if response[2] in ['HI-LIMIT', 'HI-Limit', 'HI-LIMIT T', 'HI-Limit T', 'HI-Lmt T']:
                log.info(response)
                return response
            elif retries == 10:
                raise Exception(f'hipot {response[1]} Failure: {response[2]} test_status')

    def start_test(self):
        """
        Command: TEST
        Executes a test previously selected from a  Cofiguration
        File and step.
        SF {1|0}
        Sets the Fail Stop function OFF or ON for the active
        setup file loaded into RAM. 1 sets the Fail Stop = ON,
        0 sets the Fail Stop = OFF.
        """

        log.info('SF 1')
        self.__connection.send('SF 1\n', expectphrase='\n', timeout=3)
        log.info('Send TEST')
        self.__connection.send('TEST\n', expectphrase='\n', timeout=3)

    def stop_test(self):
        """
        Command: RESET
        Resets the instrument. If a failure condition occurs
        during a test, pressing this button will reset the
        system, shut off the alarm and clear the failure
        condition. The Reset button must be pressed before
        performing another test or changing any of the setup
        parameters. This button also serves as an abort signal
        to stop any test in progress.
        """

        log.info('Send RESET')
        self.__connection.send('RESET\n', expectphrase='\n', timeout=3)

    def continuity_test(self, current, voltage, hi_limit, lo_limit, hi_limit_v, lo_limit_v, dwell, offset, offset_v,
                        frequency, margin_test=False):
        """
        HypotULTRAM continuity test configuration and execution
        Params: current: Units (A) The Current that is applied between the Current and Return lead during a ground bond
                         test.
                voltage: Units (V) The voltage that is applied to the high voltage and return terminals during a test.
                hi_limit: HI-Limit (mOhms) A maximum threshold set point that when exceeded triggers a failure.
                lo_limit: LO-Limit (mOhms) A minimum threshold set point that when not exceeded triggers a failure.
                hi_limit_v: HI-Limit Volt (V) The maximum voltage drop threshold that triggers a failure when exceeded.
                lo_limit_v: LO-Limit Volt (V) The minimum voltage drop threshold that triggers a failure when not
                            exceeded.
                dwell: Dwell Time (s) The length of time that is allowed for the programmed test voltage to be applied.
                offset: Offset (mOhms) This function allows the instrument to compensate for lead and test fixture.
                offset_v: Offset Volt (V) This function allows the instrument to compensate for lead and test fixture.
                frequency: Frequency 50 or 60 Hz
                margin_test: (bol) Determines if test will be part of the hipot margin test verification
        Return: test_status: Returns test results details
        """
        self.stop_test()
        self.file_load('GND')
        self.select_step()

        self.__connection.send('LS?\n', expectphrase='\n', timeout=3)
        response = self.__connection.recbuf
        response = response[3:].strip()
        log.info(response)
        command = f'ADD2 GND,{current:.2f},{voltage:.2f},{hi_limit},{lo_limit},{hi_limit_v},{lo_limit_v},{dwell:.1f},' \
                  f'{offset},{offset_v},{frequency}'

        log.info(command)
        if command.find(response) <= 0:
            log.info('Stored Step params do not match actual config')
            self.__connection.send('SD\n', expectphrase='\n', timeout=3)
            self.__connection.send(f'{command}\n', expectphrase='\n', timeout=3)
            self.__connection.send('FS\n', expectphrase='\n', timeout=3)
        self.start_test()

        if margin_test:
            log.info('Start Continuity margin test')
            test_status = self.margin_test_data_result()
        else:
            log.debug('Start Continuity test')
            test_status = self.test_data_result()
        return test_status

    def ac_hipot_test(self, voltage, hi_limit_t, lo_limit_t, ramp_up, dwell, arc_sense, frequency, ramp_down,
                      hi_limit_r, lo_limit_r, arc_detect, continuity, margin_test=False):
        """
        Configures and executes AC hipot test
        :param voltage: (str) Units (VAC). The voltage that is applied to the high voltage and return terminals during
        a test.
        :param hi_limit_t: (str) Units (mA). A maximum threshold set point that when exceeded triggers a failure.
        'T' total current
        :param lo_limit_t: (str) Units (mA). A minimum threshold set point that when not exceeded triggers a failure.
        'T' total current
        :param ramp_up: (str) Units (s). The length of time that is allowed for the test voltage to climb from 0 to the
        programmed test voltage.
        :param dwell: (str) Units (s). The length of time that is allowed for the programmed test voltage to be applied.
        :param arc_sense: (str) During hipot testing some low current arcing may be allowable. Arc sense is a maximum
        allowable threshold for arcing.
        :param frequency: (str) Units (Hz).
        :param ramp_down: (str) Units (s). The length of time that is allowed for the test voltage to decay from
        programmed test voltage to 0.
        :param hi_limit_r: (str) Units (mA). A maximum threshold set point that when exceeded triggers a failure. 'R'
        real current
        :param lo_limit_r: (str) Units (mA). A minimum threshold set point that when not exceeded triggers a failure.
        'R' real current
        :param arc_detect: (str) Units (ON/OFF). If the Arc Fail mode is set to ON, the program will indicate an arc
        failure when the arc current is exceeds this setting.
        :param continuity: (str) Units (ON/OFF). This function checks for a connection between the current and return
        lead.
        :param margin_test: (bol) Determines if test will be part of the hipot margin test verification

        HypotULTRAM exlusive params:
        ramp_down (str) hi_limit_r (str) lo_limit_r (str) arc_detect (str) continuity (str)

        Example:
        """
        self.stop_test()
        self.file_load('ACW')
        self.select_step()

        log.info('LS?')
        self.__connection.send('LS?\n', expectphrase='\n', timeout=3)
        response = self.__connection.recbuf
        response = response[3:].strip()
        log.info(response)
        command = f'ADD2 ACW,{voltage},{hi_limit_t:.2f},{lo_limit_t:.3f},{ramp_up:.1f},{dwell:.1f},{arc_sense:.1f},' \
                  f'{ramp_down},{hi_limit_r:.2f},{lo_limit_r:.3f},{frequency},{arc_detect},{continuity}'

        log.info(command)
        if command.find(response) <= 0:
            log.info('Stored Step params do not match actual config')
            log.info('Send SD')
            self.__connection.send('SD\n', expectphrase='\n', timeout=3)
            log.debug(command)
            self.__connection.send(f'{command}\n', expectphrase='\n', timeout=3)
            log.debug('FS')
            self.__connection.send('FS\n', expectphrase='\n', timeout=3)

        self.start_test()

        if margin_test:
            log.info('Start ACW margin test')
            test_status = self.margin_test_data_result()
        else:
            log.debug('Start ACW test')
            test_status = self.test_data_result()

        return test_status

    def dc_hipot_test(self, voltage, hi_limit, lo_limit, ramp_up, dwell, ramp_down, charge_lo, arc_sense,
                      offset, ramp_hi, arc_detect, continuity, range, low_range, margin_test=False):
        """
        Configures and executes DC hipot test
        Params: voltage: (str) Units (VDC). The voltage that is applied to the high voltage and return terminals during
                                            a test.
                hi_limit: (str) Units (uA). A maximum threshold set point that when exceeded triggers a failure.
                lo_limit: (str) Units (uA). A minimum threshold set point that when not exceeded triggers a failure.
                ramp_up: (str) Units (s). The length of time that is allowed for the test voltage to climb from 0 to the
                                          programmed test voltage.
                dwell: (str) Units (s). The length of time that is allowed for the programmed test voltage to be applied.
                charge_lo: (str) Units (uA). The Charge-LO function is used to check if the cables are connected
                                            properly at the beginning of a test. This function is only available in
                                            DC Withstand and Insulation resistance testing.
                arc_sense: (str) During hipot testing some low current arcing may be allowable. Arc sense is a maximum
                                  allowable threshold for arcing.
                offset: Offset (mOhms) This function allows the instrument to compensate for lead and test fixture.

                ramp_hi: (str) Units (ON/OFF). The Ramp-HI function is active during the Ramp period only. Ramp-HI will
                                allow current higher than the normal Max-Lmt current setting of the DC Withstand Voltage
                                test to avoid false failure due to charging current.
                arc_detect: (str) Units (ON/OFF). If the Arc Fail mode is set to ON, the program will indicate an
                                arc failure when the    arc current is exceeds this setting.
                ramp_down: (str) Units (s). The length of time that is allowed for the test voltage to decay from
                                programmed test voltage to 0.
                continuity: (str) Units (ON/OFF). This function checks for a connection between the current and
                range: (str) Units (Auto/Manual).
                low_range: (str) Units (ON/OFF).
                margin_test: (bol) Determines if test will be part of the hipot margin test verification
        Return: lead.

        HypotULTRAM exclusive params:
        ramp_down (str) continuity (str)

        Example:
        """
        self.stop_test()
        self.file_load('DCW')
        self.select_step()

        log.info('LS?')
        self.__connection.send('LS?\n', expectphrase='\n', timeout=3)
        response = self.__connection.recbuf
        response = response[3:].strip()
        log.info(response)
        command = f'ADD2 DCW,{voltage},{hi_limit},{lo_limit:.1f},{ramp_up:.1f},{dwell:.1f},{ramp_down:.1f},' \
                  f'{charge_lo:.1f},{arc_sense},{offset:.1f},{ramp_hi:.1f},{arc_detect},{continuity},{range},{low_range}'

        log.info(command)
        if command.find(response) <= 0:
            log.info('Stored Step params do not match actual config')
            self.__connection.send('SD\n', expectphrase='\n', timeout=3)
            self.__connection.send(f'{command}\n', expectphrase='\n', timeout=3)
            self.__connection.send('FS\n', expectphrase='\n', timeout=3)
        self.start_test()

        if margin_test:
            log.info('Start DCW margin test')
            test_status = self.margin_test_data_result()
        else:
            log.debug('Start DCW test')
            test_status = self.test_data_result()
        return test_status
