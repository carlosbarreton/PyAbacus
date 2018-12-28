import time
import pyAbacus as pa

# pa.constants.DEBUG = True

ports, n = pa.findDevices(False)
port = ports[list(ports.keys())[0]]

pa.open(port)
# counters, id = pa.getAllCounters(port)
# print(counters)

pa.setSetting(port, 'delay_A', 0)
# ans = pa.getAllSettings(port)
# print(ans)

stream = pa.Stream(port, ['A'])
stream.start()
time.sleep(20)
stream.stop()

pa.close(port)
