import zipfile
import io 
import os
from shutil import move
import ffmpeg
from constants import *
import numpy as np

def unzip_and_move_to_parent(response, parent_folder):
    z = zipfile.ZipFile(io.BytesIO(response))
    z.extractall(parent_folder)
    subfolder_name = os.listdir(parent_folder + "/")[0]
    #move all files to parent folder and delete folder
    for filename in os.listdir(os.path.join(parent_folder, subfolder_name)):
        move(os.path.join(parent_folder, subfolder_name, filename), os.path.join(parent_folder, filename))
    os.rmdir(os.path.join(parent_folder, subfolder_name))

def extract_one_camera(input_file, output_folder, n_of_frames):
    #TODO: either use ffmpeg to probe or assume that the .time file is correct
    #n_of_frames = ffmpeg.probe(input_file)['streams'][0]['nb_frames']
    print(input_file)
    (
        ffmpeg
        .input(input_file)
    ).output(output_folder + "/" + "%d.png", start_number=0, vframes=n_of_frames, vsync = 2, loglevel="quiet").run()

def decode_timestamp(timestamp_path):
    ts = np.fromfile(timestamp_path, dtype=np.uint64)
    return ts

def extract_frames(recording_id):
    recording_folder = recordings_folder + str(recording_id)

    nb_of_timestamps_left = len(decode_timestamp(recording_folder + "/PI left v1 ps1.time"))
    nb_of_timestamps_right = len(decode_timestamp(recording_folder + "/PI right v1 ps1.time"))
    nb_of_timestamps_world = len(decode_timestamp(recording_folder + "/PI world v1 ps1.time"))
    nb_of_timestamps = [nb_of_timestamps_left, nb_of_timestamps_right, nb_of_timestamps_world]

    try:
        os.mkdir(recording_folder + "/left_eye_frames")
        os.mkdir(recording_folder + "/right_eye_frames")
        os.mkdir(recording_folder + "/world_frames")
    except:
        pass

    for i in range(len(camera_names)):
        input_file = recording_folder + "/" + camera_names[i] + ".mp4"
        output_folder = recording_folder + "/" + camera_folders[i]
        extract_one_camera(input_file, output_folder, nb_of_timestamps[i])