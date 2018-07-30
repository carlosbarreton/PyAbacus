import PyAbacus as abacus

ports, n = abacus.findDevices()
print(ports)

port = list(ports.values())[0]

abacus.open(port)
abacus.getAllCounters(port)

abacus.setSetting("sampling", 5)
