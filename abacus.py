import pyAbacus as abacus

ports, n = abacus.findDevices()
print(ports)

port = list(ports.values())[0] #get first available device

abacus.open(port)			#open connection with device
abacus.getAllCounters(port)		#read all counter's data from device
#abacus.setSetting(port,"sampling", 5)	#set a single setting in device

#Examples reading settings
value = abacus.getSetting(port,"delay_A")
print("current delay_A=",value,"ns")
value = abacus.getSetting(port,"delay_B")
print("current delay_B=",value,"ns")
value = abacus.getSetting(port,"delay_C")
print("current delay_C=",value,"ns")
value = abacus.getSetting(port,"delay_D")
print("current delay_D=",value,"ns")
value = abacus.getSetting(port,"coincidence_window")
print("current coincidence_window=",value,"ns")
value = abacus.getSetting(port,"sampling")
print("current sampling=",value,"ms")

#Example of writing a new setting value
abacus.setSetting(port,"sampling", 1300)	    #set sampling=5ms
value = abacus.getSetting(port,"sampling")  #read sampling
print("current sampling=",value,"ms")

abacus.setSetting(port,"delay_C", 3)	    #set delay_C=3ns
value = abacus.getSetting(port,"delay_C")
print("current delay_C=",value,"ns")

abacus.close(port)			#close connection with device
