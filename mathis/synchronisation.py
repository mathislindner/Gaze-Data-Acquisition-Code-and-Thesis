#create a file that pairs each frame in the world camera with the corresponding frames in the left and right eye cameras in a csv file
#use pupil_positions.csv to get the timestamps of the frames in the world camera and then use the timestamps to find the corresponding frames in the left and right eye cameras
#Need to find a way to synchronize the 2 eye cameras to eachother.
#import pandas as pd
import numpy as np
from constants import camera_names, camera_folders, recordings_folder
import os 
import json

def decode_timestamp(timestamp_path):
    ts = np.fromfile(timestamp_path, dtype=np.uint64)
    return ts

#count the number of frames in each camera
def count_frames(recording_id):
    recording_folder = recordings_folder + str(recording_id)
    frame_counts = []
    for i in range(len(camera_names)):
        frames_folder = recording_folder + "/" + camera_folders[i]
        frames = os.listdir(frames_folder)
        frame_counts.append(len(frames))
    return frame_counts

def convert_camera_timestamps_to_system_time(camera_name, recording_id):
    recording_folder = recordings_folder + str(recording_id)
    timestamp_path = recording_folder + "/" + camera_name + ".time"
    camera_timestamps = decode_timestamp(timestamp_path)
    camera_timestamps_in_system_time = convert_timestamps_to_system_time(recording_id, camera_timestamps)
    return camera_timestamps_in_system_time

#https://docs.pupil-labs.com/developer/core/overview/#convert-pupil-time-to-system-time
def convert_timestamps_to_system_time(recording_id, timestamps):
    #get the start time of the recording
    with open(recordings_folder + recording_id + '/start_time_and_offset.json', 'r') as f:
        # Reading from json file
        recording_info = json.load(f)
    start_time_system = recording_info['start_time_system']
    #FIXME: this assumes that the recording started at the same time than the camera started recording
    first_timestamp = timestamps[0]
    #calculate the offset
    offset = start_time_system - first_timestamp
    # convert the timestamps to system time
    time_stamps_in_system_time = timestamps + offset #add the offset to each timestamp
    return time_stamps_in_system_time

left_timestamps = decode_timestamp("mathis/recordings/902a976b-1f3b-4a2c-b6e4-f40a7aefbb47/PI left v1 ps1.time")
right_timestamps = decode_timestamp("mathis/recordings/902a976b-1f3b-4a2c-b6e4-f40a7aefbb47/PI right v1 ps1.time")
world_timestamps = decode_timestamp("mathis/recordings/902a976b-1f3b-4a2c-b6e4-f40a7aefbb47/PI world v1 ps1.time")

#check if the number of frames in each camera is the same
frame_counts = count_frames("902a976b-1f3b-4a2c-b6e4-f40a7aefbb47")

frame_counts = np.array(frame_counts) - [left_timestamps.shape[0], right_timestamps.shape[0], world_timestamps.shape[0]]
#only the world camera matches, the other have max 6 frames difference, which means 6/200 of a second
print(frame_counts)


