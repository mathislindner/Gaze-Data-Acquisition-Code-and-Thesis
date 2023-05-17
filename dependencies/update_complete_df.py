#this takes all the dataframes and combines them into one big dataframe with recording_id and user_id as the index
from constants import *
import pandas as pd
import os
import json

def update_complete_df():
    #complete_df_path = os.path.join(recordings_folder, "complete_df.csv")
    #if not os.path.exists(complete_df_path):
    #    complete_df = pd.read_csv(complete_df_path)
    
    smaller_dfs =[]
    for recording in os.listdir(recordings_folder):
        try:
            recordings_df = pd.read_csv(os.path.join(recordings_folder, recording, "full_df.csv"))
            user_id = json.load(open(os.path.join(recordings_folder, recording, "wearer.json")))["uuid"]
            recordings_df["user_id"] = user_id
            #add user id for every row

            smaller_dfs.append(recordings_df)
        except:
            print("Recording " + recording + " has no full_df.csv file")
            continue

    complete_df = pd.concat(smaller_dfs)
    #change _idx to integers
    complete_df["left_eye_idx"] = complete_df["left_eye_idx"].astype(int)
    complete_df["right_eye_idx"] = complete_df["right_eye_idx"].astype(int)
    complete_df["world_idx"] = complete_df["world_idx"].astype(int)
    complete_df["imu_idx"] = complete_df["imu_idx"].astype(int)

    print(complete_df.head())
    complete_df.to_csv(os.path.join(recordings_folder, "complete_df.csv"), index = False)

update_complete_df()

    