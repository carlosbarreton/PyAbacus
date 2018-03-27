import serial
import codecs
from time import sleep
from queue import Queue
from random import random
from threading import Thread, Timer, Event
import serial.tools.list_ports as find_ports

from .constants import *
from .exceptions import *

class CommunicationPort(object):
    """ Builds a serial port from pyserial.

    Implements multiple functions that will be used by different instances of the experiment.

    **Constants**
    """
    BAUDRATE = 115200 #: Default baudrate for the serial port communication
    TIMEOUT = 0.04 #: Maximum time without answer from the serial port
    BOUNCE_TIMEOUT = 20 #: Number of times a specific transmition is tried
    PARITY = serial.PARITY_NONE #: Message will not have any parity
    STOP_BITS = serial.STOPBITS_ONE #: Message contains only one stop bit
    BYTE_SIZE = serial.EIGHTBITS #: One byte = 8 bits
    TEST_MESSAGE = [START_COMMUNICATION, READ_VALUE, 0x00,
               0x00, 0x00, END_COMMUNICATION]

    def __init__(self, name, baudrate = BAUDRATE, timeout = TIMEOUT, bounce_timeout = BOUNCE_TIMEOUT):
        self.name = name
        self.baudrate = baudrate
        self.timeout = timeout
        self.bounce_timeout = bounce_timeout

        self.serial = self.beginSerial()
        self.flush()

        # Implements a Queue to send messages
        self.stop = False
        self.thread = None
        self.queue = Queue()
        self.answer = {}
        self.beginThread()

    def flush(self):
        try:
            self.serial.flushInput()
            self.serial.flushOutput()
            # self.serial.flush()
        except Exception as e:
            self.stop = True
            raise CommunicationCriticalError(e)


    def beginThread(self):
        self.thread = Thread(target=self.queueLoop)
        self.thread.setDaemon(True)
        self.thread.start()

    def beginSerial(self):
        """ Initializes pyserial instance.

        Returns:
            pyserial.serial object

        Raises:
            PermissionError: user is not allowed to use port.
            SerialException: if it could not open port
        """
        self.is_opened = True
        __serial__ = serial.Serial(port=self.name, baudrate=self.baudrate, parity=self.PARITY,
                                        stopbits=self.STOP_BITS,
                                        bytesize=self.BYTE_SIZE, timeout=self.TIMEOUT)
        return __serial__

    def checkSum(self, hex_list):
        """ Implements a simple checksum to verify message integrity.

        Raises:
            CheckSumError(): in case checksum is wrong.
        """
        int_list = [int(value, 16) for value in hex_list]
        int_score = sum(int_list[2:-1])
        hex_score = "%04X"%int_score
        last_values = hex_score[2:]
        check = int(last_values, 16) + int(hex_list[-1], 16)
        if check != 0xff:
            raise CheckSumError()

    def write(self, content):
        """ Sends a message through the serial port.

        Raises:
            PySerialExceptions
        """
        # self.flush()
        try:
            # self.serial.flushInput()
            self.serial.write(content)
            self.serial.flush()
        except Exception as e:
            self.stop = True
            raise CommunicationCriticalError(e)

    def __read__(self, n):
        try:
            return self.serial.read(n)
        except Exception as e:
            self.stop = True
            raise CommunicationCriticalError(e)

    def read(self):
        """ Reads a message through the serial port.

        Returns:
            list: hexadecimal values decoded as strings.

        Raises:
            CommunicationError:
        """
        hexa = [codecs.encode(self.__read__(1), "hex_codec").decode()]
        if hexa[0] != "7e":
            raise CommunicationError()
        hexa += [codecs.encode(self.__read__(1), "hex_codec").decode()]

        try:
            N = int(hexa[1], 16)
        except ValueError:
            raise CommunicationError()
        byte = codecs.encode(self.__read__(N+1), "hex_codec").decode()
        byte = list(map(''.join, zip(*[iter(byte)]*2)))
        hexa += byte
        return hexa

    def receive(self):
        """ Organices information according to project requirements.

        Returns:
            list: each position on list is made up with a tuple containing
                channel and value in hexadecimal base.

        Raises:
            CheckSumError: if wrong checksum.
        """
        hexa = self.read()
        self.checkSum(hexa) # checks if checksum is correct
        hexa = hexa[2:-1]
        n = len(hexa)//3 #signal comes in groups of three

        ans = []
        for i in range(n):
            channel = int(hexa[3*i], 16)
            value = hexa[3*i+1] + hexa[3*i+2]
            ans.append((channel, value))
        return ans

    def queueLoop(self):
        """ Permanent loop in charge of sending any message withing the queue
        one by one.

        Raises:
            Exception: any type of error withing serial.
        """
        while not self.stop:
            conf, event, wait_for_answer, content = self.queue.get()
            try:
                answer = self.internalMessage(content, wait_for_answer) # call function
                self.answer[conf] = answer
                event.set()
            except Exception as e:
                if event != None:
                    event.set()

    def message(self, content, wait_for_answer = False):
        """ Method to which different instances have access. Instances use this
        method in order to communicate a message 'content' to the serial port.
        The content of the message is added to the queue and waits for an answer
        inside a loop.

        Returns:
            list: of hexadecimal values.
        Raises:
            CommunicationError: if communication port is closed, and a answer is
            expected.
        """
        conf = random()
        event = Event()
        self.queue.put((conf, event, wait_for_answer, content))
        event.wait()
        if conf in self.answer:
            return self.answer.pop(conf)
        raise CommunicationError()

    def internalMessage(self, content, wait_for_answer = False):
        """ Sends a message, and waits for answer.

        Returns:
            list: each postion on list is made up with a tuple containing
                channel and value in hexadecimal base.

        Raises:
            Exception: any type ocurred with during `bounce_timeout`.
        """

        for i in range(self.bounce_timeout):
            try:
                self.write(content)
                if wait_for_answer:
                    answer = self.receive()
                    expected = int(hex(content[-3]).replace('x', '') + hex(content[-2]).replace('x', ''), 16)
                    if expected == 0:
                        expected = 1
                    if expected != len(answer) or content[2] != answer[0][0]:
                        pass
                    else:
                        return answer
                else:
                    return None
            except CommunicationError:
                self.flush()
            except CheckSumError:
                self.flush()
            if i == self.bounce_timeout - 1:
                self.stop = True
                raise CommunicationError()
            print("Communication trial: %d"%(i+1))

    def testMessageAbacus(self):
        """ Tests whether or not the CommunicationPort corresponds to a Abacus one.

        Returns:
            boolean: True if it does, False otherwise.
        """
        try:
            self.internalMessage(serial.to_bytes(self.TEST_MESSAGE),
                                    wait_for_answer = True)
            return True
        except CommunicationError:
            return False

    def updateSerial(self, port_name):
        self.device = port_name
        self.close()
        self.serial = self.beginSerial()
        self.stop = False
        self.beginThread()

    def isOpenend(self):
        return self.is_opened

    def close(self):
        """ Closes the serial port."""
        self.serial.close()
        self.is_opened = False
        self.stop = True

    def __del__(self):
        self.close()

def findPorts(testAbacus = True):
    global CURRENT_OS
    ports_objects = list(find_ports.comports())
    ports = {}
    for i in range(len(ports_objects)):
        port = ports_objects[i]
        try:
            com =  CommunicationPort(port.device)
            result = False
            if testAbacus and com.testMessageAbacus():
                result = True
            if result or not testAbacus:
                if CURRENT_OS == "win32":
                    ports["%s"%port.description] = port.device
                else:
                    ports["%s (%s)"%(port.description, port.device)] = port.device
            com.close()
        except CommunicationError:
            pass

    return ports
