import cv2 as cv
import numpy as np
import threading
from uvc_stream import DEV_SETTINGS

#stream 1 camera with cv2

cap = cv.VideoCapture(-3, cv.CAP_DSHOW)
cap.set(cv.CAP_PROP_FRAME_WIDTH, DEV_SETTINGS['pupil_invisible']['world']['frame_size'][0])
cap.set(cv.CAP_PROP_FRAME_HEIGHT, DEV_SETTINGS['pupil_invisible']['world']['frame_size'][1])
cap.set(cv.CAP_PROP_FPS, DEV_SETTINGS['pupil_invisible']['world']['fps'])

if not cap.isOpened():
    print("Cannot open camera")
    exit()
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    # Our operations on the frame come here
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    # Display the resulting frame
    cv.imshow('frame', gray)
    if cv.waitKey(1) == ord('q'):
        break
# When everything done, release the capture
cap.release()
cv.destroyAllWindows()
