import cv2
import numpy as np
from constants import *
import os 

def get_pixel_location_of_laser(image_path):
    #read the image
    image = cv2.imread(image_path)
    #initialize the center of the laser
    x, y = 0, 0
    #convert to hsv
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    #show the image
    cv2.imshow("image", image)
    #define the range of the laser
    lower_red = np.array([0, 0, 255])
    upper_red = np.array([0, 0, 255])
    # Threshold the HSV image to get only blue colors
    mask = cv2.inRange(hsv_image, lower_red, upper_red)
    # Bitwise-AND mask and original image
    res = cv2.bitwise_and(image,image, mask= mask)
    #convert to grayscale
    gray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
    #find the contours
    contours, hierarchy = cv2.findContours(gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    #find the contour with the largest area
    max_area = 0
    max_contour = None
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > max_area:
            max_area = area
            max_contour = contour
    #find the center of the contour
    M = cv2.moments(max_contour)
    x = int(M["m10"] / M["m00"])
    y = int(M["m01"] / M["m00"])
    # if laser is not found, return None
    if x == 0 and y == 0:
        return None
    return (x,y)

laser_image_path = os.path.join(recordings_folder, "laser_test.jfif")
get_pixel_location_of_laser(laser_image_path)