import os
import shutil
from_path = r"C:\Users\mathi\Documents\GitHub\gaze_data_acquisition\mathis\recordings\50bd29b9-0ef2-425c-8f78-b9275ce3f32f\PI_world_v1_ps1_undistorted"
to_path = r"C:\Users\mathi\Documents\GitHub\gaze_data_acquisition\mathis\colmap_testing\colmap_ws_aegis_room\images"

#move every 50th images from from_path to to_path
for i, file in enumerate(os.listdir(from_path)):
    if i % 25 == 0:
        shutil.copy(os.path.join(from_path, file), to_path)


    