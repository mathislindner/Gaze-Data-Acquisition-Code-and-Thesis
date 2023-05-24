#add the path to the dependencies folder
import sys
sys.path.append("/scratch_net/snapo/mlindner/docs/gaze_data_acquisition")
import cv2
import numpy as np
import os
import glob
from time import sleep
from dependencies.constants import *
from dependencies.colmap_helpers import read_write_model
#from compare_poinclouds import get_colmap_dense_model, get_colmap_sparse_model, get_depth_distances_array, get_colmap_depth_camera
import pyrealsense2 as rs

#rectangle: top left(x,y), top right(x,y), bottom right(x,y), bottom left(x,y)
def find_laser_in_image(image, rectangle):
    #crop rectangle 10 pixels from each side because else the aruco marker is detected as the laser
    rectangle = [[[rectangle[0][0]+10], [rectangle[0][1]+10]], [[rectangle[1][0]-10], [rectangle[1][1]+10]], [[rectangle[2][0]-10], [rectangle[2][1]-10]], [[rectangle[3][0]+10], [rectangle[3][1]-10]]]
    rectangle = np.array(rectangle)
    #set to black everything outside the rectangle
    mask = np.zeros(image.shape[:2], dtype="uint8")
    cv2.drawContours(mask, [rectangle], -1, 255, -1)
    image = cv2.bitwise_and(image, image, mask=mask)
    #convert to hsv
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    #define the lower and upper boundaries of the "red" laser in the HSV color space
    lower = np.array([170, 50, 50])
    upper = np.array([180, 255, 255])
    #construct a mask for the laser, then perform a series of dilations and erosions to remove any small blobs left in the mask
    mask = cv2.inRange(hsv, lower, upper)
    #find contours in the mask and initialize the current (x, y) center of the laser
    contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

    x,y = -1,-1
    print(contours)
    #if there are contours
    if len(contours) > 0:
        print("found {} contours".format(len(contours)))
        #find the middle of all contours
        x = int(np.mean([np.mean(contour[:,:,0]) for contour in contours]))
        y = int(np.mean([np.mean(contour[:,:,1]) for contour in contours]))
        print("x: {}, y: {}".format(x,y))
    #draw a circle around the center of the laser
    cv2.circle(image, (x, y), 10, (0, 255, 0), 2)
    cv2.imshow("image", image)
    cv2.waitKey(0)
    #save the image\
    cv2.imwrite("laser_detection.png", image)
    return (x,y)

#get aruco projection rectangle ids to corners mapping
#0: top left, 1: top right, 2: bottom left, 3: bottom right
def get_aruco_rectangle(image_array):
    image=image_array.copy()
    #convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #aruco dictionary
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    #aruco parameters
    parameters = cv2.aruco.DetectorParameters_create()
    #detect the aruco markers
    corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    #if there are markers
    if ids is not None and len(ids) > 3:
        #draw the markers
        image = cv2.aruco.drawDetectedMarkers(image, corners, ids)
        cv2.imwrite('aruco_detected.png', image)
        #get the corners of the markers
        corners = np.squeeze(corners)
        #get the ids of the markers
        ids = np.squeeze(ids)
        #sort the corners by ids
        corners = corners[ids.argsort()]
        #transform rectangle to top left(x,y), top right(x,y), bottom left(x,y), bottom right(x,y)
        #FIXME when putting the aruco markers, put them in the right order (top left, top right, bottom right, bottom left) and then remove this
        resort_indexes = [0, 1, 3, 2]
        #corners = corners[resort_indexes]
        #get the inner corners of each marker (top left corner is bottom right, top right corner is bottom left, bottom left corner is top right, bottom right corner is top left)
        rectangle_corners = np.zeros((4,2))
        for i in range(4):
            rectangle_corners[i] = corners[i][(i+2) % 3]
        return rectangle_corners.astype(np.int32)
    else:
        print("only {} markers detected".format(len(ids)))
        return None
        



def get_depth_of_pixel(image_path, pixel):
    #get the depth of the pixel
    depth = image_path[pixel[1], pixel[0]]
    return depth


def get_2D_laser_position(image_array):
    '''
    returns the 2D position of the laser in the image
    if no laser is found, or if the aruco rectangle is not found, returns -1,-1
    '''
    aruco_rectangle = get_aruco_rectangle(image_array)
    if aruco_rectangle is None:
        return -1,-1 #if no aruco rectangle is found, return -1,-1
    position = find_laser_in_image(image_array, aruco_rectangle)
    return position

def get_3D_laser_position_relative_to_depth_camera(image_array, depth_array_corresponding_to_image):
    '''
    returns the 3D position of the laser in the image, relative to the depth camera
    if no laser is found, or if the aruco rectangle is not found, returns None
    '''
    #get the image path
    laser_2D_position = get_2D_laser_position(image_array)
    if laser_2D_position == (-1,-1):
        return None
    #get the depth of the pixel
    depth_of_pixel = get_depth_of_pixel(depth_array_corresponding_to_image, laser_2D_position)
    #get the 3D coordinates of the pixel
    coordinates_3D = rs.deproject_pixel_to_point(laser_2D_position, depth_of_pixel)
    return coordinates_3D


i=297
image_path = os.path.join(recordings_folder, "85854c40-066e-4825-94d6-312016ea7b85", "rgb_pngs", "{}.png".format(i))
image_path = '/scratch_net/snapo/mlindner/docs/gaze_data_acquisition/laser_test.png'
image = cv2.imread(image_path)
x,y = get_2D_laser_position(image)
print(x,y)







def depth_camera_pixel_to_3D(pixel, depths, recording_path):
    #import colmap camera parameters
    #get the depth of the pixel
    depth = depths[pixel[1], pixel[0]]
    coordinates_3D = rs.deproject_pixel_to_point(pixel, depth)
    return coordinates_3D
    
