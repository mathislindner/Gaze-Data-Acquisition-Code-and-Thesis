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

#TODO: this 
def extract_one_camera_using_timestamps(input_file, output_folder, timestamps):
    #convert nanoseconds timestamps to seconds
    timestamps = timestamps / 1000000000
    #extract 100 frames at a time until all frames are extracted
    nb_of_frames = len(timestamps)
    nb_of_frames_per_batch = 100
    nb_of_batches = nb_of_frames // nb_of_frames_per_batch
    #use the ffmpeg python wrapper to extract frames
    print(input_file)
    print(output_folder)
    for i in range(nb_of_batches):
        (
            ffmpeg
            .input(input_file, ss=timestamps[i * nb_of_frames_per_batch], t=timestamps[(i+1) * nb_of_frames_per_batch])
        ).output(output_folder + "/" + "%d.png", start_number=i * nb_of_frames_per_batch, vframes=nb_of_frames_per_batch, vsync = 2, loglevel="quiet").run()
        
    

def extract_one_camera(input_file, output_folder, n_of_frames):
    n_of_frames = ffmpeg.probe(input_file)['streams'][0]['nb_frames'] 
    print(input_file)
    (
        ffmpeg
        .input(input_file)
    ).output(output_folder + "/" + "%d.png", start_number=0, vframes=n_of_frames, vsync = 2, loglevel="quiet").run()

def decode_timestamp(timestamp_path):
    ts = np.fromfile(timestamp_path, dtype=np.uint64)
    return ts

#FIXME use the .time files to extract exactly at the right time the frames, jsut the number of.
def extract_frames(recording_id):
    recording_folder = os.path.join(recordings_folder, str(recording_id))
    
    #TODO:make this nicer
    timestamps_left = decode_timestamp(recording_folder + "/PI left v1 ps1.time")
    timestamps_right = decode_timestamp(recording_folder + "/PI right v1 ps1.time")
    timestamps_world = decode_timestamp(recording_folder + "/PI world v1 ps1.time")
    timestamps_left = timestamps_left - timestamps_left[0]
    timestamps_right = timestamps_right - timestamps_right[0]
    timestamps_world = timestamps_world - timestamps_world[0]
    timestamps = [timestamps_left, timestamps_right, timestamps_world]
    
    nb_of_timestamps_left = len(timestamps_left)
    nb_of_timestamps_right = len(timestamps_right)
    nb_of_timestamps_world = len(timestamps_world)

    nb_of_timestamps = [nb_of_timestamps_left, nb_of_timestamps_right, nb_of_timestamps_world]

    try:
        for folder in camera_folders:
            os.mkdir(recording_folder + "/" + folder)
    except:
        pass

    for i in range(len(camera_names)):
        input_file = os.path.join(recording_folder + '/' +  camera_names[i] + ".mp4")
        output_folder = os.path.join(recording_folder +'/'+ camera_folders[i])
        #extract_one_camera(input_file, output_folder, nb_of_timestamps[i])
        extract_one_camera_using_timestamps(input_file, output_folder, timestamps[i])

#extract_frames('9480f94c-6052-4d26-86b7-f2383bf34de3')