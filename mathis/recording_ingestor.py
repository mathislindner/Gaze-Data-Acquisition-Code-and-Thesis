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
#TODO import from constants instead of the init arguments
class  recordingDownloader:
    def __init__(self, recording_id, api):
        #FIXME create api object here and remove argument from init
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
        print("Curating recording:" + str(self.recording_id))

 
    def curate_recording(self):
        #TODO: remove unecessary files
        #if path exists, don t curate
        if os.path.exists(self.recording_folder + "/left_eye_frames/0.png"):
            print("Recording already curated")
            return
        #extract frames

        extract_frames(self.recording_id)
        correspond_cameras_and_gaze(self.recording_id)
        pass
