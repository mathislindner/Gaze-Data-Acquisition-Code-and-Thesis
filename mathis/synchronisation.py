#create a file that pairs each frame in the world camera with the corresponding frames in the left and right eye cameras in a csv file
#use pupil_positions.csv to get the timestamps of the frames in the world camera and then use the timestamps to find the corresponding frames in the left and right eye cameras
#Need to find a way to synchronize the 2 eye cameras to eachother.
#import pandas as pd
import numpy as np
import os
import pandas as pd
from constants import *
import json
from file_helper import decode_timestamp, get_system_start_ts

#returns the offset between the pupil labs time and the system time using the android logs command 
def get_offset_from_log(recording_id):
    recording_folder = os.path.join(recordings_folder, str(recording_id))
    #get the start time of the recording
    system_time_start = get_system_start_ts(recording_id)
    system_time_start = int(system_time_start)
    #start_time_system = recording_info['system_start_time']
    event_df = pd.read_csv(os.path.join(recording_folder, 'events.csv'))
    pupil_labs_time = event_df[event_df['name'] == 'recording.begin']['timestamp [ns]'].values[0]

    offset = pupil_labs_time - system_time_start
    return offset

#returns the offset between the pupil labs time and the system time using the local_synchronisation.json file which corresponds to the pupil labs calculated offset at the begining of the recording
def get_offset_from_local_csv(recording_id):
    recording_folder = os.path.join(recordings_folder, str(recording_id))
    local_synchronisation_series = pd.read_json(os.path.join(recording_folder, 'local_synchronisation.json'), typ='series', convert_dates=False)
    offset = local_synchronisation_series['offset']
    return offset

def add_events_from_csv_to_df(recording_id, df):
    recording_folder = os.path.join(recordings_folder, str(recording_id))
    local_synchronisation_series = pd.read_json(os.path.join(recording_folder, 'local_synchronisation.json'), typ='series', convert_dates=False)
    events_series = local_synchronisation_series[local_synchronisation_series.index.str.startswith('Event: ')]
    df['events_idx'] = None
    #whenever the event time is met by the dataframe[timestamp [ns]] then add the event index to the event column for all events until the end of the dataframe
    for event in events_series.index:
        event_time = events_series[event]
        df.loc[df['timestamp [ns]'] >= event_time, 'events_idx'] = event[-1]

    return df

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
            assert seq_2[i_2+1] >= seq_2[i_2]
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


#create a csv file that pairs the gaze timestamps with the world camera, left camera and right eye camera frames.
#
def correspond_cameras_and_gaze(recording_id):
    #check if local synchronisation file exists
    if not os.path.exists(os.path.join(recordings_folder, str(recording_id), 'local_synchronisation.json')):
        print("local synchronisation file does not exist for recording " + str(recording_id))
        return
    recording_folder = recordings_folder + recording_id + "/"
    print("correspond camera and gaze folder" + recording_folder)
    scale_factor = 10**9
    l_r_res = 1/200
    w_res = 1/30

    gaze_df = pd.read_csv(os.path.join(recording_folder, "gaze.csv"))
    gaze_timestamps = gaze_df["timestamp [ns]"].values / scale_factor
    events_df = pd.read_csv(os.path.join(recording_folder, "events.csv"))
    events_timestamps = events_df['timestamp [ns]'] / scale_factor
    imu_df = pd.read_csv(os.path.join(recording_folder, "imu.csv"))
    imu_timestamps = imu_df["timestamp [ns]"].values / scale_factor
    #depth_camera_df = pd.read_csv(os.path.join(recording_folder, "depth_camera_timestamps.csv"))
    #depth_camera_timestamps = depth_camera_df["timestamps"]/scale_factor


    left_timestamps = decode_timestamp(os.path.join(recording_folder, camera_names[0] + ".time")) / scale_factor
    right_timestamps = decode_timestamp(os.path.join(recording_folder, camera_names[1] + ".time")) / scale_factor
    world_timestamps = decode_timestamp(os.path.join(recording_folder, camera_names[2] + ".time")) / scale_factor
    
    depth_camera_footage_bool = os.path.isfile(os.path.join(recording_folder, "depth_camera_timestamps" + ".npy"))
    if depth_camera_footage_bool:
        depth_camera_timestamps = decode_timestamp(os.path.join(recording_folder, "depth_camera_timestamps" + ".npy")) / scale_factor
    else:
        depth_camera_timestamps = left_timestamps

    left_timestamps_rel = left_timestamps - gaze_timestamps[0]
    right_timestamps_rel = right_timestamps - gaze_timestamps[0]
    world_timestamps_rel = world_timestamps - gaze_timestamps[0]
    gaze_timestamps_rel = gaze_timestamps - gaze_timestamps[0]
    events_timestamps_rel = events_timestamps - gaze_timestamps[0]
    imu_timestamps_rel = imu_timestamps - gaze_timestamps[0]
    #to take care of the dummy timestamps

    if depth_camera_footage_bool:
        depth_camera_timestamps_rel = depth_camera_timestamps - gaze_timestamps[0] -  get_offset_from_local_csv(recording_id)/scale_factor #FIXME Check if + or -
    else:
        depth_camera_timestamps_rel = depth_camera_timestamps - gaze_timestamps[0]

    best_pairs_gaze_left = find_element_pairs(gaze_timestamps_rel, left_timestamps_rel)
    best_pairs_gaze_right = find_element_pairs(gaze_timestamps_rel, right_timestamps_rel)
    best_pairs_gaze_world = find_element_pairs(gaze_timestamps_rel, world_timestamps_rel)
    best_pairs_gaze_events = find_element_pairs(gaze_timestamps_rel, events_timestamps_rel)
    best_pairs_gaze_imu = find_element_pairs(gaze_timestamps_rel, imu_timestamps_rel)
    best_pairs_gaze_depth_camera = find_element_pairs(gaze_timestamps_rel, depth_camera_timestamps_rel)

    assert gaze_timestamps_rel.shape[0] == best_pairs_gaze_left.shape[0] == best_pairs_gaze_right.shape[0] == best_pairs_gaze_world.shape[0] == best_pairs_gaze_events.shape[0] == best_pairs_gaze_imu.shape[0] == best_pairs_gaze_depth_camera.shape[0]

    #convert the timestamps to system time
    idx_g_l_r_w_i =  np.concatenate((best_pairs_gaze_left[:, 0:1], 
                                     best_pairs_gaze_left[:, 2:3],
                                     best_pairs_gaze_right[:, 2:3],
                                     best_pairs_gaze_world[:, 2:3],
                                     best_pairs_gaze_imu[:, 2:3],
                                     best_pairs_gaze_events[:, 2:3],
                                     best_pairs_gaze_depth_camera[:, 2:3],
                                     ), axis=1)
    idx_g_l_r_w_i = idx_g_l_r_w_i.astype(np.int64)
    time_g_l_r_w_i =  np.concatenate((best_pairs_gaze_left[:, 1:2], 
                                    best_pairs_gaze_left[:, 3:4],
                                    best_pairs_gaze_right[:, 3:4],
                                    best_pairs_gaze_world[:, 3:4],
                                    best_pairs_gaze_imu[:, 3:4],
                                    best_pairs_gaze_events[:, 3:4],
                                    best_pairs_gaze_depth_camera[:, 3:4],
                                    ), axis=1)
    
    # Discard when there is a gap bigger than what is expected from sensors frequency
    valid_mask = (best_pairs_gaze_left[:, -1] < l_r_res) * (best_pairs_gaze_right[:, -1] < l_r_res) * (best_pairs_gaze_world[:, -1] < w_res)
    
    idx_g_l_r_w_i = idx_g_l_r_w_i[valid_mask]
    time_g_l_r_w_i = time_g_l_r_w_i[valid_mask]

    #only keep the gaze_df rows that has gaze_timestamps_rel matching
    #FIXME this might be wrong, maybe use timestamps instead of indices (but then we need to convert them to system time)
    gaze_df = gaze_df.iloc[idx_g_l_r_w_i[:, 0]]

    #create a new dataframe with all the devices timestamps and the corresponding frames
    gaze_df['left_eye_idx'] = idx_g_l_r_w_i[:, 1]
    gaze_df['right_eye_idx'] = idx_g_l_r_w_i[:, 2]
    gaze_df['world_idx'] = idx_g_l_r_w_i[:, 3]
    gaze_df['imu_idx'] = idx_g_l_r_w_i[:, 4]
    gaze_df['events_idx'] = idx_g_l_r_w_i[:, 5]
    gaze_df['depth_camera_idx'] = idx_g_l_r_w_i[:, 6]

    gaze_df["timestamp [ns]"] = gaze_df["timestamp [ns]"] + get_offset_from_local_csv(recording_id)/scale_factor #FIXME: check if - or +
    gaze_df = add_events_from_csv_to_df(recording_id, gaze_df)
    gaze_df.to_csv(recording_folder + "/full_df.csv", index=False)

#correspond_cameras_and_gaze("50bd29b9-0ef2-425c-8f78-b9275ce3f32f")
#print(get_offset("82e52db9-1cac-495d-99dd-bebb51c393a0"))
