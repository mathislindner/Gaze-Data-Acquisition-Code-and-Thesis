#pupil labs libs
from pupil_labs.realtime_api.simple import Device
import  pupil_labs
import pynput.keyboard as keyboard
from time import time_ns, sleep
from constants import recordings_folder
import os
import json

#connect to API for pupil labs device
ip = "10.5.56.134"
device = Device(address=ip, port="8080")
assert device is not None, "No device found"
print("Device found!")

#TODO: initialize the depth camera

class AcquisitionLogic:
    def __init__(self) -> None:
        #TODO: check on device if recording or not isntead of using a bool (device._get_status()) (although it would slow down the process)
        
        self.recording_bool = False
        self.event_id = 0
        self.recording_id = None

        self.start_record_key = keyboard.Key.up
        self.stop_record_key = keyboard.Key.down
        self.event_key = keyboard.Key.right
        self.cancel_recording_key = None
        self.exit_key = keyboard.Key.esc

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

        if key is self.cancel_recording_key:
            self.cancel_recording_process()
        
        if key is self.exit_key:
            self.exit_process()

    def start_record_process(self):
        #assertions
        freestorage = device.memory_num_free_bytes
        battery = device.battery_level_percent
        assert (freestorage > 5e9), "Not enough free storage on device" #at least 5GB space
        assert (battery > 0.1), "Battery is too low" #at least 10% battery
        #synchronization to the ntp server
        pc_recording_start_time = time_ns()
        self.recording_id = device.recording_start()
        self.save_offset_and_start_time(pc_recording_start_time)
        print(f'Started recording')
        self.recording_bool = True

    def stop_record_process(self):
        if self.recording_bool == False:
            print('Wait! Recording is not activated.')
            return
        #else stop recording process
        device.recording_stop_and_save()
        print(f'Ended recording.')
        self.recording_bool = False
        self.event_id = 0
        

    def trigger_event_process(self):
        event_timestamp = time_ns()
        #if recording is not activated go back to key listener
        if self.recording_bool == False:
            print('Need to record to be able to trigger events')
            return
        #else trigger event
        device.send_event(str(self.event_id), event_timestamp_unix_ns=event_timestamp)
        print(f'Triggered Event nr ({self.event_id})')
        #save event to local_syncronisation.json
        dictionary = {"Event: " + str(self.event_id) : event_timestamp}
        with open(recordings_folder + self.recording_id + '/local_synchronisation.json', 'r') as f:
            data = json.load(f)
        data.update(dictionary)    
        with open(recordings_folder + self.recording_id + '/local_synchronisation.json', 'w') as f:
            
            json_object = json.dumps(data, indent = 4)
            f.write(json_object)

        self.event_id += 1

    def cancel_recording_process(self):
        if self.recording_bool == False:
            print('Cannot cancel recording if not recording.')
            return
        #else cancel recording process
        device.recording_cancel()
        #delete recording folder and all its content
        os.rmdir(recordings_folder + self.recording_id)
        print('Cancelled recording {}'.format(self.recording_id))
        self.recording_bool = False
        self.event_id = 0

    def exit_process(self):
        if self.recording_bool == True:
            print('Wait! Recording is currently activated.')
            return
        print('Exiting program...')
        device.close()
        exit()

    #FIXME: implement this and update every 10 seconds
    def sync_device_to_system_time(self):
        #estimate the offset between the pc and the device
        current_time = time_ns()
        current_time = pupil_labs.realtime_api.time_echo.time_ms()

        estimate = device.estimate_time_offset()
        time_offset_ms_mean = estimate.time_offset_ms.mean
        roundtrip_duration_ms = estimate.roundtrip_duration_ms.mean
        time_echo = pupil_labs.realtime_api.time_echo.TimeEcho(roundtrip_duration_ms, time_offset_ms_mean)
        companion_app_time = current_time - time_offset_ms_mean

    #FIXME:
    #https://pupil-labs-realtime-api.readthedocs.io/en/latest/examples/simple.html#send-event
    def save_offset_and_start_time(self, pc_recording_start_time):
        estimate = device.estimate_time_offset()


        clock_offset_ns = round(estimate.time_offset_ms.mean * 1_000_000)
        print(f"Clock offset: {clock_offset_ns:_d} ns")

        # send event with current timestamp, but correct it manual for possible clock offset
        current_time_ns_in_client_clock = time_ns()
        current_time_ns_in_companion_clock = current_time_ns_in_client_clock - clock_offset_ns
        device.send_event("manual_clock_offset_correction",
                event_timestamp_unix_ns=current_time_ns_in_companion_clock,
                )
        #create folder in recording_id folder
        os.mkdir(recordings_folder + self.recording_id)
        dictionary = { "system_start_time": pc_recording_start_time, "offset": clock_offset_ns}
        json_object = json.dumps(dictionary, indent = 4)
        with open (recordings_folder + self.recording_id + '/local_synchronisation.json', 'a') as f:
            f.write(json_object)

acquisition_logic = AcquisitionLogic()

with keyboard.Listener(
        on_press=acquisition_logic.on_press) as listener:
    listener.join()