#pupil labs libs
from pupil_labs.realtime_api.simple import Device

import pynput.keyboard as keyboard
from time import time_ns

ip = "10.5.50.53"
device = Device(address=ip, port="8080")
assert device is not None, "No device found"
print("Device found!")

class AcquisitionLogic:
    def __init__(self) -> None:
        #TODO: check on device if recording or not isntead of using a bool
        self.recording_bool = False
        self.event_id = 0

        #constants
        self.t_record =  60 #60 seconds of recording to test
        self.t_event = 2.0 #this is the event of gaze

        self.start_record_key = keyboard.Key.up
        self.stop_record_key = keyboard.Key.down
        self.event_key = keyboard.Key.right
        self.event_key = keyboard.Key.esc

    def on_press(self, key):
        if key is self.start_record_key:
            if self.recording_bool == True:
                raise Exception('Wait! Recording is currently activated.')
            #else start recording process
            self.start_record_process()
        
        if key is self.stop_record_key:
            self.stop_record_process()
        
        if key is self.event_key:
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
        if self.recording_bool == False:
            print('Wait! Recording is not activated.')
            return
        #else stop recording process
        device.recording_stop_and_save()
        print(f'Ended recording event.')
        self.recording_bool = False
        

    def trigger_event_process(self):
        #if recording is not activated go back to key listener
        if self.recording_bool == False:
            print('Need to record to be able to trigger events')
            return
        
        #set event
        
        #TODO: check if time_ns is actually sent to the device somehow 
        # if not need to save it locally and process it later on
        device.send_event(str(self.event_id), event_timestamp_unix_ns=time_ns())
        print(f'Triggered Event. ({self.t_event} s)')
        self.event_id += 1

    def exit_process(self):
        if self.recording_bool == True:
            print('Wait! Recording is currently activated.')
            return
        print('Exiting program...')
        device.close()
        exit()

acquisition_logic = AcquisitionLogic()

with keyboard.Listener(
        on_press=acquisition_logic.on_press) as listener:
    listener.join()