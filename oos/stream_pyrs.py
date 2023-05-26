#stream pyreal sense camera to window
import pyrealsense2 as rs
import cv2
import numpy as np

from laser_detector import get_2D_laser_position, get_3D_laser_position_relative_to_depth_camera

pipeline = rs.pipeline()
config = rs.config()
color_sensor = color_sensor = config.resolve(rs.pipeline_wrapper(pipeline)).get_device().query_sensors()[1]
color_sensor.set_option(rs.option.enable_auto_exposure, True)
#color_sensor.set_option(rs.option.exposure, value = 350)
#color_sensor.set_option(rs.option.sharpness, value = 50)
#color_sensor.set_option(rs.option.brightness, value = 5)

config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
pipeline.start(config)
j = 0

try:
    while True:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()

        if not color_frame or not depth_frame:
            break

        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())
        #find laser
        laser_position_2D = get_2D_laser_position(color_image)
        #show laser
        cv2.circle(color_image, laser_position_2D, 5, (0, 0, 255), 3)
        #show image
        cv2.imshow('RealSense', color_image)
        cv2.waitKey(1)

except Exception as e:
    print(e)
finally:
    pipeline.stop()
