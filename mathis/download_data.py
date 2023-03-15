#https://cloud.pupil-labs.com/workspace/9ae5e987-5235-486f-8552-427014bbedcd/recordings

from pupilcloud import Api, ApiException

from recording_ingestor import recordingIngestor

#API object for all the requests, #FIXME: put in a config file
api = Api(api_key="K2xko4e9Vt9VXTuThUngAG2yKTW2ZRcenhEFe9K4tiSA", host="https://api.cloud.pupil-labs.com", downloads_path="mathis/recordings")
recordings_folder = "mathis/recordings/"

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

##############################################################################################
#process all recordings 
# created an object for this because it should be easier to implement multiprocessing
#TODO: implement multiprocessing
def process_all_recordings():
    recording_ids = get_recordings()
    for recording_id in recording_ids:
        recording_processor = recordingIngestor(recording_id, recordings_folder, api)
        recording_processor.process_recording()

process_all_recordings()