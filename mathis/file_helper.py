import zipfile
import io 
import os
from shutil import copy,move
import datetime
from constants import *
import numpy as np

def decode_timestamp(timestamp_path):
    ts = np.fromfile(timestamp_path, dtype=np.uint64)
    return ts

def unzip_and_move_to_parent(response, parent_folder):
    z = zipfile.ZipFile(io.BytesIO(response))
    z.extractall(parent_folder)
    subfolder_name = os.listdir(parent_folder + "/")[0]
    #TODO: this implementation does not work: it creates too many / in the path
    #subfolder_name = z.filelist[0].filename.split(os.sep)[0]
    #move all files to parent folder and delete folder
    for filename in os.listdir(os.path.join(parent_folder, subfolder_name)):
        move(os.path.join(parent_folder, subfolder_name, filename), os.path.join(parent_folder, filename))
    os.rmdir(os.path.join(parent_folder, subfolder_name))

def get_system_start_ts(recording_id):
    event_name = "manual_clock_offset_correction"
    recording_foler = os.path.join(recordings_folder, recording_id)
    zipped_name = recording_foler + "/android.log.zip"
    with zipfile.ZipFile(zipped_name) as zipped_folder:
        data = zipped_folder.read('android.log').decode('utf-8').splitlines()
    for line in data:
        if event_name in line:
            return int(line.split(" ")[-1])
    print("Could not find event {} in android.log".format(event_name))

def copy_frames_to_new_folder(from_path, to_path, step=1):
    for file in os.listdir(from_path):
        if int(file.split(".")[0]) % step == 0:
            try:
                copy(os.path.join(from_path, file), to_path)
            except:
                pass
"""
def get_start_time_from_text(recording_id, text):
    get the start time of the recording  of the event from the android log
    #recording_foler = recordings_folder + recording_id
    zipped_name = recording_foler + "/android.log.zip"
    current_year = datetime.date.today().year

    with zipfile.ZipFile(zipped_name) as zipped_folder:
        data = zipped_folder.read('android.log').decode('utf-8').splitlines()
    #get the start time of the recording
    for line in data:
        if text in line:
            recording_start_time = line.split(" ")[1]
            recording_date = line.split(" ")[0] + "-" + str(current_year)
            recording_timestamp = recording_date + " " + recording_start_time
            #convert time to nanoseconds from "%m-%d-%Y %H:%M:%S.%f"
            return int(datetime.datetime.strptime(recording_timestamp, "%m-%d-%Y %H:%M:%S.%f").timestamp() * 10e8)

def get_first_frame_time(recording_id):
    start_times = {}

    camera_names_short = [camera_name[:-4] for camera_name in camera_names] #remove ps1 from the camera names
    devices = camera_names_short + ["Gaze"]
    for device in devices:
        text = "MainActivity: updateDevice:actionType=1200, status=DeviceInfo({}/active)".format(device) #changed action type from 1000 to 1200
        start_times[device] = get_start_time_from_text(recording_id, text)
        #start_times['first_event_android_time'] = get_start_time_from_text("Deserialized event name manual_clock_offset_correction timestamp")
    return start_times

"""