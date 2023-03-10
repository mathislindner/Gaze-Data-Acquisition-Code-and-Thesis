
from pupil_labs.realtime_api.simple import discover_one_device, discover_devices


# device = discover_one_device()
# assert device is not None, "No device found"

from pupil_labs.realtime_api.simple import Device
ip = "10.6.53.12"
device = Device(address=ip, port="8082")
print(device)