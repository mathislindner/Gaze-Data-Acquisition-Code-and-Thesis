import pandas as pd
import matplotlib.pyplot as plt
from constants import *
import os

def plot_gaze_on_world(recording_id, idx):
    recording_folder = os.path.join(recordings_folder,str(recording_id))
    print("plotting gaze on world")
    #load gaze data
    full_df = pd.read_csv(os.path.join(recording_folder, "full_df.csv"))
    #load world data
    world_frame = full_df["world_idx"][idx]
    world_frame_path = os.path.join(recording_folder, "PI_world_v1_ps1", str(world_frame) + ".png")
    print("world frame path: ", world_frame_path)
    world_camera_image = plt.imread(world_frame_path)

    #load gaze data
    gaze_x = full_df["gaze x [px]"][idx]
    gaze_y = full_df["gaze y [px]"][idx]

    print("gaze x: ", gaze_x)
    print("gaze y: ", gaze_y)
    #plot gaze
    plt.imshow(world_camera_image)
    plt.scatter(gaze_x, gaze_y, color="red", s=50)
    plt.show()

plot_gaze_on_world("a0df90ce-1351-45bb-af10-72f91e67c43e", 1000)
plot_gaze_on_world("a0df90ce-1351-45bb-af10-72f91e67c43e", 3000)
