from constants import *
import os 
from file_helper import copy_frames_to_new_folder
import time
import shutil
import subprocess

def run_colmap(recording_id):
    current_working_dir = os.getcwd()
    runcolmap_batch_file = os.path.join(current_working_dir, "run_colmap.sh")
    
    recording_folder = os.path.join(recordings_folder,str(recording_id))

    undistorted_world_camera_folder = os.path.join(recording_folder, "PI_world_v1_ps1_undistorted")
    distorted_world_camera_folder = os.path.join(recording_folder, "PI_world_v1_ps1")
    depth_camera_folder = os.path.join(recording_folder, "rgb_pngs")

    colmap_ws_folder = os.path.join(recording_folder, "colmap_ws")
    colmap_dataset_folder = os.path.join(colmap_ws_folder, "dataset")
    colmap_ws_images_folder = os.path.join(colmap_dataset_folder, "images")
    colmap_world_camera_folder_undistorted = os.path.join(colmap_ws_images_folder, "world_camera_undistorted")
    colmap_world_camera_folder_distorted = os.path.join(colmap_ws_images_folder, "world_camera_distorted")
    colmap_depth_camera_folder = os.path.join(colmap_ws_images_folder, "depth_camera")
    colmap_log_dir = os.path.join(colmap_ws_folder, "log")

    #create the colmap workspace folder
    #TODO: create 2 subfolders in images, one for the world camera and one for the depth camera
    if not os.path.exists(colmap_ws_folder):
        os.makedirs(colmap_ws_folder)
    if not os.path.exists(colmap_ws_images_folder):
        os.makedirs(colmap_ws_images_folder)
    if not os.path.exists(colmap_log_dir):
        os.makedirs(colmap_log_dir)
    if not os.path.exists(colmap_world_camera_folder_distorted):
        os.makedirs(colmap_world_camera_folder_undistorted)
    if not os.path.exists(colmap_world_camera_folder_distorted):
        os.makedirs(colmap_world_camera_folder_distorted)
    if not os.path.exists(colmap_depth_camera_folder):
        os.makedirs(colmap_depth_camera_folder)


    #copy the world images to the colmap workspace folder 3 frames per second
    copy_frames_to_new_folder(undistorted_world_camera_folder, colmap_world_camera_folder_undistorted, step = 10)
    #copy distorted images to new folder
    copy_frames_to_new_folder(distorted_world_camera_folder, colmap_world_camera_folder_distorted, step = 10)
    #copy_frames_to_new_folder(world_camera_folder, colmap_ws_images_folder, step = 10)

    #copy one depth image to the colmap workspace folder (3secs after recording start)
    shutil.copy(os.path.join(depth_camera_folder, "90.png"), colmap_depth_camera_folder)
    #rename the depth image to depth_rgb.png to not have the same name as the world camera images
    os.rename(os.path.join(colmap_depth_camera_folder, "90.png"), os.path.join(colmap_depth_camera_folder, "depth_rgb.png"))
    
    #execute bash script with sbatch command
    #FIXME make sure executed in the right folder, somehow can t pass runcolmap_batch_file as argument (removes backslashes)
    #os.system("sbatch" + " " + "run_colmap.sh" + " " + recording_folder)

run_colmap("ff0acdab-123d-41d8-bfd6-b641f99fc8eb")

def convert_vectors_to_true_scale(recording_id):
    recording_folder = os.path.join(recordings_folder,str(recording_id))
    colmap_ws_folder = os.path.join(recording_folder, "colmap_ws")
    #TODO: verify that the colmap execution was successful
    if not os.path.exists(os.path.join(colmap_ws_folder, "sparse/0/images.bin")):
        print("Colmap execution was not successful, aborting")
        return
    
    #import depth matrix
    #find a clear spot in the matrix
    #find the corresponding depth point from colmap
    #calculate the scale factor thanks to rgb image
    #convert all the points/cameras/images to true scale