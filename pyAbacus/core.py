import serial
from time import sleep
import serial.tools.list_ports as find_ports

import time
from threading import Thread

from itertools import combinations

from .constants import TIMEOUT, BAUDRATE, START_COMMUNICATION, READ_VALUE, WRITE_VALUE, END_COMMUNICATION, BOUNCE_TIMEOUT
from .constants import CURRENT_OS, ABACUS_SERIALS, TEST_MESSAGE, TEST_ANSWER, ADDRESS_DIRECTORY, COUNTERS_VALUES, SETTINGS
from .exceptions import *
import pyAbacus.constants

def open(abacus_port):
    """
    """
    global ABACUS_SERIALS
    if abacus_port in ABACUS_SERIALS.keys():
        close(abacus_port)
    serial = AbacusSerial(abacus_port)
    ABACUS_SERIALS[abacus_port] = serial

def close(abacus_port):
    """
    """
    global ABACUS_SERIALS
    if abacus_port in ABACUS_SERIALS.keys():
        try:
            ABACUS_SERIALS[abacus_port].close()
        except Exception as e:
            print(e)
        del ABACUS_SERIALS[abacus_port]

def writeSerial(abacus_port, command, address, data_u16):
    """
    """
    global ABACUS_SERIALS
    ABACUS_SERIALS[abacus_port].writeSerial(command, address, data_u16)

def readSerial(abacus_port):
    """
    """
    global ABACUS_SERIALS
    return ABACUS_SERIALS[abacus_port].readSerial()

def dataStreamToDataArrays(input_string):
    """
    """
    input_string, n = input_string
    test = sum(input_string[2:]) & 0xFF # 8 bit
    if test != 0xFF:
        raise(CheckSumError())
    chuncks = input_string[2 : -1] # (addr & MSB & LSB)^n
    chuncks = [chuncks[i:i + 3] for i in range(0, n-3, 3)]
    addresses = [chunck[0] for chunck in chuncks]
    data = [(chunck[1] << 8) | (chunck[2]) for chunck in chuncks]

    return addresses, data

def dataArraysToCounters(addresses, data):
    """
    """
    global COUNTERS_VALUES
    for i in range(len(addresses)):
        COUNTERS_VALUES.setValueFromArray(addresses[i], data[i])
    return COUNTERS_VALUES

def dataArraysToSettings(addresses, data):
    """
    """
    global SETTINGS
    for i in range(len(addresses)):
        SETTINGS.setValueFromArray(addresses[i], data[i])
    return SETTINGS

def getAllCounters(abacus_port):
    """
    """
    global COUNTERS_VALUES
    writeSerial(abacus_port, READ_VALUE, 24, 6)
    data = readSerial(abacus_port)
    array, datas = dataStreamToDataArrays(data[0])
    dataArraysToCounters(array, datas)

    return COUNTERS_VALUES, getCountersID(abacus_port)

def getAllSettings(abacus_port):
    """
    """
    global SETTINGS
    writeSerial(abacus_port, READ_VALUE, 0, 24)
    data = readSerial(abacus_port)
    array, datas = dataStreamToDataArrays(data[0])
    dataArraysToSettings(array, datas)
    return SETTINGS

def getSetting(abacus_port, setting):
    """
    """
    global SETTINGS

    addr, val = SETTINGS.getAddressAndValue(setting + "_ns")
    writeSerial(abacus_port, READ_VALUE, addr, 4)

    data = readSerial(abacus_port)
    array, datas = dataStreamToDataArrays(data[0])
    dataArraysToSettings(array, datas)

    return SETTINGS.getSetting(setting)

def getIdn(abacus_port):
    """
    """
    global ABACUS_SERIALS
    return ABACUS_SERIALS[abacus_port].getIdn()

def getCountersID(abacus_port):
    """
    """
    global COUNTERS_VALUES

    writeSerial(abacus_port, READ_VALUE, ADDRESS_DIRECTORY["measure_number"], 0)
    data = readSerial(abacus_port)
    array, datas = dataStreamToDataArrays(data)

    COUNTERS_VALUES.setCountersID(datas[0])
    return datas[0]

def getTimeLeft(abacus_port):
    """
    """
    global COUNTERS_VALUES

    writeSerial(abacus_port, READ_VALUE, ADDRESS_DIRECTORY["time_to_next_sample"], 0)
    data = readSerial(abacus_port)
    array, datas = dataStreamToDataArrays(data)
    COUNTERS_VALUES.setTimeLeft(datas[0])
    return COUNTERS_VALUES.getTimeLeft()

def setSetting(abacus_port, setting, value):
    """
    """
    global SETTINGS
    SETTINGS.setSetting(setting, value)
    suffix = ["_ns", "_us", "_ms", "_s"]
    for s in suffix:
        addr, val = SETTINGS.getAddressAndValue(setting + s)
        writeSerial(abacus_port, WRITE_VALUE, addr, val)

def setAllSettings(abacus_port, new_settings):
    """
    """
    global SETTINGS
    if type(new_settings) is Settings2Ch:
        SETTINGS = new_settings
        for setting in SETTINGS.addresses.values():
            addr, val = SETTINGS.getAddressAndValue(setting)
            writeSerial(abacus_port, WRITE_VALUE, addr, val)
    else:
        raise(Exception("New settings are not a valid type."))

def findDevices(print_on = True):
    """
    """
    global CURRENT_OS
    ports_objects = list(find_ports.comports())
    ports = {}
    for i in range(len(ports_objects)):
        port = ports_objects[i]

        attrs = ["device", "name", "description", "hwid", "vid", "pid",
         "serial_number", "location", "manufacturer", "product", "interface"]

        if print_on:
            for attr in attrs:
                print(attr + ":", eval("port.%s"%attr))

        try:
            serial = AbacusSerial(port.device)
            if TEST_ANSWER in serial.getIdn():
                if CURRENT_OS == "win32":
                    ports["%s"%port.description] = port.device
                else:
                    ports["%s (%s)"%(port.description, port.device)] = port.device
            serial.close()
        except Exception as e:
            print(port.device, e)

    return ports, len(ports)

class CountersValues(object):
    """
    """
    def __init__(self, n_channels):
        letters = [chr(ord('A') + i) for i in range(n_channels)]
        channels = []
        for i in range(1, n_channels + 1):
            for item in combinations("".join(letters), i):
                item = "".join(item)
                channels.append(item)

        self.n_channels = n_channels
        self.channels_letters = channels

        for c in channels:
            setattr(self, "%s_LSB"%c, 0)
            setattr(self, "%s_MSB"%c, 0)

        self.addresses = {}

        for key in list(ADDRESS_DIRECTORY.keys()):
            for c in channels:
                if "counts_%s"%c in key:
                    addr = ADDRESS_DIRECTORY[key]
                    self.addresses[addr] = key.replace("counts_", "")

        self.addresses[30] = 'measure_number'
        self.addresses[31] = 'time_to_next_sample'
        self.counters_id = 0
        self.time_to_next_sample = 0 #: in ms

    def setValueFromArray(self, address, value):
        """
        """
        setattr(self, self.addresses[address], value)

    def getValue(self, channel):
        """
        """
        msb = getattr(self, "%s_MSB" % channel) << 16
        lsb = getattr(self, "%s_LSB" % channel)

        return msb | lsb

    def getValues(self, channels):
        return [self.getValue(c) for c in channels]

    def getValuesFormatted(self, channels):
        values = ["%d"%v for v in self.getValues(channels)]
        return "(%d) "%self.getCountersID() + ", ".join(values)

    def getCountersID(self):
        """
        """
        return self.counters_id

    def setCountersID(self, id):
        """
        """
        self.counters_id = id

    def getTimeLeft(self):
        """
        """
        return self.time_to_next_sample

    def setTimeLeft(self, time):
        self.time_to_next_sample = time # ms

    def __repr__(self):
        values = ["\t%s: %d"%(i, self.getValue(i)) for i in self.channels_letters]
        text = "COUNTERS VALUES: %d\n"%self.getCountersID() + "\n".join(values)
        return text

class Settings2Ch(object):
    """
    """
    def __init__(self):
        self.channels = ['delay_A', 'delay_B', 'sleep_A', 'sleep_B', 'coincidence_window', 'sampling']
        names = []
        for c in self.channels:
            names += ["%s_ns"%c, "%s_us"%c, "%s_ms"%c, "%s_s"%c]
        for c in names:
            setattr(self, c, 0)

        self.addresses = {}

        for key in list(ADDRESS_DIRECTORY.keys()):
            for c in self.channels:
                if c in key:
                    addr = ADDRESS_DIRECTORY[key]
                    self.addresses[addr] = key

    def setValueFromArray(self, address, value):
        """
        """
        setattr(self, self.addresses[address], value)

    def setSetting(self, setting, value):
        """
        """
        getattr(self, setting + "_ns")
        getattr(self, setting + "_us")
        getattr(self, setting + "_ms")
        getattr(self, setting + "_s")

        if "sampling" in setting:
            setattr(self, setting + "_ns", 0)
            setattr(self, setting + "_us", 0)
            setattr(self, setting + "_ms", value % 1000)
            setattr(self, setting + "_s", value // 1000)

        else:
            setattr(self, setting + "_ns", value % 1000)
            value = value // 1000
            setattr(self, setting + "_us", value % 1000)
            value = value // 1000
            setattr(self, setting + "_ms", value % 1000)
            setattr(self, setting + "_s", value // 1000)

    def getSetting(self, timer):
        """
        """
        ns = getattr(self, "%s_ns" % timer)
        us = getattr(self, "%s_us" % timer)
        ms = getattr(self, "%s_ms" % timer)
        s = getattr(self, "%s_s" % timer)
        if timer == "sampling": # ms
            return int(ms + s*1e3)
        else: # ns
            return int(ns + (us * 1e3) + (ms * 1e6) + (s * 1e9))

    def getAddressAndValue(self, timer):
        """
        """
        return ADDRESS_DIRECTORY[timer], getattr(self, timer)

    def getSettingStr(self, timer):
        value = self.getSetting(timer)
        unit = "ns"
        if timer == "sampling": unit = "ms"
        return "%s (%s): %d"%(timer, unit, value)

    def __repr__(self):
        values = ["\t%s"%(self.getSettingStr(c)) for c in self.channels]
        text = "SETTINGS:\n" + "\n".join(values)
        return text

class AbacusSerial(serial.Serial):
    """
        Builds a serial port from pyserial.
    """
    def __init__(self, port, bounce_timeout = BOUNCE_TIMEOUT):
        super(AbacusSerial, self).__init__(port, baudrate = BAUDRATE, timeout = TIMEOUT)
        self.bounce_timeout = bounce_timeout
        self.flush()

    def flush(self):
        """
        """
        self.flushInput()
        self.flushOutput()

    def getIdn(self):
        """
        """
        self.write(TEST_MESSAGE)
        ans = self.read(30)
        return ans.decode()

    def writeSerial(self, command, address, data_u16):
        """
        """
        if data_u16 > 0xFF:
            msb = data_u16 >> 8
            lsb = data_u16 & 0xFF
        else:
            msb = 0
            lsb = data_u16 & 0xFF
        message = [START_COMMUNICATION, command, address, msb, lsb, END_COMMUNICATION]
        if pyAbacus.constants.DEBUG:
            print('writeSerial:', message)
        self.write(message)

    def readSerial(self):
        """
        """
        for i in range(BOUNCE_TIMEOUT):
            val = self.read()[0]
            if pyAbacus.constants.DEBUG: print('readSerial:', val)
            if val == 0x7E:
                break
        if i == BOUNCE_TIMEOUT - 1:
            raise(TimeOutError())

        numbytes = self.read()[0]
        bytes_read = list(self.read(numbytes))
        checksum = self.read()[0]
        message = [0x7E, numbytes] +  bytes_read + [checksum], numbytes + 3
        if pyAbacus.constants.DEBUG: print('readSerial:', message)
        return message

class Stream(object):
    def __init__(self, abacus_port, counters, output_function = print):
        self.abacus_port = abacus_port
        self.counters = counters
        self.output_function = output_function
        self.stream_on = False
        self.exceptions = []

    def threadFunc(self):
        try:
            counters, id = getAllCounters(self.abacus_port)
            if id != 0:
                values = counters.getValuesFormatted(self.counters)
                self.output_function(values)

            while self.stream_on:
                try:
                    left = getTimeLeft(self.abacus_port)
                    counters, id2 = getAllCounters(self.abacus_port)
                    if id == id2:
                        time.sleep(left / 1000)
                        counters, id = getAllCounters(self.abacus_port)
                    else: id = id2
                    values = counters.getValuesFormatted(self.counters)
                    self.output_function(values)
                except Exception as e: self.exceptions.append(e)
        except Exception as e:
            self.exceptions.append(e)


    def start(self):
        self.stream_on = True
        self.thread = Thread(target = self.threadFunc, daemon = True)
        self.thread.start()

    def stop(self):
        self.stream_on = False

    def setCounters(self, counters):
        self.counters = counters

COUNTERS_VALUES = CountersValues(2)
SETTINGS = Settings2Ch()
