import os
import pandas as pd
from dependencies.synchronisation import correspond_cameras_and_gaze
from dependencies.constants import *
from dependencies.file_helper import move_subfolder_content_to_parent #, extract_frames
from dependencies.frames_extractor import extract_frames, extract_depth_camera_frames, undistort_world_camera
from dependencies.colmap_executer import run_colmap_automatic_reconstructor, clean_up_temp_and_export_colmap, run_colmap_exhaustive_matcher
from pupilcloud import Api, ApiException
import io
import requests
import json
import zipfile
import yaml
from yaml.loader import SafeLoader

with open("configuration.yaml", 'r') as f:
    config = yaml.load(f, Loader=SafeLoader)
api_key = str(config["API_KEY"])
#object to download process one recording
class  recordingDownloader:
    def __init__(self, recording_id, api):
        self.workspace_id = workspace_id
        self.recording_id = recording_id
        self.recording_folder = recordings_folder + '/' + str(self.recording_id) 
        self.api_key = api_key
        self.api = api
    # process recording by id
    def download_recording_and_events(self):
        #check if recording already downloaded
        if os.path.exists(self.recording_folder +"/"+ camera_names[0] + ".mp4"):
            print("Recording already downloaded")
            return
        #TODO: check if recording has been processed in the pupil cloud
        downloads_path = os.path.join(self.recording_folder, 'downloads')
        self.download_videos(downloads_path)
        self.download_timeseries(downloads_path)
        #move files to parent of parent folder
        move_subfolder_content_to_parent(downloads_path)

    #download and extract recording by id  
    def download_videos(self, downloads_path):
        # Download recording files as a zip file in memory
        try:
            response = self.api.download_recording_zip(self.recording_id, _preload_content=False)
            z = zipfile.ZipFile(io.BytesIO(response.read()))
            z.extractall(downloads_path)
        except ApiException as e:
            print("Exception when calling RecordingsApi->download_recording_zip: %s\n" % e)

    #unfortunately, the timeseries data is not available in the pupil cloud api, so we have to make it through a request
    def download_timeseries(self, downloads_path):
        timeseries_data_link = "https://api.cloud.pupil-labs.com/v2/workspaces/{}/recordings:raw-data-export?ids=".replace("{}", self.workspace_id)
        try :
            response = requests.get(url = timeseries_data_link  + str(self.recording_id), headers =  {"api-key": self.api_key}, stream=True)
        except:
            print("couldn t get timeseries data")
        z = zipfile.ZipFile(io.BytesIO(response.content))
        z.extractall(downloads_path)

class recordingCurator:
    def __init__(self, recording_id):
        self.recording_id = recording_id
        self.recording_folder = os.path.join(recordings_folder,str(self.recording_id))
 
    def curate_recording(self):
        extract_frames(self.recording_id)
        extract_depth_camera_frames(self.recording_id)
        correspond_cameras_and_gaze(self.recording_id)
        undistort_world_camera(self.recording_id)
        #run COLMAP on the world camera frames
        print("Running colmap on recording:" + str(self.recording_id))
        run_colmap_exhaustive_matcher(self.recording_id)
        #run_colmap_automatic_reconstructor(self.recording_id)
        clean_up_temp_and_export_colmap()
        #TODO: use colmap results and laser data to create 3D labeling
        #create a file that says that the recording has been curated
        with open(os.path.join(self.recording_folder, "curated.txt"), "w") as f:
            f.write("This recording has been curated")
            

#Object that does the final exportation of the recording to the final folder (where we only keep the frames where the gaze is looking for 2 seconds...)
class recordingExporter:
    def __init__(self, recording_id):
        self.recording_id = recording_id
        self.recording_folder = os.path.join(recordings_folder,str(self.recording_id))
        self.export_folder = os.path.join(exports_folder,str(self.recording_id))

    def is_already_exported(self):
        if os.path.exists(self.export_folder):
            print("Recording already exported")
            return True
        else:
            return False
        
    def export_recording(self):
        if self.is_already_exported():
            return
        print("Exporting recording:" + str(self.recording_id))
        #create export folder
        #os.mkdir(self.export_folder)
        full_df = pd.read_csv(os.path.join(self.recording_folder, "full_df.csv"),dtype={"event": str}) #importing as string because of NaN values
        first_event_occurences = full_df.groupby("event").first().index.values
        #after event seen for the first time in the full_df, skip 0.1 seconds and take the next 400frames
        timestamps_start = first_event_occurences + 1/200*0.1 #0.1 seconds after the first occurence
        for i in range(len(timestamps_start)):
            sub_df = full_df[full_df.index > timestamps_start[i]].head(400)
            print(sub_df)
            event_folder = os.path.join(self.export_folder, str(i))
            os.mkdir(event_folder)
            #add a csv file with the gaze data
            sub_df.to_csv(os.path.join(event_folder, "gaze_data.csv"), index = False)
            #add wearer information to the folder
            os.system("copy " + os.path.join(self.recording_folder, "wearer.json") + " " + event_folder)
            for camera_folder, indices_name in zip(camera_names, indices_names):
                os.mkdir(path = os.path.join(event_folder, camera_folder))
                #copy frames to new camera folder according to the indices in the sub_df
                camera_frames = sub_df[indices_name]
                for camera_frame in camera_frames:
                    os.system("copy " + os.path.join(self.recording_folder, camera_folder, str(camera_frame) + ".png") + " " + os.path.join(event_folder, camera_folder))
                    
    #TODO: (not used atm) this function would be used differently (not in the the class since it is not related to a specific recording))        
    def export_all_recordings_by_wearer_folder(self):
        #go through all the recordings in the recordings folder and look for wearer.json
        recordings = os.listdir(recordings_folder)
        for recording in recordings:
            user_id = json.load(open(os.path.join(recordings_folder, recording, "wearer.json")))["user_id"]
            #create a folder for the user if it doesn t exist
            try:
                os.mkdir(path = os.path.join(exports_folder, user_id))
            except:
                pass
            #create a subfolder for the recording
            try:
                os.mkdir(path = os.path.join(exports_folder, user_id, recording))
            except:
                pass
            
            #do the same as in the export_recording function
            full_df = pd.read_csv(os.path.join(self.recording_folder, "full_df.csv"),dtype={"event": str}) #importing as string because of NaN values
            first_event_occurences = full_df.groupby("event").first().index.values
            #after event seen for the first time in the full_df, skip 0.1 seconds and take the next 400frames
            timestamps_start = first_event_occurences + 1/200*0.1 #0.1 seconds after the first occurence
            for i in range(len(timestamps_start)):
                sub_df = full_df[full_df.index > timestamps_start[i]].head(400)
                print(sub_df)
                event_folder = os.path.join(self.export_folder, user_id, recording, str(i))
                os.mkdir(path = event_folder)
                #add a csv file with the gaze data
                sub_df.to_csv(os.path.join(event_folder, "gaze_data.csv"), index = False)
                
                for camera_folder, indices_name in zip(camera_names, indices_names):
                    os.mkdir(path = os.path.join(event_folder, camera_folder))
                    #copy frames to new camera folder according to the indices in the sub_df
                    camera_frames = sub_df[indices_name]
                    for camera_frame in camera_frames:
                        os.system("copy " + os.path.join(self.recording_folder, camera_folder, str(camera_frame) + ".png") + " " + os.path.join(event_folder, camera_folder))
            