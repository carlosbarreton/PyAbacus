#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
*Required modules*
"""
from itertools import combinations
from time import sleep, localtime, strftime, time, asctime

#################
import numpy as np
#################

#################
from .channels import *
from .constants import *
from .exceptions import *
#################

class Detector(object):
    """ Implements a detector, an object representation of multiple memory addresses.
    A detector is made of one data channel and two timer channels.

    **Constants**
    """
    BASE_DELAY = 1e-9 #: Default channnel delay time (seconds)
    BASE_SLEEP = 1e-9 #: Default channel sleep time (seconds)
    def __init__(self, identifier, port, data_interval = 100, timer_check_interval = 1000):
        self.identifier = identifier
        self.name = "Detector %s"%self.identifier
        self.port = port
        self.data_channel = DataChannel("counts%s"%self.identifier, self.port)
        self.delay_channel = TimerChannel("delay%s"%self.identifier, self.port, self.BASE_DELAY)
        self.sleep_channel = TimerChannel("sleepTime%s"%self.identifier, self.port, self.BASE_SLEEP)
        self.first_data_address = self.data_channel.channels[1].address
        self.first_timer_address = self.delay_channel.first_address
        self.current_data = 0

    def readValues(self, values):
        """ Reads incoming values at the data channel."""
        self.data_channel.readValues(values)

    def getTimerValues(self):
        """ Gets the values at each timer channel.

        Returns:
            tuple: each value in a position of the tuple..
        """
        return self.delay_channel.value, self.sleep_channel.value

    def getValue(self):
        """ Stores and returns the current value of the data channel.

        Returns:
            int: current value at the data channel.
        """
        self.current_data = self.data_channel.getValue()
        return self.current_data

    def updateData(self):
        """ Stores a fresh value of the data channel."""
        self.current_data = self.data_channel.updateValues()

    def setTimersValues(self, values):
        """ Sets the incoming values in each timer channel."""
        self.delay_channel.readValues(values[:4])
        self.sleep_channel.readValues(values[4:])

    def setDelay(self, value):
        """ Saves the incoming value, writes it to device and verifies writing. """
        self.delay_channel.setWriteValue(value)

    def setSleep(self, value):
        self.sleep_channel.setWriteValue(value)

    def setTimes(self, delay, sleep):
        self.setDelay(delay)
        self.setSleep(sleep)

class Experiment(object):
    """
    Constants
    """
    BASE_SAMPLING = 1e-3 #: Default sampling time (seconds)
    BASE_COINWIN = 1e-9 #: Default coincidence window (seconds)
    global READ_VALUE, WRITE_VALUE, START_COMMUNICATION, END_COMMUNICATION
    def __init__(self, port, number_detectors = 2):
        self.port = port
        self.number_detectors = number_detectors
        self.detector_identifiers = [chr(i + ord('A')) for i in range(self.number_detectors)]
        self.coins_identifiers = self.getCombinations()
        self.number_coins = len(self.coins_identifiers)
        self.detector_dict = {self.detector_identifiers[i]: i for i in range(self.number_detectors)}
        self.coins_dict = {self.coins_identifiers[i]: i for i in range(self.number_coins)}
        self.detectors = [Detector(identifier, self.port) for identifier in self.detector_identifiers]
        self.coin_channels = [DataChannel("coincidences%s"%identifier, self.port) for identifier in self.coins_identifiers]

        self.sampling_channel = TimerChannel("samplingTime", port, self.BASE_SAMPLING)
        self.coinWindow_channel = TimerChannel("coincidenceWindow", port, self.BASE_COINWIN)

    def constructMessage(self, data = True):
        if data:
            number = "%08X"%(2*(self.number_detectors + self.number_coins))
            first = self.detectors[0].first_data_address
        else:
            number = "%08X"%(self.coinWindow_channel.last_address - self.detectors[0].first_timer_address +1)
            first = self.detectors[0].first_timer_address

        msb = int(number[:4], 16)
        lsb = int(number[4:], 16)
        return [START_COMMUNICATION, READ_VALUE, first,
                msb, lsb, END_COMMUNICATION]

    def currentValues(self):
        try:
            ans = self.port.message(self.constructMessage(), wait_for_answer = True)
            detector_values = []
            coin_values = []
            for i in range(self.number_detectors):
                self.detectors[i].readValues(ans[2*i:2*i+2])
                detector_values.append(self.detectors[i].getValue())
            for j in range(self.number_coins):
                self.coin_channels[j].readValues(ans[2*(i+j+1):2*(i+j+1)+2])
                coin_values.append(self.coin_channels[j].getValue())
        except Exception as e:
            raise ExperimentError(str(e))
        return time(), detector_values, coin_values

    def setSampling(self, value):
        try:
            self.sampling_channel.setWriteValue(value)
        except Exception as e:
            raise ExperimentError(str(e))

    def setCoinWindow(self, value):
        try:
            self.coinWindow_channel.setWriteValue(value)
        except Exception as e:
            raise ExperimentError(str(e))

    def getSamplingValue(self):
        return self.sampling_channel.value

    def getCoinwinValue(self):
        return self.coinWindow_channel.value

    def getDetectorsTimersValues(self):
        return [detector.getTimerValues() for detector in self.detectors]

    def getCombinations(self):
        letters = "".join(self.detector_identifiers)
        coins = []
        for i in range(1, self.number_detectors):
            coins += list(combinations(letters, i+1))

        return ["".join(values) for values in coins]

    def periodicCheck(self):
        try:
            message = self.constructMessage(data = False)
            values = self.port.message(message, wait_for_answer = True)
            for i in range(self.number_detectors):
                begin_delay = 4*i
                delay = values[begin_delay: begin_delay + 4]
                sleep = values[begin_delay + 8: begin_delay + 12]
                value = delay + sleep
                self.detectors[i].setTimersValues(value)
            last = 8*(i+1)
            self.sampling_channel.readValues(values[last: 4 + last])
            self.coinWindow_channel.readValues(values[last + 4:])
        except Exception as e:
            raise ExperimentError(str(e))

    def sleepSweep(self, channel, sleep_time, n):
        channel = ord(channel) - ord("A")
        detector = self.detectors[channel]
        detector.setSleep(sleep_time)
        try:
            for j in range(n):
                detector.updateData()
                yield detector.getValue()
                sleep(self.getSamplingValue()*self.BASE_SAMPLING)

        except Exception as e:
            raise ExperimentError(str(e))

    def delaySweep(self, channel1, channel2, delay1, delay2, n):
        c1 = ord(channel1) - ord("A")
        c2 = ord(channel2) - ord("A")
        self.detectors[c1].setDelay(delay1)
        self.detectors[c2].setDelay(delay2)
        channel = self.coin_channels[self.coins_dict[channel1 + channel2]]
        try:
            for j in range(n):
                yield channel.updateValues()
                sleep(self.getSamplingValue()*self.BASE_SAMPLING)

        except Exception as e:
            raise ExperimentError(str(e))
