import pyrealsense2 as rs
import numpy as np
import time
import datetime
import json
import threading
import queue
import keyboard


import os
from constants import *


class CameraManager:
    def __init__(self, config, output_path):
        self.pipeline = rs.pipeline()
        self.config = config
        self.output_path = output_path
        self.frames = []
        self.timestamps = []
        self.running = False
        self.queue = queue.Queue(maxsize=100)
        self.stop_event = threading.Event()

    def start(self):
        self.pipeline.start(self.config)
        self.running = True
        self.thread = threading.Thread(target=self.capture_frames)
        self.thread.start()

    def stop(self):
        self.running = False
        self.stop_event.set()
        self.thread.join()
        self.pipeline.stop()

    def capture_frames(self):
        while self.running and not self.stop_event.is_set():
            try:
                frames = self.pipeline.wait_for_frames()
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
            except:
                continue
            if not depth_frame or not color_frame:
                continue
            else:
                depth_image = np.asanyarray(depth_frame.get_data())
                color_image = np.asanyarray(color_frame.get_data())
                ts = time.time()
                timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H-%M-%S.%f')
                self.queue.put((timestamp, color_image, depth_image))
                print(self.queue.qsize())

    def save_frames(self):
        while self.running or not self.queue.empty():
            if not self.queue.empty():
                timestamp, color_image, depth_image = self.queue.get()
                self.frames.append((timestamp, color_image, depth_image))
                self.timestamps.append(timestamp)
                print(len(self.frames))
                if len(self.frames) >= 100:
                    print('Saving 1000 frames to {}'.format(self.output_path))
                    np.savez(self.output_path, **{ts: frame for ts, frame, _ in self.frames})
                    self.frames.clear()
                    print('Saved 1000 frames to {}'.format(self.output_path))
            else:
                time.sleep(0.01)

    def save_timestamps(self, file_path):
        with open(file_path, 'w') as f:
            json.dump(self.timestamps, f)
        self.timestamps.clear()

if __name__ == '__main__':
    recording_id = "test"
    recording_path = os.path.join(recordings_folder, recording_id)

    config = rs.config()
    config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, 30)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    output_path = os.path.join(recording_path, 'frames_{}.npz'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))
    camera_manager = None
    save_thread = None
    
    is_recording = False
    while True:
        if keyboard.is_pressed('r'):
            if not is_recording:
                is_recording = True
                camera_manager = CameraManager(config, output_path)
                camera_manager.start()
                save_thread = threading.Thread(target=camera_manager.save_frames)
                save_thread.start()
        if keyboard.is_pressed('t'):
            timestamp_path = 'timestamps_{}.json'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
            camera_manager.save_timestamps(timestamp_path)
            print('Timestamps saved to {}'.format(timestamp_path))
        if keyboard.is_pressed('s'):
            camera_manager.stop()
            save_thread.join()
            break
        time.sleep(0.1)
