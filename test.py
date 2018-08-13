import pyAbacus as pa
from time import sleep

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
