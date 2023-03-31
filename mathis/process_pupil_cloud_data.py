#https://cloud.pupil-labs.com/workspace/9ae5e987-5235-486f-8552-427014bbedcd/recordings
#this script should run in the background and download all the recordings periodically and process them

from pupilcloud import Api, ApiException
from recording_ingestor import recordingDownloader, recordingCurator
from constants import *
import os
import multiprocessing

#API object for all the requests, #FIXME: put in a config file, and create api object in the recording ingestor
api = Api(api_key="K2xko4e9Vt9VXTuThUngAG2yKTW2ZRcenhEFe9K4tiSA", host="https://api.cloud.pupil-labs.com", downloads_path="mathis/recordings")

# Returns a list of recordings
#FIXME do not include unprocessed recordings (or do a try except in the download function)
def get_recordings():
    recordings = api.get_recordings().result 
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
    #python_file_dir = os.path.dirname(os.path.abspath(__file__))
    recordings = os.listdir(recordings_folder)
    print(recordings_folder)
    to_curate = []
    #for each folder check if curated
    for recording in recordings:
        recording = os.path.join(recordings_folder, recording)
        if not os.path.exists(os.path.join(recording,"PI_left_v1_ps1","0" + ".png")): #TODO: make this prettiermaybe? or create metadata file that says if curated or not
            to_curate.append(recording)
    pool = multiprocessing.Pool(processes=4)
    pool.map(curate_recording, to_curate)

def curate_recording(recording_id):
    recording_curator = recordingCurator(recording_id)
    recording_curator.curate_recording()

#print current directory
if __name__ == "__main__":
    download_all_recordings_multiprocessing()
    curate_all_recordings_multiprocessing()
    #export_all_recordings_multiprocessing()

