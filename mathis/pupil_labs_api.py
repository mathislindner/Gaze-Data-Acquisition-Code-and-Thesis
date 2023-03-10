from pupil_labs.realtime_api.simple import discover_one_device
from time import time 
#https://pupil-labs-realtime-api.readthedocs.io/en/stable/api/index.html

device = discover_one_device()
assert device is not None, "No device found"

#freestorage = device.memory_num_free_bytes
#assert (freestorage > 5e9), "Not enough free storage on device"


#https://pupil-labs-realtime-api.readthedocs.io/en/stable/api/async.html#module-pupil_labs.realtime_api.time_echo
computer_time = time.time()
estimate = device.estimate_time_offset()

#offset_ms = ((t1 + t2) / 2) - tHost
mean_offset = estimate.time_offset_ms.mean

device_time = computer_time + mean_offset


#keep track of events
#https://docs.pupil-labs.com/invisible/real-time-api/track-your-experiment-progress-using-events/#how-to-use-events-to-keep-track


device.send_event(name + "_start")
present_stimulus(img)    
device.send_event(name + "_end")