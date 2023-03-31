import zipfile
import io 
import os
from shutil import move
import datetime
from constants import *
import numpy as np

def decode_timestamp(timestamp_path):
    ts = np.fromfile(timestamp_path, dtype=np.uint64)
    return ts

def unzip_and_move_to_parent(response, parent_folder):
    z = zipfile.ZipFile(io.BytesIO(response))
    z.extractall(parent_folder)
    #subfolder_name = os.listdir(parent_folder + "/")[0]
    subfolder_name = z.filelist[0].filename.split(os.sep)[0]
    #move all files to parent folder and delete folder
    for filename in os.listdir(os.path.join(parent_folder, subfolder_name)):
        move(os.path.join(parent_folder, subfolder_name, filename), os.path.join(parent_folder, filename))
    os.rmdir(os.path.join(parent_folder, subfolder_name))


def get_start_time_from_text(recording_id, text):
    """
    get the start time of the recording  of the event from the android log
    """
    recording_foler = recordings_folder + recording_id
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
def unzip_and_move_to_parent(response, parent_folder):
    z = zipfile.ZipFile(io.BytesIO(response))
    z.extractall(parent_folder)
    subfolder_name = os.listdir(parent_folder + "/")[0]
    #move all files to parent folder and delete folder
    for filename in os.listdir(os.path.join(parent_folder, subfolder_name)):
        move(os.path.join(parent_folder, subfolder_name, filename), os.path.join(parent_folder, filename))
    os.rmdir(os.path.join(parent_folder, subfolder_name))
"""
"""
#TODO: this 
def extract_one_camera_using_timestamps(input_file, output_folder, timestamps):
    #convert nanoseconds timestamps to seconds
    timestamps = timestamps / 1000000000
    #extract 100 frames at a time until all frames are extracted
    nb_of_frames = len(timestamps)
    nb_of_frames_per_batch = 100
    nb_of_batches = nb_of_frames // nb_of_frames_per_batch
    #use the ffmpeg python wrapper to extract frames
    for i in range(nb_of_batches):
        (
            ffmpeg
            .input(input_file, ss=timestamps[i * nb_of_frames_per_batch], t=timestamps[(i+1) * nb_of_frames_per_batch])
        ).output(output_folder + "/" + "%d.png", start_number=i * nb_of_frames_per_batch, vframes=nb_of_frames_per_batch, vsync = 2, loglevel="quiet").run()
        
    
#TODO:remove this when the other one works
def extract_one_camera(input_file, output_folder, n_of_frames):
    n_of_frames = ffmpeg.probe(input_file)['streams'][0]['nb_frames'] 
    print(input_file)
    (
        ffmpeg
        .input(input_file)
    ).output(output_folder + "/" + "%d.png", start_number=0, vframes=n_of_frames, vsync = 2, vf = "showinfo").run() #loglevel = 0

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

    
    for folder in camera_folders:
        os.mkdir(recording_folder + "/" + folder)

    for i in range(len(camera_names)):
        input_file = os.path.join(recording_folder + '/' +  camera_names[i] + ".mp4")
        output_folder = os.path.join(recording_folder +'/'+ camera_folders[i])
        extract_one_camera(input_file, output_folder, nb_of_timestamps[i])
        #extract_one_camera_using_timestamps(input_file, output_folder, timestamps[i])

extract_frames('82e52db9-1cac-495d-99dd-bebb51c393a0')
"""