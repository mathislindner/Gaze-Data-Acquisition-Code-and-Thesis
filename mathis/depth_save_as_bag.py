import pyrealsense2 as rs
import numpy as np
import os
from constants import *

recording_folder = os.path.join(recordings_folder,"test")

pipeline = rs.pipeline()

config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_record_to_file(os.path.join(recording_folder, "rec.bag"))


pipeline.start(config)
i = 0

try:
    while True:
        pass
    #while True:
        #frames = pipeline.wait_for_frames()
        #color_frame = frames.get_color_frame()
        #depth_frame = frames.get_depth_frame()
        
        #color_filename = os.path.join(recording_folder, "color", str(i) + ".png")
        #depth_filename = os.path.join(recording_folder, "depth", str(i) + ".png")
        #rs.save_to_png(color_filename, color_frame)
        #rs.save_to_png(depth_filename, depth_frame)
        #i += 1
        # Save color frame as a PNG file
        #color_image = np.asanyarray(color_frame.get_data())
        #color_image = np.flip(color_image, axis=2)  # Convert from BGR to RGB
        #rs.save_to_png(color_filename, color_frame)

        # Save depth frame as a PNG file
        #depth_image = np.asanyarray(depth_frame.get_data())
        #rs.save_to_png(depth_filename, depth_frame)

except KeyboardInterrupt:
    pipeline.stop()
