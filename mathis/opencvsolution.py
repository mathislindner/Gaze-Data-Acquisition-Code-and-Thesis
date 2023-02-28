import cv2
import numpy as np
import threading
from uvc_stream import DEV_SETTINGS

#create Thread class for each camera
class camThread(threading.Thread):
    def __init__(self, previewName, camID):
        threading.Thread.__init__(self)
        self.previewName = previewName
        self.camID = camID
    def run(self):
        print ("Starting " + self.previewName)
        camPreview(self.previewName, self.camID)


def camPreview(previewName, camID):
    cv2.namedWindow(previewName)
    cam = cv2.VideoCapture(camID)
    #set camera properties
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, DEV_SETTINGS['pupil_invisible'][previewName]['frame_size'][0])
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, DEV_SETTINGS['pupil_invisible'][previewName]['frame_size'][1])
    cam.set(cv2.CAP_PROP_FPS, DEV_SETTINGS['pupil_invisible'][previewName]['fps'])
    
    if cam.isOpened():  # try to get the first frame
        ret, frame = cam.read()
    else:
        ret = False

    while ret:
        cv2.imshow(previewName, frame)
        ret, frame = cam.read()
    cam.release()
    cv2.destroyWindow(previewName)

# Create two threads as follows
thread1 = camThread("world", 0)
#thread2 = camThread("eye_left", 1)
#thread3 = camThread("eye_right", 2)

thread1.start()
#thread2.start()
#thread3.start()
