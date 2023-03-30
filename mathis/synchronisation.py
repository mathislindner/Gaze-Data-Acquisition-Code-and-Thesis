#create a file that pairs each frame in the world camera with the corresponding frames in the left and right eye cameras in a csv file
#use pupil_positions.csv to get the timestamps of the frames in the world camera and then use the timestamps to find the corresponding frames in the left and right eye cameras
#Need to find a way to synchronize the 2 eye cameras to eachother.
#import pandas as pd
import numpy as np
import pandas as pd
from constants import *
import json
import zipfile
import datetime

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
#
def correspond_cameras_and_gaze(recording_id):
    recording_folder = recordings_folder + recording_id + "/"
    gaze_df = pd.read_csv(recording_folder + "gaze.csv")
    events_df = pd.read_csv(recording_folder + "events.csv")
    left_timestamps = decode_timestamp(recording_folder + camera_names[0] + ".time")
    right_timestamps = decode_timestamp(recording_folder + camera_names[1] + ".time")
    world_timestamps = decode_timestamp(recording_folder + camera_names[2] + ".time")

    print("original left timestamps: " + str(left_timestamps[0]))
    #convert the timestamps to system time
    gaze_df['system_timestamp [ns]'] = convert_timestamps_to_system_time(recording_id, gaze_df['timestamp [ns]'])
    events_df['system_timestamp [ns]'] = convert_timestamps_to_system_time(recording_id, events_df['timestamp [ns]']) 

    left_timestamps = convert_timestamps_to_system_time(recording_id, left_timestamps)
    right_timestamps = convert_timestamps_to_system_time(recording_id, right_timestamps)
    world_timestamps = convert_timestamps_to_system_time(recording_id, world_timestamps)

    print("left timestamps in system time: " + str(left_timestamps[0]))
          
    #FIXME: add offset found in log to the timestamps (right eye will be the reference)
    phone_start_times = get_first_frame_time(recording_id)

    reference_point = "Gaze"
    left_offset_to_reference = phone_start_times[reference_point+ "_recording_start_time"] - phone_start_times[camera_names[0][:-4] + "_recording_start_time"]
    right_offset_to_reference = phone_start_times[reference_point + "_recording_start_time"] - phone_start_times[camera_names[1][:-4] + "_recording_start_time"]
    world_offset_to_reference = phone_start_times[reference_point + "_recording_start_time"] - phone_start_times[camera_names[2][:-4] + "_recording_start_time"]
    event_offset_to_reference = phone_start_times[reference_point + "_recording_start_time"] - phone_start_times["events_recording_start_time"]

    print("left offset to reference: " + str(left_offset_to_reference))
    print("right offset to reference: " + str(right_offset_to_reference))
    print("world offset to reference: " + str(world_offset_to_reference))
    print("event offset to reference: " + str(event_offset_to_reference))

    left_timestamps = left_timestamps - left_offset_to_reference
    right_timestamps = right_timestamps - right_offset_to_reference
    world_timestamps = world_timestamps - world_offset_to_reference


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
        events_frame = find_closest_frame_to_timestamp(gaze_timestamp, events_df['system_timestamp [ns]'])
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

#####################################################################################################################################################
#this works for left and right eye cameras, but somehow the timestamp of the world camera is completely off
#TODO: either keep correspond_cameras_and_gaze() or correspond_cameras_and_gaze_2()
def correspond_cameras_and_gaze_2(recording_id):
    recording_folder = recordings_folder + recording_id + "/"

    gaze_df = pd.read_csv(recording_folder + "gaze.csv")
    events_df = pd.read_csv(recording_folder + "events.csv")

    left_timestamps = decode_timestamp(recording_folder + camera_names[0] + ".time")
    right_timestamps = decode_timestamp(recording_folder + camera_names[1] + ".time")
    world_timestamps = decode_timestamp(recording_folder + camera_names[2] + ".time")
    #gaze_timestamps = decode_timestamp(recording_folder + "gaze_200hz.time") #FIXME we don t need the .time file because it is the same as the gaze.csv file
    events_timestamps = decode_timestamp(recording_folder + "event.time")
    # I am assuming that the first timestamp of of events is the timestamp of the event to synchronize the cameras
    phone_times = get_first_frame_time(recording_id=recording_id)

    #offset_left_to_events = phone_times[camera_names[0][:-4] + "_recording_start_time"] - phone_times["first_event_android_time"]
    #offset_right_to_events = phone_times[camera_names[1][:-4] + "_recording_start_time"] - phone_times["first_event_android_time"]
    #offset_world_to_events = phone_times[camera_names[2][:-4] + "_recording_start_time"] - phone_times["first_event_android_time"]
    #offset_gaze_to_events = phone_times["Gaze_recording_start_time"] - phone_times["first_event_android_time"]

    offset_phone_to_pc = phone_times["first_event_android_time"] - phone_times["first_event_pc_time"] 

    #remove offset relative to the first event from all the timestamps and add the first event timestamp to all the timestamps
    #left_timestamps = left_timestamps + offset_left_to_events + offset_phone_to_pc
    #right_timestamps = right_timestamps + offset_right_to_events + offset_phone_to_pc
    #world_timestamps = world_timestamps + offset_world_to_events + offset_phone_to_pc
    #gaze_timestamps = gaze_timestamps - offset_gaze_to_events + offset_phone_to_pc
    #events_df['system_timestamp [ns]'] = events_df['timestamp [ns]'] - offset_gaze_to_events + offset_phone_to_pc
    #gaze_df['system_timestamp [ns]'] = gaze_df['timestamp [ns]'] + offset_phone_to_pc #FIXME not sure if this is correct, the offset is not the same as the one for the events bc it doesn t need to travel through the internet
    #events_timestamps = events_timestamps + offset_phone_to_pc

    #print("left timestamp offset: " + str(offset_left_to_events/1000000000))
    #print("right timestamp offset: " + str(offset_right_to_events/1000000000))
    #print("world timestamp offset: " + str(offset_world_to_events/1000000000))
    #print("gaze timestamp offset: " + str(offset_gaze_to_events/1000000000))
    #print("events timestamp offset: " + str(offset_phone_to_pc/1000000000))

    left_timestamps = left_timestamps + offset_phone_to_pc
    right_timestamps = right_timestamps + offset_phone_to_pc
    world_timestamps = world_timestamps + offset_phone_to_pc #+ 4366424608
    gaze_df['system_timestamp [ns]'] = gaze_df['timestamp [ns]'] + offset_phone_to_pc
    events_df['system_timestamp [ns]'] = events_df['timestamp [ns]'] + offset_phone_to_pc



    #find the closest timestamp in the left and right eye cameras to the gaze timestamps
    left_eye_frames = []
    right_eye_frames = []
    world_frames = []
    events_frames = []
    for gaze_timestamp in gaze_df['system_timestamp [ns]']:
        left_eye_frame = find_closest_frame_to_timestamp(gaze_timestamp, left_timestamps)
        right_eye_frame = find_closest_frame_to_timestamp(gaze_timestamp, right_timestamps)
        world_frame = find_closest_frame_to_timestamp(gaze_timestamp, world_timestamps)
        events_frame = find_closest_frame_to_timestamp(gaze_timestamp, events_df['system_timestamp [ns]'])
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

    return None

#correspond_cameras_and_gaze_2("82e52db9-1cac-495d-99dd-bebb51c393a0")

def find_closest_frame_to_timestamp(gaze_timestamp, camera_timestamps):
    return np.searchsorted(camera_timestamps, gaze_timestamp, side="left")

#from android log file get the start time of the recording and corespong it to the start time of the camera
#use the first timestamp of the camera to calculate the offset
#returns a dictionary with the true first frame start time of the recording and the start time of the cameras and the first received event
def get_first_frame_time(recording_id):
    recording_foler = recordings_folder + recording_id
    zipped_name = recording_foler + "/android.log.zip"
    start_times  ={}
    current_year = datetime.date.today().year

    with zipfile.ZipFile(zipped_name) as zipped_folder:
        data = zipped_folder.read('android.log').decode('utf-8').splitlines()
    #get the start time of the recording

    camera_names_short = [camera_name[:-4] for camera_name in camera_names] #remove ps1 from the camera names
    devices = camera_names_short + ["Gaze"]
    print(devices)
    for device in devices:
        for line in data:
            line_to_search = "MainActivity: updateDevice:actionType=1200, status=DeviceInfo({}/active)".format(device) #changed action type from 1000 to 1200
            if line_to_search in line:
                recording_start_time = line.split(" ")[1]
                recording_date = line.split(" ")[0] + "-" + str(current_year)
                recording_timestamp = recording_date + " " + recording_start_time
                #convert time to nanoseconds from "%m-%d-%Y %H:%M:%S.%f"
                start_times['{}_recording_start_time'.format(device)] = int(datetime.datetime.strptime(recording_timestamp, "%m-%d-%Y %H:%M:%S.%f").timestamp() * 10e8)
    #get the first event
    for line in data:
        if "Deserialized event name manual_clock_offset_correction timestamp" in line:
            event_start_time = line.split(" ")[1]
            event_date = line.split(" ")[0] + "-" + str(current_year)
            event_timestamp = event_date + " " + event_start_time
            print(event_timestamp)
            #convert time to nanoseconds from "%m-%d-%Y %H:%M:%S.%f"
            start_times['first_event_android_time'] = int(datetime.datetime.strptime(event_timestamp, "%m-%d-%Y %H:%M:%S.%f").timestamp() * 10e8)
            start_times['first_event_pc_time'] = int(line.split(" ")[-1])
    return start_times

correspond_cameras_and_gaze_2("82e52db9-1cac-495d-99dd-bebb51c393a0")

#correspond_cameras_and_gaze("82e52db9-1cac-495d-99dd-bebb51c393a0")

