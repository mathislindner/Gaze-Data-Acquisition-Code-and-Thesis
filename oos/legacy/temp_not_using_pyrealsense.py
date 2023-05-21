import multiprocessing as mp
import cv2
import pynput.keyboard as keyboard
import os
from constants import *

class cameraStream(mp.Process):
    def __init__(self, frame_queue):
        super(cameraStream, self).__init__()
        self.queue = frame_queue
        self.stop_event = mp.Event()
        self.rgb_camera = None
        self.depth_camera = None

    def run(self):
        self.rgb_camera = cv2.VideoCapture(1)
        self.depth_camera = cv2.VideoCapture(2)
        while not self.stop_event.is_set():
            rgb_ret, rgb_frame = self.rgb_camera.read()
            depth_ret, depth_frame = self.depth_camera.read()
            if rgb_ret and depth_ret:
                self.queue.put((rgb_frame, depth_frame))
            else:
                pass

    def stop(self):
        self.stop_event.set()
        self.join()
        #self.rgb_camera.release()
        #self.depth_camera.release()
        self.queue.close()


class StorageProcess(mp.Process):
    def __init__(self, frame_queue):
        super().__init__()
        self.queue = frame_queue
        self.stop_event = mp.Event()
        self.i = 0
        self.recording_path = os.path.join(recordings_folder, "test")

    def run(self):
        while not self.stop_event.is_set():
            rgb_frame, depth_frame = self.queue.get()
            print("saving images")
            cv2.imwrite(os.path.join(self.recording_path, "rgb_image", "{}.png".format(self.i)), rgb_frame)
            cv2.imwrite(os.path.join(self.recording_path, "depth_image", "{}.png".format(self.i)), depth_frame)
            self.i += 1

    def stop(self):
        self.stop_event.set()
        self.join()
        self.queue.close()


class acquisitionLogic(): # mp.Process):
    def __init__(self):
        #super().__init__()
        self.frame_queue = mp.Queue()
        self.cam_stream = cameraStream(self.frame_queue)
        self.storage_process = StorageProcess(self.frame_queue)
        self.kb_listener = keyboard.Listener(on_press=self.on_press)

        self.kb_listener.start()
        


    def on_press(self, key):
        if key == keyboard.Key.right:
            self.start_all_devices()
        if key == keyboard.Key.left:
            self.stop_all_devices()
        if key == keyboard.Key.esc:
            self.stop_all_devices()
            self.kb_listener.stop()
            self.kb_listener.join()
            exit()

    def start_all_devices(self):
        self.cam_stream.start()
        self.storage_process.start()

    def stop_all_devices(self):
        print("stopping threads")
        self.cam_stream.stop()
        self.storage_process.stop()
        print("threads stopped")



if __name__ == "__main__":

    a = acquisitionLogic()
    while True:
        pass
