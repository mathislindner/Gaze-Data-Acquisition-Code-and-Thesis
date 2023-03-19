#https://cloud.pupil-labs.com/workspace/9ae5e987-5235-486f-8552-427014bbedcd/recordings
#this script should run in the background and download all the recordings periodically and process them

from pupilcloud import Api, ApiException
from recording_ingestor import recordingDownloader, recordingCurator
import os
import multiprocessing

#API object for all the requests, #FIXME: put in a config file, and create api object in the recording ingestor
api = Api(api_key="K2xko4e9Vt9VXTuThUngAG2yKTW2ZRcenhEFe9K4tiSA", host="https://api.cloud.pupil-labs.com", downloads_path="mathis/recordings")
recordings_folder = "mathis/recordings/"

# Returns a list of recordings
def get_recordings():
    recordings = api.get_recordings().result #probs have to extract id's
    recording_ids = [recording.id for recording in recordings]
    return recording_ids

##############################################################################################

def download_all_recordings_multiprocessing():
    recording_ids = get_recordings()
    pool = multiprocessing.Pool(processes=4)
    pool.map(download_recording, recording_ids)

def download_recording(recording_id):
    recording_downloader = recordingDownloader(recording_id, api)
    recording_downloader.download_recording_and_events()

def curate_all_recordings_multiprocessing():
    # list all folders in recordings folder
    recordings = os.listdir(recordings_folder)
    to_curate = []
    #for each folder check if curated
    for recording in recordings:
        if not os.path.exists(recordings_folder + recording + "/left_eye_frames"): #TODO: make this prettiermaybe? or create metadata file that says if curated or not
            to_curate.append(recording)
    pool = multiprocessing.Pool(processes=4)
    pool.map(curate_recording, to_curate)

def curate_recording(recording_id):
    recording_curator = recordingCurator(recording_id)
    recording_curator.curate_recording()


if __name__ == "__main__":
    download_all_recordings_multiprocessing()
    curate_all_recordings_multiprocessing()
