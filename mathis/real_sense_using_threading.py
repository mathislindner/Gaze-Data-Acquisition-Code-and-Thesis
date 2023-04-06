import pyrealsense2 as rs
import numpy as np
import cv2
from threading import Thread
from time import sleep
import os
from constants import *

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

    def start(self):
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

    def stop(self):
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
        self.event_loop = Thread(target=self.start)

    def start(self):
        while self.event_loop:
            depth_image, color_image, t, frame_number = self.cam_stream.load_recent_frame()
            if depth_image is None:
                continue
            else:
                print(type(frame_number))
                cv2.imwrite(os.path.join(self.path,"depth_image","{}.png".format(frame_number)), depth_image)
                cv2.imwrite(os.path.join(self.path,"color_image","{}.png".format(frame_number)), color_image)
                self.timestamps[frame_number] = t
                #print("Images saved")
            if frame_number > 100:
                self.event_loop.stop()

    def stop(self):
        #remove all non-zero elements from timestamps
        self.timestamps = self.timestamps[self.timestamps != 0]
        np.save(os.path.join(self.path,"depth_cam_timestamps.npy"), self.timestamps)
        pass

class acquisitionLogic(Thread):
    def __init__(self, stop_time = 2):
        super().__init__()
        self.stop_time = stop_time
        
        self.cam_thread = RealSenseStream()
        self.cam_thread.start()
        self.storage_thread = Storage(self.cam_thread)
        self.storage_thread.start()
        self.start()

    def start(self):
        sleep(3)
        print("hello")
        self.stop()

    def stop(self):
        self.cam_thread.stop()
        self.storage_thread.stop()

        self.cam_thread.join()
        self.storage_thread.join()

if __name__ == '__main__':
    acqlog = acquisitionLogic()
    print("hello")
    acqlog.start()
    

        
