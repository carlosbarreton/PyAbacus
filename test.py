import time
import pyAbacus as pa
from time import sleep

pa.constants.DEBUG = True

ports, n = pa.findDevices()#False)
print(ports)
port = ports[list(ports.keys())[0]]

pa.open(port)
counters, id = pa.getAllCounters(port)
print(counters)

# pa.setSetting(port, 'sampling', 10000)
# ans = pa.getAllSettings(port)
# print(ans)

# stream = pa.Stream(port, ['A'])
# stream.start()
# time.sleep(20)
# stream.stop()
#
# pa.close(port)

# from pywinusb import hid
#
# hid.find_all_hid_devices()
