import os
import subprocess
import json
import numpy as np
from file_helper import decode_timestamp
from constants import *
import cv2
import pyrealsense2 as rs


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
    args = ['ffmpeg', '-i', filename, '-vsync', '0', f'{os.path.join(out_dir, "%d.png")}']  #'-frame_pts', 'true' # '-skip_frame', 'nokey'
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
            print(f'Folder {output_folder} already exists. Skipping curation.')
            return

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


def extract_depth_camera_frames(recording_id):
    recording_folder = os.path.join(recordings_folder, str(recording_id))
    #make sure that timestamps are in ns and not ms
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_device_from_file(os.path.join(recording_folder, "realsensed435.bag"), repeat_playback=False)
    profile = pipeline.start(config)

    #save the frames to png, save the timestamps to a csv file corresponding to the frame number
    i = 0

    timestamps = []
    #while the bag file is not finished
    while True:
        try:
            frames = pipeline.wait_for_frames()
        except:
            break
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()
        if not color_frame or not depth_frame:
            continue
        else:
            #save the frames to png
            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())

            cv2.imwrite(os.path.join(recording_folder, "rgb_image", str(i) + ".png"), color_image)
            cv2.imwrite(os.path.join(recording_folder, "depth_image", str(i) + ".png"), depth_image)
            

            #add the timestamp to the list and convert from ms to ns
            timestamps.append(frames.get_timestamp() * 1000)
            i += 1

    #save the timestamps to a csv file
    timestamps_df = pd.DataFrame(timestamps)
    timestamps_df.to_csv(os.path.join(recording_folder, "depth_camera_timestamps.csv"), index=False)

    #stop the pipeline
    pipeline.stop()

#extract_frames("82e52db9-1cac-495d-99dd-bebb51c393a0")
