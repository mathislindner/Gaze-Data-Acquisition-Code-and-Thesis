from pupil_labs.realtime_api.simple import Device
import pyrealsense2 as rs
import os
from dependencies.constants import *
import json
from time import time_ns


class depthAndRgbCameras():
    def __init__(self):
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.profile = None
        self.i = 0
        print("depth and rgb cameras initialized")

    def start_recording(self, recording_id):
        recording_path = os.path.join(recordings_folder, recording_id, "realsensed435.bag")
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.config.enable_record_to_file(recording_path)
        self.profile = self.pipeline.start(self.config)

    def stop_recording(self):
        self.pipeline.stop()
        self.config.disable_all_streams()

    def cancel_recording(self):
        self.pipeline.stop()
        self.config.disable_all_streams()
        #the recording is deleted automatically in the acquisition logic


    #TODO
    def change_options_for_laser(self, exposure):
        '''
        exposure: int
        changed the exposure of the color camera while recording
        'Defines general configuration controls. These can generally be mapped to camera UVC controls, and can be set / queried at any time unless stated otherwise.'
        '''
        color_sensor = self.profile.get_device().query_sensors()[1]
        #turn off auto exposure
        color_sensor.set_option(rs.option.enable_auto_exposure, False)
        ##set exposure
        color_sensor.set_option(rs.option.exposure, value = 400)
        color_sensor.set_option(rs.option.sharpness, value = 50)
        color_sensor.set_option(rs.option.brightness, value = 5)
        
class PupilCamera():
    def __init__(self, ip, port):
        try:
            print('connecting to device')
            self.device = Device(address = ip, port = port)
        except:
            raise Exception("No device found")
            
        print("Device found!")
        self.recording_id = None

    def start_recording(self):
        self.recording_id = self.device.recording_start()
        self.save_offset_and_start_time(time_ns())
        return self.recording_id
    
    def stop_recording(self):
        self.device.recording_stop_and_save()

    def cancel_recording(self):
        self.device.recording_cancel()
        return self.recording_id

    #https://pupil-labs-realtime-api.readthedocs.io/en/latest/examples/simple.html#send-event
    def save_offset_and_start_time(self, pc_recording_start_time):
        estimate = self.device.estimate_time_offset()

        clock_offset_ns = round(estimate.time_offset_ms.mean * 1_000_000)
        print(f"Clock offset: {clock_offset_ns:_d} ns")

        # send event with current timestamp, but correct it manual for possible clock offset
        current_time_ns_in_client_clock = time_ns()
        current_time_ns_in_companion_clock = current_time_ns_in_client_clock - clock_offset_ns
        self.device.send_event("manual_clock_offset_correction",
                event_timestamp_unix_ns=current_time_ns_in_companion_clock,
                )
        #create folder in recording_id folder
        recording_folder = os.path.join(recordings_folder, self.recording_id)
        os.mkdir(recording_folder)
        dictionary = { "system_start_time": pc_recording_start_time, "offset": clock_offset_ns}
        json_object = json.dumps(dictionary, indent = 4)
        with open (os.path.join(recording_folder,'local_synchronisation.json'), 'a') as f:
            f.write(json_object)

#this class is just to test the d435 alone
class PupilCameraTest():
    def __init__(self):
        pass

    def start_recording(self):
        return "test"
    
    def stop_recording(self):
        pass

    def cancel_recording(self):
        pass
