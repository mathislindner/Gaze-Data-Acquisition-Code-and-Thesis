from constants import *
import os 
from file_helper import copy_frames_to_new_folder
import time

def run_colmap(recording_id):
    pass
    recording_folder = os.path.join(recordings_folder,str(recording_id))
    undistorted_world_camera_folder = os.path.join(recording_folder, "undistorted_world_camera")
    colmap_ws_folder = os.path.join(recording_folder, "colmap_ws")
    colmap_ws_images_folder = os.path.join(colmap_ws_folder, "images")
    colmap_log_dir = os.path.join(colmap_ws_folder, "log")

    #create the colmap workspace folder
    if not os.path.exists(colmap_ws_folder):
        os.makedirs(colmap_ws_folder)
    if not os.path.exists(colmap_ws_images_folder):
        os.makedirs(colmap_ws_images_folder)
    if not os.path.exists(colmap_log_dir):
        os.makedirs(colmap_log_dir)


    #copy the frames to the colmap workspace folder 3 frames per second
    copy_frames_to_new_folder(undistorted_world_camera_folder, colmap_ws_folder, step = 10)

    #create batch file to run colmap on cluster
    world_batch_file_path = os.path.join(colmap_ws_folder, "run_colmap_on_world.sh")
    with open(world_batch_file_path, "w") as batch_file:
        batch_file.write("#!/bin/bash")
        batch_file.write("#SBATCH --job-name=colmap {}".format(recording_id))
        batch_file.write("#SBATCH --output={}%j.out".format(colmap_log_dir))
        batch_file.write("#SBATCH --gres=gpu:1")
        batch_file.write("#SBATCH --mem=32G")
        batch_file.write("colmap automatic_reconstructor --workspace_path " + colmap_ws_folder + " --image_path " + colmap_ws_images_folder)
        #FIXME: add the rest of the parameters (same camera model, video sequence, etc.)
    #run colmap on the frames with sbatch
    os.system("sbatch " + world_batch_file_path)
    
    #TODO: wait until colmap is done (check by job id)
    pass
    #once once colmap is done, try to locate the depth camera from there
    #https://colmap.github.io/faq.html#register-localize-new-images-into-an-existing-reconstruction
    depth_batch_file = os.path.join(colmap_ws_folder, "run_colmap_on_depth.sh")
    with open(depth_batch_file, "w") as batch_file:
        batch_file.write("#!/bin/bash")
        batch_file.write("#SBATCH --job-name=colmap {}".format(recording_id))
        batch_file.write("#SBATCH --output={}%j.out".format(colmap_log_dir))
        batch_file.write("#SBATCH --gres=gpu:1")
        batch_file.write("#SBATCH --mem=8G")

        batch_file.write("colmap feature_extractor --database_path $PROJECT_PATH/database.db --image_path $PROJECT_PATH/images --image_list_path /path/to/image-list.txt")
        batch_file.write("colmap vocab_tree_matcher --database_path $PROJECT_PATH/database.db --VocabTreeMatching.vocab_tree_path /path/to/vocab-tree.bin -VocabTreeMatching.match_list_path /path/to/image-list.txt")
        batch_file.write("colmap image_registrator --database_path $PROJECT_PATH/database.db --input_path /path/to/existing-model --output_path /path/to/model-with-new-images ")