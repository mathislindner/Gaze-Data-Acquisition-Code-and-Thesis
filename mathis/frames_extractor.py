import os
import subprocess
import json
import numpy as np
from file_helper import decode_timestamp
from constants import *
import cv2
import pyrealsense2 as rs
import pandas as pd


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


#save the frames to png, save the timestamps to a csv file corresponding to the frame number
def extract_depth_camera_frames(recording_id):
    recording_folder = os.path.join(recordings_folder, str(recording_id))
    if not os.path.exists(os.path.join(recording_folder, "realsensed435.bag")):
        print("no realsense bag file")
        return
    rgb_images_path = os.path.join(recording_folder, "rgb_pngs")
    depth_images_path = os.path.join(recording_folder, "depth_pngs")

    #check if the depth camera frames have already been extracted
    if os.path.exists(rgb_images_path) and os.path.exists(depth_images_path) and os.path.exists(os.path.join(recording_folder, "depth_camera_timestamps.npy")):
        print("depth camera frames already extracted")
        return
    try:
        os.mkdir(depth_images_path)
        os.mkdir(rgb_images_path)
    except:
        print("could not create new folders for depth camera frames")
    
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_device_from_file(os.path.join(recording_folder, "realsensed435.bag"), repeat_playback=False)
    profile = pipeline.start(config)
    playback = profile.get_device().as_playback()
    playback.set_real_time(False)
    
    i = 0

    timestamps = []
    depth_images_list = []
    #while the bag file is not finished
    j = 0
    while True:
        try:
            frames = pipeline.wait_for_frames()
            playback.pause() #added this because else the frames are not saved correctly: https://stackoverflow.com/questions/58482414/frame-didnt-arrived-within-5000-while-reading-bag-file-pyrealsense2
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

            cv2.imwrite(os.path.join(rgb_images_path, str(i) + ".png"), color_image)
            cv2.imwrite(os.path.join(depth_images_path, str(i) + ".png"), depth_image)
            depth_images_list.append(depth_image)
            
            #add the timestamp to the list and convert from ms to ns
            timestamps.append(frames.get_timestamp())
            i += 1
            playback.resume()
    #save the depth images to a npz
    np.savez_compressed(os.path.join(recording_folder, "depth_array"), np.array(depth_images_list))
    #convert timestamps to ns 
    timestamps = [x * 1e6 for x in timestamps]
    # convert timestamps to uint64
    timestamps = np.array(timestamps).astype(np.uint64)
    timestamps.tofile(os.path.join(recording_folder, "depth_camera_timestamps.npy"))
    #save the timestamps to a numpy array
    #np.save(os.path.join(recording_folder, "depth_camera_timestamps"), timestamps)
    #stop the pipeline
    pipeline.stop()

#undistort world images according to the calibration parameters
def undistort_world_camera(recording_id):
    recording_folder = os.path.join(recordings_folder, str(recording_id))

    distorted_images_path = os.path.join(recording_folder, camera_folders[2])
    scene_camera_path = os.path.join(recording_folder, "scene_camera.json")
    undistorted_images_path = os.path.join(recording_folder, camera_folders[2] + "_undistorted")

    #read_json
    with open(scene_camera_path) as f:
        data = json.load(f)
    #get the camera matrix and distortion coefficients
    camera_matrix = np.array(data["camera_matrix"])
    distortion_coefficients = np.array(data["dist_coefs"])

    #check if the undistorted images have already been extracted
    if os.path.exists(undistorted_images_path):
        print("undistorted images already extracted")
        return
    
    os.mkdir(undistorted_images_path)

    #undistort the images
    for image_path in os.listdir(distorted_images_path):
        image = cv2.imread(os.path.join(distorted_images_path, image_path))
        undistorted_image = cv2.undistort(image, camera_matrix, distortion_coefficients)
        cv2.imwrite(os.path.join(undistorted_images_path, image_path), undistorted_image)
    return
    #undistort the gaze data
    undistorted_points = cv2.undistortPoints(points.reshape(-1, 2), camera_matrix, 
                                             distortion_coefficients)
    example_points_undist = example_points_undist.reshape(-1, 2)
    

#undistort_images("3026e32b-3e15-40a7-9a46-8e8512cdfe5c")
#extract_depth_camera_frames("test")
#extract_frames("3026e32b-3e15-40a7-9a46-8e8512cdfe5c")
