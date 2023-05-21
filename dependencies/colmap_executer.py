try:
    from dependencies.constants import *
    from dependencies.file_helper import copy_frames_to_new_folder
    from dependencies.colmap_helpers import read_write_model
except:
    from constants import *
    from file_helper import copy_frames_to_new_folder
    from colmap_helpers import read_write_model
import os 
import numpy as np
import shutil

def create_image_folders(recording_id, colmap_ws_folder):
    recording_folder = os.path.join(recordings_folder,str(recording_id))

    undistorted_world_camera_folder = os.path.join(recording_folder, "PI_world_v1_ps1_undistorted")
    depth_camera_folder = os.path.join(recording_folder, "rgb_pngs")

    colmap_ws_images_folder = os.path.join(colmap_ws_folder, "all_images")

    if not os.path.exists(colmap_ws_images_folder):
        os.makedirs(colmap_ws_images_folder)
        #copy the world images to the colmap workspace folder 3 frames per second
        copy_frames_to_new_folder(undistorted_world_camera_folder, colmap_ws_images_folder, step = 10)

        #copy one depth image to the colmap workspace folder (3secs after recording start)
        shutil.copy(os.path.join(depth_camera_folder, "95.png"), colmap_ws_images_folder)
        #rename the depth image to depth_rgb.png to not have the same name as the world camera images
        os.rename(os.path.join(colmap_ws_images_folder, "95.png"), os.path.join(colmap_ws_images_folder, "depth_rgb.png"))
        
    #create 2 txt files in colmap workspace folder that contain the names of the world camera images and the depth camera image
    all_images_names = os.listdir(colmap_ws_images_folder)
    all_images_names.sort()
    with open(os.path.join(colmap_ws_folder, "world_images.txt"), "w") as f:
        for image_name in all_images_names[:-1]:
            f.write(image_name + "\n")
    with open(os.path.join(colmap_ws_folder, "depth_images.txt"), "w") as f:
        f.write(all_images_names[-1])


def copy_ws_to_scratch(recording_id, colmap_ws_folder):
    ws_name = colmap_ws_folder.split("/")[-1]
    ws_scratch_path = os.path.join(scratch_net_folder_tmp, str(recording_id), ws_name)
    #copy all files from colmap_ws to scratch
    shutil.copytree(colmap_ws_folder, ws_scratch_path, dirs_exist_ok=True)
    return ws_scratch_path

#FIXME: do the same thing that is in the exhaustive amtcher with moving the ws to scratch
def run_colmap_automatic_reconstructor(recording_id):
    if os.path.exists(os.path.join(recordings_folder,str(recording_id), "colmap_AR_ws","automatic_reconstruction_done.txt")):
        print("Automatic reconstructor already run")
        return
    
    current_working_dir = os.getcwd()
    runcolmap_batch_file = os.path.join(current_working_dir, 'dependencies', "run_colmap_automatic_reconstructor.sh")
    
    recording_folder = os.path.join(recordings_folder,str(recording_id))
    colmap_AR_ws_folder = os.path.join(recording_folder, "colmap_AR_ws")

    #create the colmap workspace folder
    if not os.path.exists(colmap_AR_ws_folder):
        os.makedirs(colmap_AR_ws_folder)

    #copy the world images to the colmap workspace folder
    create_image_folders(recording_id, colmap_AR_ws_folder)
    #copy the ws to scratch
    ws_scratch_path = copy_ws_to_scratch(recording_id, colmap_AR_ws_folder)
    
    #run command for colmapsh
    command = "sbatch" + " " + runcolmap_batch_file + " " + ws_scratch_path
    print(command)
    os.system(command)

#run_colmap_automatic_reconstructor('d89f66fb-a3b2-443a-b417-cf4346262dc2')
def run_colmap_exhaustive_matcher(recording_id):
    if os.path.exists(os.path.join(recordings_folder,str(recording_id), "colmap_EM_ws","exhaustive_matcher_out")):
        print("exhaustive matcher already run")
        return
    #if path exists on scratch_net, copy it back to recordings folder and delete it from scratch_net
    if os.path.exists(os.path.join(scratch_net_folder_tmp, str(recording_id), "colmap_EM_ws", "exhaustive_matching_done.txt")):
        clean_up_colmap_temp()

    current_working_dir = os.getcwd()
    runcolmap_batch_file = os.path.join(current_working_dir, 'dependencies', "run_colmap_exhaustive_matcher.sh")
    
    recording_folder = os.path.join(recordings_folder,str(recording_id))

    colmap_EM_ws_folder = os.path.join(recording_folder, "colmap_EM_ws")

    #create the colmap workspace folder
    #TODO: create 2 subfolders in images, one for the world camera and one for the depth camera
    if not os.path.exists(colmap_EM_ws_folder):
        os.makedirs(colmap_EM_ws_folder)

    #copy the world images to the colmap workspace folder
    create_image_folders(recording_id, colmap_EM_ws_folder)
    #copy the ws to scratch
    ws_scratch_path = copy_ws_to_scratch(recording_id, colmap_EM_ws_folder)

    #run command for colmapsh
    command = "sbatch" + " " + runcolmap_batch_file + " " + ws_scratch_path
    print(command)
    os.system(command)


def clean_up_colmap_temp():
    #copy ws from scratch_net to recordings folder if exhaustive_matching_done.txt exists
    recording_ids = os.listdir(scratch_net_folder_tmp)
    for recording_id in recording_ids:
        #check EM
        if os.path.exists(os.path.join(scratch_net_folder_tmp, recording_id, "colmap_EM_ws", "exhaustive_matching_done.txt")):
            print("copying colmap ws from scratch_net to recordings folder for recording: " + recording_id)
            #force copytree to overwrite existing folder
            shutil.copytree(os.path.join(scratch_net_folder_tmp, recording_id, "colmap_EM_ws"), os.path.join(recordings_folder, recording_id, "colmap_EM_ws"), dirs_exist_ok=True)
            #delete colmap ws from scratch_net_tmp
            shutil.rmtree(os.path.join(scratch_net_folder_tmp, recording_id, "colmap_EM_ws"))
        #check AR
        if os.path.exists(os.path.join(scratch_net_folder_tmp, recording_id, "colmap_AR_ws", "automatic_reconstruction_done.txt")):
            print("copying colmap ws from scratch_net to recordings folder for recording: " + recording_id)
            #force copytree to overwrite existing folder
            shutil.copytree(os.path.join(scratch_net_folder_tmp, recording_id, "colmap_AR_ws"), os.path.join(recordings_folder, recording_id, "colmap_AR_ws"), dirs_exist_ok=True)
            #delete colmap ws from scratch_net_tmp
            shutil.rmtree(os.path.join(scratch_net_folder_tmp, recording_id, "colmap_AR_ws"))
