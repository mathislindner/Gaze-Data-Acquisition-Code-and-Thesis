import sys
sys.path.append("/scratch_net/snapo/mlindner/docs/gaze_data_acquisition")
from dependencies.constants import *
import os
import json

def get_wearer_id_and_name(recording_id):
    wearer_dict = json.load(open(os.path.join(recordings_folder, recording_id, "wearer.json")))
    return wearer_dict["uuid"], wearer_dict["name"]

def print_wearer_ids_and_names():
    #uniquely print wearer ids and names
    wearer_ids_and_names = []
    for recording_id in os.listdir(recordings_folder):
        if os.path.exists(os.path.join(recordings_folder, recording_id, "wearer.json")):
            wearer_id, wearer_name = get_wearer_id_and_name(recording_id)
            if (wearer_id, wearer_name) not in wearer_ids_and_names:
                wearer_ids_and_names.append((wearer_id, wearer_name))
                print(wearer_id, wearer_name)

    

if __name__ == "__main__":
    print_wearer_ids_and_names()