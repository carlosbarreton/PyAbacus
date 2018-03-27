#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import serial

from .core import *
from .constants import *

class Channel(object):
    """ Implements a channel, an object representation of a memory address.

    **Constants**
    """
    global ADDRESS, READ_VALUE, WRITE_VALUE, START_COMMUNICATION, END_COMMUNICATION
    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.address = ADDRESS[name]
        self.hex_value = "x00"
        self.int_value = 0
        self.msb_value = 0
        self.lsb_value = 0

    def setValue(self, value):
        """ Writes and incoming int value to class attributes. """
        self.int_value = value
        self.hex_value = "%04X"%value
        self.splitValue()

    def splitValue(self):
        """ Updates the most/least significant byte."""
        self.msb_value = int(self.hex_value[:2], 16)
        self.lsb_value = int(self.hex_value[2:], 16)

    def readValue(self, hex_list):
        """ Reads a `hex_list` and updates class attributes values."""
        self.hex_value = hex_list[0][1]
        self.int_value = int(self.hex_value, 16)
        self.splitValue()

    def constructMessage(self, read = False):
        """ Construcs a message with project requirements.

        Returns:
            list: list of bytes containing channel info.
        """
        if read:
            message = [START_COMMUNICATION, READ_VALUE, self.address,
                       0x00, 0x00, END_COMMUNICATION]
        else:
            message = [START_COMMUNICATION, WRITE_VALUE, self.address,
                       self.msb_value, self.lsb_value, END_COMMUNICATION]
        return serial.to_bytes(message)

    def verifyValues(self, hex_list):
        """ Verifies if current values have changed.

        Returns:
            bool: The return value. True if values are the same, False otherwise.
        """
        if self.hex_value == hex_list[0][1]:
            return True
        else:
            return False

    def exchangeValues(self, read = True):
        """ Exchanges values from computer to utility.

        Returns: can return None, or a list containing a `hex_list`
        """
        message = self.constructMessage(read)
        return self.port.message(message, wait_for_answer = read)

    def updateValues(self, read = True):
        """ Updates values read from device.

        Returns:
            list of string hexadecimal values
        """
        answer = self.exchangeValues(read)
        if read:
            self.readValue(answer)
        return answer

class TimerChannel(object):
    """ Implements a timer channel, an object representation of multiple memory addresses.

    Timer channels are a construction of four simple channels, each for every time unit.

    **Constants**
    """
    UNITS = ['ns', 'us', 'ms', 's'] #: Units contained in each channel.
    NUMBER_OF_CHANNELS = len(UNITS) #: Number of channels in a timer channel.
    global ADDRESS, READ_VALUE, WRITE_VALUE, START_COMMUNICATION, END_COMMUNICATION, MAXIMUM_WRITING_TRIES
    def __init__(self, prefix, port, base):
        self.prefix = prefix
        self.port = port
        self.base = base
        self.channels_names = ["%s_%s"%(prefix, unit) for unit in self.UNITS]
        self.channels = [Channel(name, port) for name in self.channels_names]
        self.first_address = self.channels[0].address
        self.last_address = self.channels[3].address
        self.value = 0 # in base
        self.values = [0, 0, 0, 0]

    def setValue(self, value):
        """ Writes an incoming integer value to memory, and parses it into time units.
        Information is passed down the tree.
        """
        self.value = value
        self.parseToUnits()
        [channel.setValue(value) for (channel, value) in zip(self.channels, self.values)]

    def readValues(self, values):
        """ Writes an incoming tuple of hexadecimal values to memory and constructs
        simple representation. """
        self.values = self.unnestedValues(values)
        self.value = int((1e-9/self.base)*sum([self.values[i]*10**(3*i) for i in range(self.NUMBER_OF_CHANNELS)]))

    def unnestedValues(self, values):
        """ Removes addresses from incoming hexadecimal values.

        Returns:
            list: each position contains an integer representation of a hexadecimal value.
        """
        return [int(value[1], 16) for value in values]

    def parseToUnits(self):
        """ Breaks a simple value representation to time units. """
        first_order = int(self.base*self.value*1e9)
        micro, nano = divmod(first_order, 1000)
        unit, mili = divmod(int(micro/1000), 1000)
        if micro >= 1000:
            micro = 0
        self.values = [nano, micro, mili, unit]

    def verifyValues(self, values_to_verify):
        """ Verifies if incoming values are equal to the stored ones.

        Return:
            bool: True if they are the same, False otherwise.
        """
        n = sum([self.values[i] == values_to_verify[i] for i in range(self.NUMBER_OF_CHANNELS)])
        if n == self.NUMBER_OF_CHANNELS:
            return True
        else:
            return False

    def exchangeValues(self, read = True):
        """ Exchanges information with device.

        If `read = True` means it will only send a message to device in order to get its answer.
        Otherwise the communication will try to write at the device.
        """
        return [channel.exchangeValues(read) for channel in self.channels]

    def updateValues(self, read = True):
        """ Updates current values with the device ones.

        Returns:
            int: current value estored at the timer channel.
        """
        answer = [channel.updateValues(read) for channel in self.channels]
        if read:
            self.readValues(answer)
        return self.value

    def constructMessage(self):
        """ Constructs the message to be send to the device to
        gather the values written in memory for all four channels.

        Returns:
            list: containing integer representations of hexadecimal values.
        """
        return [START_COMMUNICATION, READ_VALUE,
                self.first_address, 0x00, 0x04, END_COMMUNICATION]

    def checkValues(self):
        """ Sends message and waits for answer, in which current device values are stored.
        Checks if those values are the same with the channel ones.

        Returns:
            bool: True if values are the same, False otherwise.
        """
        values = self.port.message(self.constructMessage(), wait_for_answer = True)
        values = self.unnestedValues(values)
        check = self.verifyValues(values)
        return check

    def setWriteValue(self, value):
        """ Sets the incoming value to the class attribute, writtes them to device.
        The process is done as many times are in `MAXIMUM_WRITING_TRIES`,
        if values are different raises and Exception.

        Raises:
            Exception: Maximum writting tries.
        """
        try:
            for i in range(MAXIMUM_WRITING_TRIES):
                self.setValue(value)

                self.updateValues(False)
                if self.checkValues():
                    break
            if i == MAXIMUM_WRITING_TRIES -1:
                raise Exception("Maximum writting tries.")
        except Exception as e:
            raise e

class DataChannel(object):
    """ Implements a data channel, an object representation of multiple memory addresses.
    Timer channels are a construction of two simple channels, one for the Most Significant Bytes (MSB)
    and another for the Least Significant Bytes (LSB).

    **Constants**
    """
    SIGNIFICANT_BYTES = ["MSB", "LSB"] #: Significant bytes.
    NUMBER_OF_CHANNELS = len(SIGNIFICANT_BYTES) #: Number of channels in data channel.
    global ADDRESS
    def __init__(self, prefix, port):
        letters = prefix.strip()
        letters = [letter for letter in letters if letter.isupper()]
        pos = len(prefix.split(letters[0])[0])
        self.name = "%s %s"%(prefix[:pos].title(), prefix[pos:])
        self.prefix = prefix
        self.port = port
        self.channels_names = ["%s_%s"%(prefix, sig) for sig in self.SIGNIFICANT_BYTES]
        self.channels = [Channel(name, port) for name in self.channels_names]
        self.hex_value = "0x00"
        self.value = 0
        self.values = [0, 0]

    def getValue(self):
        """ Returns the current value.

        Returns:
            int: current value.
        """
        return self.value

    def readValues(self, values):
        """ Saves an incoming set of tuples containg the values of each channel.
        """
        self.hex_value = "".join([values[1][1], values[0][1]])
        self.value = int(self.hex_value, 16)
        self.values = [int(self.hex_value[:4], 16), int(self.hex_value[4:], 16)]

    def updateValues(self):
        """ Sends a message to the device, the answer contains current device values.
        It then stores them with the help of `read_values(values)`.

        Returns:
            int: current value.
        """
        answer = self.port.message(self.constructMessage(), wait_for_answer = True)
        self.readValues(answer)
        return self.value

    def constructMessage(self):
        """ Constructs the message to be send to the device in order to get its current values.

        Returns:
            list: containing integer representations of hexadecimal values.
        """
        return [START_COMMUNICATION, READ_VALUE,
                self.channels[1].address, 0x00, 0x02, END_COMMUNICATION]
