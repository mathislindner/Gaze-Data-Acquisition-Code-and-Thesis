import zipfile
import os
from shutil import copy,move,rmtree
try:
    from dependencies.constants import *
except ModuleNotFoundError:
    from constants import *
import numpy as np
import pandas as pd
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
        n = int(file.split(".")[0])
        if n % step == 0:
            try:
                copy(os.path.join(from_path, file), to_path)
            except:
                pass
def copy_frames_to_new_folder_during_event(from_path, to_path, recording_id, step=1):
    #get the df
    recording_folder = os.path.join(recordings_folder, recording_id)
    df = pd.read_csv(os.path.join(recording_folder, "full_df.csv"))
    #remove all the rows were events are nan
    df = df[df['events_idx'].notna()]
    #get indices of the world camera images that were taken at event times world_idx
    indices_of_world_images = df['world_idx'].values
    #only copy frames where the index is in idx
    for file in os.listdir(from_path):
        n = int(file.split(".")[0])
        if n % step == 0 and n in indices_of_world_images:
            try:
                copy(os.path.join(from_path, file), to_path)
            except:
                pass