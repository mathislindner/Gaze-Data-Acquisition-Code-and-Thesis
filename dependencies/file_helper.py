import zipfile
import os
from shutil import copy,move,rmtree
try:
    from dependencies.constants import *
except ModuleNotFoundError:
    from constants import *
import numpy as np

def decode_timestamp(timestamp_path):
    ts = np.fromfile(timestamp_path, dtype=np.uint64)
    return ts

def move_subfolder_content_to_parent(downloads_path):
    parent_path = os.path.dirname(downloads_path)
    #get subfolder name
    for files in os.listdir(downloads_path):
        if os.path.isdir(os.path.join(downloads_path, files)):
            subfolder_name = files
    subfolder_files_names = os.listdir(os.path.join(downloads_path, subfolder_name))
    #move all files to parent folder and delete folder
    for filename in subfolder_files_names:
        move(os.path.join(downloads_path, subfolder_name, filename), os.path.join(parent_path, filename))
    #delete subfolder using shutil.rmtree (os.rmdir only works for empty folders)
    rmtree(downloads_path)

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