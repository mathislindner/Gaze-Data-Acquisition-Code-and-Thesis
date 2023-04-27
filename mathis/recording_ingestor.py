import os
import pandas as pd
from synchronisation import correspond_cameras_and_gaze
from pupilcloud import Api, ApiException
from constants import *
import requests
import json
from file_helper import unzip_and_move_to_parent #, extract_frames
from frames_extractor import extract_frames, extract_depth_camera_frames, undistort_world_camera
from colmap_executer import run_colmap
#object to download process one recording
class  recordingDownloader:
    def __init__(self, recording_id, api):
        self.workspace_id = workspace_id
        self.recording_id = recording_id
        self.recording_folder = recordings_folder + '/' + str(self.recording_id) 
        self.api_key = "K2xko4e9Vt9VXTuThUngAG2yKTW2ZRcenhEFe9K4tiSA"
        self.api = api
    # process recording by id
    def download_recording_and_events(self):
        #check if recording already downloaded
        if os.path.exists(self.recording_folder +"/"+ camera_names[0] + ".mp4"):
            print("Recording already downloaded")
            return
        #TODO: check if recording has been processed in the pupil cloud
        self.download_videos()
        self.download_timeseries()

    #download and extract recording by id  
    def download_videos(self):
        # Download recording files as a zip file in memory
        try:
            response = self.api.download_recording_zip(self.recording_id, _preload_content=False)

            unzip_and_move_to_parent(response.read(), self.recording_folder)
        except ApiException as e:
            print("Exception when calling RecordingsApi->download_recording_zip: %s\n" % e)

    #unfortunately, the timeseries data is not available in the pupil cloud api, so we have to make it through a request
    def download_timeseries(self):
        timeseries_data_link = "https://api.cloud.pupil-labs.com/v2/workspaces/{}/recordings:raw-data-export?ids=".replace("{}", self.workspace_id)
        try :
            response = requests.get(url = timeseries_data_link  + str(self.recording_id), headers =  {"api-key": self.api_key}, stream=True)
        except:
            print("couldn t get timeseries data")
        unzip_and_move_to_parent(response.content, self.recording_folder)

class recordingCurator:
    def __init__(self, recording_id):
        self.recording_id = recording_id
        self.recording_folder = os.path.join(recordings_folder,str(self.recording_id))
 
    def curate_recording(self):
        #if path exists, don t curate
        #TODO: move the path checking function from extract frames to here
        frames_path = os.path.join(self.recording_folder, camera_names[0].replace(" ","_"), "0.png")
        #if os.path.exists(frames_path): #already in the exctract frames function
        #    print("Recording already curated")
        #    return
        
        #else extract frames
        extract_frames(self.recording_id)
        extract_depth_camera_frames(self.recording_id)
        correspond_cameras_and_gaze(self.recording_id)
        undistort_world_camera(self.recording_id)
        #run COLMAP on the world camera frames
        #run_colmap(self.recording_id)

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
            
                
                
        
        
#recording_exporter = recordingExporter("a0df90ce-1351-45bb-af10-72f91e67c43e")
#recording_exporter.export_recording()