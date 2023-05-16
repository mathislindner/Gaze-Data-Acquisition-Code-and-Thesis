from constants import *
import os 
from file_helper import copy_frames_to_new_folder
from colmap_testing.colmap_helpers import read_write_model
import numpy as np
import shutil

#FIXME: will probably run into issues if we have the recordings ina different folder than on scratch net
def run_colmap_automatic_reconstructor(recording_id):
    current_working_dir = os.getcwd()
    runcolmap_batch_file = os.path.join(current_working_dir, 'mathis', "run_colmap.sh")
    
    recording_folder = os.path.join(recordings_folder,str(recording_id))

    undistorted_world_camera_folder = os.path.join(recording_folder, "PI_world_v1_ps1_undistorted")
    #distorted_world_camera_folder = os.path.join(recording_folder, "PI_world_v1_ps1")
    depth_camera_folder = os.path.join(recording_folder, "rgb_pngs")

    colmap_ws_folder = os.path.join(recording_folder, "colmap_ws")
    colmap_ws_images_folder = os.path.join(colmap_ws_folder, "all_images")
    colmap_ws_out = os.path.join(colmap_ws_folder, "automatic_recontructor_out")
    #colmap_log_dir = os.path.join(colmap_ws_folder, "log")

    #create the colmap workspace folder
    #TODO: create 2 subfolders in images, one for the world camera and one for the depth camera
    if not os.path.exists(colmap_ws_folder):
        os.makedirs(colmap_ws_folder)
    if not os.path.exists(colmap_ws_images_folder):
        os.makedirs(colmap_ws_images_folder)
    if not os.path.exists(colmap_ws_out):
        os.makedirs(colmap_ws_out)


    #copy the world images to the colmap workspace folder 3 frames per second
    copy_frames_to_new_folder(undistorted_world_camera_folder, colmap_ws_images_folder, step = 10)

    #copy one depth image to the colmap workspace folder (3secs after recording start)
    shutil.copy(os.path.join(depth_camera_folder, "95.png"), colmap_ws_images_folder)
    #rename the depth image to depth_rgb.png to not have the same name as the world camera images
    os.rename(os.path.join(colmap_ws_images_folder, "95.png"), os.path.join(colmap_ws_images_folder, "depth_rgb.png"))
    
    #run command for colmapsh
    command = "sbatch" + " " + runcolmap_batch_file + " " + recording_folder
    print(command)
    os.system(command)

run_colmap_automatic_reconstructor('d89f66fb-a3b2-443a-b417-cf4346262dc2')

def run_colmap_exhaustive_matcher(recording_id):
    pass

#run_colmap("ff0acdab-123d-41d8-bfd6-b641f99fc8eb")
def get_colmap_sparse_model(recording_path):
    path = os.path.join(recording_path, "colmap_ws/colmap_out_1/sparse")
    cameras, images, points_3d = read_write_model.read_model(path, ".bin")
    return cameras, images, points_3d

def get_colmap_dense_model(recording_path):
    path = os.path.join(recording_path, "colmap_ws/automatic_recontructor/dense/0/sparse")
    cameras, images, points_3d = read_write_model.read_model(path, ".bin")
    return cameras, images, points_3d

#TODO: instead of just using the 90th frame, average over a few frames from the beginning of the recording
def get_depth_distances_array(recording_path):
    depth_camera_distances = np.load(os.path.join(recording_path, "depth_array.npz"))
    file_name = depth_camera_distances.files[0]
    return depth_camera_distances[file_name][95] #depth_camera_distances[file_name][95] is the depth array of the 90th frame

#returns the colmap image dict
def get_colmap_depth_image(images):
    for image_id in images:
        if images[image_id].name == "depth_rgb.png":
            return images[image_id]

#returns the depths of the points thatare non zero in from the depth array
def get_depths_and_colmap_point_ids(colmap_depth_image, colmap_points, depth_array):
    #get the visible points
    visible_colmap_point_ids, depths = [], []
    for point_ids, pixel_location in zip(colmap_depth_image.point3D_ids, colmap_depth_image.xys):
        if point_ids != -1:
            pixel_location = np.round(pixel_location).astype(int) #round pixel locations
            x = pixel_location[0]
            y = pixel_location[1]
            if depth_array[y, x] != 0:
                visible_colmap_point_ids.append(point_ids)
                depths.append(depth_array[y, x])
                
    return np.array(depths), np.array(visible_colmap_point_ids)

def get_scale(colmap_cameras, colmap_images, colmap_points, depth_array):
    colmap_depth_image = get_colmap_depth_image(colmap_images)
    depths, point_ids = get_depths_and_colmap_point_ids(colmap_depth_image, colmap_points, depth_array)
    visible_3Dpoints_by_depth_camera = np.array([colmap_points[point_id].xyz for point_id in point_ids])
    camera_position = colmap_depth_image.tvec
    #calculate distance between camera and points
    distances = np.linalg.norm(visible_3Dpoints_by_depth_camera - camera_position, axis=1)
    #calculate scale
    scale = np.mean(depths / distances)
    return scale / 1000 #convert to meters (because the pointcloud is in meters)