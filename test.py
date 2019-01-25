import time
import pyAbacus as pa

pa.constants.DEBUG = False

ports, n = pa.findDevices()
port = list(ports.keys())[0]

pa.open(port)

val = 1 << 24
print(val, hex(val))

# pa.writeSerial(abacus_port, pa.READ_VALUE, 0, 1 << 24)
# data = pa.readSerial(abacus_port)

# pa.setSetting(port, 'delay_A', 55)
#
# ans = pa.getAllSettings(port)
# print(ans)
#
# stream = pa.Stream(port, ['A'])
# stream.start()
# time.sleep(20)
# stream.stop()
#
# time.sleep(1)

pa.close(port)
