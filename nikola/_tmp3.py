from pupil_labs.realtime_api.simple import discover_one_device, Device

ip = '10.6.50.110'

device = discover_one_device()
device = Device(address=ip, port="8080")

a = 1