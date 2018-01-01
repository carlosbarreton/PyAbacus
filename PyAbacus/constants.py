#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

CURRENT_OS = sys.platform

# if CURRENT_OS == "win32":
#     from .specialfolders import *

ADDRESS_2CH = {'delayA_ns': 0,
           'delayA_us': 1,
           'delayA_ms': 2,
           'delayA_s': 3,
           'delayB_ns': 4,
           'delayB_us': 5,
           'delayB_ms': 6,
           'delayB_s': 7,
           'sleepTimeA_ns': 8,
           'sleepTimeA_us': 9,
           'sleepTimeA_ms': 10,
           'sleepTimeA_s': 11,
           'sleepTimeB_ns': 12,
           'sleepTimeB_us': 13,
           'sleepTimeB_ms': 14,
           'sleepTimeB_s': 15,
           'samplingTime_ns': 16,
           'samplingTime_us': 17,
           'samplingTime_ms': 18,
           'samplingTime_s': 19,
           'coincidenceWindow_ns': 20,
           'coincidenceWindow_us': 21,
           'coincidenceWindow_ms': 22,
           'coincidenceWindow_s': 23,
           'countsA_LSB': 24,
           'countsA_MSB': 25,
           'countsB_LSB': 26,
           'countsB_MSB': 27,
           'coincidencesAB_LSB': 28,
           'coincidencesAB_MSB': 29} #: Memory addresses

ADDRESS = ADDRESS_2CH

DELIMITER = ", "

READ_VALUE = 0x0e #: Reading operation signal
WRITE_VALUE = 0x0f #: Writing operation signal
START_COMMUNICATION = 0x02 #: Begin message signal
END_COMMUNICATION = 0x04 #: End of message
MAXIMUM_WRITING_TRIES = 20 #: Number of tries done to write a value

"""
main
"""
coeff = [2, 5, 10]
SAMP_VALUES = []
for i in range(0, 6):
	for c in coeff:
		j = i%3
		value = c*10**j
		unit = 's'
		if i == 2 and c == 10:
			value *= 1/1000
		elif i < 3:
			unit = 'ms'

		SAMP_VALUES.append("%d %s"%(value, unit))

SAMP_VALUES.insert(0, "1 ms")
SAMP_VALUES = SAMP_VALUES[::-1] # inverted

DEFAULT_SAMP = '100 ms'
SAMP_CUTOFF = 100

MIN_COIN = 5
MAX_COIN = 50000
DEFAULT_COIN = 5
STEP_COIN = 5

MIN_DELAY = 0 #: Minimum delay time value.
MAX_DELAY = 100 #: Maximum delay time value.
STEP_DELAY = 5 #: Increase ratio on the delay time value.
DEFAULT_DELAY = 100 #: Default delay time value (ns).
MIN_SLEEP = 0 #: Minimum sleep time value.
MAX_SLEEP = 100 #: Maximum sleep time value.
STEP_SLEEP = 5 #: Increase ratio on the sleep time value.
DEFAULT_SLEEP = 25 #: Default sleep time value (ns).
