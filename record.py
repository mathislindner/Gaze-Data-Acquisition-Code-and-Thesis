#uses the classes from recording_devices.py
import os
import shutil
from dependencies.constants import *
import pynput.keyboard as keyboard
from dependencies.recording_devices import *
from time import time_ns
import json
import yaml
from yaml.loader import SafeLoader

class acquisitionLogic():
    def __init__(self, ip, port):
        self.recording_bool = False
        self.event_id = None
        self.recording_id = "temp"
        self.pupil_camera = PupilCamera(ip, port)
         #self.pupil_camera = PupilCameraTest() #to test without having the pupil camera running
        self.depth_and_rgb_cameras = depthAndRgbCameras()

        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.keyboard_listener.start()
        
        print("to start recording press right arrow")
        print("to stop recording press left arrow")
        print("to trigger event press space")
        print("to cancel recording press delete")
        print("to exit press esc")
        self.keyboard_listener.join()
        
    def on_press(self, key):
        if key == keyboard.Key.right:
            self.start_recording_all_devices()
            print("recording")

        if key == keyboard.Key.left:
            self.stop_recording_all_devices()
            print("stop recording")

        if key == keyboard.Key.space:
            self.trigger_event()

        if key == keyboard.Key.esc:
            if self.recording_bool:
                print("warning: recording is still on")
            else:
                # stop the listener
                self.keyboard_listener.stop()
                print("exiting")
                os._exit(1)

        if key == keyboard.Key.delete:
            self.cancel_recording()
            print("recording cancelled")

        elif key != keyboard.Key.right and key != keyboard.Key.left and key != keyboard.Key.space and key != keyboard.Key.esc:
            print('key doesn t exist')
            
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
        self.depth_and_rgb_cameras.cancel_recording()

        #delete_recording_folder(self.recording_id)
        shutil.rmtree(os.path.join(recordings_folder, self.recording_id))

    def trigger_event(self):
        event_timestamp = time_ns()
        recording_path = os.path.join(recordings_folder, self.recording_id)
        local_synchronisation_path = os.path.join(recording_path, "local_synchronisation.json")
        #if recording is not activated go back to key listener
        if self.recording_bool == False:
            print('Need to record to be able to trigger events')
            return
        #else trigger event on pupil camera
        self.pupil_camera.device.send_event(str(self.event_id), event_timestamp_unix_ns=event_timestamp)
        print(f'Triggered Event nr ({self.event_id})')
        #and save event to local_syncronisation.json
        dictionary = {"Event: " + str(self.event_id) : event_timestamp}
        with open(local_synchronisation_path, 'r') as f:
            data = json.load(f)
        data.update(dictionary)    
        with open(local_synchronisation_path, 'w') as f:
            json_object = json.dumps(data, indent = 4)
            f.write(json_object)

        self.event_id += 1


if __name__ == "__main__":
    with open('configuration.yaml') as f:
        config = yaml.load(f, Loader=SafeLoader)
    #TODO: make sure these are strings
    ip_address = str(config['IP_ADDRESS'])
    port = str(config['PORT'])
    acquisition_logic = acquisitionLogic(ip_address, port)
