#uses the classes from recording_devices.py
import pyrealsense2 as rs
import os
from constants import *
import pynput.keyboard as keyboard
from recording_devices import *
from time import time_ns
import json

class acquisitionLogic():
    def __init__(self, ip, port):

        self.recording_bool = False
        self.event_id = None
        self.recording_id = "temp"

        #TODO:change back to PupilCamera
        #self.pupil_camera = PupilCamera(ip, port)
        self.pupil_camera = PupilCameraTest()
        self.depth_and_rgb_cameras = depthAndRgbCameras()

        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.keyboard_listener.start()
        self.keyboard_listener.join()

    def on_press(self, key):
        if key == keyboard.Key.right:
            print("recording")
            self.start_recording_all_devices()

        if key == keyboard.Key.left:
            print("stop recording")
            self.stop_recording_all_devices()

        if key == keyboard.Key.space:
            self.trigger_event()

        if key == keyboard.Key.esc:
            if self.recording_bool:
                print("warning: recording is still on")
            exit()


    def start_recording_all_devices(self):
        self.recording_bool = True
        self.event_id = 0
        self.recording_id = self.pupil_camera.start_recording()
        self.depth_and_rgb_cameras.start_recording(self.recording_id)

    def stop_recording_all_devices(self):
        self.recording_bool = False
        self.pupil_camera.stop_recording()
        self.depth_and_rgb_cameras.stop_recording()

    def cancel_recording(self):
        self.recording_bool = False
        self.pupil_camera.cancel_recording()
        recording_id = self.depth_and_rgb_cameras.cancel_recording()
        #delete_recording_folder(self.recording_id)
        os.rmdir(os.path.join(recordings_folder, recording_id))

    def trigger_event(self):
        event_timestamp = time_ns()
        recording_path = os.path.join(recordings_folder, self.recording_id)
        local_synchronisation_path = os.path.join(recording_path, "local_synchronisation.json")
        #if recording is not activated go back to key listener
        if self.recording_bool == False:
            print('Need to record to be able to trigger events')
            return
        #else trigger event
        #device.send_event(str(self.event_id), event_timestamp_unix_ns=event_timestamp)
        print(f'Triggered Event nr ({self.event_id})')
        #save event to local_syncronisation.json
        dictionary = {"Event: " + str(self.event_id) : event_timestamp}
        with open(local_synchronisation_path, 'r') as f:
            data = json.load(f)
        data.update(dictionary)    
        with open(local_synchronisation_path, 'w') as f:
            
            json_object = json.dumps(data, indent = 4)
            f.write(json_object)

        self.event_id += 1


if __name__ == "__main__":
    acquisition_logic = acquisitionLogic(ip = "0.0.0.0",port = "8080")
    #while True:
    #    pass