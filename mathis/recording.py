#pupil labs libs
from pupil_labs.realtime_api.simple import Device

import pynput.keyboard as keyboard
from time import time_ns

ip = "10.5.50.141"
device = Device(address=ip, port="8080")
assert device is not None, "No device found"
print("Device found!")

class AcquisitionLogic:
    def __init__(self) -> None:
        #TODO: check on device if recording or not
        self.recording_bool = False
        self.event_id = 0

        #constants
        self.t_record =  60 #60 seconds of recording to test
        self.t_event = 2.0 #this is the event of gaze

        self.start_record_key = keyboard.Key.up
        self.stop_record_key = keyboard.Key.down
        self.event_key = keyboard.Key.right

    def on_press(self, key):
        if key is self.start_record_key:
            if self.recording_bool == True:
                raise Exception('Wait! Recording is currently activated.')
            #else start recording process
            self.start_record_process()
        
        if key is self.stop_record_key:
            if self.recording_bool == False:
                raise Exception('Wait! Recording is not activated.')
            #else stop recording process
            self.stop_record_process()
        
        if key is self.event_key:
            if self.recording_bool == False:
                raise Exception('Need to record to be able to trigger events')
            #else trigger event
            self.trigger_event_process()

    def start_record_process(self):
        #assertions
        freestorage = device.memory_num_free_bytes
        battery = device.battery_level_percent
        assert (freestorage > 5e9), "Not enough free storage on device" #at least 5GB space
        assert (battery > 0.1), "Battery is too low" #at least 10% battery

        recording_id = device.recording_start()
        print(f'Started recording event. ({self.t_record} s)')
        self.recording_bool = True

    def stop_record_process(self):
        #stop recording
        device.recording_stop_and_save()
        print(f'Ended recording event.')
        self.recording_bool = False
        

    def trigger_event_process(self):
        #assertions
        assert self.recording_bool == True, "Need to record to be able to trigger events"
        #set event
        device.send_event(str(self.event_id), event_timestamp_unix_ns=time_ns())
        print(f'Triggered Event. ({self.t_event} s)')
        self.event_id += 1


acquisition_logic = AcquisitionLogic()

with keyboard.Listener(
        on_press=acquisition_logic.on_press) as listener:
    listener.join()