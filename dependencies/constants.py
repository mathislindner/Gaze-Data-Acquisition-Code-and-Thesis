#include API key, recordings folder, camera names...
import getpass
import socket

#include API key, recordings folder, camera names...
camera_names = ["PI left v1 ps1", "PI right v1 ps1", "PI world v1 ps1"]
camera_folders = ["PI_left_v1_ps1", "PI_right_v1_ps1", "PI_world_v1_ps1"]
workspace_id = "9ae5e987-5235-486f-8552-427014bbedcd"
indices_names = ["left_idx", "right_idx", "world_idx"]

username = getpass.getuser()
host = socket.gethostname()
if username == 'nipopovic' and host == 'archer':
    recordings_folder = "/home/nipopovic/MountedDirs/aegis_cvl/aegis_cvl_root/data/data_collection/test_recordings/"
    #recordings_folder = "/home/nipopovic/MountedDirs/aegis_cvl/aegis_cvl_root/data/data_collection/recordings"
elif username == 'Mathis':
    recordings_folder = "C:/Users/Mathis/Documents/GitHub/gaze_data_acquisition/mathis/recordings/"
elif username == 'mathi':
    recordings_folder = "C:/Users/mathi/Documents/GitHub/gaze_data_acquisition/mathis/recordings/"
    exports_folder = "C:/Users/mathi/Documents/GitHub/gaze_data_acquisition/mathis/exports/"
elif username == "mlindner":
    #recordings_folder = "/scratch_net/snapo/mlindner/docs/gaze_data_acquisition/oos/recordings"
    scratch_net_folder_tmp = "/scratch_net/snapo/mlindner/tmp" #this folder is to run colmap, which is why it s in the scratch net!
    recordings_folder = "/srv/beegfs02/scratch/aegis_cvl/data/data_collection/recordings"
else:
    raise AssertionError