import pyAbacus as abacus
import time

print("********************")
print("pyAbacus example")
print("********************")
print("1. Find devices and establish a connection\n")

ports, n = abacus.findDevices()

if n==0:
    print("\nNo valid devices were found. Closing.")
    
else:
    print("\nAvailable valid devices:")
    print(ports)

    port = list(ports.values())[0] #get first available device

    abacus.open(port)			#open connection with device

    print("\nConnected to the following device:")
    name = abacus.getIdn(port)
    numchannels = abacus.getChannelsFromName(name)
    resolution = abacus.getResolutionFromName(name)
    print("   device port =",port)
    print("   device name =",name)
    print("   number of channels =",numchannels)
    print("   resolution =",resolution,"ns")

    print("\n********************")
    print("2. Read device settings\n")

    #Example of reading all device settings
    settings = abacus.getAllSettings(port)
    print("Settings read from device, using getAllSettings method:")
    print("   settings =",settings)

    #Examples reading single settings
    value = abacus.getSetting(port,"delay_A")
    print("current delay_A=",value,"ns")
    value = abacus.getSetting(port,"delay_B")
    print("current delay_B=",value,"ns")
    value = abacus.getSetting(port,"sleep_A")
    print("current sleep_A=",value,"ns")
    value = abacus.getSetting(port,"sleep_B")
    print("current sleep_B=",value,"ns")
    value = abacus.getSetting(port,"coincidence_window")
    print("current coincidence_window=",value,"ns")
    value = abacus.getSetting(port,"sampling")
    print("current sampling=",value,"ms")

    print("\n********************")
    print("3. Write device settings\n")

    #Example of writing a new setting value
    abacus.setSetting(port,"sampling", 2000)    #set sampling=2000ms
    value = abacus.getSetting(port,"sampling")  #read sampling
    print("current sampling=",value,"ms")

    abacus.setSetting(port,"delay_B", 20)	    #set delay_B=20ns
    value = abacus.getSetting(port,"delay_B")
    print("current delay_B=",value,"ns")

    abacus.setSetting(port,"coincidence_window", 50)	    #set coincidence_window=50ns
    value = abacus.getSetting(port,"coincidence_window")
    print("current coincidence_window=",value,"ns")

    print("waiting 2 seconds to complete the measurement")
    time.sleep(2); #wait sampling time (2s) to get a valid measurement

    print("\n********************")
    print("4. Read measurements from device\n")

    #Example of reading measurements from counters
    counters, counters_id = abacus.getAllCounters(port)
    print("Measurements read from device, using getAllCounters method:")
    print("   counters_id =",counters_id)
    print("   counters =",counters)
    print("   counters type=",type(counters))
    print("   counts in A:                    counters.getValue('A')  =",counters.getValue('A'))
    print("   coincidences between A and B:   counters.getValue('AB') =",counters.getValue('AB'))

    print("   counts in A and B:              counters.getValues({'A','B'}) =",counters.getValues({'A','B'}))

    abacus.close(port)			#close connection with device
