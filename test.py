import time
import pyAbacus as pa
from time import sleep

<<<<<<< HEAD
pa.constants.DEBUG = False

ports, n = pa.findDevices(False)

port = ports[list(ports.keys())[0]]

pa.open(port)
# counters, id = pa.getAllCounters(port)
# print(counters)

# pa.setSetting(port, 'sampling', 10000)
# ans = pa.getAllSettings(port)
# print(ans)

stream = pa.Stream(port, ['A'])
stream.start()
time.sleep(20)
stream.stop()

pa.close(port)
=======
# pa.findDevices()

abacus_port = "/dev/ttyACM0"

pa.open(abacus_port)

# idn = pa.getIdn(abacus_port)
# print(idn)

# cid = pa.getCountersID(abacus_port)
# print(cid)

while True:
    try:
        val = pa.getAllSettings(abacus_port)
        print(val)
        sleep(1)
    except KeyboardInterrupt:
        break

pa.setSetting(abacus_port, "delay_A", 520)

pa.close(abacus_port)
>>>>>>> 58c68efaf7e6ba04f3486c5055b200f6ff5244c2
