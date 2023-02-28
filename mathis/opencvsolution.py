import cv2
import numpy as np
import threading
from uvc_stream import DEV_SETTINGS

class VideoGet :
    def __init__(self, src=0, camera_name=''):
        self.stream = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, DEV_SETTINGS['pupil_invisible'][camera_name]['frame_size'][0])
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, DEV_SETTINGS['pupil_invisible'][camera_name]['frame_size'][1])
        self.stream.set(cv2.CAP_PROP_FPS, DEV_SETTINGS['pupil_invisible'][camera_name]['fps'])

        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.get, args=()).start()
        return self

    def get(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = self.stream.read()

    def stop(self):
        self.stopped = True

class VideoShow:
    def __init__(self, frame=None, camera_name=''):
        self.frame = frame
        self.stopped = False
        self.camera_name = camera_name
    def start(self):
        threading.Thread(target=self.show, args=()).start()
        return self

    def show(self):
        while not self.stopped:
            cv2.imshow(self.camera_name, self.frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stopped = True

    def stop(self):
        self.stopped = True

def camera_stream(src=0, camera_name=''):
    video_getter = VideoGet(src, camera_name).start()
    video_shower = VideoShow(video_getter.frame, camera_name).start()

    while True:
        if video_getter.stopped or video_shower.stopped:
            video_getter.stop()
            video_shower.stop()
            break

        frame = video_getter.frame
        video_shower.frame = frame

def launch_camera_streams():
    threads = []
    for i, camera_name in enumerate (DEV_SETTINGS['pupil_invisible'].keys()):
        t = threading.Thread(target=camera_stream, args=(i+1, camera_name))
        threads.append(t)
        t.start()
    for thread in threads:
        thread.join()

#world always works, eye camera only work for one eye at a time
launch_camera_streams()