#record with changed exposure, save recording and replay it after
#add path
import sys
sys.path.append("/scratch_net/snapo/mlindner/docs/gaze_data_acquisition")
import pyrealsense2 as rs
import numpy as np
import cv2
import os
from time import sleep
from dependencies.constants import *
from dependencies.recording_devices import depthAndRgbCameras
import shutil
#color_sensor = profile.get_device().query_sensors()[1]
#color_sensor.set_option(rs.option.enable_auto_exposure, False)
#color_sensor.set_option(rs.option.exposure, value = 350)
#color_sensor.set_option(rs.option.sharpness, value = 50)
#color_sensor.set_option(rs.option.brightness, value = 5)


def rec():
    #create recording dir
    if not os.path.exists(os.path.join(recordings_folder, "test")):
        os.mkdir(os.path.join(recordings_folder, "test"))
    else:
        #delete old recording
        bag_file = os.path.join(recordings_folder, "test", "realsensed435.bag")
        if os.path.exists(bag_file):
            os.remove(bag_file)


    depth_and_rgb_cameras = depthAndRgbCameras()
    depth_and_rgb_cameras.start_recording("test")
    input("press enter to stop recording")
    depth_and_rgb_cameras.stop_recording()
    sleep(1)

def playback():
    #replay
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_device_from_file(os.path.join(recordings_folder, "test", "realsensed435.bag"), repeat_playback = False)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    pipeline.start(config)


    while True:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue
        color_image = np.asanyarray(color_frame.get_data())
        cv2.imshow("color", color_image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            pipeline.stop()
            cv2.destroyAllWindows()

from dependencies.frames_extractor import extract_depth_camera_frames
def playback_with_settings():
    #delete every file except the bag file
    recording_folder = os.path.join(recordings_folder, "test")
    for file in os.listdir(recording_folder):
        if file != "realsensed435.bag":
            shutil.rmtree(os.path.join(recording_folder, file), ignore_errors=True)
    recording_id = 'test'
    extract_depth_camera_frames(recording_id)
    '''
    recording_folder = os.path.join(recordings_folder, str(recording_id))
    if not os.path.exists(os.path.join(recording_folder, "realsensed435.bag")):
        print("no realsense bag file")
        return
    rgb_images_path = os.path.join(recording_folder, "rgb_pngs")
    depth_images_path = os.path.join(recording_folder, "depth_pngs")
    try:
        os.mkdir(depth_images_path)
        os.mkdir(rgb_images_path)
    except:
        print("could not create new folders for depth camera frames")
    
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_device_from_file(os.path.join(recording_folder, "realsensed435.bag"), repeat_playback=False)
    pipeline_wrapper = rs.pipeline_wrapper(pipeline)
    pipeline_profile = config.resolve(pipeline_wrapper)
    device = pipeline_profile.get_device()
    

    profile = pipeline.start(config)
    playback = profile.get_device().as_playback()
    playback.set_real_time(False)
    
    profile = pipeline.get_active_profile()
    depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
    depth_intrinsics = depth_profile.get_intrinsics()
    color_profile = rs.video_stream_profile(profile.get_stream(rs.stream.color))
    color_intrinsics = color_profile.get_intrinsics()
    depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()
    print('worked til here')

    
    i = 0
    align_to = rs.stream.color
    align = rs.align(align_to)

    timestamps = []
    depth_images_list = []
    #while the bag file is not finished
    while True:
        try:
            frames = pipeline.wait_for_frames()
            playback.pause() #added this because else the frames are not saved correctly: https://stackoverflow.com/questions/58482414/frame-didnt-arrived-within-5000-while-reading-bag-file-pyrealsense2
        except:
            break

        aligned_frames = align.process(frames)

        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        aligned_depth_frame = aligned_frames.get_depth_frame()
        aligned_color_frame = aligned_frames.get_color_frame()

        if not color_frame or not depth_frame or not aligned_depth_frame or not aligned_color_frame:
            return None
        else:
            #save the frames to png
            color_image = np.asanyarray(aligned_color_frame.get_data()) 
            depth_image = np.asanyarray(aligned_depth_frame.get_data()) * depth_scale

            cv2.imwrite(os.path.join(rgb_images_path, str(i) + ".png"), color_image)
            cv2.imwrite(os.path.join(depth_images_path, str(i) + ".png"), depth_image)
            depth_images_list.append(depth_image)
            
            #add the timestamp to the list and convert from ms to ns
            timestamps.append(frames.get_timestamp())
            i += 1
            playback.resume()
            '''
    
#playback()
playback_with_settings()