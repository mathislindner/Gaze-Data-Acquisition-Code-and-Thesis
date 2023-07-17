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
if username == 'yourusername' and host == 'yourhostname':
    scratch_net_folder_tmp = "temporary/folder/for/colmap/called/tmp" #this folder is to run colmap, which is why it s in the scratch net!
    recordings_folder = "/this/one/is/for/your/recordings"
    exports_folder = "/lastly/for/your/exports"
else:
    raise AssertionError