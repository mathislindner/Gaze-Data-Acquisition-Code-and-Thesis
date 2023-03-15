import os
from shutil import move
from pupilcloud import Api, ApiException
import requests
import zipfile
import os
#object to download process one recording
class  recordingIngestor:
    def __init__(self, recording_id, recordings_folder, api):
        self.recording_id = recording_id
        self.recording_folder = recordings_folder + '/' + str(self.recording_id) 
        self.api = api
    # process recording by id
    def process_recording(self):
        self.download_recording_videos()
        self.download_recording_events()
        self.curate_recording()

    #download and extract recording by id
    #TODO: use os.path.join instead of + for paths     
    def download_recording_videos(self):
        #check if recording already downloaded
        if os.path.exists(self.recording_folder):
            print("Recording already downloaded")
            return
        # Download recording files as a zip file in memory
        #TODO: maybe optimize this
        try:
            response = self.api.download_recording_zip(self.recording_id, _preload_content=False)
            bytes = response.read()
            #create zip file
            with open(self.recording_folder + ".zip", "wb") as f:
                f.write(bytes)
            #unzip file
            with open(self.recording_folder + ".zip", "rb") as data:
                zipped_recording =  zipfile.ZipFile(data)
                os.mkdir(self.recording_folder)      
                ############################################
                zipped_recording.extractall(self.recording_folder + "/") #extract("new_hello.txt", path="output_dir/")
                #move all files to parent folder and delete folder
                subfolder_name = os.listdir(self.recording_folder + "/")[0]
                for filename in os.listdir(os.path.join(self.recording_folder, subfolder_name)):
                    move(os.path.join(self.recording_folder, subfolder_name, filename), os.path.join(self.recording_folder, filename))
                os.rmdir(os.path.join(self.recording_folder, subfolder_name))
            #delete zip file
            os.remove(self.recording_folder + ".zip")
            print("Recording downloaded:" + str(self.recording_id))
        except ApiException as e:
            print("Exception when calling RecordingsApi->download_recording_zip: %s\n" % e)

    #TODO: using requests because python API somehow give None as response
    def download_recording_events(self):
        #response = self.api.get_recording_events(self.recording_id)
        try :
            response = requests.get(url = "https://api.cloud.pupil-labs.com/recordings/" + str(self.recording_id) + "/events", headers =  {"api-key": "K2xko4e9Vt9VXTuThUngAG2yKTW2ZRcenhEFe9K4tiSA"})
        except ApiException as e:
            print("Exception when calling RecordingsApi->get_recording_events: %s\n" % e)
        events = response.json()
        #save events to file in recording folder
        with open(self.recording_folder + "/events.json", "w") as f:
            f.write(str(events))

    #curate recording by id 
    #TODO: implement
    def curate_recording(self):
        #remove unecessary files
        #only keep frames that are 2 seconds after the event
        #remove blinks thanks to file 
        # ~convert video to images
        pass