#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

CURRENT_OS = sys.platform #: Current operative system

ADDRESS_DIRECTORY_2CH = {'delay_A_ns': 0,
           'delay_A_us': 1,
           'delay_A_ms': 2,
           'delay_A_s': 3,
           'delay_B_ns': 4,
           'delay_B_us': 5,
           'delay_B_ms': 6,
           'delay_B_s': 7,
           'sleep_A_ns': 8,
           'sleep_A_us': 9,
           'sleep_A_ms': 10,
           'sleep_A_s': 11,
           'sleep_B_ns': 12,
           'sleep_B_us': 13,
           'sleep_B_ms': 14,
           'sleep_B_s': 15,
           'sampling_ns': 16,
           'sampling_us': 17,
           'sampling_ms': 18,
           'sampling_s': 19,
           'coincidence_window_ns': 20,
           'coincidence_window_us': 21,
           'coincidence_window_ms': 22,
           'coincidence_window_s': 23,
           'counts_A_LSB': 24,
           'counts_A_MSB': 25,
           'counts_B_LSB': 26,
           'counts_B_MSB': 27,
           'counts_AB_LSB': 28,
           'counts_AB_MSB': 29,
           'measure_number': 30,
           'time_to_next_sample': 31} #: Memory addresses

ADDRESS_DIRECTORY = ADDRESS_DIRECTORY_2CH

READ_VALUE = 0x0e #: Reading operation signal
WRITE_VALUE = 0x0f #: Writing operation signal
START_COMMUNICATION = 0x02 #: Begin message signal
END_COMMUNICATION = 0x04 #: End of message
MAXIMUM_WRITING_TRIES = 20 #: Number of tries done to write a value



COINCIDENCE_WINDOW_MINIMUM_VALUE = 5 #: Minimum coincidence window time value (ns).
COINCIDENCE_WINDOW_MAXIMUM_VALUE = 50000 #: Maximum coincidence window time value (ns).
COINCIDENCE_WINDOW_STEP_VALUE = 5 #: Increase ratio on the coincidence window time value (ns).
COINCIDENCE_WINDOW_DEFAULT_VALUE = 5 #: Default coincidence window time value (ns).

DELAY_MINIMUM_VALUE = 0 #: Minimum delay time value (ns).
DELAY_MAXIMUM_VALUE = 100 #: Maximum delay time value (ns).
DELAY_STEP_VALUE = 5 #: Increase ratio on the delay time value (ns).
DELAY_DEFAULT_VALUE = 100 #: Default delay time value (ns).

SLEEP_MINIMUM_VALUE = 0 #: Minimum sleep time value (ns).
SLEEP_MAXIMUM_VALUE = 100 #: Maximum sleep time value (ns).
SLEEP_STEP_VALUE = 5 #: Increase ratio on the sleep time value (ns).
SLEEP_DEFAULT_VALUE = 25 #: Default sleep time value (ns).

coeff = [1, 2, 5]
SAMPLING_VALUES = [int(c*10**i) for i in range(6) for c in coeff] + [int(1e6)] #: From (1, 2, 5) ms to 1000 s
SAMPLING_DEFAULT_VALUE = 100 #: Default sampling time value (ms)

SETTINGS = None #: Global settings variable

COUNTERS_VALUES = None #: Global counters values variable


<<<<<<< HEAD
BAUDRATE = 115200 #: Default baudrate for the serial port communication
TIMEOUT = 0.04 #: Maximum time without answer from the serial port
BOUNCE_TIMEOUT = 40 #: Number of times a specific transmition is tried
=======

BAUDRATE = 115200 #: Default baudrate for the serial port communication
# TIMEOUT = 0.04 #: Maximum time without answer from the serial port
TIMEOUT = 1
BOUNCE_TIMEOUT = 15 #: Number of times a specific transmition is tried
>>>>>>> 58c68efaf7e6ba04f3486c5055b200f6ff5244c2

# TEST_MESSAGE = "*IDN?".encode()
TEST_MESSAGE = [START_COMMUNICATION, 0x0D, 0, 0, 0, END_COMMUNICATION]
TEST_ANSWER = "Tausand AB"

ABACUS_SERIALS = {}

DEBUG = False
