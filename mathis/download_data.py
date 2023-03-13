#https://cloud.pupil-labs.com/workspace/9ae5e987-5235-486f-8552-427014bbedcd/recordings

from pupilcloud import Api, ApiException
import requests
from io import StringIO
import zipfile
import os


api = Api(api_key="K2xko4e9Vt9VXTuThUngAG2yKTW2ZRcenhEFe9K4tiSA", host="https://api.cloud.pupil-labs.com", downloads_path="mathis/recordings")
recording_folder = "mathis/recordings/"
try:
    # Returns the current logged in user based on auth token
    user = api.get_profile().result
    print('Sucessfully logged in as: %s' % user.email)
except ApiException as e:
    print("Exception when calling AuthApi->get_profile: %s\n" % e)

# Returns a list of recordings
def get_recordings():
    recordings = api.get_recordings().result #probs have to extract id's
    recording_ids = [recording.id for recording in recordings]
    return recording_ids

#object to process one recording
class  Recording_Processor:
    def __init__(self, recording_id):
        self.recording_id = recording_id

    # process recording by id
    def process_recording(self):
        self.download_recording()
        #self.curate_recording(recording_id)

    #download recording by id 
    def download_recording(self):
        #check if recording already downloaded
        if os.path.exists(recording_folder + '/' + str(self.recording_id)):
            print("Recording already downloaded")
            return
        # Download recording files as a zip file in memory
        #TODO: maybe optimize this
        try:
            response = api.download_recording_zip(self.recording_id, _preload_content=False)
            bytes = response.read()
            #create zip file
            with open("mathis/recordings/" + self.recording_id + ".zip", "wb") as f:
                f.write(bytes)
            #unzip file
            with open("mathis/recordings/" + self.recording_id + ".zip", "rb") as data:
                zipped_recording =  zipfile.ZipFile(data)
                os.mkdir(recording_folder + '/' + str(self.recording_id))       
                zipped_recording.extractall(recording_folder + '/' + str(self.recording_id))
            #delete zip file
            os.remove("mathis/recordings/" + self.recording_id + ".zip")

        except ApiException as e:
            print("Exception when calling RecordingsApi->download_recording_zip: %s\n" % e)
        
    #curate recording by id 
    #TODO: implement
    def curate_recording(self):
        #remove unecessary files
        #only keep frames that are 2 seconds after the event
        #remove blinks thanks to file 
        # ~convert video to images
        pass

#process all recordings 
# created an object for this because it should be easier to implement multiprocessing
#TODO: implement
def process_all_recordings():
    recording_ids = get_recordings()
    for recording_id in recording_ids:
        recording_processor = Recording_Processor(recording_id)
        recording_processor.process_recording(recording_id)

#download first recording
recording_processor = Recording_Processor(get_recordings()[0])
recording_processor.process_recording()