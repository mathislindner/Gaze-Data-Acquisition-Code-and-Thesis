import cv2
import numpy as np
from constants import *
import os
import glob
from time import sleep
from colmap_testing.colmap_helpers import read_write_model
from compare_poinclouds import get_colmap_dense_model, get_colmap_sparse_model, get_depth_distances_array, get_colmap_depth_camera
import pyrealsense2 as rs

def get_pixel_location_of_laser(image_path):
    #read the image
    image = cv2.imread(image_path)
    cv2.imshow("image", image)
    cv2.waitKey(0)
    #initialize the center of the laser
    x, y = 0, 0
    #define the range of the laser in HSV
    lower = 60
    upper = 255
    #convert the image to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
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
    #draw a circle around the center of the laser
    cv2.circle(image, (x, y), 7, (0, 255, 0), -1)
    cv2.imshow("image", image)
    cv2.waitKey(0)
    return (x,y)

laser_image_path = os.path.join(recordings_folder, "laser_test.jpeg")
x,y = get_pixel_location_of_laser(laser_image_path)
print(x,y)

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
    
