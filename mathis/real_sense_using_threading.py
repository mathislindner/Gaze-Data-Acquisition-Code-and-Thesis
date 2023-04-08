import pyrealsense2 as rs
import numpy as np
import cv2
from threading import Thread, Event
from time import sleep
import os
from constants import *
import pynput.keyboard as keyboard

# Code taken and modified from:
# https://github.com/IntelRealSense/librealsense/blob/master/wrappers/python/examples/python-rs400-advanced-mode-example.py
class RealSenseStream(Thread):
    def __init__(self):
        super().__init__()
        # Configure depth and color streams
        self.pipeline = rs.pipeline()
        self.config = rs.config()

        # Get device product line for setting a supporting resolution
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        pipeline_profile = self.config.resolve(pipeline_wrapper)
        device = pipeline_profile.get_device()
        device_product_line = str(device.get_info(rs.camera_info.product_line))
        self.queue = rs.frame_queue(50, keep_frames=True)
        
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    def start_recording(self):
        self.start()
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

#grabs frames from camera queue and stores them in a png
#https://superfastpython.com/stop-a-thread-in-python/
class Storage(Thread):
    def __init__(self, cam_stream):
        super().__init__()
        self.i = 0
        self.recording_id = "test"
        self.path = os.path.join(recordings_folder, self.recording_id)
        self.cam_stream = cam_stream
        self.timestamps = np.zeros((100000), dtype=np.int64)
        self.stop_event = Event()

    def start_saving(self):
        self.start()
        while not self.stop_event.is_set():
            depth_image, color_image, t, frame_number = self.cam_stream.load_recent_frame()
            if depth_image is None:
                continue
            else:
                print(type(frame_number))
                cv2.imwrite(os.path.join(self.path,"depth_image","{}.png".format(frame_number)), depth_image)
                cv2.imwrite(os.path.join(self.path,"color_image","{}.png".format(frame_number)), color_image)
                self.timestamps[frame_number] = t
                #print("Images saved")

    def stop_saving(self):
        #remove all non-zero elements from timestamps
        self.timestamps = self.timestamps[self.timestamps != 0]
        np.save(os.path.join(self.path,"depth_cam_timestamps.npy"), self.timestamps)
        pass

class acquisitionLogic():
    def __init__(self):
        #super().__init__()
        self.storage_thread = None
        self.cam_thread = None    

    def on_press(self, key):
        if key == keyboard.Key.down:
            self.stop()
        if key == keyboard.Key.esc:
            exit()
        else:
            print("key pressed")
        
    def start(self):
        self.cam_thread = RealSenseStream()
        self.cam_thread.start_recording()
        self.storage_thread = Storage(self.cam_thread)
        self.storage_thread.start_saving()

    def stop(self):
        self.storage_thread.stop_event.set()
        self.cam_thread.join()
        self.storage_thread.join()

        self.cam_thread.stop_recording()
        self.storage_thread.stop_saving()
        print("threads stopped and everything is saved")

        

if __name__ == '__main__':
    #add keyboard interrupt
    acqlog = acquisitionLogic()
    
    with keyboard.Listener(on_press=acqlog.on_press) as listener:
        acqlog.start()
        listener.join()
       

        
