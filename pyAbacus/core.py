import serial
import serial.tools.list_ports as find_ports

from itertools import combinations

from .constants import TIMEOUT, BAUDRATE, START_COMMUNICATION, READ_VALUE, WRITE_VALUE, END_COMMUNICATION, BOUNCE_TIMEOUT
from .constants import CURRENT_OS, ABACUS_SERIALS, TEST_MESSAGE, TEST_ANSWER, ADDRESS_DIRECTORY, COUNTERS_VALUES, SETTINGS
from .exceptions import *

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
    test = sum(input_string[2:]) & 0xFF # 8 bit
    if test != 0xFF:
        raise(CheckSumError())
    n = input_string[1]
    chuncks = input_string[2 : -1] # (addr & MSB & LSB)^n
    chuncks = [chuncks[i:i + 3] for i in range(0, n, 3)]
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
    writeSerial(abacus_port, READ_VALUE, 24, 8)
    data = readSerial(abacus_port)
    array, datas = dataStreamToDataArrays(data)
    dataArraysToCounters(array, datas)
    return COUNTERS_VALUES, COUNTERS_VALUES.getCountersID()

def getAllSettings(abacus_port):
    """
    """
    global SETTINGS
    writeSerial(abacus_port, READ_VALUE, 0, 24)
    data = readSerial(abacus_port)
    array, datas = dataStreamToDataArrays(data)
    dataArraysToSettings(array, datas)
    return SETTINGS

def getSetting(abacus_port, setting):
    """
    """
    global SETTINGS

    addr, val = SETTINGS.getAddressAndValue(setting + "_ns")
    writeSerial(abacus_port, READ_VALUE, addr, 4)

    data = readSerial(abacus_port)
    array, datas = dataStreamToDataArrays(data)
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
    global SETTINGS

    writeSerial(abacus_port, READ_VALUE, ADDRESS_DIRECTORY["measure_number"], 0)
    data = readSerial(abacus_port)
    array, datas = dataStreamToDataArrays(data)
    dataArraysToSettings(array, datas)

    return SETTINGS.getCountersID()

def getTimeLeft(abacus_port):
    """
    """
    global SETTINGS

    writeSerial(abacus_port, READ_VALUE, ADDRESS_DIRECTORY["time_to_next_sample"], 0)
    data = readSerial(abacus_port)
    array, datas = dataStreamToDataArrays(data)
    dataArraysToSettings(array, datas)

    return SETTINGS.getTimeLeft()

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

def findDevices():
    """
    """
    global CURRENT_OS
    ports_objects = list(find_ports.comports())
    ports = {}
    for i in range(len(ports_objects)):
        port = ports_objects[i]

        attrs = ["device", "name", "description", "hwid", "vid", "pid",
         "serial_number", "location", "manufacturer", "product", "interface"]

        for attr in attrs:
            print(attr + ":", eval("port.%s"%attr))
            
        try:
            serial = AbacusSerial(port.device)
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
        self.measure_number = 0
        self.time_to_next_sample = 0

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

    def getCountersID(self):
        """
        """
        return self.measure_number

    def getTimeLeft(self):
        """
        """
        return self.time_to_next_sample

class Settings2Ch(object):
    """
    """
    def __init__(self):
        channels = ['delay_A', 'delay_B', 'sleep_A', 'sleep_B', 'coincidence_window', 'sampling']
        names = []
        for c in channels:
            names += ["%s_ns"%c, "%s_us"%c, "%s_ms"%c, "%s_s"%c]
        for c in names:
            setattr(self, c, 0)

        self.addresses = {}

        for key in list(ADDRESS_DIRECTORY.keys()):
            for c in channels:
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

class AbacusSerial(serial.Serial):
    """
        Builds a serial port from pyserial.
    """
    def __init__(self, port, bounce_timeout = BOUNCE_TIMEOUT):
        super(AbacusSerial, self).__init__(port, baudrate = BAUDRATE, timeout = TIMEOUT)
        self.bounce_timeout = bounce_timeout
        self.flush()
        # self.testAbacus()

    def flush(self):
        """
        """
        self.flushInput()
        self.flushOutput()

    def getIdn(self):
        """
        """
        self.write(TEST_MESSAGE)
        ans = self.read(20)

    def writeSerial(self, command, address, data_u16):
        """
        """
        if data_u16 > 0xFF:
            msb = data_u16 >> 8
            lsb = data_u16 & 0xFF
        else:
            msb = 0
            lsb = data_u16 & 0xFF
        self.write([START_COMMUNICATION, command, address, msb, lsb, END_COMMUNICATION])

    def readSerial(self):
        """
        """
        for i in range(BOUNCE_TIMEOUT):
            if self.read() == 0x7E:
                break
        if i == BOUNCE_TIMEOUT - 1:
            raise(TimeOutError())

        numbytes = self.read()
        bytes_read = self.read(numbytes)
        checksum = self.read()

        return [0x7E, numbytes] +  bytes_read + [checksum], numbytes + 3

COUNTERS_VALUES = CountersValues(2)
SETTINGS = Settings2Ch()
