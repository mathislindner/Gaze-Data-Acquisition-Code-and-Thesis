import os
import pyrealsense2 as rs
import numpy as np
import cv2
from  constants import *
import time
#create a script that tests different sizes of the depth and rgb camera to check how much storage we would need
#save depth as numpy 
#save rgb as png

def record_depth_and_rgb(rgb_size, depth_size, rec_time = 10):
    print("recording depth and rgb with rgb size: " + str(rgb_size) + " and depth size: " + str(depth_size) + " for " + str(time) + " seconds")
    path = os.path.join(recordings_folder, "testing_sizes", "rgb_size_" + str(rgb_size[0]) + "x" + str(rgb_size[1]) + "_depth_size_" + str(depth_size[0]) + "x" + str(depth_size[1]))
    if not os.path.exists(path):
        os.mkdir(path)

    config = rs.config()
    config.enable_stream(rs.stream.depth, depth_size[0], depth_size[1], rs.format.z16, 30)
    config.enable_stream(rs.stream.color, rgb_size[0], rgb_size[1], rs.format.bgr8, 15)
    config.enable_record_to_file(os.path.join(path, "rec.bag"))
    pipeline = rs.pipeline()

    # Start streaming
    profile = pipeline.start(config)

    depth_images = []
    #start timer
    start_time = time.time()
    while time.time() - start_time < rec_time:
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            continue
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        #add depth image to list
        depth_images.append(depth_image)
        #save color image
        cv2.imwrite(os.path.join(path, "color" + ".png"), color_image)
    #convert depth images to numpy array
    depth_images = np.array(depth_images)
    #save depth images
    np.save(os.path.join(path, "depth.npy"), depth_images)
    # Stop streaming
    pipeline.stop()

#record_depth_and_rgb((640,480), (640,480), rec_time = 10)
record_depth_and_rgb((1280,720), (640,480), rec_time = 10)
#record_depth_and_rgb((1920,1080), (1280,720), rec_time = 10)