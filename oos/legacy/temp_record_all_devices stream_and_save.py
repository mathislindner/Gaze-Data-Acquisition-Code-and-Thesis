#pupil labs libs
from pupil_labs.realtime_api.simple import Device
import  pupil_labs

#depth camera libs
import pyrealsense2 as rs

#general libs
import pynput.keyboard as keyboard
from time import time_ns, sleep
#import multiprocessing as mp
import threading
import queue
import cv2
from constants import recordings_folder
import numpy as np
import os
import json

#this class is more for consistency than usefullness
class Pupil_Camera():
    def __init__(self, device) -> None:
        return
        self.device = device

    def start_recording(self):
        return
        self.device.start_recording()

    def stop_recording(self):
        return
        self.device.stop_recording()

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


############################################################################################################
class AcquisitionLogic:
    def __init__(self) -> None:
        device = None
        """
        #connect to API for pupil labs device
        ip = "10.5.56.134"
        device = Device(address=ip, port="8080")
        assert device is not None, "No device found"
        print("Device found!")
        """
        self.recording_bool = False
        self.event_id = 0
        self.recording_id = None

        self.pupil_camera = Pupil_Camera(device)
        self.depth_camera_thread = DepthCamera()

        self.storage_thread = None
        #self.depth_camera_process = None #we need to store the process to be able to stop it
        #self.pupil_camera_process = None

        self.start_record_key = keyboard.Key.up
        self.stop_record_key = keyboard.Key.down
        self.event_key = keyboard.Key.right
        self.cancel_recording_key = None
        self.exit_key = keyboard.Key.esc

        print("press up to start recording")

    def on_press(self, key):
        if key is self.start_record_key:
            if self.recording_bool == True:
                print('Recording is currently activated.')
            #else start recording process
            self.start_record_process()
        
        if key is self.stop_record_key:
            self.recording_bool = False
            self.stop_record_process()
        
        if key is self.event_key:
            self.trigger_event_process()

        if key is self.cancel_recording_key:
            self.cancel_recording_process()
        
        if key is self.exit_key:
            self.exit_process()

    def start_record_process(self):
        #we have to start the pupil camera process first, otherwise we can t get the recording id
        self.recording_id = self.pupil_camera.start_recording()
        #self.depth_camera_process = mp.Process(target=self.depth_camera.start_recording, args=(self.recording_id,))
        self.depth_camera_thread.start_recording()

        self.storage_thread = Storage_Thread(self.recording_id) #we need tostart it here,else error
        self.storage_thread.start()
        self.recording_bool = True

        while True:
            print("in true loop")
            depth_frames = self.depth_camera_thread.frame_queue.get()
            self.storage_thread.frame_queue.put(depth_frames)
            if self.recording_bool == False:
                self.stop_record_process()
                break        

        print("recording started")

    def stop_record_process(self):
        if self.recording_bool == False:
            raise Exception('Recording is currently deactivated.')
        
        
        self.pupil_camera.stop_recording()
        self.depth_camera_thread.stop_recording()
        self.storage_thread.stop()

        self.depth_camera_thread.join()
        self.storage_thread.join()

        self.recording_bool = False
        print("recording stopped")
        
#https://stackoverflow.com/questions/55880569/how-do-i-make-pynput-keyboard-run-as-a-thread
if __name__ == "__main__":
    acquisition_logic = AcquisitionLogic()
    with keyboard.Listener(on_press=acquisition_logic.on_press) as listener:
        listener.join()


# for inspiration to save the data in a different way
"""import cv2
import threading
import queue

class CameraThread(threading.Thread):
    def __init__(self, cam_id):
        super().__init__()
        self.cam_id = cam_id
        self.stop_event = threading.Event()
        self.frame_queue = queue.Queue()

    def run(self):
        cap = cv2.VideoCapture(self.cam_id)
        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if ret:
                self.frame_queue.put(frame)
        cap.release()

    def stop(self):
        self.stop_event.set()

class StorageThread(threading.Thread):
    def __init__(self, output_file):
        super().__init__()
        self.output_file = output_file
        self.stop_event = threading.Event()
        self.frame_queue = queue.Queue()

    def run(self):
        while not self.stop_event.is_set():
            try:
                frame = self.frame_queue.get(timeout=0.1)
                # save the frame to disk or process it in some way
                cv2.imwrite(self.output_file, frame)
            except queue.Empty:
                pass

    def stop(self):
        self.stop_event.set()

if __name__ == '__main__':
    # Create a camera thread for each camera
    cam1_thread = CameraThread(0)
    cam2_thread = CameraThread(1)

    # Create a storage thread for each camera
    cam1_storage_thread = StorageThread('output1.avi')
    cam2_storage_thread = StorageThread('output2.avi')

    # Start the camera and storage threads
    cam1_thread.start()
    cam2_thread.start()
    cam1_storage_thread.start()
    cam2_storage_thread.start()

    # Continuously get frames from the camera threads and put them in the corresponding storage thread's frame queue
    while True:
        frame1 = cam1_thread.frame_queue.get()
        cam1_storage_thread.frame_queue.put(frame1)
        frame2 = cam2_thread.frame_queue.get()
        cam2_storage_thread.frame_queue.put(frame2)

        # Check if the user pressed 'q' to stop the program
        if cv2.waitKey(1) == ord('q'):
            cam1_thread.stop()
            cam2_thread.stop()
            cam1_storage_thread.stop()
            cam2_storage_thread.stop()
            break

    # Wait for all threads to finish
    cam1_thread.join()
    cam2_thread.join()
    cam1_storage_thread.join()
    cam2_storage_thread.join()

    cv2.destroyAllWindows()
"""