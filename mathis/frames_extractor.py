import os
import subprocess
import json
import numpy as np
from file_helper import decode_timestamp
from constants import *


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

#extract_frames("82e52db9-1cac-495d-99dd-bebb51c393a0")
