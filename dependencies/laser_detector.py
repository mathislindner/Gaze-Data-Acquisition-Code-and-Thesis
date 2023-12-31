#add the path to the dependencies folder
import sys
sys.path.append("/scratch_net/snapo/mlindner/docs/gaze_data_acquisition")
import cv2
import numpy as np
import pandas as pd
import os
import math
from dependencies.constants import *
from dependencies.coordinates_transformation_helpers import convert_3D_coordinates_from_depth_to_pupil_world, project_3D_points_to_pupil_world
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
    lower = np.array([170, 30, 50])
    upper = np.array([180, 255, 255])
    #construct a mask for the laser, then perform a series of dilations and erosions to remove any small blobs left in the mask
    mask = cv2.inRange(hsv, lower, upper)
    #find contours in the mask and initialize the current (x, y) center of the laser
    contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

    x,y = None, None
    #if there are contours
    if len(contours) > 0:
        #find the middle of all contours
        x = int(np.mean([np.mean(contour[:,:,0]) for contour in contours]))
        y = int(np.mean([np.mean(contour[:,:,1]) for contour in contours]))
    return x,y

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
        #cv2.imwrite('aruco_detected.png', image)
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
        
import pyrealsense2 as rs
def deproject_pixels_to_points(u_array, v_array,depth, depth_camera_idx_array):
    # Create a pipeline and start streaming frames
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    profile = pipeline.start(config)
    # Get the depth sensor's depth scale
    depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
    intrinsics = depth_profile.get_intrinsics()

    points = np.zeros((len(u_array), 3))
    no_points = np.array([None, None, None])
    for i in range(len(u_array)-1):
        u= u_array[i]
        v = v_array[i]
        if math.isnan(u) or math.isnan(v):
            points[i] = no_points
            continue
        else:
            u = int(u)
            v = int(v)
            depth_at_pixel = get_depth_of_pixel(depth[depth_camera_idx_array[i]], [u, v])
        #if the depth is 0, or u or v is None, skip this point
        if depth_at_pixel == 0:
            points[i] = no_points
            continue
        # Deproject from pixel to point in 3D
        points[i] = rs.rs2_deproject_pixel_to_point(intrinsics, [u, v], depth_at_pixel)
    return points[:,0], points[:,1], points[:,2]


def get_depth_of_pixel(depth_array, pixel):
    #get the depth of the pixel
    if pixel[0] < 0 or pixel[0] >= depth_array.shape[0] or pixel[1] < 0 or pixel[1] >= depth_array.shape[1]:
        return 0
    depth = depth_array[pixel[0]][pixel[1]]
    return depth


def get_2D_laser_position(image_array):
    '''
    returns the 2D position of the laser in the image
    if no laser is found, or if the aruco rectangle is not found, returns -1,-1
    '''
    aruco_rectangle = get_aruco_rectangle(image_array)
    if aruco_rectangle is None:
        return None, None
    x,y = find_laser_in_image(image_array, aruco_rectangle)
    return x,y

#FIXME use df 2D laser position insteaed of calling function again
def get_3D_laser_position_relative_to_depth_camera(laser_2D_position, depth_array_corresponding_to_image):
    '''
    returns the 3D position of the laser in the image, relative to the depth camera
    if no laser is found, or if the aruco rectangle is not found, returns None
    '''
    if laser_2D_position == (None, None):
        return None
    #get the depth of the pixel
    depth_of_pixel = get_depth_of_pixel(depth_array_corresponding_to_image, laser_2D_position)
    if depth_of_pixel == 0:
        return np.array([None, None, None])
    #get the 3D coordinates of the pixel
    coordinates_3D = rs.deproject_pixel_to_point(laser_2D_position, depth_of_pixel)
    return coordinates_3D


def add_laser_coordinates_to_df(recording_id):
    #TODO:add the scale transformation to COLMAP coordinates txt file
    if not os.path.exists(os.path.join(recordings_folder, recording_id, "colmap_EM_export", "cameras.txt")):
        print("colmap EM export does not exist yet for recording {}".format(recording_id))
        return
    #paths
    recording_path = os.path.join(recordings_folder, recording_id)
    df_path = os.path.join(recording_path, "full_df.csv")
    rgb_pngs_path = os.path.join(recording_path, "rgb_pngs")
    depth_array_path = os.path.join(recording_path, "depth_array.npz")

    #imports
    depth_array = np.load(depth_array_path)['arr_0']
    df = pd.read_csv(df_path)
    # if laser wsa already added, skip
    if 'laser_2D_u_depth_camera' in df.columns:
        print("laser coordinates already added to df for recording {}".format(recording_id))
        return
    #create columns for laser 2D and 3D coordinates
    df[['laser_2D_u_depth_camera','laser_2D_v_depth_camera']] = df['depth_camera_idx'].apply(lambda x: get_2D_laser_position(cv2.imread(os.path.join(rgb_pngs_path, str(x) + ".png")))).to_list()
    #interpolate the laser 2D coordinates
    df['laser_2D_u_depth_camera'] = df['laser_2D_u_depth_camera'].interpolate()
    df['laser_2D_v_depth_camera'] = df['laser_2D_v_depth_camera'].interpolate()
    u_array = df['laser_2D_u_depth_camera'].to_numpy()
    v_array = df['laser_2D_v_depth_camera'].to_numpy()

    depth_camera_idx_array = df['depth_camera_idx'].to_numpy()
    world_camera_idx = df['world_idx'].to_numpy()
    df.to_csv(df_path, index=False)
    laser_3D_rel_to_depth = deproject_pixels_to_points(u_array, v_array, depth_array,depth_camera_idx_array)
    x,y,z = laser_3D_rel_to_depth
    laser_3D_rel_to_depth = np.array([x,y,z]).T
    points_in_colmap  = convert_3D_coordinates_from_depth_to_pupil_world(laser_3D_rel_to_depth, recording_id)
    df['laser_3D_x_colmap'] = points_in_colmap[:,0]
    df['laser_3D_y_colmap'] = points_in_colmap[:,1]
    df['laser_3D_z_colmap'] = points_in_colmap[:,2]
    #interpolate all the nan values
    df['laser_3D_x_colmap'] = df['laser_3D_x_colmap']
    df['laser_3D_y_colmap'] = df['laser_3D_y_colmap']
    df['laser_3D_z_colmap'] = df['laser_3D_z_colmap']
    points_in_colmap = df[['laser_3D_x_colmap','laser_3D_y_colmap','laser_3D_z_colmap']].to_numpy()
    laser_2d_in_world_coordinates = project_3D_points_to_pupil_world(points_in_colmap, recording_id, world_camera_idx)
    #df['laser_2D_u_world_camera'] = laser_2d_in_world_coordinates[:,0]
    #df['laser_2D_v_world_camera'] = laser_2d_in_world_coordinates[:,1]
    df.to_csv(df_path, index=False)
    