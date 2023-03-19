import zipfile
import io 
import os
from shutil import move
import ffmpeg
from constants import *

def unzip_and_move_to_parent(response, parent_folder):
    z = zipfile.ZipFile(io.BytesIO(response))
    z.extractall(parent_folder)
    subfolder_name = os.listdir(parent_folder + "/")[0]
    #move all files to parent folder and delete folder
    for filename in os.listdir(os.path.join(parent_folder, subfolder_name)):
        move(os.path.join(parent_folder, subfolder_name, filename), os.path.join(parent_folder, filename))
    os.rmdir(os.path.join(parent_folder, subfolder_name))

def extract_one_camera(input_file, output_folder):
    n_of_frames = ffmpeg.probe(input_file)['streams'][0]['nb_frames']
    (
        ffmpeg
        .input(input_file)
    ).output(output_folder + "/" + "%d.png", start_number=0, vframes=n_of_frames, vsync = 2, loglevel="quiet").run()

def extract_frames(recording_id):
    recording_folder = recordings_folder + str(recording_id)
    try:
        os.mkdir(recording_folder + "/left_eye_frames")
        os.mkdir(recording_folder + "/right_eye_frames")
        os.mkdir(recording_folder + "/world_frames")
    except:
        pass

    for i in range(len(camera_names)):
        input_file = recording_folder + "/" + camera_names[i] + ".mp4"
        output_folder = recording_folder + "/" + camera_folders[i]
        extract_one_camera(input_file, output_folder)