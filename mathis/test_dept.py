#https://intelrealsense.github.io/librealsense/python_docs/_generated/pyrealsense2.html#module-pyrealsense2

import pyrealsense2 as rs
import threading
import queue
import numpy as np
from time import time_ns, sleep

class DepthCamera(threading.Thread):
    def __init__(self, recording_time = 15):
        super().__init__()
        self.stop_event = threading.Event()
        self.frame_queue = queue.Queue()
        
        self.max_frames =  recording_time * 30 * 60
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        #initialize the arrays
        self.recording_timestamps = np.zeros((self.max_frames), dtype=np.int64)
        
    def start_recording(self):
        i = 0
        self.pipeline.start(self.config)
        while not self.stop_event.is_set():
            
            frames = self.pipeline.wait_for_frames(timeout_ms = 10000)
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            frame_number = frames.get_frame_number()
            timestamp = time_ns()
            if not depth_frame or not color_frame:
                continue
            else:
                print (f"frame number: {frame_number}")
                self.recording_timestamps[i] = timestamp
                self.frame_queue.put((depth_frame,color_frame, frame_number))
        
    def stop_recording(self):
        self.pipeline.stop()
        self.stop_event.set()
        #TODO: wait until all the images are saved before resetting the class
        
        #self.__init__() #reset the class for next recording
    
class Storage_Thread(threading.Thread):
    
    def start_recording(self,recording_id):
        super().__init__()
        self.recording_id = recording_id
        self.output_file = os.path.join(recordings_folder, self.recording_id, "depth_camera.npz")
        self.stop_event = threading.Event()
        self.frame_queue = queue.Queue()
        
    def run(self):
        while not self.stop_event.is_set():
            try:
                depth_frame, color_frame, frame_number = self.frame_queue.get(timeout=0.1)
                #save the frames to png
                cv2.imwrite(os.path.join(recordings_folder, self.recording_id, "depth", f"{frame_number}.png"), depth_frame)
                cv2.imwrite(os.path.join(recordings_folder, self.recording_id, "color", f"{frame_number}.png"), color_frame)
            except queue.Empty:
                pass

    def stop(self):
        self.stop_event.set()


if __name__ == "__main__":
    ctx = rs.context()
    devices = ctx.query_devices()
    for dev in devices:
        dev.hardware_reset()

    depth_camera = DepthCamera()
    depth_camera.start_recording()
    sleep(5)
    depth_camera.stop_recording()
    print (depth_camera.recording_timestamps)