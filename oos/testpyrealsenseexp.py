#record with changed exposure, save recording and replay it after
#add path
import sys
sys.path.append("/scratch_net/snapo/mlindner/docs/gaze_data_acquisition")
import pyrealsense2 as rs
import numpy as np
import cv2
import os
from dependencies.constants import *
from dependencies.recording_devices import depthAndRgbCameras
import pynput.keyboard as keyboard
import shutil
#color_sensor = profile.get_device().query_sensors()[1]
#color_sensor.set_option(rs.option.enable_auto_exposure, False)
#color_sensor.set_option(rs.option.exposure, value = 350)
#color_sensor.set_option(rs.option.sharpness, value = 50)
#color_sensor.set_option(rs.option.brightness, value = 5)

class rec_test():
    def __init__(self):
        self.depth_and_rgb_cameras = depthAndRgbCameras()
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        self.keyboard_listener.start()
        self.keyboard_listener.join()


    def on_press(self, key):
        if key == keyboard.Key.right:
            self.rec()
            print("recording")

        if key == keyboard.Key.left:
            #self.keyboard_listener.stop()
            self.stop_recording()
            print("stop recording")
            
    def rec(self):
        #create recording dir
        if not os.path.exists(os.path.join(recordings_folder, "test")):
            os.mkdir(os.path.join(recordings_folder, "test"))
        else:
            #delete old recording
            bag_file = os.path.join(recordings_folder, "test", "realsensed435.bag")
            if os.path.exists(bag_file):
                os.remove(bag_file)
        self.depth_and_rgb_cameras.start_recording("test")

    def stop_recording(self):
        self.depth_and_rgb_cameras.stop_recording()

def playback(recording_id):
    #replay
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    path = os.path.join(recordings_folder, recording_id, "realsensed435.bag")
    config.enable_device_from_file(os.path.join(path), repeat_playback = False)
    profile = pipeline.start(config)


    while True:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue
        color_image = np.asanyarray(color_frame.get_data())
        cv2.imshow("color", color_image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            pipeline.stop()
            cv2.destroyAllWindows()

from dependencies.frames_extractor import extract_depth_camera_frames
def playback_with_settings(recording_id):
    extract_depth_camera_frames(recording_id)


#playback('test')
#playback_with_settings()



if __name__ == "__main__":
    playback('529a21a7-72c5-4853-b9ce-39be4ac31e62')
    #rec_obj = rec_test()
