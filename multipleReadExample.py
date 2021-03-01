import pyAbacus as abacus
import time

samples_to_read = 18000 #18000: 5h*3600s. change this parameter to set how many samples to read
my_sampling_time_ms = 1000 #change this parameter to set your sampling time. 1000=1s.

print("******************************")
print("pyAbacus multiple read example")
print("******************************")
print("1. Find devices and establish a connection\n")

ports, n = abacus.findDevices() #required to scan devices before opening a connection

if n==0:
    print("\nNo valid devices were found. Closing.")
    
else:
    print("\nAvailable valid devices:")
    print(ports)

    mydevice = list(ports.keys())[0] #get first available device
    abacus.open(mydevice)	    #open connection with device

    print("\nConnected to the following device:")
    idnstring = abacus.getIdn(mydevice)
    numchannels = abacus.getChannelsFromName(mydevice)
    resolution = abacus.getResolutionFromName(mydevice)
    physicalport = abacus.getPhysicalPort(mydevice)
    print("   device name =",mydevice)
    print("   device physical port =",physicalport)
    print("   device identifier string =",idnstring)
    print("   number of channels =",numchannels)
    print("   resolution =",resolution,"ns")

    #########
    print("\n2. Write and read new settings\n")
    #write settings:
    abacus.setSetting(mydevice,"sampling", my_sampling_time_ms) #set sampling, in milliseconds (default: 1000ms)
    abacus.setSetting(mydevice,"coincidence_window", 50)    #set coincidence_window=50ns
    abacus.setSetting(mydevice,"delay_A", 0)	            #set delay_A=0ns
    abacus.setSetting(mydevice,"delay_B", 0)	            #set delay_B=0ns
    abacus.setSetting(mydevice,"sleep_A", 0)	            #set sleep_A=0ns
    abacus.setSetting(mydevice,"sleep_B", 0)	            #set sleep_B=0ns
    #TO DO: incluir multiples coinc

    #read settings:
    current_settings = abacus.getAllSettings(mydevice)
    print(current_settings)


    
    print("\nFunction test: waitAndGetValues")

    date_time_string = time.strftime("%Y-%m-%d_%H%M%S", time.localtime())
    column_headers = ["PC time","countersID","A","B","AB"];
    
    myfile = open("data_multipleReadExample_"+date_time_string+".txt", "a")
    myfile.write('multipleReadExample\n')
    myfile.write('-------------------\n')
    myfile.write('Begin time: '+date_time_string+'\n')
    myfile.write('Device: '+mydevice+'\n')
    myfile.write('Settings: '+str(current_settings)+'\n')
    myfile.write("\n\n")
    myfile.write(str(column_headers))
    myfile.write("\n")

    full_data=[]
    for sample in range(samples_to_read):
        print(sample,end=',')
        try:
            my_data, my_id = abacus.waitAndGetValues(mydevice,{'A','B','AB'},print_on=True) #for debug purposes, turn print_on=True; by default is False.
            my_data.insert(0,my_id) #prepend my_id to my_data
            my_data.insert(0,time.time()) #prepend current PC time to my_data
            print(my_data)
            full_data.append(my_data)
            myfile.write(str(my_data))
            myfile.write("\n")
        except abacus.CheckSumError:
            print("Data integrity error in waitAndGetValues: missing or wrong bits.")
        except (abacus.serial.serialutil.SerialException,KeyError):
            print("Communication error in waitAndGetValues: device might be disconnected or turned off.")
        except:
            print("Unexpected error. Device connection closed. File access closed.")
            abacus.close(mydevice)  #close connection with device
            myfile.close()          #close file
            raise
        
        
    abacus.close(mydevice)  #close connection with device
    myfile.close()          #close file
    print("\nFull set of data is:")
    print(full_data)
