import os
import subprocess
import json
import numpy as np
import pandas as pd

from constants import *


def decode_timestamp(timestamp_path):
    ts = np.fromfile(timestamp_path, dtype=np.uint64)
    return ts

def convert_kwargs_to_cmd_line_args(kwargs):
    """Helper function to build command line arguments out of dict."""
    args = []
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        args.append('-{}'.format(k))
        if v is not None:
            args.append('{}'.format(v))
    return args


def ffprobe_extract_metadata(filename, **kwargs):
    """
    Run ffprobe on the specified file and return a JSON representation of the output.
    https://ffmpeg.org/ffprobe.html
    """
    args =  ['ffprobe', '-show_format', '-show_streams', '-of', 'json']
    args += convert_kwargs_to_cmd_line_args(kwargs)
    args += [filename]

    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        raise RuntimeError

    return json.loads(out.decode('utf-8'))


def ffprobe_extract_timestamps(filename, **kwargs):
    """
    Run ffprobe on the specified file and return a JSON representation of the output.
    https://ffmpeg.org/ffprobe.html
    """
    # ffmpeg-python.probe():
    #args = ['ffprobe', '-show_format', '-show_streams', '-of', 'json']
    #-f lavfi 
    #-i movie={input_file}
    args = ['ffprobe', '-print_format', 'json', '-show_frames', '-show_entries', 'frame=pkt_pts_time'] 
    args += convert_kwargs_to_cmd_line_args(kwargs)
    args += [filename]

    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        raise RuntimeError
    
    json_data = json.loads(out.decode('utf-8'))
    timestamps = [float(x['pkt_pts_time']) for x in json_data['frames']]
    timestamps = np.asarray(timestamps)

    return timestamps


def ffmpeg_extract_frames(filename, out_dir, **kwargs):
    """
    """
    args = ['ffmpeg', '-i', filename, '-vsync', '0', f'{os.path.join(out_dir, "out%d.png")}']  #'-frame_pts', 'true' # '-skip_frame', 'nokey'
    args += convert_kwargs_to_cmd_line_args(kwargs)
    string = 'ffmpeg'
    for x in args[1:]:
        string += ' '+x

    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        raise RuntimeError
    return out.decode('utf-8')


def extract_frames(recording_id):
    recording_folder = os.path.join(recordings_folder, str(recording_id))

    timestamps_time = {}
    timestamps_ffprobe = {}
    metadata_ffprobe = {}
    for cam_i in camera_names:
        cam_i_ = cam_i.replace(' ', '_')
        # # Replace ' ' with '_'
        # os.rename(f"{cam_i}.time", f"{cam_i_}.time")
        # os.rename(f"{cam_i}.mp4", f"{cam_i_}.mp4")
        # cam_i = cam_i_; del cam_i_
        
        # Define all file/folder names
        mp4_file = os.path.join(recording_folder, f"{cam_i}.mp4")
        assert os.path.isfile(mp4_file)
        time_file = os.path.join(recording_folder, f"{cam_i}.time")
        assert os.path.isfile(time_file)
        output_folder = os.path.join(recording_folder, cam_i_)
        
        # Make sure this recording was not already processed
        try:
            os.mkdir(output_folder)
        except:
            raise FileExistsError

        timestamps_time[cam_i_] = decode_timestamp(time_file)
        timestamps_ffprobe[cam_i_] = ffprobe_extract_timestamps(mp4_file)
        metadata_ffprobe[cam_i_] = ffprobe_extract_metadata(mp4_file)

        #np.save(os.path.join(recording_folder, f"{cam_i}.ffprobe"), timestamps_ffprobe[cam_i_])
        timestamps_ffprobe[cam_i_].tofile(os.path.join(recording_folder, f"{cam_i}.ffprobe"))

        out_log = ffmpeg_extract_frames(mp4_file, output_folder)
        num_extracted_frames = len([f for f in os.listdir(output_folder) if os.path.isfile(os.path.join(output_folder, f)) and '.png' in f])

        if not len(timestamps_time[cam_i_]) == len(timestamps_ffprobe[cam_i_]) == num_extracted_frames:
            print(f'Frame count mismathc form {cam_i}:')
            print(f'.time file: {len(timestamps_time[cam_i_])}')
            print(f'ffprobe: {len(timestamps_ffprobe[cam_i_])}')
            print(f'ffmpeg: {num_extracted_frames}')


#https://docs.pupil-labs.com/developer/core/overview/#convert-pupil-time-to-system-time=
def convert_timestamps_to_system_time(recording_id, timestamps):
    #get the start time of the recording
    with open(recordings_folder + recording_id + '/local_synchronisation.json', 'r') as f:
        # Reading from json file
        recording_info = json.load(f)
    start_time_system = recording_info['system_start_time']

    #FIXME: this assumes that the recording started at the same time than the camera started recording
    first_timestamp = timestamps[0]
    #calculate the offset
    offset = start_time_system - first_timestamp
    # convert the timestamps to system time
    time_stamps_in_system_time = timestamps + offset #add the offset to each timestamp
    return time_stamps_in_system_time


def find_element_pairs(seq_1, seq_2):
    '''
    Assumption: Both sequences are in ascending order

    For every element of seq_1, we construct a following row in a table:
    [idx_1, val_1, idx_2_best, val_2_best, error]
    where 2_best corrresponds to the element of seq_2, which is closest to val_1
    and error = abs(val_1-val_2_best)
    '''

    def get_best(curr_diff, best_diff, curr_i, best_i):
        if curr_diff < best_diff:
            return curr_diff, curr_i
        else:
            return best_diff, best_i
        
    push_back = 3
        
    # Pointer initialization
    i_1 = 0
    val_1 = seq_1[i_1]
    i_2 = 0
    val_2 = seq_2[i_2]

    # Skip elements of seq_2 which that are behind the seq_1 pointer (in terms of value).
    while True:
        if val_1 > val_2:
            i_2 += 1
            val_2 = seq_2[i_2]
        else:
            break
    # Send the seq_2 pointer slightly behind the seq_1 pointer (in terms of value).
    i_2 = max(0, i_2 - push_back)
    val_2 = seq_2[i_2]
        
    best_pairs = []
    seq_1_len = len(seq_1)
    seq_2_len = len(seq_2)
    # Iterate over seq_1
    while True:

        # Find best match in seq_2
        best_diff = abs(val_1 - val_2)
        best_i_2 = i_2
        while True:
            curr_diff = abs(val_1 - val_2)
            if val_2 > val_1:
                best_diff, best_i_2 = get_best(curr_diff, best_diff, i_2, best_i_2)
                break
            else:
                best_diff, best_i_2 = get_best(curr_diff, best_diff, i_2, best_i_2)
            
            # Check can the seq_2 pointer be incremented
            if (i_2+1) > (seq_2_len-1):
                break 
            # Check ascending order assumption
            assert seq_2[i_2+1] > seq_2[i_2]
            # Increment seq_2 pointer
            i_2 += 1
            val_2 = seq_2[i_2]

        # Record best pair
        error = abs(val_1 - seq_2[best_i_2])
        best_pairs.append((i_1, val_1, best_i_2, seq_2[best_i_2], error))
        
        # Send the seq_2 pointer slightly behind the seq_1 pointer (in terms of value).
        i_2 = max(0, i_2 - push_back)
        val_2 = seq_2[i_2]
        
        # Check can the seq_1 pointer be incremented
        if (i_1+1) > (seq_1_len-1):
            break 
        # Check ascending order assumption
        assert seq_1[i_1+1] > seq_1[i_1]
        # Increment seq_1 pointer
        i_1 += 1
        val_1 = seq_1[i_1]

    return np.asarray(best_pairs)


def correspond_cameras_and_gaze(recording_id):

    recording_folder = os.path.join(recordings_folder, str(recording_id))

    scale_factor = 10**9
    l_r_res = 1/200
    w_res = 1/30

    gaze_df = pd.read_csv(os.path.join(recording_folder, "gaze.csv"))
    gaze_timestamps = gaze_df.values[:, 2] / scale_factor
    events_df = pd.read_csv(os.path.join(recording_folder, "events.csv"))
    imu_df = pd.read_csv(os.path.join(recording_folder, "imu.csv"))
    imu_timestamps = imu_df.values[:, 2] / scale_factor
    left_timestamps = decode_timestamp(os.path.join(recording_folder, camera_names[0] + ".time")) / scale_factor
    right_timestamps = decode_timestamp(os.path.join(recording_folder, camera_names[1] + ".time")) / scale_factor
    world_timestamps = decode_timestamp(os.path.join(recording_folder, camera_names[2] + ".time")) / scale_factor

    # FIXME sync to computer clock
    left_timestamps_rel = left_timestamps - gaze_timestamps[0]
    right_timestamps_rel = right_timestamps - gaze_timestamps[0]
    world_timestamps_rel = world_timestamps - gaze_timestamps[0]
    gaze_timestamps_rel = gaze_timestamps - gaze_timestamps[0]
    imu_timestamps_rel = imu_timestamps - gaze_timestamps[0]

    best_pairs_gaze_left = find_element_pairs(gaze_timestamps_rel, left_timestamps_rel)
    best_pairs_gaze_right = find_element_pairs(gaze_timestamps_rel, right_timestamps_rel)
    best_pairs_gaze_world = find_element_pairs(gaze_timestamps_rel, world_timestamps_rel)
    best_pairs_gaze_imu = find_element_pairs(gaze_timestamps_rel, imu_timestamps_rel)

    assert gaze_timestamps_rel.shape[0] == best_pairs_gaze_left.shape[0] == best_pairs_gaze_right.shape[0] == best_pairs_gaze_world.shape[0]

    idx_g_l_r_w_i =  np.concatenate((best_pairs_gaze_left[:, 0:1], 
                                     best_pairs_gaze_left[:, 2:3],
                                     best_pairs_gaze_right[:, 2:3],
                                     best_pairs_gaze_world[:, 2:3],
                                     best_pairs_gaze_imu[:, 2:3],
                                     ), axis=1)
    idx_g_l_r_w_i = idx_g_l_r_w_i.astype(np.int64)
    time_g_l_r_w_i =  np.concatenate((best_pairs_gaze_left[:, 1:2], 
                                    best_pairs_gaze_left[:, 3:4],
                                    best_pairs_gaze_right[:, 3:4],
                                    best_pairs_gaze_world[:, 3:4],
                                    best_pairs_gaze_imu[:, 3:4],
                                    ), axis=1)
    
    # Discard when there is a gap bigger than what is expected from sensors frequency
    valid_mask = (best_pairs_gaze_left[:, -1] < l_r_res) * (best_pairs_gaze_right[:, -1] < l_r_res) * (best_pairs_gaze_world[:, -1] < w_res)
    
    idx_g_l_r_w_i = idx_g_l_r_w_i[valid_mask]
    time_g_l_r_w_i = time_g_l_r_w_i[valid_mask]

    return idx_g_l_r_w_i, time_g_l_r_w_i


if __name__ == "__main__":  
    import matplotlib.pyplot as plt  
    import cv2

    def plot_10_images_from_gaze(recording_id, idx_g_l_r_w, time_g_l_r_w, first_left_idx):
        recording_folder = os.path.join(recordings_folder, str(recording_id))

        fig, axs = plt.subplots(3, 10, figsize=(30, 10))
        for i in range(10):
            i_tmp = i + first_left_idx
            left_i = idx_g_l_r_w[i_tmp, 1]
            left_t = time_g_l_r_w[i_tmp, 1]
            left_path = os.path.join(recording_folder, 'PI_left_v1_ps1', f'out{left_i+1}.png')
            assert os.path.isfile(left_path)
            left_img = cv2.imread(left_path)

            right_i = idx_g_l_r_w[i_tmp, 2]
            right_t = time_g_l_r_w[i_tmp, 2]
            right_path = os.path.join(recording_folder, 'PI_right_v1_ps1', f'out{right_i+1}.png')
            assert os.path.isfile(right_path)
            right_img = cv2.imread(right_path)

            world_i = idx_g_l_r_w[i_tmp, 3]
            world_t = time_g_l_r_w[i_tmp, 3]
            world_path = os.path.join(recording_folder, 'PI_world_v1_ps1', f'out{world_i+1}.png')
            assert os.path.isfile(world_path)
            world_img = cv2.imread(world_path)

            axs[0, i].imshow(left_img)
            axs[0, i].set_title(f't={left_t}')
            axs[1, i].imshow(right_img)
            axs[1, i].set_title(f't={right_t}')
            axs[2, i].imshow(world_img)
            axs[2, i].set_title(f't={world_t}')
        plt.savefig('10_frames_debug.png')
        plt.close()

    extract_frames('82e52db9-1cac-495d-99dd-bebb51c393a0')
    idx_g_l_r_w, time_g_l_r_w = correspond_cameras_and_gaze('82e52db9-1cac-495d-99dd-bebb51c393a0')
    # left flash idx: 3943 is 3955 unfiltered

    plot_10_images_from_gaze(recording_id='82e52db9-1cac-495d-99dd-bebb51c393a0', 
                             idx_g_l_r_w=idx_g_l_r_w, 
                             time_g_l_r_w=time_g_l_r_w,
                             first_left_idx=4314) #3943 on # 4318 off

    a = 1