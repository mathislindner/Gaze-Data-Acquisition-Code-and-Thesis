import cv2
import numpy as np
from constants import *
import os 
from time import sleep

def get_pixel_location_of_laser(image_path):
    #read the image
    image = cv2.imread(image_path)
    cv2.imshow("image", image)
    cv2.waitKey(0)
    #initialize the center of the laser
    x, y = 0, 0
    #define the range of the laser in HSV
    lower = 70
    upper = 255
    #convert the image to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    cv2.imshow("hsv", hsv)
    cv2.waitKey(0)
    mask = cv2.inRange(hsv, (lower, lower, lower), (upper, upper, upper))
    cv2.imshow("mask", mask)
    cv2.waitKey(0)
    #find the contours of the laser
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    #if there are contours
    if len(contours) > 0:
        #find the largest contour
        c = max(contours, key=cv2.contourArea)
        #find the center of the contour
        M = cv2.moments(c)
        if M["m00"] != 0:
            x = int(M["m10"] / M["m00"])
            y = int(M["m01"] / M["m00"])
    return (x,y)

laser_image_path = os.path.join(recordings_folder, "laser_test.jpeg")
x,y = get_pixel_location_of_laser(laser_image_path)
print(x,y)