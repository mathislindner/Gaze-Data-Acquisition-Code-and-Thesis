import os
import shutil
from_path = r"C:\Users\mathi\Documents\GitHub\gaze_data_acquisition\mathis\recordings\3026e32b-3e15-40a7-9a46-8e8512cdfe5c\PI_world_v1_ps1_undistorted"
to_path = r"C:\Users\mathi\Documents\GitHub\gaze_data_acquisition\mathis\colmap_testing\colmap_ws_meeting_room_2\images"

for i, file in enumerate(os.listdir(from_path)):
    if i % 25 == 0:
        shutil.copy(os.path.join(from_path, file), to_path)


    