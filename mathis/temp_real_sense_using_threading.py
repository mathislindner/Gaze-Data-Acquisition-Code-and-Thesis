import pyrealsense2 as rs
import numpy as np
import cv2
from threading import Thread, Event
from time import sleep
import os
from constants import *
import pynput.keyboard as keyboard
"""
# Code taken and modified from:
# https://github.com/IntelRealSense/librealsense/blob/master/wrappers/python/examples/python-rs400-advanced-mode-example.py
class RealSenseStream():
    def __init__(self):
        # Configure depth and color streams
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.stop_event = Event()

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
                if frame_number % 30 == 0:
                    print(t)
                cv2.imwrite(os.path.join(self.path,"depth_image","{}.png".format(frame_number)), depth_image)
                cv2.imwrite(os.path.join(self.path,"color_image","{}.png".format(frame_number)), color_image)
                self.timestamps[frame_number] = t
                #print("Images saved")

    def stop_saving(self):
        #remove all non-zero elements from timestamps
        self.stop_event.set()
        self.timestamps = self.timestamps[self.timestamps != 0]
        np.save(os.path.join(self.path,"depth_cam_timestamps.npy"), self.timestamps)
        pass

class acquisitionLogic(Thread):
    def __init__(self):
        super().__init__()
        self.storage_thread = None
        self.cam_thread = None    

    def on_press(self, key):
        if key == keyboard.Key.down:
            self.start()
            self.start_all_devices()
        if key == keyboard.Key.esc:
            self.stop_all_devices()
            self.stop()
        else:
            print("key pressed")
        
    def start_all_devices(self):
        self.cam_thread = RealSenseStream()
        self.cam_thread.start_recording()
        self.storage_thread = Storage(self.cam_thread)
        self.storage_thread.start_saving()
        print("threads started")

    def stop_all_devices(self):
        print("stopping threads")
        self.storage_thread.stop_event.set()
        self.cam_thread.stop_event.set()
        self.cam_thread.join()
        self.storage_thread.join()

        self.cam_thread.stop_recording()
        self.storage_thread.stop_saving()
        print("threads stopped and everything is saved")

"""        
#FIXME: maybe we don t need to inherit from Thread because the pipeline is already a thread
class RealSenseCamera():
    def __init__(self):
        # Configure depth and color streams
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.depth_camera_frames_queue = rs.frame_queue(200)
        self.color_camera_frames_queue = rs.frame_queue(200)
        self.stop_event = Event()

    def start_recording(self):
        # Get device product line for setting a supporting resolution
        #pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        #pipeline_profile = self.config.resolve(pipeline_wrapper)
        #device = pipeline_profile.get_device()
        #device_product_line = str(device.get_info(rs.camera_info.product_line))        
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        #self.pipeline.start(self.config)
        self.pipeline.start(self.config, self.depth_camera_frames_queue, self.color_camera_frames_queue)
    def stop_recording(self):
        self.pipeline.stop()
        self.config.disable_all_streams()

class StorageThread():
    def __init__(self, cam_stream):
        self.recording_id = "test"
        self.path = os.path.join(recordings_folder, self.recording_id)
        self.cam_stream = cam_stream
        self.timestamps = np.zeros((100000), dtype=np.int64)
        self.stop_event = False

    def start_saving(self):
        #check keyboard listener
        while not self.stop_event:
            #depth_image, color_image, t, frame_number = self.frames_queue. #TODO: THISSSSS
            frames = self.cam_stream.frames_queue.wait_for_frame()
            print(frames)
            frame_data = frames.get_data()
            print(frame_data)
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            t = frames.get_timestamp()
            frame_number = depth_frame.get_frame_number()
            if depth_frame is None:
                continue
            else:
                depth_image =  np.asanyarray(depth_frame.get_data())
                color_image = np.asanyarray(color_frame.get_data())

                if frame_number % 30 == 0:
                    print(t)
                cv2.imwrite(os.path.join(self.path,"depth_image","{}.png".format(frame_number)), depth_image)
                cv2.imwrite(os.path.join(self.path,"color_image","{}.png".format(frame_number)), color_image)
                self.timestamps[frame_number] = t
                #print("Images saved")

    def stop_saving(self):
        #remove all non-zero elements from timestamps
        self.stop_event = True
        self.timestamps = self.timestamps[self.timestamps != 0]
        np.save(os.path.join(self.path,"depth_cam_timestamps.npy"), self.timestamps)
        pass

#FIXME maybe create a class for camera and storage in one class, since the queue is already a thread?
#or this would be blocking?
class acquisitionLogic():
    def __init__(self):
        self.camera = RealSenseCamera()
        self.storage_thread = StorageThread(self.camera)
        self.kblistener_thread = keyboard.Listener(on_press=self.on_press)
        self.kblistener_thread.start()
        self.kblistener_thread.join()

    def on_press(self, key):
        if key == keyboard.Key.right:
            self.start_all_devices()
        if key == keyboard.Key.esc:
            self.stop_all_devices()
        else:
            print("key pressed")

    def start_all_devices(self):
        self.camera.start_recording()
        self.storage_thread.start_saving()
        print("threads started")

    def stop_all_devices(self):
        print("stopping threads")
        #First stop all recordings
        self.storage_thread.stop_event = True
        #then wait for the storage thread to finish saving
        self.storage_thread.join()

        self.camera.stop_recording()
        self.storage_thread.stop_saving()
        print("threads stopped and everything is saved")

if __name__ == '__main__':
    #add keyboard interrupt
    acq_log = acquisitionLogic()


        
