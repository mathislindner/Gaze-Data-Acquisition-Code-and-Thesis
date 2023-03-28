#create a file that pairs each frame in the world camera with the corresponding frames in the left and right eye cameras in a csv file
#use pupil_positions.csv to get the timestamps of the frames in the world camera and then use the timestamps to find the corresponding frames in the left and right eye cameras
#Need to find a way to synchronize the 2 eye cameras to eachother.
#import pandas as pd
import numpy as np
import pandas as pd
from constants import *
import json

def decode_timestamp(timestamp_path):
    ts = np.fromfile(timestamp_path, dtype=np.uint64)
    return ts

def convert_camera_timestamps_to_system_time(camera_name, recording_id):
    recording_folder = recordings_folder + str(recording_id)
    timestamp_path = recording_folder + "/" + camera_name + ".time"
    camera_timestamps = decode_timestamp(timestamp_path)
    camera_timestamps_in_system_time = convert_timestamps_to_system_time(recording_id, camera_timestamps)
    return camera_timestamps_in_system_time

#https://docs.pupil-labs.com/developer/core/overview/#convert-pupil-time-to-system-time
def convert_timestamps_to_system_time(recording_id, timestamps):
    #get the start time of the recording
    with open(recordings_folder + recording_id + '/local_synchronisation.json', 'r') as f:
        # Reading from json file
        recording_info = json.load(f)
    start_time_system = recording_info['system_start_time']
    #FIXME: this assumes that the recording started at the same time than the camera started recording
    first_timestamp = timestamps[0]
    #calculate the offset
    offset = start_time_system - first_timestamp
    # convert the timestamps to system time
    time_stamps_in_system_time = timestamps + offset #add the offset to each timestamp
    return time_stamps_in_system_time

#create a csv file that pairs the gaze timestamps with the world camera, left camera and right eye camera frames.
def correspond_cameras_and_gaze(recording_id):
    recording_folder = recordings_folder + recording_id + "/"
    gaze_df = pd.read_csv(recording_folder + "gaze.csv")
    events_df = pd.read_csv(recording_folder + "events.csv")
    left_timestamps = decode_timestamp(recording_folder + camera_names[0] + ".time")
    right_timestamps = decode_timestamp(recording_folder + camera_names[1] + ".time")
    world_timestamps = decode_timestamp(recording_folder + camera_names[2] + ".time")

    #convert the timestamps to system time
    gaze_df['system_timestamp [ns]'] = convert_timestamps_to_system_time(recording_id, gaze_df['timestamp [ns]'])
    events_df['system_timestamp [ns]'] = convert_timestamps_to_system_time(recording_id, events_df['timestamp [ns]']) 

    left_timestamps = convert_timestamps_to_system_time(recording_id, left_timestamps)
    right_timestamps = convert_timestamps_to_system_time(recording_id, right_timestamps)
    world_timestamps = convert_timestamps_to_system_time(recording_id, world_timestamps)


    #TODO:convert to numpy array to make implementation faster
    #find the closest timestamp in the left and right eye cameras to the gaze timestamps
    left_eye_frames = []
    right_eye_frames = []
    world_frames = []
    events_frames = []
    for gaze_timestamp in gaze_df['system_timestamp [ns]']:
        left_eye_frame = find_closest_frame_to_timestamp(gaze_timestamp, left_timestamps)
        right_eye_frame = find_closest_frame_to_timestamp(gaze_timestamp, right_timestamps)
        world_frame = find_closest_frame_to_timestamp(gaze_timestamp, world_timestamps)
        events_frame = find_closest_frame_to_timestamp(gaze_timestamp, events_df['system_timestamp [ns]']) #TODO: test if it works
        left_eye_frames.append(left_eye_frame)
        right_eye_frames.append(right_eye_frame)
        world_frames.append(world_frame)
        events_frames.append(events_frame)

    #create a new dataframe with the gaze timestamps and the corresponding frames in the left and right eye cameras
    gaze_df['left_eye_frame'] = left_eye_frames
    gaze_df['right_eye_frame'] = right_eye_frames
    gaze_df['world_frame'] = world_frames
    gaze_df['events_frame'] = events_frames
    gaze_df.to_csv(recording_folder + "/gaze_with_frames_and_events.csv")

def find_closest_frame_to_timestamp(gaze_timestamp, camera_timestamps):
    return np.searchsorted(camera_timestamps, gaze_timestamp, side="left")

#TODO:
#from android log file get the start time of the recording and corespong it to the start time of the camera
#use the first timestamp of the camera to calculate the offset
#returns a dictionary with the true first frame start time of the recording and the start time of the camera
def get_first_frame_time(recording_id):
    recording_foler = 'recordings/' + recording_id
    zipped_name = recording_foler + "/android.log.zip"
    start_times  ={}
    current_year = datetime.now().year
    with zipfile.ZipFile(zipped_name) as zipped_folder:
        data = zipped_folder.read('android.log').decode('utf-8').splitlines()
    #get the start time of the recording
    for camera_name in camera_names:
        
        for line in data:
            line_to_search = "MainActivity: updateDevice:actionType=1000, status=DeviceInfo({}/active)".format(camera_name[:-4])
            if line_to_search in line:
                recording_start_time = line.split(" ")[1]
                recording_date = line.split(" ")[0] + "-" + str(current_year)
                recording_timestamp = recording_date + " " + recording_start_time
                print(recording_timestamp)
                #convert time to nanoseconds from "%m-%d-%Y %H:%M:%S.%f"
                start_times['{} recording_start_time'.format(camera_name)] = int(datetime.strptime(recording_timestamp, "%m-%d-%Y %H:%M:%S.%f").timestamp() * 1e9)
    return start_times

#correspond_cameras_and_gaze("82e52db9-1cac-495d-99dd-bebb51c393a0")

