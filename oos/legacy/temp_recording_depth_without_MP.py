import pynput.keyboard as keyboard
import multiprocessing as mp
import pyrealsense2 as rs
from time import sleep
import numpy as np
import cv2
from constants import *
import os

class RealSenseStream():
    def __init__(self):
        # Configure depth and color streams
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.stop_event = mp.Event()

        # Get device product line for setting a supporting resolution
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        pipeline_profile = self.config.resolve(pipeline_wrapper)
        device = pipeline_profile.get_device()
        device_product_line = str(device.get_info(rs.camera_info.product_line))
        self.queue = rs.frame_queue(50, keep_frames=True)
        
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    def start_recording(self):
         # Start streaming
        self.pipeline.start(self.config)
        
    def load_recent_frame(self):
        # Wait for a coherent pair of frames: depth and color
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        frame_number = frames.get_frame_number()
        #print(color_frame)
        # timestamp in milliseconds
        t = frames.get_timestamp()
        #t_domain = frames.get_frame_timestamp_domain()
        if not depth_frame or not color_frame:
            return None
        
        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        return depth_image, color_image, t, frame_number

    def stop_recording(self):
        self.pipeline.stop()
        self.config.disable_all_streams()

class Storage():
    def __init__(self, cam_stream):
        self.cam_stream = cam_stream
        self.stop_event = False
        self.timestamps = np.zeros(50000, dtype=np.uint64)

        self.recording_id = "test"
    def run(self):
        while not self.stop_event == True:
            frames = self.cam_stream.load_recent_frame() #FIXME: this would ve delaying the events
            if frames is None:
                continue
            else:
                depth_image, color_image, t, frame_number = frames


                #save the images
                depth_folder = os.path.join(recordings_folder, self.recording_id, "depth")
                color_folder = os.path.join(recordings_folder, self.recording_id, "color")

                cv2.imwrite(os.path.join(depth_folder, str(frame_number) + ".png"), depth_image)
                cv2.imwrite(os.path.join(color_folder, str(frame_number) + ".png"), color_image)
                #convert timestamp from milliseconds to nanoseconds
                t = t * 1000000
                self.timestamps[frame_number] = t
    #this is just to pause the storage so we can record the events
    def pause(self):
        self.stop_event = True

        
    def stop(self):
        self.stop_event = True
        print("Saving timestamps")
        np.save(os.path.join(recordings_folder, self.recording_id, "depth_cam_timestamps.npy"), self.timestamps)


class acq():
    def __init__(self):
        self.cam_stream = RealSenseStream()
        self.storage = Storage(self.cam_stream)

    def run(self):
        self.cam_stream.start_recording()
        self.storage.run()

    def stop_recording(self):
        self.storage.stop()
        self.cam_stream.stop_recording()

    #workaround to trigger events in non multiprocessed code
    def trigger_event(self):
        self.storage.pause()
        print("Event triggered")
        self.storage.run()

    def on_press(self, key):
        if key.char == 'w':
            self.run()
            print("Recording started")
        if key.char == 'q':
            self.stop_recording()
            print("Recording stopped")
        if key.char == 'e':
            self.trigger_event()


        
        
if __name__ == '__main__':
    a = acq()
    keyboard_listener = keyboard.Listener(on_press=a.on_press)
    with keyboard_listener:
        keyboard_listener.join()
        