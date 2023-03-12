from pupilcloud import Api, ApiException
import zipfile
import os


api = Api(api_key="K2xko4e9Vt9VXTuThUngAG2yKTW2ZRcenhEFe9K4tiSA", host="https://api.cloud.pupil-labs.com")
recording_folder = "mathis/recordings/"
try:
    # Returns the current logged in user based on auth token
    data = api.get_profile().result
    print(data)
except ApiException as e:
    print("Exception when calling AuthApi->get_profile: %s\n" % e)

# Returns a list of recordings
    def get_recordings():
        recording_ids = api.get_recordings().result #probs have to extract id's
        print(recording_ids)
        return recording_ids

#object to process one recording
class  Recording_Processor:
    def __init__(self, recording_id):
        self.recording_id = recording_id

    # process recording by id
    def process_recording(self, recording_id):
        self.download_recording(recording_id)
        self.curate_recording(recording_id)

    #download recording by id 
    def download_recording(self, recording_id):
        #check if recording already downloaded
        if os.path.exists(recording_folder + '/' + str(recording_id)):
            print("Recording already downloaded")
            return
        try:
            # Returns the current logged in user based on auth token
            download = api.download_recording_zip(recording_id).result
        except ApiException as e:
            print("Exception downloading file: %s\n" % e)
        zipped_recording = zipfile.ZipFile(download)
        zipped_recording.extractall(recording_folder + '/' + str(recording_id))
        
    #curate recording by id 
    #TODO: implement
    def curate_recording(self, recording_id):
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