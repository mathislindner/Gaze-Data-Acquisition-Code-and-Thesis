#https://cloud.pupil-labs.com/workspace/9ae5e987-5235-486f-8552-427014bbedcd/recordings
#this script should run in the background and download all the recordings periodically and process them
#TODO:rename this file since we are not just procssing pupil cloud data, but also depth camera data

from pupilcloud import Api, ApiException
from dependencies.recording_ingestor import recordingDownloader, recordingCurator, recordingExporter
from dependencies.constants import *
import os
import multiprocessing
import yaml
from yaml.loader import SafeLoader

with open("configuration.yaml", 'r') as f:
    config = yaml.load(f, Loader=SafeLoader)
api_key = str(config["API_KEY"])
#API object for all the requests
try:
    api = Api(api_key=api_key, host="https://api.cloud.pupil-labs.com")
    print(api.get_profile().status)
except:
    print("couldn't connect to pupil cloud")
# Returns a list of recordings
#FIXME do not include unprocessed recordings (unprocessed in the cloud) (or do a try except in the download function)
def get_recordings():
    recordings = api.get_recordings().result 
    recording_ids = [recording.id for recording in recordings if recording.is_viewable == True]
    return recording_ids

##############################################################################################



def download_recording(recording_id):
    recording_downloader = recordingDownloader(recording_id, api)
    recording_downloader.download_recording_and_events()

def curate_recording(recording_id):
    recording_curator = recordingCurator(recording_id)
    recording_curator.curate_recording()

def export_recording(recording_id):
    recording_exporter = recordingExporter(recording_id)
    recording_exporter.export_recording()


def download_all_recordings():
    recording_ids = get_recordings()
    for recording_id in recording_ids:
        download_recording(recording_id)

def curate_all_recordings():
    # list all folders in recordings folder
    recordings = os.listdir(recordings_folder)
    #only get the recording ids
    recordings = [recording.split("/")[-1] for recording in recordings]
    to_curate = []
    #for each folder check if curated
    for recording in recordings:
        recording = os.path.join(recordings_folder, recording)
        #cannot synchronize if there is no local_synchronization file!
        local_synchronization_file = os.path.join(recording, "local_synchronisation.json")
        if not os.path.exists(os.path.join(recording,'curated.txt')) and os.path.exists(local_synchronization_file):
            recording_id = recording.split("/")[-1]
            to_curate.append(recording_id)
    for recording in to_curate:
        curate_recording(recording)

def export_all_recordings():
    curated_recordings = os.listdir(recordings_folder)
    #if curated.txt is in the folder, then it is curated
    curated_recordings = [recording for recording in curated_recordings if os.path.exists(os.path.join(recordings_folder, recording, 'curated.txt'))]
    for recording in curated_recordings:
        export_recording(recording)

def download_all_recordings_multiprocessing():
    recording_ids = get_recordings()
    pool = multiprocessing.Pool(processes=4)
    pool.map(download_recording, recording_ids)

def curate_all_recordings_multiprocessing():
    # list all folders in recordings folder
    recordings = os.listdir(recordings_folder)
    #only get the recording ids
    recordings = [recording.split("/")[-1] for recording in recordings]
    to_curate = []
    #for each folder check if curated
    for recording in recordings:
        recording = os.path.join(recordings_folder, recording)
        #cannot synchronize if there is no local_synchronization file!
        local_synchronization_file = os.path.join(recording, "local_synchronisation.json")
        if not os.path.exists(os.path.join(recording,"PI_left_v1_ps1","0" + ".png")) and os.path.exists(local_synchronization_file): #TODO: make this prettiermaybe? or create metadata file that says if curated or not
            recording_id = recording.split("/")[-1]
            to_curate.append(recording_id)
    pool = multiprocessing.Pool(processes=4)
    pool.map(curate_recording, to_curate)


#print current directory
if __name__ == "__main__":
    download_all_recordings()
    #TODO check if all necessary files are there before curating
    curate_all_recordings()
    export_all_recordings()
    #download_recording('b6a73239-5f5b-4fad-ad65-fcefb27ba4d8')
    #curate_recording('b6a73239-5f5b-4fad-ad65-fcefb27ba4d8')
    #download_all_recordings_multiprocessing()
    #curate_all_recordings_multiprocessing()
    #export_all_recordings_multiprocessing()

