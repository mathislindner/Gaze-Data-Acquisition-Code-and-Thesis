import os
import pandas as pd
from synchronisation import correspond_cameras_and_gaze
from pupilcloud import Api, ApiException
from constants import *
import requests
import os
from file_helper import unzip_and_move_to_parent #, extract_frames
from frames_extractor import extract_frames

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
        correspond_cameras_and_gaze(self.recording_id)
        pass

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
        first_event_occurences = full_df.groupby("event").first()["timestamp [ns]"]
        #after event seen for the first time in the full_df, skip 0.1 seconds and take the next 2 seconds
        timestamps_start = first_event_occurences + 100000000 
        timestamps_end = timestamps_start + 2000000000
        for timestamp_start, timestamp_end in zip(timestamps_start, timestamps_end):
            #get the frames in the time interval
            frames = full_df[(full_df["timestamp [ns]"] > timestamp_start) & (full_df["timestamp [ns]"] < timestamp_end)]
            for camera_name in camera_names:
                frames = frames[frames["camera"] == camera_name] #FIXME: left_idx ... right_idx ... world_idx                
                #create folder for the camera
                camera_export_folder = os.path.join(self.export_folder, camera_name)
                if not os.path.exists(camera_export_folder):
                    os.mkdir(camera_export_folder)
                #copy frames to the export folder
                for frame in frames["frame"]:
                    frame_path = os.path.join(self.recording_folder, camera_name.replace(" ","_"), str(frame) + ".png")
                    #print(frame_path)
                    os.system("copy " + frame_path + " " + camera_export_folder)
        
#recording_exporter = recordingExporter("a0df90ce-1351-45bb-af10-72f91e67c43e")
#recording_exporter.export_recording()