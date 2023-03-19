#pupil labs libs
from pupil_labs.realtime_api.simple import Device

import pynput.keyboard as keyboard
from time import time_ns, sleep
from constants import recordings_folder
import os
import json

ip = "10.5.50.53"
device = Device(address=ip, port="8080")
assert device is not None, "No device found"
print("Device found!")

class AcquisitionLogic:
    def __init__(self) -> None:
        #TODO: check on device if recording or not isntead of using a bool (device._get_status())
        
        self.recording_bool = False
        self.event_id = 0

        self.start_record_key = keyboard.Key.up
        self.stop_record_key = keyboard.Key.down
        self.event_key = keyboard.Key.right
        self.event_key = keyboard.Key.esc

        #sleep to statbilize the connection and save the offset
        print("Initializing...")
        sleep(2)
        self.save_time_offset()
        print("press up to start recording")

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

        recording_start_time = time_ns()
        recording_id = device.recording_start()
        self.save_offset_and_start_time(recording_id, recording_start_time)
        print(f'Started recording event.')
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
        #else trigger event
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

    #https://pupil-labs-realtime-api.readthedocs.io/en/latest/examples/simple.html#send-event
    def save_offset_and_start_time(self, recording_id, recording_start_time):
        estimate = device.estimate_time_offset()
        clock_offset_ns = round(estimate.time_offset_ms.mean * 1_000_000)
        print(f"Clock offset: {clock_offset_ns:_d} ns")

        # send event with current timestamp, but correct it manual for possible clock offset
        current_time_ns_in_client_clock = time_ns()
        current_time_ns_in_companion_clock = current_time_ns_in_client_clock - clock_offset_ns
        print(
            device.send_event(
                "manual_clock_offset_correction",
                event_timestamp_unix_ns=current_time_ns_in_companion_clock,
            )
        )
        #create folder in recording_id folder
        os.mkdir(recordings_folder + recording_id)
        dictionary = { "system_start_time": recording_start_time, "offset": clock_offset_ns}
        json_object = json.dumps(dictionary, indent = 4)
        with open (recordings_folder + recording_id + '/start_time_and_offset.json', 'w') as f:
            f.write(json_object)

acquisition_logic = AcquisitionLogic()

with keyboard.Listener(
        on_press=acquisition_logic.on_press) as listener:
    listener.join()