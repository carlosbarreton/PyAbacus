import serial
import serial.tools.list_ports as find_ports

import time
from math import log10
from threading import Thread

from itertools import combinations

from .constants import TIMEOUT, BAUDRATE, START_COMMUNICATION, READ_VALUE, WRITE_VALUE, END_COMMUNICATION, BOUNCE_TIMEOUT
from .constants import CURRENT_OS, ABACUS_SERIALS, TEST_MESSAGE, TEST_ANSWER, COUNTERS_VALUES, SETTINGS
from .constants import ADDRESS_DIRECTORIES, ADDRESS_DIRECTORY_2CH, ADDRESS_DIRECTORY_8CH

from .constants import SAMPLING_VALUES
from .constants import DELAY_MINIMUM_VALUE, DELAY_MAXIMUM_VALUE, DELAY_STEP_VALUE
from .constants import SLEEP_MINIMUM_VALUE, SLEEP_MAXIMUM_VALUE, SLEEP_STEP_VALUE
from .constants import COINCIDENCE_WINDOW_MINIMUM_VALUE, COINCIDENCE_WINDOW_MAXIMUM_VALUE, COINCIDENCE_WINDOW_STEP_VALUE

from .exceptions import *
import pyAbacus.constants

def open(abacus_port):
    """
    """
    global ABACUS_SERIALS, ADDRESS_DIRECTORIES, DEVICES
    if abacus_port in ABACUS_SERIALS.keys():
        close(abacus_port)
    serial = AbacusSerial(DEVICES[abacus_port])
    ABACUS_SERIALS[abacus_port] = serial
    n = serial.getNChannels()
    if n == 2:
        ADDRESS_DIRECTORIES[abacus_port] = ADDRESS_DIRECTORY_2CH
        COUNTERS_VALUES[abacus_port] = CountersValues(2)
        SETTINGS[abacus_port] = Settings2Ch()
    elif n == 4:
        ADDRESS_DIRECTORIES[abacus_port] = ADDRESS_DIRECTORY_8CH
        COUNTERS_VALUES[abacus_port] = CountersValues(4)
        SETTINGS[abacus_port] = Settings4Ch()
    elif n == 8:
        ADDRESS_DIRECTORIES[abacus_port] = ADDRESS_DIRECTORY_8CH
        COUNTERS_VALUES[abacus_port] = CountersValues(8)
        SETTINGS[abacus_port] = Settings8Ch()

def close(abacus_port):
    """
    """
    global ABACUS_SERIALS, ADDRESS_DIRECTORIES
    if abacus_port in ABACUS_SERIALS.keys():
        try:
            ABACUS_SERIALS[abacus_port].close()
        except Exception as e:
            print(e)
        del ABACUS_SERIALS[abacus_port]
    if abacus_port in ADDRESS_DIRECTORIES.keys():
        del ADDRESS_DIRECTORIES[abacus_port]

def getChannelsFromName(name):
    """
    """
    if "AB1002" in name:
        return 2
    elif "AB1004" in name:
        return 4
    elif "AB1008" in name:
        return 8
    else:
        raise(AbacusError("Not a valid abacus."))

def writeSerial(abacus_port, command, address, data_16o32):
    """
    """
    global ABACUS_SERIALS

    serial = ABACUS_SERIALS[abacus_port]
    serial.writeSerial(command, address, data_16o32)

def readSerial(abacus_port):
    """
    """
    global ABACUS_SERIALS
    return ABACUS_SERIALS[abacus_port].readSerial()

def dataStreamToDataArrays(input_string, chunck_size = 3):
    """
    """
    input_string, n = input_string
    test = sum(input_string[2:]) & 0xFF # 8 bit
    # if test != 0xFF:
    #     raise(CheckSumError())
    if test == 0xFF:
        chuncks = input_string[2 : -1] # (addr & MSB & LSB)^n
        if chunck_size == 3:
            chuncks = [chuncks[i:i + 3] for i in range(0, n-3, 3)]
            addresses = [chunck[0] for chunck in chuncks]
            data = [(chunck[1] << 8) | (chunck[2]) for chunck in chuncks]
        elif chunck_size == 5:
            chuncks = [chuncks[i:i + 5] for i in range(0, n-5, 5)]
            addresses = [chunck[0] for chunck in chuncks]
            data = [(chunck[1] << 8 * 3) | (chunck[2] << 8 * 2) | (chunck[3] << 8 * 1) | (chunck[4]) for chunck in chuncks]
        else:
            raise(AbacusError("Input string is not valid chuck size must either be 3 or 5."))
        return addresses, data
    else:
        if pyAbacus.constants.DEBUG: print("CheckSumError")
        return [], []

def dataArraysToCounters(abacus_port, addresses, data):
    """
    """
    global COUNTERS_VALUES
    for i in range(len(addresses)):
        COUNTERS_VALUES[abacus_port].setValueFromArray(addresses[i], data[i])
    return COUNTERS_VALUES[abacus_port]

def dataArraysToSettings(abacus_port, addresses, data):
    """
    """
    global SETTINGS
    for i in range(len(addresses)):
        SETTINGS[abacus_port].setValueFromArray(addresses[i], data[i])
    return SETTINGS[abacus_port]

def getAllCounters(abacus_port):
    """
    """
    global COUNTERS_VALUES
    n = ABACUS_SERIALS[abacus_port].getNChannels()
    counters = COUNTERS_VALUES[abacus_port]
    if n == 2:
        writeSerial(abacus_port, READ_VALUE, 24, 6)
        data = readSerial(abacus_port)
        array, datas = dataStreamToDataArrays(data)
        dataArraysToCounters(abacus_port, array, datas)
    else:
        mode = 1 << 24
        writeSerial(abacus_port, READ_VALUE, 0, mode & 0x00)
        data = readSerial(abacus_port)
        # addresses = list(counters.getNumericAddresses().keys())
        # multiple_a = []
        # multiple_d = []
        # for address in addresses:
        #     writeSerial(abacus_port, READ_VALUE, address, 0)
        #     data = readSerial(abacus_port)
        #     array, datas = dataStreamToDataArrays(data, chunck_size = 5)
        #     multiple_a += array
        #     multiple_d += datas
        # dataArraysToCounters(abacus_port, array, datas)
    return COUNTERS_VALUES[abacus_port], getCountersID(abacus_port)

def getFollowingCounters(abacus_port, counters):
    """
    """
    global COUNTERS_VALUES
    if len(counters) > 0:
        n = ABACUS_SERIALS[abacus_port].getNChannels()
        counter = COUNTERS_VALUES[abacus_port]
        address = ADDRESS_DIRECTORIES[abacus_port]
        if n == 2:
            counters = ["counts_%s_LSB"%c for c in counters]
            multiple_a = []
            multiple_d = []
            for c in counters:
                writeSerial(abacus_port, READ_VALUE, address[c], 2)
                data = readSerial(abacus_port)
                array, datas = dataStreamToDataArrays(data)
                multiple_a += array
                multiple_d += datas
            dataArraysToCounters(abacus_port, array, datas)
        else:
            single_double = ["counts_%s"%c for c in counters if len(c) < 3]
            multiple = ["custom_c%d"%(i + 1) for i in range(len(counters) - len(single_double))]
            counters = single_double + multiple
            multiple_a = []
            multiple_d = []
            for c in counters:
                writeSerial(abacus_port, READ_VALUE, address[c], 0)
                data = readSerial(abacus_port)
                array, datas = dataStreamToDataArrays(data, chunck_size = 5)
                multiple_a += array
                multiple_d += datas
            dataArraysToCounters(abacus_port, array, datas)
    return COUNTERS_VALUES[abacus_port], getCountersID(abacus_port)

def getAllSettings(abacus_port):
    """
    """
    global SETTINGS
    def get(abacus_port, first, last, chunck_size):
        writeSerial(abacus_port, READ_VALUE, first, last - first + 1)
        data = readSerial(abacus_port)
        array, datas = dataStreamToDataArrays(data, chunck_size)
        dataArraysToSettings(abacus_port, array, datas)

    tp =  type(SETTINGS[abacus_port])

    if tp is Settings2Ch:
        first = ADDRESS_DIRECTORY_2CH["delay_A_ns"]
        last = ADDRESS_DIRECTORY_2CH["coincidence_window_s"]
        get(abacus_port, first, last, 3)
    elif tp is Settings4Ch:
        first = ADDRESS_DIRECTORY_8CH["delay_A"]
        last = ADDRESS_DIRECTORY_8CH["delay_D"]
        get(abacus_port, first, last, 5)
        first = ADDRESS_DIRECTORY_8CH["sleep_A"]
        last = ADDRESS_DIRECTORY_8CH["sleep_D"]
        get(abacus_port, first, last, 5)
        first = ADDRESS_DIRECTORY_8CH["sampling"]
        last = ADDRESS_DIRECTORY_8CH["coincidence_window"]
        get(abacus_port, first, last, 5)
        first = ADDRESS_DIRECTORY_8CH["config_custom_c1"]
        get(abacus_port, first, first, 5)

    elif tp is Settings8Ch:
        first = ADDRESS_DIRECTORY_8CH["delay_A"]
        last = ADDRESS_DIRECTORY_8CH["coincidence_window"]
        get(abacus_port, first, last)

    return SETTINGS[abacus_port]

def getSetting(abacus_port, setting):
    """
    """
    global SETTINGS

    settings = SETTINGS[abacus_port]
    if type(settings) is Settings2Ch:
        addr, val = settings.getAddressAndValue(setting + "_ns")
        writeSerial(abacus_port, READ_VALUE, addr, 4)

    else:
        addr, val = settings.getAddressAndValue(setting)
        writeSerial(abacus_port, READ_VALUE, addr, 0)

    data = readSerial(abacus_port)
    if ABACUS_SERIALS[abacus_port].getNChannels() == 2:
        array, datas = dataStreamToDataArrays(data)
    else:
        array, datas = dataStreamToDataArrays(data, chunck_size = 5)
    dataArraysToSettings(abacus_port, array, datas)

    return SETTINGS[abacus_port].getSetting(setting)

def getIdn(abacus_port):
    """
    """
    global ABACUS_SERIALS
    return ABACUS_SERIALS[abacus_port].getIdn()

def getCountersID(abacus_port):
    """
    """
    global COUNTERS_VALUES, ADDRESS_DIRECTORIES

    writeSerial(abacus_port, READ_VALUE, ADDRESS_DIRECTORIES[abacus_port]["dataID"], 0)
    data = readSerial(abacus_port)
    if ABACUS_SERIALS[abacus_port].getNChannels() == 2:
        array, datas = dataStreamToDataArrays(data)
    else:
        array, datas = dataStreamToDataArrays(data, chunck_size = 5)
    COUNTERS_VALUES[abacus_port].setCountersID(datas[0])
    return datas[0]

def getTimeLeft(abacus_port):
    """
    """
    global COUNTERS_VALUES, ADDRESS_DIRECTORIES

    writeSerial(abacus_port, READ_VALUE, ADDRESS_DIRECTORIES[abacus_port]["time_left"], 0)
    data = readSerial(abacus_port)
    if ABACUS_SERIALS[abacus_port].getNChannels() == 2:
        array, datas = dataStreamToDataArrays(data)
    else:
        array, datas = dataStreamToDataArrays(data, chunck_size = 5)
    COUNTERS_VALUES[abacus_port].setTimeLeft(datas[0])
    return COUNTERS_VALUES[abacus_port].getTimeLeft()

def setSetting(abacus_port, setting, value):
    """
    """
    global SETTINGS
    settings = SETTINGS[abacus_port]
    settings.setSetting(setting, value)

    if type(settings) is Settings2Ch:
        suffix = ["_ns", "_us", "_ms", "_s"]
        for s in suffix:
            addr, val = settings.getAddressAndValue(setting + s)
            writeSerial(abacus_port, WRITE_VALUE, addr, val)
    else:
        addr, val = settings.getAddressAndValue(setting)
        writeSerial(abacus_port, WRITE_VALUE, addr, val)

def setAllSettings(abacus_port, new_settings):
    """
    """
    global SETTINGS
    if type(new_settings) is Settings2Ch:
        SETTINGS[abacus_port] = new_settings
        for setting in SETTINGS[abacus_port].addresses.values():
            addr, val = SETTINGS[abacus_port].getAddressAndValue(setting)
            writeSerial(abacus_port, WRITE_VALUE, addr, val)
    else:
        raise(Exception("New settings are not a valid type."))

def findDevices(print_on = True):
    """
    """
    global CURRENT_OS, DEVICES
    ports_objects = list(find_ports.comports())
    ports = {}
    keys = []
    for i in range(len(ports_objects)):
        port = ports_objects[i]
        attrs = ["device", "name", "description", "hwid", "vid", "pid",
         "serial_number", "location", "manufacturer", "product", "interface"]

        if print_on:
            for attr in attrs:
                print(attr + ":", eval("port.%s"%attr))
        try:
            serial = AbacusSerial(port.device)
            idn = serial.getIdn()
            keys = list(renameDuplicates(keys + [idn]))
            ports[keys[-1]] = port.device
            serial.close()
        except AbacusError:
            pass
        except Exception as e:
            print(port.device, e)
    DEVICES = ports
    return ports, len(ports)

def renameDuplicates(old):
    """
    """
    seen = {}
    for x in old:
        if x in seen:
            seen[x] += 1
            yield "%s-%d" % (x, seen[x])
        else:
            seen[x] = 0
            yield x

def customBinaryToLetters(number):
    binary = bin(number)[2:]
    n = len(binary)
    if n < 8: binary = '0' * (8 - n) + binary
    letters = [chr(i + ord('A')) for i in range(8) if binary[i] == '1']
    return ''.join(letters)

def customLettersToBinary(letters):
    valid = [chr(i + ord('A')) for i in range(8)]
    numbers = ['1' if valid[i] in letters else '0' for i in range(8)]
    number = int('0b' + ''.join(numbers), base = 2)
    return number

class CountersValues(object):
    """
    """
    def __init__(self, n_channels):
        if not n_channels in [2, 4, 8]:
            raise(BaseError("%d is not a valid number of channels (2, 4, 6)."%n_channels))
        letters = [chr(ord('A') + i) for i in range(n_channels)]
        channels = []
        for i in range(1, 3): # n_channels + 1
            for item in combinations("".join(letters), i):
                item = "".join(item)
                channels.append(item)

        self.n_channels = n_channels
        self.channels_letters = channels

        if n_channels == 2:
            for c in channels:
                setattr(self, "%s_LSB"%c, 0)
                setattr(self, "%s_MSB"%c, 0)
        else:
            for c in channels:
                setattr(self, "%s"%c, 0)

        self.addresses = {}

        if n_channels == 2:
            directory = ADDRESS_DIRECTORY_2CH
        else:
            directory = ADDRESS_DIRECTORY_8CH

        for key in list(directory.keys()):
            for c in channels:
                txt = "counts_%s"%c
                if n_channels == 2:
                    if ("%s_LSB"%txt == key) or ("%s_MSB"%txt == key): pass
                    else: continue
                else:
                    if txt != key: continue
                addr = directory[key]
                self.addresses[addr] = key.replace("counts_", "")

        self.numeric_addresses = self.addresses.copy()

        if n_channels == 2:
            self.addresses[30] = 'dataID'
            self.addresses[31] = 'time_left'

        else:
            self.addresses[83] = 'dataID'
            self.addresses[84] = 'time_left'
            self.addresses[96] = 'custom_c1'
            if n_channels > 4:
                self.addresses[83] = 'dataID'
                self.addresses[84] = 'time_left'
                self.addresses[97] = 'custom_c2'
                self.addresses[98] = 'custom_c3'
                self.addresses[99] = 'custom_c4'
                self.addresses[100] = 'custom_c5'
                self.addresses[101] = 'custom_c6'
                self.addresses[102] = 'custom_c7'
                self.addresses[103] = 'custom_c8'

        self.counters_id = 0
        self.time_left = 0 #: in ms

    def setValueFromArray(self, address, value):
        """
        """
        setattr(self, self.addresses[address], value)

    def getValue(self, channel):
        """
        """
        if self.n_channels == 2:
            msb = getattr(self, "%s_MSB" % channel) << 16
            lsb = getattr(self, "%s_LSB" % channel)

            return msb | lsb
        else:
            return getattr(self, "%s" % channel)

    def getValues(self, channels):
        """
        """
        return [self.getValue(c) for c in channels]

    def getValuesFormatted(self, channels):
        """
        """
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
        return self.time_left

    def setTimeLeft(self, time):
        """
        """
        self.time_left = time # ms

    def getNumericAddresses(self):
        """
        """
        return self.numeric_addresses

    def __repr__(self):
        values = ["\t%s: %d"%(i, self.getValue(i)) for i in self.channels_letters]
        text = "COUNTERS VALUES: %d\n"%self.getCountersID() + "\n".join(values)
        return text

class SettingsBase(object):
    def __init__(self):
        self.addresses = {}

    def setValueFromArray(self, address, value):
        """
        """
        setattr(self, self.addresses[address], value)

    def valueCheck(self, value, min, max, step):
        """
        """
        if (value >= min) and (value <= max) and (value % step == 0):
            return True
        else: return False

    def verifySetting(self, setting, value):
        """
        """
        if "delay" in setting:
            if not self.valueCheck(value, DELAY_MINIMUM_VALUE, \
                DELAY_MAXIMUM_VALUE, DELAY_STEP_VALUE):
                txt = "(%d <= %d delay (ns) <= %d) with steps of: %d"%(DELAY_MINIMUM_VALUE, \
                value, DELAY_MAXIMUM_VALUE, DELAY_STEP_VALUE)
                raise(InvalidValueError(txt))

        elif "sleep" in setting:
            if not self.valueCheck(value, SLEEP_MINIMUM_VALUE, \
                SLEEP_MAXIMUM_VALUE, SLEEP_STEP_VALUE):
                txt = "(%d <= %d sleep (ns) <= %d) with steps of: %d"%(SLEEP_MINIMUM_VALUE, \
                value, SLEEP_MAXIMUM_VALUE, SLEEP_STEP_VALUE)
                raise(InvalidValueError(txt))

        elif "coincidence_window" in setting:
            if not self.valueCheck(value, COINCIDENCE_WINDOW_MINIMUM_VALUE, \
                COINCIDENCE_WINDOW_MAXIMUM_VALUE, COINCIDENCE_WINDOW_STEP_VALUE):
                txt = " (%d <= %d coincidence window (ns) <= %d) with steps of: %d"%(COINCIDENCE_WINDOW_MINIMUM_VALUE, \
                value, COINCIDENCE_WINDOW_MAXIMUM_VALUE, COINCIDENCE_WINDOW_STEP_VALUE)
                raise(InvalidValueError(txt))

        elif "sampling" in setting:
            if not int(value) in SAMPLING_VALUES:
                sampling = ", ".join(["%d"%i for i in SAMPLING_VALUES])
                txt = ", sampling time must be one of the following: %s (ms)"%sampling
                raise(InvalidValueError(txt))

    def __repr__(self):
        values = ["\t%s"%(self.getSettingStr(c)) for c in self.channels]
        text = "SETTINGS[abacus_port]:\n" + "\n".join(values)
        return text

class Settings48Ch(SettingsBase):
    """
        4 and 8 channel devices use as time base a second. Nevertheless 2 channel uses ns for all timers with the exception of the sampling time (ms).
    """
    def __init__(self):
        super(Settings48Ch, self).__init__()

    def initAddreses(self):
        """
        """
        for c in self.channels:
            setattr(self, c, 0)

        keys = list(ADDRESS_DIRECTORY_8CH.keys())
        for c in self.channels:
            if c in keys:
                addr = ADDRESS_DIRECTORY_8CH[c]
                self.addresses[addr] = c

    def getChannels(self):
        """
        """
        return self.channels

    def setSetting(self, setting, value):
        """
            For all timers: value is in nanoseconds, for sampling in ms.
        """
        if 'custom' in setting:
            bits = customLettersToBinary(value)
        else:
            if setting == "sampling":
                if self.valueCheck(value, min(SAMPLING_VALUES), \
                    max(SAMPLING_VALUES), 1):
                    c, e = self.valueToExponentRepresentation(value / 1000)
                else:
                    raise(InvalidValueError("Sampling value of %d is not valid."%value))
            else:
                self.verifySetting(setting, value)
                c, e = self.valueToExponentRepresentation(value / int(1e9))
            bits = self.exponentsToBits(c, e)
        setattr(self, setting, bits)

    def getSetting(self, timer):
        """
            For all timers: returns nanoseconds, for sampling returns ms.
        """
        bits = getattr(self, timer)
        if 'custom' in timer:
            return customBinaryToLetters(bits)
        else:
            value = self.fromBitsToValue(bits)
            if timer == "sampling":
                return value * 1000
            return value * int(1e9)

    def getAddressAndValue(self, timer):
        """
        """
        return ADDRESS_DIRECTORY_8CH[timer], getattr(self, timer)

    def getSettingStr(self, timer):
        """
        """
        value = self.getSetting(timer)
        unit = "ns"
        if timer == "sampling": unit = "ms"
        return "%s (%s): %d"%(timer, unit, value)

    def fromBitsToValue(self, bits):
        """
        """
        e = bits >> 12
        c = bits & 0xFFF
        return self.exponentRepresentationToValue(c, e)

    def exponentRepresentationToValue(self, c, e):
        """
        """
        return int(c) * 10 ** (int(e) - 10)

    def valueToExponentRepresentation(self, number):
        """
        """
        if number == 0:
            return 0, 0
        else:
            r = log10(number) + 10
            e = int(r)
            c = round(10 ** (r - e), 2)
            if (c < 10):
                e -= 1
                c *= 10
            c = int(c)
            if (e > 12) or (e < 0) or (c < 10) or (c > 99):
                raise(InvalidValueError(". %.1e is a value outside range."%number))
            n = self.exponentRepresentationToValue(c, e)
            if abs(n - number) < 1e-10:
                return c, e
            else:
                raise(InvalidValueError(". Only two signficant figures are posible %f"%number))

    def exponentsToBits(self, c, e):
        """
        """
        e = e << 12
        c = c & 0xFFF
        return e | c

class Settings2Ch(SettingsBase):
    """
    """
    def __init__(self):
        super(Settings2Ch, self).__init__()

        names = []
        self.channels = ['delay_A', 'delay_B', 'sleep_A', 'sleep_B', 'coincidence_window', 'sampling']
        for c in self.channels:
            names += ["%s_ns"%c, "%s_us"%c, "%s_ms"%c, "%s_s"%c]
        for c in names:
            setattr(self, c, 0)

        for key in list(ADDRESS_DIRECTORY_2CH.keys()):
            for c in self.channels:
                if c in key:
                    addr = ADDRESS_DIRECTORY_2CH[key]
                    self.addresses[addr] = key

    def setSetting(self, setting, value):
        """
        """
        self.verifySetting(setting, value)
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
        return ADDRESS_DIRECTORY_2CH[timer], getattr(self, timer)

    def getSettingStr(self, timer):
        """
        """
        value = self.getSetting(timer)
        unit = "ns"
        if timer == "sampling": unit = "ms"
        return "%s (%s): %d"%(timer, unit, value)

class Settings4Ch(Settings48Ch):
    """
        4 and 8 channel devices use as time base a second. Nevertheless 2 channel uses ns for all timers with the exception of the sampling time (ms).
    """
    def __init__(self):
        super(Settings4Ch, self).__init__()
        self.channels = ['delay_A', 'delay_B', 'delay_C', 'delay_D',
                        'sleep_A', 'sleep_B', 'sleep_C', 'sleep_D',
                        'coincidence_window', 'sampling', 'config_custom_c1']

        self.initAddreses()

class Settings8Ch(Settings48Ch):
    """
        4 and 8 channel devices use as time base a second. Nevertheless 2 channel uses ns for all timers with the exception of the sampling time (ms).
    """
    def __init__(self):
        super(Settings8Ch, self).__init__()
        self.channels = ['delay_A', 'delay_B', 'delay_C', 'delay_D',
                        'delay_E', 'delay_F', 'delay_G', 'delay_H',
                        'sleep_A', 'sleep_B', 'sleep_C', 'sleep_D',
                        'sleep_E', 'sleep_F', 'sleep_G', 'sleep_H',
                        'coincidence_window', 'sampling', 'config_custom_c1',
                        'config_custom_c2', 'config_custom_c3', 'config_custom_c4',
                        'config_custom_c5', 'config_custom_c6', 'config_custom_c7',
                         'config_custom_c8']

        self.initAddreses()

class AbacusSerial(serial.Serial):
    """
        Builds a serial port from pyserial.
    """
    def __init__(self, port, bounce_timeout = BOUNCE_TIMEOUT):
        super(AbacusSerial, self).__init__(port, baudrate = BAUDRATE, timeout = TIMEOUT)
        self.bounce_timeout = bounce_timeout
        self.idn = ""
        self.flush()
        if self.testDevice():
            self.n_channels = getChannelsFromName(self.getIdn())
        else:
            if pyAbacus.constants.DEBUG:
                print(port, "answered: %s"%self.getIdn())
            self.close()
            raise(AbacusError("Not a valid abacus."))

    def flush(self):
        """
        """
        self.flushInput()
        self.flushOutput()

    def findIdn(self):
        """
        """
        self.write(TEST_MESSAGE)
        self.idn = self.read(21).decode()
        time.sleep(1)
        return self.idn

    def getIdn(self):
        """
        """
        return self.idn

    def testDevice(self):
        """
        """
        ans = self.findIdn()
        if TEST_ANSWER in ans: return True
        return False

    def writeSerial(self, command, address, data_16o32):
        """
        """
        if self.n_channels == 2:
            msb = (data_16o32 >> 8) & 0xFF
            lsb = data_16o32 & 0xFF
            message = [START_COMMUNICATION, command, address, msb, lsb, END_COMMUNICATION]
        else:
            bits = [(data_16o32 >> 8 * i) & 0xFF for i in range(3, -1, -1)]
            message = [START_COMMUNICATION, command, address] + bits + [END_COMMUNICATION]
        if pyAbacus.constants.DEBUG:
            print('writeSerial:', message)
        self.write(message)

    def readSerial(self):
        """
        """
        # for i in range(BOUNCE_TIMEOUT):
        #     val = self.read()
        #     if val != b"":
        #         val = val[0]
        #         if pyAbacus.constants.DEBUG: print('readSerial:', val)
        #         if val == 0x7E:
        #             break
        # if i == BOUNCE_TIMEOUT - 1:
        #     raise(TimeOutError())

        try:
            if self.read()[0] == 0x7E:
                numbytes = self.read()[0]
                bytes_read = list(self.read(numbytes))
                checksum = self.read()[0]
                message = [0x7E, numbytes] +  bytes_read + [checksum], numbytes + 3
                if pyAbacus.constants.DEBUG: print('readSerial:', message)
                return message
        except IndexError:
            pass
        if pyAbacus.constants.DEBUG:
            print("Error on readSerial")
        return [], 0

    def getNChannels(self):
        """
        """
        return self.n_channels

class Stream(object):
    """
    """
    def __init__(self, abacus_port, counters, output_function = print):
        self.abacus_port = abacus_port
        self.counters = counters
        self.output_function = output_function
        self.stream_on = False
        self.exceptions = []
        self.all = False
        if len(counters) == ABACUS_SERIALS[abacus_port].getNChannels():
            self.all = True

    def threadFunc(self):
        # try:
        if self.all: counters, id = getAllCounters(self.abacus_port)
        else: counters, id = getFollowingCounters(self.abacus_port, self.counters)
        if id != 0:
            values = counters.getValuesFormatted(self.counters)
            self.output_function(values)

        while self.stream_on:
            # try:
            left = getTimeLeft(self.abacus_port)
            if self.all: counters, id2 = getAllCounters(self.abacus_port)
            else: counters, id2 = getFollowingCounters(self.abacus_port, self.counters)
            if id == id2:
                time.sleep(left / 1000)
                if self.all: counters, id = getAllCounters(self.abacus_port)
                else: counters, id = getFollowingCounters(self.abacus_port, self.counters)
            else: id = id2
            values = counters.getValuesFormatted(self.counters)
            self.output_function(values)
        # except Exception as e:
        #     self.exceptions.append(e)

    def start(self):
        """
        """
        self.stream_on = True
        self.thread = Thread(target = self.threadFunc, daemon = True)
        self.thread.start()

    def stop(self):
        """
        """
        self.stream_on = False

    def setCounters(self, counters):
        """
        """
        self.counters = counters
