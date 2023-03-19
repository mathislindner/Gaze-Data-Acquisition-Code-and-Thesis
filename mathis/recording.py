#pupil labs libs
from pupil_labs.realtime_api.simple import Device

import pynput.keyboard as keyboard
from time import time_ns, sleep
from constants import recordings_folder
import os


ip = "10.5.50.53"
device = Device(address=ip, port="8080")
assert device is not None, "No device found"
print("Device found!")

class AcquisitionLogic:
    def __init__(self) -> None:
        #TODO: check on device if recording or not isntead of using a bool
        self.recording_bool = False
        self.event_id = 0
        self.recording_id = None

        #constants
        self.t_record =  60 #60 seconds of recording to test
        self.t_event = 2.0 #this is the event of gaze

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

        self.recording_id = device.recording_start()
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

    #https://pupil-labs-realtime-api.readthedocs.io/en/latest/examples/simple.html#send-event
    #TODO: test this out and see if it works
    def save_time_offset(self):
        # send event with current timestamp
        print(
            device.send_event(
                "test event; timestamped by the client, relying on NTP for sync",
                event_timestamp_unix_ns=time_ns(),
            )
        )

        # Estimate clock offset between Companion device and client script
        # (only needs to be done once)
        estimate = device.estimate_time_offset()
        clock_offset_ns = round(estimate.time_offset_ms.mean * 1_000_000)
        print(f"Clock offset: {clock_offset_ns:_d} ns")

        # send event with current timestamp, but correct it manual for possible clock offset
        current_time_ns_in_client_clock = time_ns()
        current_time_ns_in_companion_clock = current_time_ns_in_client_clock - clock_offset_ns
        print(
            device.send_event(
                "test event; timestamped by the client, manual clock offset correction",
                event_timestamp_unix_ns=current_time_ns_in_companion_clock,
            )
        )
        #create folder in recording_id folder
        os.mkdir(recordings_folder + self.recording_id)
        #save offset to file
        offset_string = "{offset: " + str(clock_offset_ns) + "}" # kinda ugly but works
        with open (recordings_folder + self.recording_id + '/offset.txt', 'w') as f:
            f.write(offset_string)


acquisition_logic = AcquisitionLogic()

with keyboard.Listener(
        on_press=acquisition_logic.on_press) as listener:
    listener.join()