#include API key, recordings folder, camera names...
import getpass
import socket

#include API key, recordings folder, camera names...
camera_names = ["PI left v1 ps1", "PI right v1 ps1", "PI world v1 ps1"]
camera_folders = ["PI_left_v1_ps1", "PI_right_v1_ps1", "PI_world_v1_ps1","rgb_pngs"]
workspace_id = "9ae5e987-5235-486f-8552-427014bbedcd"
indices_names = ["left_eye_idx", "right_eye_idx", "world_idx", "depth_camera_idx"]
columns_to_remove = ['section id','gaze x [px]','gaze y [px]','worn','fixation id','blink id','azimuth [deg]','elevation [deg]']
files_to_export = ['imu.csv']
folders_to_export = ['colmap_EM_export']

username = getpass.getuser()
host = socket.gethostname()
if username == 'nipopovic' and host == 'archer':
    recordings_folder = "/home/nipopovic/MountedDirs/aegis_cvl/aegis_cvl_root/data/data_collection/test_recordings/"
    #recordings_folder = "/home/nipopovic/MountedDirs/aegis_cvl/aegis_cvl_root/data/data_collection/recordings/"
elif username == 'Mathis':
    recordings_folder = "C:/Users/Mathis/Documents/GitHub/gaze_data_acquisition/mathis/recordings/"
elif username == 'mathi':
    recordings_folder = "C:/Users/mathi/Documents/GitHub/gaze_data_acquisition/mathis/recordings/"
    exports_folder = "C:/Users/mathi/Documents/GitHub/gaze_data_acquisition/mathis/exports/"
elif username == "mlindner":
    #recordings_folder = "/scratch_net/snapo/mlindner/docs/gaze_data_acquisition/oos/recordings"
    scratch_net_folder_tmp = "/scratch_net/snapo/mlindner/tmp" #this folder is to run colmap, which is why it s in the scratch net!
    recordings_folder = "/srv/beegfs02/scratch/aegis_cvl/data/data_collection/recordings"
    exports_folder = "/srv/beegfs02/scratch/aegis_cvl/data/data_collection/exports"
    #recordings_folder = "/scratch_net/snapo/mlindner/recordings"
else:
    raise AssertionError