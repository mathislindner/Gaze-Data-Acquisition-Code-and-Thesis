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

#rectangle: top left(x,y), top right(x,y), bottom left(x,y), bottom right(x,y)
def find_laser_in_image(image_array, rectangle):
    #read the image
    image = image_array
    #set to black everything outside the rectangle
    mask = np.zeros(image.shape[:2], dtype="uint8")
    mask = cv2.drawContours(mask, [rectangle], -1, 255, -1)
    #apply the mask
    masked_image = cv2.bitwise_and(image, image, mask=mask)
    #show the masked image
    cv2.imshow("masked_image", masked_image)
    cv2.waitKey(0)
    #initialize the center of the laser
    x, y = -1, -1
    #define the range of the laser in HSV
    lower = 60
    upper = 255
    #convert the image to HSV
    hsv = cv2.cvtColor(masked_image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (lower, lower, lower), (upper, upper, upper))
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
    #draw a circle around the center of the laser
    cv2.circle(image, (x, y), 7, (0, 255, 0), -1)
    cv2.imshow("image", image)
    cv2.waitKey(0)
    return (x,y)

#get aruco projection rectangle ids to corners mapping
#0: top left, 1: top right, 2: bottom left, 3: bottom right
def get_aruco_rectangle(image_array):
    image=image_array
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
        corners = corners[resort_indexes]
        #get the inner corners of each marker (top left corner is bottom right, top right corner is bottom left, bottom left corner is top right, bottom right corner is top left)
        rectangle_corners = np.zeros((4,2))
        for i in range(4):
            rectangle_corners[i] = corners[i][(i+2) % 3]
            print(corners[i][(i+2) % 3])
        return rectangle_corners.astype(np.int32)
        

def get_2D_laser_position(image_array):
    aruco_rectangle = get_aruco_rectangle(image_array)
    position = find_laser_in_image(image_path, aruco_rectangle)
    return position

def get_depth_of_pixel(image_path, pixel):
    #get the depth of the pixel
    depth = image_path[pixel[1], pixel[0]]
    return depth

def get_3D_laser_position(image_array, depth_array_corresponding_to_image):
    #get the image path
    laser_2D_position = get_2D_laser_position(image_array)
    #get the depth of the pixel
    depth_of_pixel = get_depth_of_pixel(depth_array_corresponding_to_image, laser_2D_position)
    #get the 3D coordinates of the pixel
    coordinates_3D = rs.deproject_pixel_to_point(laser_2D_position, depth_of_pixel)
    return coordinates_3D


#i=205
#image_path = os.path.join(recordings_folder, "b6a73239-5f5b-4fad-ad65-fcefb27ba4d8", "rgb_pngs", "{}.png".format(i))
#x,y = get_2D_laser_position(image_path)
#print(x,y)

def depth_camera_pixel_to_3D(pixel, depths, recording_path):
    #import colmap camera parameters
    #get the depth of the pixel
    depth = depths[pixel[1], pixel[0]]
    coordinates_3D = rs.deproject_pixel_to_point(pixel, depth)
    return coordinates_3D

def save_laser_3D_location(recording_id, camera_name = "rgb_pngs"):
    recording_path = os.path.join(recordings_folder, recording_id)
    image_paths = glob.glob(os.path.join(recording_path, camera_name, "*.png"))
    #import colmap camera parameters
    #cameras, images, points3D = get_colmap_dense_model(recording_path)
    #depth_camera = get_colmap_depth_camera(images=images, cameras=cameras)
    depth_array = get_depth_distances_array(recording_path=recording_path, camera_name=camera_name)

    laser_2D_coordinates = np.zeros((len(image_paths), 2))
    laser_3D_coordinates = np.zeros((len(image_paths), 3))
    for i, image_path in enumerate(image_paths):
        laser_2D_coordinates[i, :] = get_pixel_location_of_laser(image_path)
        laser_3D_coordinates[i, :] = depth_camera_pixel_to_3D(laser_2D_coordinates[i, :], depth_array)
    np.save(os.path.join(recording_path, "laser_2D_coordinates.npy"), laser_2D_coordinates)
    np.save(os.path.join(recording_path, "laser_3D_coordinates.npy"), laser_3D_coordinates)
    
