
from pupil_labs.realtime_api.simple import discover_one_device, discover_devices


# device = discover_one_device()
# assert device is not None, "No device found"

from pupil_labs.realtime_api.simple import Device
ip = "10.5.55.58"
device = Device(address=ip, port="8080")
estimate = device.estimate_time_offset()
print(estimate)
print(device)